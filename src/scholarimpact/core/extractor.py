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
from typing import Dict, List, Optional

import pyalex
import requests
from pyalex import Works
from scholarly import scholarly

logger = logging.getLogger(__name__)


class AuthorExtractor:
    """Extract author data from Google Scholar."""

    def __init__(self, delay=2, use_openalex=True, openalex_email=None, use_altmetric=True):
        """Initialize the extractor.

        Args:
            delay: Delay between requests in seconds
            use_openalex: Whether to use OpenAlex enrichment (default: True)
            openalex_email: Email for OpenAlex API (optional, for higher rate limits)
            use_altmetric: Whether to use Altmetric enrichment (default: True, requires OpenAlex)
        """
        self.delay = delay
        self.use_openalex = use_openalex
        self.openalex_email = openalex_email
        self.use_altmetric = use_altmetric and use_openalex  # Altmetric requires OpenAlex
        
        # Configure pyalex if OpenAlex is enabled
        if use_openalex:
            if openalex_email:
                pyalex.config.email = openalex_email
                logger.info(f"OpenAlex configured with email: {openalex_email}")
            else:
                logger.info("OpenAlex enabled with default rate limits")
        
        if self.use_altmetric:
            logger.info("Altmetric enrichment enabled")

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
                
                # Enrich with OpenAlex data if enabled
                if self.use_openalex:
                    openalex_data = self._enrich_with_openalex(title, year)
                    if openalex_data:
                        result_record.update(openalex_data)
                        
                        # Enrich with Altmetric data if enabled and OpenAlex found identifiers
                        if self.use_altmetric and 'openalex_ids' in result_record:
                            altmetric_data = self._enrich_with_altmetric(result_record['openalex_ids'])
                            if altmetric_data:
                                result_record.update(altmetric_data)

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
    
    def _enrich_with_openalex(self, title: str, year: str) -> Optional[Dict]:
        """Enrich publication data with OpenAlex information.
        
        Args:
            title: Publication title
            year: Publication year
            
        Returns:
            Dictionary with OpenAlex data or None if not found
        """
        try:
            # Search for the work by title and year
            search_query = f'"{title}"'
            if year and year != "Unknown":
                search_query += f' AND publication_year:{year}'
            
            # Use pyalex to search
            works = Works().filter(title_and_abstract={"search": title}).get()
            
            if not works or len(works) == 0:
                logger.debug(f"No OpenAlex match found for: {title}")
                return None
            
            # Get the best match (first result)
            work = works[0]
            
            # Extract relevant fields with openalex_ prefix
            openalex_data = {
                "openalex_ids": work.get("ids", {}),  # Contains openalex, doi, mag, pmid, etc.
                "openalex_type": work.get("type"),
                "openalex_citation_normalized_percentile": work.get("citation_normalized_percentile"),
                "openalex_cited_by_percentile_year": work.get("cited_by_percentile_year", {}).get("value") if work.get("cited_by_percentile_year") else None,
                "openalex_fwci": work.get("fwci"),  # Field-Weighted Citation Impact
                "openalex_cited_by_count": work.get("cited_by_count"),
                "openalex_primary_topic": work.get("primary_topic", {}).get("display_name") if work.get("primary_topic") else None,
                "openalex_domain": work.get("primary_topic", {}).get("domain", {}).get("display_name") if work.get("primary_topic") and work.get("primary_topic").get("domain") else None,
                "openalex_field": work.get("primary_topic", {}).get("field", {}).get("display_name") if work.get("primary_topic") and work.get("primary_topic").get("field") else None,
                "openalex_subfield": work.get("primary_topic", {}).get("subfield", {}).get("display_name") if work.get("primary_topic") and work.get("primary_topic").get("subfield") else None,
            }
            
            # Clean up None values
            openalex_data = {k: v for k, v in openalex_data.items() if v is not None}
            
            logger.debug(f"OpenAlex enrichment successful for: {title}")
            return openalex_data
            
        except Exception as e:
            logger.warning(f"Error enriching with OpenAlex for '{title}': {e}")
            return None
    
    def _enrich_with_altmetric(self, ids: Dict) -> Optional[Dict]:
        """Enrich publication data with Altmetric information.
        
        Args:
            ids: Dictionary of identifiers from OpenAlex (doi, pmid, etc.)
            
        Returns:
            Dictionary with Altmetric data or None if not found
        """
        if not ids:
            return None
        
        # Try DOI first, then PMID
        doi = ids.get('doi', '').replace('https://doi.org/', '') if ids.get('doi') else None
        pmid = ids.get('pmid', '').replace('https://pubmed.ncbi.nlm.nih.gov/', '') if ids.get('pmid') else None
        
        altmetric_url = None
        if doi:
            altmetric_url = f"https://api.altmetric.com/v1/doi/{doi}"
        elif pmid:
            altmetric_url = f"https://api.altmetric.com/v1/pmid/{pmid}"
        else:
            return None
        
        try:
            # Make request to Altmetric API
            response = requests.get(altmetric_url, timeout=10)
            
            if response.status_code == 404:
                logger.debug(f"No Altmetric data found for DOI: {doi} or PMID: {pmid}")
                return None
            
            response.raise_for_status()
            data = response.json()
            
            # Extract relevant fields with altmetric_ prefix
            altmetric_data = {
                "altmetric_score": data.get("score"),
                "altmetric_cited_by_wikipedia_count": data.get("cited_by_wikipedia_count"),
                "altmetric_cited_by_patents_count": data.get("cited_by_patents_count"),
                "altmetric_cited_by_accounts_count": data.get("cited_by_accounts_count"),
                "altmetric_cited_by_posts_count": data.get("cited_by_posts_count"),
                "altmetric_scopus_subjects": data.get("scopus_subjects"),
                "altmetric_readers": data.get("readers"),
                "altmetric_readers_count": data.get("readers_count"),
                "altmetric_images": data.get("images"),
                "altmetric_details_url": data.get("details_url"),
            }
            
            # Clean up None values
            altmetric_data = {k: v for k, v in altmetric_data.items() if v is not None}
            
            logger.debug(f"Altmetric enrichment successful for DOI: {doi} or PMID: {pmid}")
            return altmetric_data
            
        except requests.RequestException as e:
            logger.warning(f"Error fetching Altmetric data: {e}")
            return None
        except Exception as e:
            logger.warning(f"Error processing Altmetric data: {e}")
            return None
