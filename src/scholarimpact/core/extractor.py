"""
Author extraction module for Google Scholar profiles.

This module provides the AuthorExtractor class for extracting
author publications and metadata from Google Scholar.
"""

import json
import logging
import os
import time
from datetime import datetime

from scholarly import scholarly

logger = logging.getLogger(__name__)


class AuthorExtractor:
    """Extract author data from Google Scholar."""

    def __init__(self, delay=2):
        """Initialize the extractor.

        Args:
            delay: Delay between requests in seconds
        """
        self.delay = delay

    def extract(self, author_id, max_papers=None, output_file=None, output_dir="data"):
        """Extract author publications from Google Scholar.

        Args:
            author_id: Google Scholar author ID
            max_papers: Maximum number of papers to analyze (None for all)
            output_file: Path to output file (if None, defaults to data/author.json)
            output_dir: Output directory for data files

        Returns:
            Dictionary containing author data and publications
        """
        # Set default output file
        if output_file is None:
            output_file = os.path.join(output_dir, "author.json")

        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        # Store results
        results = []
        author_data = {}

        try:
            logger.info(f"Fetching author profile for ID: {author_id}")

            # Search for author by ID
            author = scholarly.search_author_id(author_id)

            # Fill in author details
            author = scholarly.fill(
                author, sections=["basics", "indices", "coauthors", "publications"]
            )

            # Extract author information
            author_name = author.get("name", "Unknown")
            author_affiliation = author.get("affiliation", "Unknown")
            total_citations = author.get("citedby", 0)
            interests = author.get("interests", [])
            email_domain = author.get("email_domain", "")
            homepage = author.get("homepage", "")
            hindex = author.get("hindex", 0)
            i10index = author.get("i10index", 0)
            hindex5y = author.get("hindex5y", 0)
            i10index5y = author.get("i10index5y", 0)

            # Construct Google Scholar profile URL
            scholar_profile_url = f"https://scholar.google.com/citations?user={author_id}"

            logger.info(f"Author: {author_name}")
            logger.info(f"Total Citations: {total_citations}")

            publications = author.get("publications", [])

            # Limit papers if specified
            if max_papers:
                publications = publications[:max_papers]

            # Process each publication
            for i, pub in enumerate(publications, 1):
                logger.info(f"Processing publication {i}/{len(publications)}")

                # Fill publication details
                try:
                    pub_filled = scholarly.fill(pub, sections=["bib", "citations"])
                    pub = pub_filled
                except Exception as e:
                    logger.warning(f"Could not fill publication details: {e}")

                # Basic publication info
                title = pub.get("bib", {}).get("title", "Unknown Title")
                year = pub.get("bib", {}).get("pub_year", "Unknown")
                num_citations = pub.get("num_citations", 0)
                authors = pub.get("bib", {}).get("author", "Unknown")

                # Get citedby_url and cites_id
                citedby_url = pub.get("citedby_url", "")
                if citedby_url and not citedby_url.startswith("http"):
                    citedby_url = f"https://scholar.google.com{citedby_url}"

                cites_id = pub.get("cites_id", [])
                if isinstance(cites_id, list):
                    cites_id_str = ",".join(cites_id) if cites_id else ""
                else:
                    cites_id_str = str(cites_id) if cites_id else ""

                # Get publication URL
                pub_url = pub.get("pub_url", "")
                if not pub_url:
                    pub_url = pub.get("eprint_url", "")
                if not pub_url and "author_pub_id" in pub:
                    pub_url = f"https://scholar.google.com/citations?view_op=view_citation&hl=en&user={author_id}&citation_for_view={pub.get('author_pub_id', '')}"

                # Create result record
                result_record = {
                    "title": title,
                    "authors": authors,
                    "year": year,
                    "total_citations": num_citations,
                    "google_scholar_url": pub_url,
                    "citedby_url": citedby_url,
                    "cites_id": cites_id_str,
                    "analysis_date": datetime.now().isoformat(),
                }

                results.append(result_record)

                # Delay between requests
                if i < len(publications):
                    time.sleep(self.delay)

            # Prepare complete data structure
            author_data = {
                "scholar_id": author_id,
                "name": author_name,
                "affiliation": author_affiliation,
                "total_citations": total_citations,
                "interests": interests,
                "email_domain": email_domain,
                "homepage": homepage,
                "hindex": hindex,
                "i10index": i10index,
                "hindex5y": hindex5y,
                "i10index5y": i10index5y,
                "scholar_profile_url": scholar_profile_url,
                "total_publications": len(publications),
                "analysis_date": datetime.now().isoformat(),
                "publications_analyzed": len(results),
                "articles": results,
            }

            # Write to JSON file
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(author_data, f, indent=2, ensure_ascii=False)

            logger.info(
                f"Successfully wrote author data with {len(results)} articles to {output_file}"
            )

        except Exception as e:
            logger.error(f"Error: {e}")
            raise

        return author_data
