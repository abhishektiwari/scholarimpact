"""
Data loading utilities for ScholarImpact.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

logger = logging.getLogger(__name__)

def load_data(data_dir: str = 'data') -> Dict[str, Any]:
    """
    Load citation data from the data directory.
    
    Args:
        data_dir: Directory containing the data files
        
    Returns:
        Dictionary containing loaded data
    """
    data = {}
    data_path = Path(data_dir)
    
    if not data_path.exists():
        logger.warning(f"Data directory {data_dir} does not exist")
        return data
    
    # Load author.json
    author_file = data_path / 'author.json'
    if author_file.exists():
        try:
            with open(author_file, 'r', encoding='utf-8') as f:
                data['author'] = json.load(f)
                
                # Extract articles if present
                if 'articles' in data['author']:
                    data['articles'] = pd.DataFrame(data['author']['articles'])
                    
            logger.info(f"Loaded author data from {author_file}")
        except Exception as e:
            logger.error(f"Error loading author data: {e}")
    
    # Load citation files
    citation_files = list(data_path.glob('cites-*.json'))
    if citation_files:
        data['citation_files'] = {}
        for citation_file in citation_files:
            try:
                with open(citation_file, 'r', encoding='utf-8') as f:
                    citations = json.load(f)
                    # Extract cites_id from filename
                    cites_id = citation_file.stem.replace('cites-', '')
                    data['citation_files'][cites_id] = citations
                    
            except Exception as e:
                logger.warning(f"Error loading {citation_file}: {e}")
        
        logger.info(f"Loaded {len(data['citation_files'])} citation files")
    
    # Process and enhance articles data if available
    if 'articles' in data and not data['articles'].empty:
        data['articles'] = enhance_articles_data(data['articles'], data.get('citation_files', {}))
    
    return data

def enhance_articles_data(articles_df: pd.DataFrame, citation_files: Dict[str, Any]) -> pd.DataFrame:
    """
    Enhance articles data with citation analysis.
    
    Args:
        articles_df: DataFrame containing article data
        citation_files: Dictionary of citation files
        
    Returns:
        Enhanced DataFrame
    """
    # Initialize new columns
    articles_df['crawler_data_available'] = False
    articles_df['unique_citing_authors'] = 0
    articles_df['unique_countries'] = 0
    articles_df['unique_institutions'] = 0
    
    for idx, row in articles_df.iterrows():
        cites_id = row.get('cites_id', '')
        if not cites_id:
            continue
        
        # Handle multiple IDs
        if ',' in str(cites_id):
            file_cites_id = str(cites_id).replace(',', '_')
        else:
            file_cites_id = str(cites_id)
        
        # Check if we have citation data
        if file_cites_id in citation_files:
            articles_df.at[idx, 'crawler_data_available'] = True
            citations = citation_files[file_cites_id]
            
            # Count unique citing authors
            citing_authors = set()
            countries = set()
            institutions = set()
            
            for citation in citations:
                # Extract authors
                if 'citing_authors' in citation:
                    authors = citation['citing_authors'].split(',')
                    for author in authors:
                        author = author.strip()
                        if author and author != 'Unknown':
                            citing_authors.add(author)
                
                # Extract countries and institutions from author details
                for author_detail in citation.get('citing_authors_details', []):
                    country = author_detail.get('country', '')
                    if country and country not in ['Unknown', '']:
                        countries.add(country)
                    
                    institution = author_detail.get('institution_display_name', '')
                    if institution and institution not in ['Unknown', '']:
                        institutions.add(institution)
            
            articles_df.at[idx, 'unique_citing_authors'] = len(citing_authors)
            articles_df.at[idx, 'unique_countries'] = len(countries)
            articles_df.at[idx, 'unique_institutions'] = len(institutions)
    
    return articles_df