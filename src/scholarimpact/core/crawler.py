"""
Google Scholar Citation Crawler Module

This module provides the CitationCrawler class for extracting
detailed citation information from Google Scholar.
"""

import argparse
import json
import logging
import random
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlparse

import pandas as pd
import pyalex
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Constants
ROBOT_KW = ["unusual traffic from your computer network", "not a robot", "captcha"]
BASE_URL = "https://scholar.google.com"
CITATION_URL_PATTERN = "https://scholar.google.com/scholar?cites={}&hl=en"

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class CitationCrawler:
    def __init__(
        self,
        headless=False,
        delay_range=(5, 10),
        use_openalex=True,
        openalex_email=None,
        use_scholar_fallback=True,
    ):
        """Initialize the crawler with Chrome driver."""
        self.driver = None
        self.headless = headless
        self.delay_range = delay_range
        self.citations_data = []
        self.cites_id = None
        self.use_openalex = use_openalex
        self.use_scholar_fallback = use_scholar_fallback

        # Configure PyAlex
        if use_openalex:
            if openalex_email:
                pyalex.config.email = openalex_email
                logger.info(f"Configured OpenAlex with email: {openalex_email}")
            else:
                logger.info(
                    "Using OpenAlex without email (consider adding --openalex-email for higher rate limits)"
                )

    def setup_driver(self):
        """Setup Chrome WebDriver with appropriate options."""
        logger.info("Setting up Chrome WebDriver...")
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument("--headless")

        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

    def wait_for_captcha_resolution(self):
        """Wait for user to manually solve CAPTCHA."""
        logger.warning("CAPTCHA detected! Please solve it manually in the browser.")
        input("Press Enter after solving the CAPTCHA to continue...")

    def check_for_robot_detection(self):
        """Check if Google has detected automated behavior."""
        try:
            page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
            if any(kw in page_text for kw in ROBOT_KW):
                return True
        except:
            pass
        return False

    def random_delay(self):
        """Add random delay to avoid detection."""
        delay = random.uniform(self.delay_range[0], self.delay_range[1])
        logger.debug(f"Waiting {delay:.2f} seconds...")
        time.sleep(delay)

    def extract_citation_id_from_url(self, url):
        """Extract citation ID from a Google Scholar article URL."""
        try:
            # Parse the URL
            parsed = urlparse(url)

            # Check if it's a citation view URL
            if "view_citation" in url:
                query_params = parse_qs(parsed.query)
                citation_for_view = query_params.get("citation_for_view", [None])[0]
                if citation_for_view:
                    # Extract the citation ID (part after the colon)
                    return citation_for_view.split(":")[-1]

            # Check if it's already a cites URL
            if "cites=" in url:
                query_params = parse_qs(parsed.query)
                return query_params.get("cites", [None])[0]

        except Exception as e:
            logger.error(f"Error extracting citation ID from URL: {e}")

        return None

    def get_citations_url(self, article_url_or_id):
        """Convert article URL or ID to citations URL."""
        # Clean up the input - remove any parameter name artifacts
        if "=" in article_url_or_id and not article_url_or_id.startswith("http"):
            # This looks like a malformed parameter, try to extract the actual URL
            parts = article_url_or_id.split("=", 1)
            if len(parts) > 1:
                article_url_or_id = parts[1]
                logger.debug(f"Cleaned input from parameter artifact: {article_url_or_id}")

        # If it's already a citation ID (just numbers)
        if not article_url_or_id.startswith("http"):
            return CITATION_URL_PATTERN.format(article_url_or_id)

        # If it's already a citations URL (contains 'cites=' parameter)
        if "cites=" in article_url_or_id:
            return article_url_or_id

        # Try to extract citation ID from URL
        citation_id = self.extract_citation_id_from_url(article_url_or_id)
        if citation_id:
            return CITATION_URL_PATTERN.format(citation_id)

        logger.error("Could not extract citation ID from the provided URL")
        return None

    def parse_citation_element(self, element):
        """Parse a single citation element from Google Scholar."""
        citation_data = {
            "citing_paper_title": "Unknown",
            "citing_authors": "Unknown",
            "citing_year": "Unknown",
            "citing_venue": "Unknown",
            "citing_paper_url": "Unknown",
            "pdf_url": None,
            "scholar_profiles": [],
            "citations_count": 0,
            "citing_authors_details": [],
        }

        # If we're working with gs_ri elements, find the parent gs_r
        if "gs_ri" in element.get_attribute("class"):
            try:
                parent = element.find_element(By.XPATH, "./parent::div[@class='gs_r gs_or gs_scl']")
                if parent:
                    element = parent
            except:
                pass

        try:
            # Get the title and URL
            title_element = element.find_element(By.CSS_SELECTOR, "h3.gs_rt a")
            citation_data["citing_paper_title"] = title_element.text.strip()
            citation_data["citing_paper_url"] = title_element.get_attribute("href")
        except NoSuchElementException:
            try:
                # Sometimes title is without link
                title_element = element.find_element(By.CSS_SELECTOR, "h3.gs_rt")
                citation_data["citing_paper_title"] = title_element.text.strip()
            except NoSuchElementException:
                pass

        # Remove "[CITATION] " prefix if present
        if citation_data["citing_paper_title"].startswith("[CITATION] "):
            citation_data["citing_paper_title"] = citation_data["citing_paper_title"][
                11:
            ]  # Remove "[CITATION] " (11 characters)

        try:
            # Get author info, venue, year from the gs_a div
            author_div = element.find_element(By.CSS_SELECTOR, "div.gs_a")
            author_info_text = author_div.text

            # Parse author info (format: "Authors - Venue, Year - Publisher")
            parts = author_info_text.split(" - ")
            if len(parts) >= 1:
                citation_data["citing_authors"] = parts[0].strip()

            if len(parts) >= 2:
                venue_year = parts[1].strip()
                # Try to extract year
                year_match = re.search(r"\b(19|20)\d{2}\b", venue_year)
                if year_match:
                    citation_data["citing_year"] = int(year_match.group())
                    # Remove year from venue
                    venue = re.sub(r",?\s*\b(19|20)\d{2}\b", "", venue_year).strip().rstrip(",")
                    citation_data["citing_venue"] = venue if venue else "Unknown"
                else:
                    citation_data["citing_venue"] = venue_year

            # Extract author profile URLs
            author_links = author_div.find_elements(By.TAG_NAME, "a")
            scholar_profiles = []
            for link in author_links:
                href = link.get_attribute("href")
                if href and "citations?user=" in href:
                    author_name = link.text.strip()
                    scholar_profiles.append({"name": author_name, "profile_url": href})

            citation_data["scholar_profiles"] = scholar_profiles

        except NoSuchElementException:
            pass

        # Note: Snippet extraction removed - we focus on author profiles instead

        try:
            # Get PDF link if available
            pdf_element = element.find_element(By.CSS_SELECTOR, "div.gs_ggs a")
            citation_data["pdf_url"] = pdf_element.get_attribute("href")
        except NoSuchElementException:
            pass

        try:
            # Get citation count for this citing paper
            cited_by_text = element.find_element(
                By.XPATH, ".//a[contains(text(), 'Cited by')]"
            ).text
            citations_match = re.search(r"Cited by (\d+)", cited_by_text)
            if citations_match:
                citation_data["citations_count"] = int(citations_match.group(1))
        except NoSuchElementException:
            pass

        # Get OpenAlex data for this citing paper
        if self.use_openalex and citation_data["citing_paper_title"] != "Unknown":
            try:
                citation_data, openalex_affiliations = self.get_openalex_data(citation_data)
                # Convert OpenAlex data to citing_authors_details format
                if openalex_affiliations:
                    citing_authors_details = []
                    for author in openalex_affiliations:
                        author_details = {
                            "name": author.get("name", "Unknown"),
                            "affiliation": author.get("affiliation", "Unknown"),
                            "institution_display_name": author.get(
                                "institution_display_name", "Unknown"
                            ),
                            "country": author.get("country", "Unknown"),
                            "openalex_author_id": author.get("openalex_author_id"),
                            "openalex_institution_id": author.get(
                                "openalex_institution_id", "Unknown"
                            ),
                            "source": "openalex",
                        }

                        # If affiliation or country is Unknown, try to get more details from author API
                        if (
                            author_details["affiliation"] == "Unknown"
                            or author_details["country"] == "Unknown"
                        ) and author_details["openalex_author_id"]:

                            enhanced_details = self.get_openalex_author_details(
                                author_details["openalex_author_id"]
                            )
                            if enhanced_details:
                                # Update with enhanced details if they're not Unknown
                                if (
                                    enhanced_details["affiliation"] != "Unknown"
                                    and author_details["affiliation"] == "Unknown"
                                ):
                                    author_details["affiliation"] = enhanced_details["affiliation"]
                                if (
                                    enhanced_details["institution_display_name"] != "Unknown"
                                    and author_details["institution_display_name"] == "Unknown"
                                ):
                                    author_details["institution_display_name"] = enhanced_details[
                                        "institution_display_name"
                                    ]
                                if (
                                    enhanced_details["country"] != "Unknown"
                                    and author_details["country"] == "Unknown"
                                ):
                                    author_details["country"] = enhanced_details["country"]
                                # Update institution ID if we got a new one
                                if (
                                    enhanced_details.get("institution_id")
                                    and author_details["openalex_institution_id"] == "Unknown"
                                ):
                                    author_details["openalex_institution_id"] = enhanced_details[
                                        "institution_id"
                                    ]

                                logger.debug(
                                    f"Enhanced author details from API for {author_details['name']}: {enhanced_details['affiliation']} ({enhanced_details['country']})"
                                )

                        citing_authors_details.append(author_details)

                    citation_data["citing_authors_details"] = citing_authors_details
                    logger.debug(
                        f"Added OpenAlex author details for: {citation_data['citing_paper_title']}"
                    )
            except Exception as e:
                logger.debug(
                    f"Could not get OpenAlex affiliations for '{citation_data['citing_paper_title']}': {e}"
                )

        # Note: Scholar profile extraction is now done in crawl_citations_page after all elements are parsed
        # This avoids stale element reference issues when navigating away from the page

        return citation_data

    def get_country_from_email_domain(self, email_domain):
        """
        Extract country code from email domain using educational patterns and TLD mapping.

        Args:
            email_domain: Email domain (e.g., 'mit.edu', 'ox.ac.uk')

        Returns:
            ISO country code (e.g., 'US', 'GB') or 'Unknown'
        """
        if not email_domain:
            return "Unknown"

        try:
            # Import domain mappings
            from .utils import get_country_code_from_tld

            # Clean domain
            domain = email_domain.lower().strip()
            if domain.startswith("www."):
                domain = domain[4:]

            # Check for specific Canadian domains first (special case)
            # These need to be checked before general .edu pattern
            canadian_domains = ["toronto.edu"]
            for cdn_domain in canadian_domains:
                if cdn_domain in domain:
                    return "CA"

            # TLD mapping using the centralized method
            country_code = get_country_code_from_tld(domain)
            if country_code:
                return country_code

            logger.debug(f"Could not extract country from domain {email_domain}: {e}")
            return "Unknown"

        except Exception as e:
            logger.debug(f"Could not extract country from domain {email_domain}: {e}")

        return "Unknown"

    def extract_scholar_profile_affiliation(self, profile_url):
        """
        Extract author's affiliation from their Google Scholar profile.
        Uses the existing browser instance to avoid detection.

        Args:
            profile_url: Google Scholar profile URL

        Returns:
            Dictionary with affiliation information
        """
        try:
            logger.debug(f"Extracting affiliation from Scholar profile: {profile_url}")

            # Navigate to profile
            self.driver.get(profile_url)
            self.random_delay()

            # Check for robot detection
            if self.check_for_robot_detection():
                logger.warning("Robot detection on Scholar profile page")
                return None

            # Wait for profile to load
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "gsc_prf"))
                )
            except TimeoutException:
                logger.debug(f"Timeout loading Scholar profile: {profile_url}")
                return None

            # Extract scholar name
            scholar_name = "Unknown"
            try:
                name_element = self.driver.find_element(By.CSS_SELECTOR, "#gsc_prf_in")
                scholar_name = name_element.text.strip()
            except NoSuchElementException:
                pass

            # Extract affiliation
            affiliation = "Unknown"
            try:
                # Try multiple selectors for affiliation
                affiliation_selectors = ["#gsc_prf_i .gsc_prf_il", ".gsc_prf_il", "#gsc_prf_ivh"]

                for selector in affiliation_selectors:
                    try:
                        affiliation_element = self.driver.find_element(By.CSS_SELECTOR, selector)

                        # First try to extract institution name from link
                        try:
                            institution_link = affiliation_element.find_element(
                                By.CSS_SELECTOR, "a.gsc_prf_ila"
                            )
                            institution_name = institution_link.text.strip()
                            if institution_name:
                                affiliation = institution_name
                                break
                        except NoSuchElementException:
                            pass

                        # Fallback to full text
                        text = affiliation_element.text.strip()
                        if text and not text.startswith("Verified email"):
                            affiliation = text
                            break

                    except NoSuchElementException:
                        continue

            except Exception as e:
                logger.debug(f"Could not extract affiliation: {e}")

            # Extract email domain for country inference
            email_domain = ""
            try:
                email_element = self.driver.find_element(By.CSS_SELECTOR, "#gsc_prf_ivh")
                email_text = email_element.text.strip()
                if "Verified email at" in email_text:
                    email_domain = email_text.split("Verified email at")[-1].strip()
                    if " - Homepage" in email_domain:
                        email_domain = email_domain.split(" - Homepage")[0].strip()
            except:
                pass

            # Extract country from email domain
            country_code = "Unknown"
            if email_domain:
                country_code = self.get_country_from_email_domain(email_domain)
                logger.debug(
                    f"Extracted country code '{country_code}' from domain '{email_domain}'"
                )

            # Note: We don't return to the original page here anymore
            # That will be handled by crawl_citations_page after all profiles are processed

            return {
                "name": scholar_name,
                "affiliation": affiliation,
                "email_domain": email_domain,
                "country": country_code,
            }

        except Exception as e:
            logger.error(f"Error extracting Scholar profile affiliation: {e}")
            return None

    def get_openalex_author_details(self, openalex_author_id):
        """
        Fetch detailed author information from OpenAlex author API using pyalex.

        Args:
            openalex_author_id: OpenAlex author ID (e.g., 'https://openalex.org/A5036984647')

        Returns:
            Dictionary with author affiliation details or None if not found
        """
        if not openalex_author_id:
            return None

        try:
            # Extract the author ID from the full URL
            if openalex_author_id.startswith("https://openalex.org/"):
                author_id = openalex_author_id.split("/")[-1]
            else:
                author_id = openalex_author_id

            logger.debug(f"Fetching OpenAlex author details for: {author_id}")

            # Use pyalex to fetch author details
            author_data = pyalex.Authors()[author_id]

            if not author_data:
                return None

            # Extract the most recent affiliation
            if "affiliations" in author_data and author_data["affiliations"]:
                # Get the most recent affiliation (first in list)
                recent_affiliation = author_data["affiliations"][0]

                institution = recent_affiliation.get("institution", {})
                institution_name = institution.get("display_name", "Unknown")
                country_code = institution.get("country_code", "Unknown")

                return {
                    "affiliation": institution_name,
                    "institution_display_name": institution_name,
                    "country": country_code,
                    "institution_id": institution.get("id"),
                    "years": recent_affiliation.get("years", []),
                }

            # Fallback: check last_known_institution
            if "last_known_institution" in author_data and author_data["last_known_institution"]:
                institution = author_data["last_known_institution"]
                institution_name = institution.get("display_name", "Unknown")
                country_code = institution.get("country_code", "Unknown")

                return {
                    "affiliation": institution_name,
                    "institution_display_name": institution_name,
                    "country": country_code,
                    "institution_id": institution.get("id"),
                    "years": [],
                }

        except Exception as e:
            logger.debug(f"Error fetching OpenAlex author details for {openalex_author_id}: {e}")

        return None

    def get_openalex_data(self, citation_data):
        """
        Search OpenAlex for a paper and extract author affiliations and other metadata.

        Args:
            citation_data (dict): Citation data dictionary with 'citing_paper_title'

        Returns:
            tuple: (updated_citation_data, openalex_affiliations)
        """
        title = citation_data["citing_paper_title"]
        try:
            # Clean the title - remove commas which cause issues with OpenAlex API
            clean_title = title.replace(",", "").strip()

            if clean_title != title:
                logger.debug(f"Cleaned title for OpenAlex search: '{title}' -> '{clean_title}'")

            # Use exact title search with title.search filter
            # This provides more accurate matching
            works = pyalex.Works().filter(**{"title.search": clean_title}).get()

            if not works:
                logger.debug(f"No OpenAlex results found for title: {clean_title}")
                return citation_data, []

            # Get the first (most relevant) result
            work = works[0]

            # Extract author information with affiliations
            authors_with_affiliations = []

            if "authorships" in work:
                for authorship in work["authorships"]:
                    author_info = {
                        "name": "Unknown",
                        "affiliation": "Unknown",
                        "country": "Unknown",
                        "institution_display_name": "Unknown",
                        "openalex_author_id": None,
                        "openalex_institution_id": "Unknown",
                    }

                    # Extract author name
                    if authorship.get("author") and authorship["author"].get("display_name"):
                        author_info["name"] = authorship["author"]["display_name"]
                        author_info["openalex_author_id"] = authorship["author"].get("id")

                    # Extract institution information
                    institutions = authorship.get("institutions", [])
                    if institutions:
                        # Use the first institution if multiple are available
                        institution = institutions[0]

                        if institution.get("display_name"):
                            author_info["institution_display_name"] = institution["display_name"]
                            author_info["affiliation"] = institution["display_name"]

                        if institution.get("country_code"):
                            author_info["country"] = institution["country_code"]

                        author_info["openalex_institution_id"] = institution.get("id", "Unknown")

                    if author_info["affiliation"] == "Unknown" and authorship.get(
                        "raw_affiliation_strings", False
                    ):
                        # Fallback: use raw affiliation string if available
                        author_info["affiliation"] = authorship["raw_affiliation_strings"][0]

                    if author_info["country"] == "Unknown" and authorship.get("countries", False):
                        # Fallback: use the first country from the countries list
                        author_info["country"] = authorship["countries"][0]

                    authors_with_affiliations.append(author_info)

            # Update citation_data with OpenAlex information if fields contain "…"
            if "…" in citation_data.get("citing_paper_title", ""):
                if work.get("title"):
                    citation_data["citing_paper_title"] = work["title"]
                    logger.debug(f"Updated truncated title from OpenAlex: {work['title']}")

            # Check if citing_venue needs updating (contains "…", "Unknown", or is None/empty)
            venue_field = citation_data.get("citing_venue", "")
            should_update_venue = (
                not venue_field
                or venue_field == "Unknown"
                or "…" in venue_field
                or venue_field.strip() == ""
            )

            if should_update_venue:
                # Try to get publication name from OpenAlex
                venue_info = None
                if work.get("primary_location") and work["primary_location"].get("source"):
                    venue_info = work["primary_location"]["source"].get("display_name")
                elif work.get("host_venue") and work["host_venue"].get("display_name"):
                    venue_info = work["host_venue"]["display_name"]

                if venue_info:
                    citation_data["citing_venue"] = venue_info
                    logger.debug(f"Updated venue from OpenAlex: {venue_info} (was: {venue_field})")

            # Extract primary topic information (domain, field, subfield)
            if work.get("primary_topic"):
                primary_topic = work["primary_topic"]
                citation_data["primary_topic"] = {
                    "display_name": primary_topic.get("display_name"),
                }

                # Add subfield information
                if primary_topic.get("subfield"):
                    citation_data["primary_topic"]["subfield"] = {
                        "display_name": primary_topic["subfield"].get("display_name")
                    }

                # Add field information
                if primary_topic.get("field"):
                    citation_data["primary_topic"]["field"] = {
                        "display_name": primary_topic["field"].get("display_name")
                    }

                # Add domain information
                if primary_topic.get("domain"):
                    citation_data["primary_topic"]["domain"] = {
                        "display_name": primary_topic["domain"].get("display_name")
                    }

                logger.debug(
                    f"Added primary topic: {primary_topic.get('display_name')} (Domain: {primary_topic.get('domain', {}).get('display_name')})"
                )

            logger.debug(
                f"Found {len(authors_with_affiliations)} authors with affiliations for: {title}"
            )
            return citation_data, authors_with_affiliations

        except Exception as e:
            logger.error(f"Error searching OpenAlex for '{title}': {e}")
            return citation_data, []

    def crawl_citations_page(self, url):
        """Crawl a single page of citations."""
        logger.info(f"Crawling page: {url}")

        try:
            self.driver.get(url)
            self.random_delay()

            # Check for robot detection
            if self.check_for_robot_detection():
                self.wait_for_captcha_resolution()

            # Wait for results to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.gs_or, div.gs_r"))
            )

            # Find all citation elements
            # Use more specific selector to get only citation results, not headers or footers
            citation_elements = self.driver.find_elements(By.CSS_SELECTOR, "div.gs_ri")

            # If gs_ri doesn't work, fall back to gs_r but filter more carefully
            if not citation_elements:
                all_elements = self.driver.find_elements(By.CSS_SELECTOR, "div.gs_or, div.gs_r")
                citation_elements = []
                for element in all_elements:
                    try:
                        # Must have a title element to be a valid citation
                        title = element.find_element(By.CSS_SELECTOR, "h3.gs_rt")
                        # Check if this element is inside gs_res_ccl (original article)
                        try:
                            parent_ccl = element.find_element(
                                By.XPATH, "./ancestor::div[contains(@class, 'gs_res_ccl')]"
                            )
                            # If we found a gs_res_ccl ancestor, skip this element
                            continue
                        except NoSuchElementException:
                            # No gs_res_ccl ancestor found, this is a citing article
                            citation_elements.append(element)
                    except NoSuchElementException:
                        # No title found, not a valid citation
                        continue

            page_citations = []
            for element in citation_elements:
                citation_data = self.parse_citation_element(element)
                # Filter out invalid/empty citations
                if (
                    citation_data["citing_paper_title"] != "Unknown"
                    or citation_data["citing_authors"] != "Unknown"
                ):
                    page_citations.append(citation_data)
                else:
                    logger.debug("Skipping invalid citation entry")

            # Now handle Scholar profile extraction if needed - do this after all elements are parsed
            # This avoids stale element references
            if self.use_scholar_fallback:
                # Check if any citations need Scholar affiliation extraction (no citing_authors_details yet)
                citations_needing_scholar = [
                    c
                    for c in page_citations
                    if (
                        (
                            not c.get("citing_authors_details")
                            or len(c["citing_authors_details"]) == 0
                        )
                        and c.get("scholar_profiles")
                    )
                ]

                if citations_needing_scholar:
                    logger.info(
                        f"Extracting Scholar affiliations for {len(citations_needing_scholar)} citation(s)"
                    )

                    for citation_data in citations_needing_scholar:
                        logger.debug(
                            f"Extracting Scholar affiliations for: {citation_data['citing_paper_title']}"
                        )
                        citing_authors_details = []

                        for profile in citation_data["scholar_profiles"]:
                            try:
                                profile_url = profile.get("profile_url")
                                if profile_url:
                                    affiliation_data = self.extract_scholar_profile_affiliation(
                                        profile_url
                                    )
                                    if affiliation_data:
                                        citing_authors_details.append(
                                            {
                                                "name": affiliation_data["name"],
                                                "affiliation": affiliation_data["affiliation"],
                                                "institution_display_name": affiliation_data[
                                                    "affiliation"
                                                ],
                                                "country": affiliation_data["country"],
                                                "email_domain": affiliation_data.get(
                                                    "email_domain", ""
                                                ),
                                                "scholar_profile_url": profile_url,
                                                "source": "google_scholar_profile",
                                            }
                                        )
                            except Exception as e:
                                logger.debug(f"Error extracting Scholar profile affiliation: {e}")

                        if citing_authors_details:
                            citation_data["citing_authors_details"] = citing_authors_details
                            logger.info(
                                f"Extracted {len(citing_authors_details)} Scholar author details"
                            )

                    # Return to the original citations page after all profiles are processed
                    logger.debug(f"Returning to citations page: {url}")
                    self.driver.get(url)
                    self.random_delay()

            logger.info(f"Found {len(page_citations)} citations on this page")
            return page_citations

        except TimeoutException:
            logger.error("Timeout waiting for page to load")
            return []
        except Exception as e:
            logger.error(f"Error crawling page: {e}")
            return []

    def get_next_page_url(self):
        """Get the URL for the next page of results."""
        try:
            # Look for various pagination elements
            # Try multiple strategies to find the next page

            # Strategy 1: Look for Google Scholar specific navigation
            # The Next link is in a td with align="left" containing gs_ico_nav_next
            next_selectors = [
                "//td[@align='left']//a[contains(.//span/@class, 'gs_ico_nav_next')]",  # GS specific
                "//a[.//span[contains(@class, 'gs_ico_nav_next')]]",  # Next icon
                "//a[contains(.//b/text(), 'Next')]",  # Next text in bold
                "//a[contains(text(), 'Next')]",  # Generic Next
                "//button[contains(text(), 'Next')]",
                "//a[@aria-label='Next']",
            ]

            for selector in next_selectors:
                try:
                    next_elements = self.driver.find_elements(By.XPATH, selector)
                    for element in next_elements:
                        if element.is_displayed():
                            # Check if it's disabled
                            class_attr = element.get_attribute("class")
                            if class_attr and ("gs_dis" in class_attr or "disabled" in class_attr):
                                logger.info("Next button found but disabled - reached last page")
                                return None

                            href = element.get_attribute("href")
                            if href:
                                logger.debug(
                                    f"Found next page link via selector '{selector}': {href}"
                                )
                                return href
                except NoSuchElementException:
                    continue

            # Strategy 2: Look for pagination with page numbers in gs_n div
            # Find the current page and look for the next page number
            try:
                # Look for pagination container - Google Scholar uses div#gs_n
                pagination_elements = self.driver.find_elements(By.XPATH, "//div[@id='gs_n']//a")
                if not pagination_elements:
                    # Fallback to any links with start parameter
                    pagination_elements = self.driver.find_elements(
                        By.XPATH, "//a[contains(@href, 'start=')]"
                    )

                current_url = self.driver.current_url
                import re

                # Extract current start value
                current_start = 0
                if "start=" in current_url:
                    start_match = re.search(r"start=(\d+)", current_url)
                    if start_match:
                        current_start = int(start_match.group(1))

                # Look for links with higher start values
                next_url = None
                min_next_start = float("inf")

                for element in pagination_elements:
                    href = element.get_attribute("href")
                    if href and "start=" in href:
                        start_match = re.search(r"start=(\d+)", href)
                        if start_match:
                            start_value = int(start_match.group(1))
                            # Find the smallest start value that's greater than current
                            if start_value > current_start and start_value < min_next_start:
                                min_next_start = start_value
                                next_url = href

                if next_url:
                    logger.debug(f"Found next page via pagination: {next_url}")
                    return next_url

            except Exception as e:
                logger.debug(f"Error checking pagination: {e}")

            # Strategy 3: Check if we can construct the next page URL
            # Google Scholar typically uses start=10, 20, 30, etc.
            try:
                current_url = self.driver.current_url
                import re

                # Check if there are still results on the current page
                # If we have 10 results, there might be more pages
                results = self.driver.find_elements(By.CSS_SELECTOR, "div.gs_ri")
                if not results:
                    results = self.driver.find_elements(By.CSS_SELECTOR, "div.gs_r")

                # Filter out invalid results
                valid_results = [r for r in results if r.is_displayed() and r.text.strip()]

                if len(valid_results) >= 10:
                    # Likely more pages exist
                    if "start=" in current_url:
                        current_start = int(re.search(r"start=(\d+)", current_url).group(1))
                        next_start = current_start + 10
                    else:
                        next_start = 10

                    # Construct next URL
                    if "start=" in current_url:
                        next_url = re.sub(r"start=\d+", f"start={next_start}", current_url)
                    else:
                        connector = "&" if "?" in current_url else "?"
                        next_url = f"{current_url}{connector}start={next_start}"

                    logger.debug(f"Constructed next page URL based on result count: {next_url}")
                    return next_url
                else:
                    logger.info(
                        f"Only {len(valid_results)} results on this page - likely the last page"
                    )

            except Exception as e:
                logger.debug(f"Error constructing next URL: {e}")

            # If we get here, no next page found
            logger.info("No next page found - reached last page")
            return None

        except Exception as e:
            logger.error(f"Error in get_next_page_url: {e}")

        return None

    def crawl_all_citations(self, article_url_or_id, max_pages=None):
        """Crawl all citations for a given article."""

        if not self.driver:
            self.setup_driver()

        # Get the citations URL
        citations_url = self.get_citations_url(article_url_or_id)
        if not citations_url:
            logger.error("Could not generate citations URL")
            return []

        # Extract cites ID from the URL for file naming
        self.cites_id = None
        if "cites=" in citations_url:
            import re
            from urllib.parse import parse_qs, unquote, urlparse

            # Try parsing with urlparse first
            parsed = urlparse(citations_url)
            params = parse_qs(parsed.query)

            if "cites" in params:
                cites_id = params["cites"][0]
                # Clean up the cites_id - remove any URL encoding
                cites_id = unquote(cites_id)

                # Check for parameter artifacts (like 'article_url_or_id=...')
                if "=" in cites_id and not "," in cites_id:
                    # This is a malformed parameter, skip it
                    logger.warning(f"Malformed cites parameter detected: {cites_id}")
                    self.cites_id = None
                elif "," in cites_id:
                    # Multiple citation IDs - replace comma with underscore for filename
                    # e.g., "14327779248726238147,7620908687830067523" -> "14327779248726238147_7620908687830067523"
                    ids = cites_id.split(",")
                    # Clean each ID and join with underscore
                    clean_ids = []
                    for id_str in ids:
                        id_str = id_str.strip()
                        if id_str.isdigit():
                            clean_ids.append(id_str)
                    if clean_ids:
                        self.cites_id = "_".join(clean_ids)
                        logger.info(f"Multiple cites IDs found, combined as: {self.cites_id}")
                    else:
                        logger.warning(f"Could not clean multiple cites IDs: {cites_id}")
                        self.cites_id = None
                elif cites_id.isdigit():
                    # Single clean numeric ID
                    self.cites_id = cites_id
                else:
                    # Try to extract just the numeric ID
                    id_match = re.search(r"(\d{10,})", cites_id)  # Look for at least 10 digits
                    if id_match:
                        self.cites_id = id_match.group(1)
                    else:
                        logger.warning(f"Could not extract clean cites ID from: {cites_id}")
                        # Don't use malformed IDs as fallback
                        self.cites_id = None
            else:
                # Fallback to regex if urlparse doesn't work
                cites_match = re.search(r"cites=([^&]+)", citations_url)
                if cites_match:
                    cites_id = cites_match.group(1)
                    if "," in cites_id:
                        # Handle multiple IDs
                        self.cites_id = cites_id.replace(",", "_")
                    else:
                        self.cites_id = cites_id

            if self.cites_id:
                logger.info(f"Extracted cites ID: {self.cites_id}")
            else:
                logger.warning(f"Could not extract cites ID from URL: {citations_url}")

        logger.info(f"Starting citation crawl for: {article_url_or_id}")
        logger.info(f"Citations URL: {citations_url}")

        all_citations = []
        current_url = citations_url
        page_count = 0

        while current_url and (max_pages is None or page_count < max_pages):
            page_count += 1
            logger.info(f"Crawling page {page_count}...")

            page_citations = self.crawl_citations_page(current_url)
            if not page_citations:
                logger.warning("No citations found on this page, stopping")
                break

            all_citations.extend(page_citations)

            # Get next page URL
            current_url = self.get_next_page_url()
            if current_url:
                current_url = urljoin(BASE_URL, current_url)
                logger.info(f"Next page URL: {current_url}")
            else:
                logger.info("No more pages found")
                break

            self.random_delay()

        logger.info(
            f"Crawling completed. Found {len(all_citations)} total citations across {page_count} pages"
        )
        self.citations_data = all_citations
        return all_citations

    def save_to_csv(self, filename=None, include_timestamp=False, citation_info_format=False):
        """
        Save citations data to CSV file.

        Args:
            filename: Output CSV filename (if None, uses cites_id for naming)
            include_timestamp: Whether to add timestamp to filename
            citation_info_format: Whether to use citation_info.csv compatible format
        """
        if not self.citations_data:
            logger.error("No citations data to save")
            return False

        # Create data directory if it doesn't exist
        Path("data").mkdir(parents=True, exist_ok=True)

        # Use cites_id for filename if not provided
        if filename is None and hasattr(self, "cites_id") and self.cites_id:
            filename = f"data/cites-{self.cites_id}.csv"
        elif filename is None:
            filename = "citations.csv"

        # Add timestamp to filename if requested
        if include_timestamp:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = Path(filename)
            filename = path.parent / f"{path.stem}_{timestamp}{path.suffix}"

        df = pd.DataFrame(self.citations_data)

        if citation_info_format:
            # Create citation_info.csv compatible format
            df_compatible = pd.DataFrame()

            df_compatible["citing author name"] = df["citing_authors"]
            df_compatible["citing paper title"] = df["citing_paper_title"]
            df_compatible["cited paper title"] = (
                "Target Article"  # This would need to be set from input
            )
            df_compatible["year"] = df["citing_year"]

            # Extract affiliation information from citing_authors_details
            def extract_affiliations(row):
                citing_authors_details = row.get("citing_authors_details", [])
                if (
                    citing_authors_details
                    and isinstance(citing_authors_details, list)
                    and len(citing_authors_details) > 0
                ):
                    affiliations = []
                    countries = []

                    for author in citing_authors_details:
                        if author.get("affiliation") and author["affiliation"] != "Unknown":
                            affiliations.append(author["affiliation"])
                        if author.get("country") and author["country"] != "Unknown":
                            countries.append(author["country"])

                    if affiliations:
                        affiliation_str = "; ".join(set(affiliations))
                        country_str = "; ".join(set(countries)) if countries else "Unknown"
                        return affiliation_str, country_str

                return "Unknown", "Unknown"

            # Apply affiliation extraction
            affiliation_info = df.apply(extract_affiliations, axis=1)
            df_compatible["affiliation"] = [info[0] for info in affiliation_info]
            df_compatible["country"] = [info[1] for info in affiliation_info]

            # Extract profile URLs into separate columns
            df_compatible["scholar_profile_urls"] = df["scholar_profiles"].apply(
                lambda profiles: (
                    "; ".join([f"{prof['name']}: {prof['profile_url']}" for prof in profiles])
                    if profiles
                    else ""
                )
            )

            # Add detailed author info
            df_compatible["citing_authors_details_json"] = df["citing_authors_details"].apply(
                lambda details: json.dumps(details) if details else "[]"
            )

            # Add placeholder columns for compatibility
            df_compatible["latitude"] = ""
            df_compatible["longitude"] = ""
            df_compatible["county"] = ""
            df_compatible["city"] = ""
            df_compatible["state"] = ""

            df_to_save = df_compatible

        else:
            # Process scholar profiles and author details for CSV - flatten to JSON string for easier handling
            if "scholar_profiles" in df.columns:
                df["scholar_profiles_json"] = df["scholar_profiles"].apply(
                    lambda x: json.dumps(x) if x else "[]"
                )

            if "citing_authors_details" in df.columns:
                df["citing_authors_details_json"] = df["citing_authors_details"].apply(
                    lambda x: json.dumps(x) if x else "[]"
                )

            # Reorder columns
            column_order = [
                "citing_paper_title",
                "citing_authors",
                "citing_year",
                "citing_venue",
                "citing_paper_url",
                "pdf_url",
                "citations_count",
                "scholar_profiles_json",
                "citing_authors_details_json",
            ]

            df_to_save = df.reindex(columns=column_order)

        df_to_save.to_csv(filename, index=False, encoding="utf-8")
        logger.info(f"Citations data saved to: {filename}")
        return True

    def save_to_json(self, filename=None, include_timestamp=False):
        """Save citations data to JSON file."""
        if not self.citations_data:
            logger.error("No citations data to save")
            return False

        # Create data directory if it doesn't exist
        Path("data").mkdir(parents=True, exist_ok=True)

        # Use cites_id for filename if not provided
        if filename is None and hasattr(self, "cites_id") and self.cites_id:
            filename = f"data/cites-{self.cites_id}.json"
        elif filename is None:
            filename = "data/citations.json"

        if include_timestamp:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = Path(filename)
            filename = path.parent / f"{path.stem}_{timestamp}{path.suffix}"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.citations_data, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"Citations data saved to: {filename}")
        return True

    def close(self):
        """Close the WebDriver."""
        if self.driver:
            self.driver.quit()
            self.driver = None
