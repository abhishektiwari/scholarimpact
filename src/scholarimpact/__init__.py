"""
ScholarImpact: Citation Analysis and Dashboard Package

A comprehensive tool for analyzing Google Scholar citations with geographic
and institutional insights, featuring interactive Streamlit dashboards.
"""

from .core.crawler import CitationCrawler
from .core.extractor import AuthorExtractor
from .dashboard.app import Dashboard
from .data.loader import load_data

__version__ = "0.1.0"
__author__ = "ScholarImpact Team"
__email__ = "contact@scholarimpact.com"

# Main convenience functions
def extract_author(scholar_id, **kwargs):
    """Extract author publications from Google Scholar."""
    extractor = AuthorExtractor()
    return extractor.extract(scholar_id, **kwargs)

def crawl_citations(url_or_data, **kwargs):
    """Crawl citations from Google Scholar."""
    crawler = CitationCrawler(**kwargs)
    return crawler.crawl_all_citations(url_or_data)

def create_dashboard(data_dir, **kwargs):
    """Create a Streamlit dashboard for citation analysis."""
    return Dashboard(data_dir=data_dir, **kwargs)


# Quick start function
def quick_analysis(scholar_id, openalex_email=None, launch_dashboard=True, data_dir='./data'):
    """Complete analysis pipeline from Scholar ID to dashboard."""
    import os
    
    # Set default data directory
    os.makedirs(data_dir, exist_ok=True)
    
    # Extract author data
    print(f"Extracting author data for {scholar_id}...")
    author_data = extract_author(scholar_id, output_dir=data_dir)
    
    # Crawl citations
    print("Crawling citations...")
    citation_data = crawl_citations(
        f"{data_dir}/author.json",
        openalex_email=openalex_email
    )
    
    # Create and optionally launch dashboard
    print("Creating dashboard...")
    dashboard = create_dashboard(data_dir)
    
    if launch_dashboard:
        print("Launching dashboard...")
        dashboard.run()
    
    return {
        'author': author_data,
        'citations': citation_data,
        'dashboard': dashboard
    }

__all__ = [
    'CitationCrawler',
    'AuthorExtractor',
    'Dashboard',
    'load_data',
    'extract_author',
    'crawl_citations',
    'create_dashboard',
    'quick_analysis'
]