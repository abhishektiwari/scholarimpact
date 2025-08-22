"""
Main streamlit app component that replicates the exact original streamlit_app.py functionality.
"""

import json
import os
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pycountry
import streamlit as st
from plotly.subplots import make_subplots

from .base import BaseComponent, ComponentRegistry


class StreamlitAppComponent(BaseComponent):
    """Component that replicates the exact original streamlit_app.py functionality."""

    def get_required_data_keys(self) -> List[str]:
        """Required data keys."""
        return ["author", "articles"]

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate that required data is available."""
        return (
            data.get("author") is not None
            and data.get("articles") is not None
            and not data["articles"].empty
        )

    def render(self, data: Dict[str, Any], data_dir: str = "data", **kwargs) -> None:
        """
        Render the complete streamlit app functionality.

        Args:
            data: Data dictionary containing author and articles
            data_dir: Directory containing citation data files
            **kwargs: Additional options
        """
        if not self.validate_data(data):
            st.error("No citation data found. Please run citation crawler first.")
            st.info("Run: `scholarimpact extract-author YOUR_SCHOLAR_ID`")
            return

        def _render_app():
            # Get theme colors dynamically (exact match to original)
            THEME_COLORS = st.get_option("theme.chartCategoricalColors") or [
                "#0ea5e9",
                "#059669",
                "#fbbf24",
            ]

            # Consistent color scheme matching Streamlit theme (exact match to original)
            COLOR_PALETTE = {
                "primary": st.get_option("theme.primaryColor") or "#cb785c",
                "chart_colors": THEME_COLORS,
                "bar_color": THEME_COLORS[0],
                "line_color": THEME_COLORS[2],
                "fill_color": THEME_COLORS[2],
                "gradient": [
                    "#e6fef5",
                    "#b8f5e0",
                    "#8aeccc",
                    "#5ce3b7",
                    "#2dd4a3",
                    "#0dc58e",
                    "#059669",
                ],
                "qualitative": THEME_COLORS
                + ["#cb785c", "#8b5cf6", "#ec4899", "#6366f1", "#78716c"],
                "sequential": "Greens",
                "diverging": "RdBu",
            }

            # Main content description
            st.markdown(
                """
            Select a publication from the sidebar to view comprehensive citation analytics.
            """
            )

            # Prepare enhanced articles data (exact match to original)
            pub_analysis = self._prepare_articles_data(data["articles"], data_dir)

            if pub_analysis is None or pub_analysis.empty:
                st.error("Could not process articles data.")
                return

            # Sidebar - Author info and publication selector (exact match to original)
            self._display_author_info(data["author"], show_interests=False)

            # Publication selector
            st.sidebar.markdown("### Select Publication")

            # Sort options (exact match to original)
            sort_options = {
                "Most Citations": "total_citations",
                "Alphabetical": "title",
                "Most Recent": "year" if "year" in pub_analysis.columns else "total_citations",
            }

            sort_by = st.sidebar.selectbox("Sort by:", list(sort_options.keys()))
            ascending = sort_by == "Alphabetical"

            # Sort dataframe
            if sort_options[sort_by] in pub_analysis.columns:
                pub_analysis_sorted = pub_analysis.sort_values(
                    sort_options[sort_by], ascending=ascending
                )
            else:
                pub_analysis_sorted = pub_analysis.sort_values("total_citations", ascending=False)

            # Publication selector
            publication_titles = pub_analysis_sorted["title"].tolist()

            # Create display titles with citation counts (exact match to original)
            display_titles = []
            for _, row in pub_analysis_sorted.iterrows():
                title = row["title"]
                citations = row["total_citations"]
                display_title = (
                    f"{title[:60]}{'...' if len(title) > 60 else ''} ({citations} citations)"
                )
                display_titles.append(display_title)

            # URL fragment handling (exact match to original)
            url_fragment = st.query_params.get("article", "")

            # Initialize session state for article selection
            if "selected_article_slug" not in st.session_state:
                st.session_state.selected_article_slug = None
                st.session_state.selected_article_index = 0
                st.session_state.last_sort_by = sort_by

            # Reset selection if sort option changed
            if st.session_state.get("last_sort_by") != sort_by:
                st.session_state.selected_article_index = 0
                st.session_state.selected_article_slug = None
                st.session_state.last_sort_by = sort_by

            # Determine default index based on URL fragment
            default_index = 0

            if url_fragment:
                matched_idx = self._find_article_by_slug(url_fragment, pub_analysis_sorted)
                if matched_idx is not None:
                    matched_title = pub_analysis_sorted.iloc[matched_idx]["title"]
                    pub_analysis_reset = pub_analysis_sorted.reset_index(drop=True)
                    for i, row in pub_analysis_reset.iterrows():
                        if row["title"] == matched_title:
                            default_index = i
                            if url_fragment != st.session_state.selected_article_slug:
                                st.session_state.selected_article_index = i
                                st.session_state.selected_article_slug = url_fragment
                            break
            elif "selected_article_index" in st.session_state:
                default_index = st.session_state.selected_article_index

            selected_display = st.sidebar.selectbox(
                "Choose a publication:", display_titles, index=default_index, key=f"pub_selector_{sort_by}"
            )

            # Track selectbox changes
            current_selection_index = (
                display_titles.index(selected_display) if selected_display in display_titles else 0
            )
            if (
                current_selection_index != st.session_state.selected_article_index
                and not url_fragment
            ):
                st.session_state.selected_article_index = current_selection_index
                st.session_state.selected_article_slug = None

            # Display Research Interests after publication selection (exact match to original)
            if data["author"].get("interests"):
                st.sidebar.markdown("### Research Interests")
                for interest in data["author"]["interests"]:
                    st.sidebar.markdown(f"• {interest}")

            if selected_display:
                # Get the actual title
                selected_idx = display_titles.index(selected_display)
                selected_title = publication_titles[selected_idx]

                # Get publication data
                pub_data = pub_analysis_sorted[pub_analysis_sorted["title"] == selected_title].iloc[
                    0
                ]

                # Update URL with article slug
                article_slug = self._create_url_slug(selected_title)
                if article_slug:
                    st.query_params["article"] = article_slug

                # Main content area - exact match to original streamlit_app.py
                self._render_main_content(pub_data, COLOR_PALETTE, data_dir)

        self._render_in_container(_render_app)

    def _display_author_info(self, author_data: Dict[str, Any], show_interests: bool = False):
        """Display author information with icons and links (exact match to original)."""
        if not author_data:
            st.sidebar.warning("No author information available")
            return

        # Author name
        st.sidebar.markdown(f"### {author_data.get('name', 'Unknown')}")

        # Affiliation
        if author_data.get("affiliation"):
            st.sidebar.markdown(f"{author_data['affiliation']}")

        # Navigation-style links
        if author_data.get("scholar_profile_url") or author_data.get("homepage"):
            
            if author_data.get("scholar_profile_url"):
                st.sidebar.page_link(
                    author_data["scholar_profile_url"], 
                    label="Google Scholar",
                    icon=":material/school:"
                )
            
            if author_data.get("homepage"):
                st.sidebar.page_link(
                    author_data["homepage"], 
                    label="Homepage",
                    icon=":material/home:"
                )

        # Metrics
        st.sidebar.markdown("### Metrics")

        col1, col2 = st.sidebar.columns(2)
        with col1:
            st.metric("Total Citations", f"{author_data.get('total_citations', 0):,}")

        with col2:
            st.metric("Publications", author_data.get("total_publications", 0))

        # Add h-index and i10-index
        col3, col4 = st.sidebar.columns(2)
        with col3:
            st.metric("h-index", author_data.get("hindex", 0))

        with col4:
            st.metric("i10-index", author_data.get("i10index", 0))

        # Interests (only if show_interests is True)
        if show_interests and author_data.get("interests"):
            st.sidebar.markdown("### Research Interests")
            for interest in author_data["interests"]:
                st.sidebar.markdown(f"• {interest}")

    def _prepare_articles_data(
        self, articles_df: pd.DataFrame, data_dir: str = "data"
    ) -> pd.DataFrame:
        """Prepare articles data exactly as in original streamlit_app.py."""
        if articles_df is None or articles_df.empty:
            return None

        # Clean and process the articles data
        df_clean = articles_df.copy()

        # Initialize new columns for complex data to avoid assignment issues
        df_clean["top_countries_from_affiliations"] = None
        df_clean["country_locations"] = None
        df_clean["crawler_data_available"] = False

        # Ensure numeric types
        df_clean["total_citations"] = pd.to_numeric(
            df_clean["total_citations"], errors="coerce"
        ).fillna(0)

        if "year" in df_clean.columns:
            df_clean["year"] = pd.to_numeric(df_clean["year"], errors="coerce")

        # Check for crawler JSON files for each article with cites_id
        for idx, row in df_clean.iterrows():
            if "cites_id" in row and row["cites_id"]:
                cites_id = str(row["cites_id"])

                # Handle multiple comma-separated IDs by joining with underscore
                if "," in cites_id:
                    file_cites_id = cites_id.replace(",", "_")
                else:
                    file_cites_id = cites_id

                # Check for crawler JSON file
                json_file = os.path.join(data_dir, f"cites-{file_cites_id}.json")
                if os.path.exists(json_file):
                    try:
                        with open(json_file, "r", encoding="utf-8") as f:
                            citations_data = json.load(f)

                        # Count unique citing authors
                        citing_authors = set()
                        for citation in citations_data:
                            if "citing_authors" in citation and citation["citing_authors"]:
                                authors = citation["citing_authors"].split(",")
                                for author in authors:
                                    author = author.strip()
                                    if author and author != "Unknown":
                                        citing_authors.add(author)

                        # Add the count to the dataframe
                        df_clean.at[idx, "unique_citing_authors_from_crawler"] = len(citing_authors)
                        df_clean.at[idx, "crawler_data_available"] = True

                        # Enhanced country analysis using citing_authors_details
                        citing_countries = {}
                        country_locations = []

                        # Extract country information from citing_authors_details
                        for citation in citations_data:
                            citing_authors_details = citation.get("citing_authors_details", [])
                            processed_countries = set()

                            for author_details in citing_authors_details:
                                if isinstance(author_details, dict):
                                    country = author_details.get("country", "") or ""
                                    institution_name = (
                                        author_details.get("institution_display_name", "") or ""
                                    )

                                    country = country.strip() if country else ""

                                    if (
                                        country
                                        and country not in ["Unknown", "Invalid", ""]
                                        and country not in processed_countries
                                    ):
                                        if country in citing_countries:
                                            citing_countries[country] += 1
                                        else:
                                            citing_countries[country] = 1

                                        processed_countries.add(country)

                        # Store enhanced country data
                        if citing_countries:
                            df_clean.at[idx, "unique_countries_from_crawler"] = len(
                                citing_countries
                            )

                            try:
                                df_clean.at[idx, "top_countries_from_affiliations"] = (
                                    citing_countries
                                )
                                df_clean.at[idx, "country_locations"] = (
                                    country_locations if country_locations else []
                                )
                            except (ValueError, TypeError) as assign_error:
                                print(
                                    f"Warning: Could not assign complex data for {file_cites_id}: {assign_error}"
                                )
                                df_clean.at[idx, "top_countries_from_affiliations"] = {}
                                df_clean.at[idx, "country_locations"] = []

                    except Exception as e:
                        print(f"Error loading crawler data for cites_id {file_cites_id}: {e}")
                        df_clean.at[idx, "crawler_data_available"] = False
                        if "top_countries_from_affiliations" not in df_clean.columns or pd.isna(
                            df_clean.at[idx, "top_countries_from_affiliations"]
                        ):
                            df_clean.at[idx, "top_countries_from_affiliations"] = {}
                        if "country_locations" not in df_clean.columns or pd.isna(
                            df_clean.at[idx, "country_locations"]
                        ):
                            df_clean.at[idx, "country_locations"] = []
                else:
                    df_clean.at[idx, "crawler_data_available"] = False

        # Sort by citations descending
        df_clean = df_clean.sort_values("total_citations", ascending=False)

        return df_clean

    def _create_url_slug(self, title: str) -> str:
        """Create a URL-friendly slug from article title (exact match to original)."""
        if not title:
            return ""

        # Convert to lowercase
        slug = title.lower()

        # Replace spaces and special characters with hyphens
        slug = re.sub(r"[^\w\s-]", "", slug)
        slug = re.sub(r"[-\s]+", "-", slug)

        # Remove leading/trailing hyphens
        slug = slug.strip("-")

        return slug

    def _find_article_by_slug(self, slug: str, pub_analysis: pd.DataFrame) -> Optional[int]:
        """Find article by URL slug (exact match to original)."""
        if not slug or pub_analysis is None or pub_analysis.empty:
            return None

        # Reset index to ensure we get positional indices
        pub_analysis_reset = pub_analysis.reset_index(drop=True)

        # Try exact slug match first
        for i, row in pub_analysis_reset.iterrows():
            article_slug = self._create_url_slug(row["title"])
            if article_slug == slug:
                return i

        # Try partial match
        for i, row in pub_analysis_reset.iterrows():
            article_slug = self._create_url_slug(row["title"])
            if slug in article_slug or article_slug.startswith(slug):
                return i

        return None

    def _render_main_content(
        self, pub_data: pd.Series, COLOR_PALETTE: Dict[str, Any], data_dir: str
    ):
        """Render main content area exactly as in original streamlit_app.py."""
        # Generate and display insight
        insight = self._generate_insight(pub_data)
        st.markdown(insight)

        # Citation Summary

        # Create a 2x2 grid for metrics
        row1_col1, row1_col2 = st.columns(2)
        row2_col1, row2_col2 = st.columns(2)

        # Get comprehensive stats
        has_enhanced_geo_data = (
            "top_countries_from_affiliations" in pub_data
            and pub_data["top_countries_from_affiliations"]
            and isinstance(pub_data["top_countries_from_affiliations"], dict)
        )

        if has_enhanced_geo_data:
            institutions_data = self._analyze_citing_institutions(pub_data, data_dir)
            countries_data = pub_data.get("top_countries_from_affiliations", {})
            total_authors = int(pub_data.get("unique_citing_authors_from_crawler", 0))
            total_citations = int(pub_data.get("total_citations", 0))

            with row1_col1:
                st.metric(
                    "Total Citations",
                    f"{total_citations:,}",
                    border=True,
                    help="Total number of citations for this publication",
                )

            with row1_col2:
                st.metric(
                    "Unique Authors",
                    f"{total_authors:,}",
                    border=True,
                    help="Number of unique authors who have cited this work",
                )

            with row2_col1:
                st.metric(
                    "Countries",
                    f"{len(countries_data):,}",
                    border=True,
                    help="Number of countries from which citations originate",
                )

            with row2_col2:
                st.metric(
                    "Institutions",
                    f"{len(institutions_data):,}",
                    border=True,
                    help="Number of institutions whose researchers have cited this work",
                )
        else:
            # Fallback metrics when enhanced data is Unknown
            with row1_col1:
                st.metric(
                    "Total Citations", 
                    f"{pub_data['total_citations']:,}",
                    border=True,
                    help="Total number of citations for this publication"
                )

            with row1_col2:
                if "unique_citing_authors_from_crawler" in pub_data and pd.notna(
                    pub_data["unique_citing_authors_from_crawler"]
                ):
                    st.metric(
                        "Citing Authors", 
                        f"{int(pub_data['unique_citing_authors_from_crawler']):,}",
                        border=True,
                        help="Number of unique authors who have cited this work"
                    )
                elif "unique_citing_authors" in pub_data:
                    st.metric(
                        "Citing Authors", 
                        f"{int(pub_data['unique_citing_authors']):,}",
                        border=True,
                        help="Number of unique authors who have cited this work"
                    )

            with row2_col1:
                if "unique_countries" in pub_data:
                    st.metric(
                        "Countries", 
                        f"{int(pub_data['unique_countries']):,}",
                        border=True,
                        help="Number of countries from which citations originate"
                    )

            with row2_col2:
                if "unique_institutions" in pub_data:
                    st.metric(
                        "Institutions", 
                        f"{int(pub_data['unique_institutions']):,}",
                        border=True,
                        help="Number of institutions whose researchers have cited this work"
                    )

        # Visualizations
        st.markdown("---")

        # All the visualization sections exactly as in original
        self._render_visualizations(pub_data, COLOR_PALETTE, data_dir, has_enhanced_geo_data)

        # Detailed Citations Table
        st.markdown("---")
        st.markdown("### Detailed Citations Table")

        citations_table_data = self._create_citations_table(pub_data, data_dir)

        if citations_table_data and len(citations_table_data) > 0:
            citations_df = pd.DataFrame(citations_table_data)

            # Replace None values with NaN for proper handling in Streamlit
            citations_df["Year"] = citations_df["Year"].replace({None: pd.NA})

            # Display the enhanced citations table
            st.dataframe(
                citations_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Paper Title": st.column_config.TextColumn("Citing Paper", width="large"),
                    "Authors": st.column_config.TextColumn("Authors", width="medium"),
                    "Year": st.column_config.NumberColumn("Year", width="small", format="%d"),
                    "Venue": st.column_config.TextColumn("Venue", width="medium"),
                    "Author Affiliations": st.column_config.TextColumn(
                        "Affiliations", width="large", help="Institutions of citing authors"
                    ),
                    "Countries": st.column_config.TextColumn(
                        "Countries", width="medium", help="Countries of citing authors"
                    ),
                },
            )

            st.info(f"Showing {len(citations_df)} citing papers with detailed author information")
        else:
            st.info(
                "No detailed citation data available. Run the citation crawler to generate detailed citation information."
            )

    def _generate_insight(self, pub_data: pd.Series) -> str:
        """Generate human-readable insight exactly as in original."""
        title = pub_data.get("title", "Unknown Title")
        citations = pub_data.get("total_citations", 0)
        year = pub_data.get("year", "Unknown")
        authors = pub_data.get("authors", "Unknown")
        venue = pub_data.get("venue", "Unknown")
        google_scholar_url = pub_data.get("google_scholar_url", "")

        # Use crawler data if available, otherwise use citation_info data
        if "unique_citing_authors_from_crawler" in pub_data and pd.notna(
            pub_data["unique_citing_authors_from_crawler"]
        ):
            unique_citing_authors = int(pub_data["unique_citing_authors_from_crawler"])
        else:
            unique_citing_authors = pub_data.get("unique_citing_authors", 0)

        # Use enhanced country data from affiliations if available
        if (
            "top_countries_from_affiliations" in pub_data
            and pub_data["top_countries_from_affiliations"]
            and isinstance(pub_data["top_countries_from_affiliations"], dict)
        ):
            unique_countries = len(pub_data["top_countries_from_affiliations"])
        elif "unique_countries_from_crawler" in pub_data and pd.notna(
            pub_data["unique_countries_from_crawler"]
        ):
            unique_countries = int(pub_data["unique_countries_from_crawler"])
        else:
            unique_countries = pub_data.get("unique_countries", 0)

        # Generate main insight
        if google_scholar_url:
            insight = f"### {title} [→]({google_scholar_url})\n\n"
        else:
            insight = f"### {title}\n\n"

        insight += f"**Authors:** {authors}\n\n"
        insight += f"**Published:** {year}\n\n"
        insight += f"**Citation Summary:**\n"
        insight += f"This article has been cited **{citations} times** since publication"

        if unique_citing_authors > 0:
            insight += f" by **{unique_citing_authors} unique authors**"

        if unique_countries > 0:
            insight += f" from **{unique_countries} different countries**"

            # Add note about enhanced geographic data if available
            if (
                "top_countries_from_affiliations" in pub_data
                and pub_data["top_countries_from_affiliations"]
                and isinstance(pub_data["top_countries_from_affiliations"], dict)
            ):
                insight += " (with geographic locations traced through author affiliations)"

        insight += ".\n\n"

        return insight

    def _analyze_citing_institutions(self, pub_data: pd.Series, data_dir: str) -> Dict[str, int]:
        """Analyze citing institutions exactly as in original."""
        # Get the citation data for this publication
        cites_id = pub_data.get("cites_id", "")
        if not cites_id:
            return {}

        # Handle multiple cites IDs
        if "," in cites_id:
            file_cites_id = cites_id.replace(",", "_")
        else:
            file_cites_id = cites_id

        # Try to load the citation JSON file
        json_file = f"{data_dir}/cites-{file_cites_id}.json"
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                citations_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

        # Count citations per institution
        institution_counts = {}

        for citation in citations_data:
            citing_authors_details = citation.get("citing_authors_details", [])
            processed_institutions = set()

            for author_details in citing_authors_details:
                if isinstance(author_details, dict):
                    institution = author_details.get("institution_display_name", "") or ""

                    institution = institution.strip() if institution else ""

                    if (
                        institution
                        and institution not in ["Unknown", "Invalid", ""]
                        and institution not in processed_institutions
                    ):

                        if institution in institution_counts:
                            institution_counts[institution] += 1
                        else:
                            institution_counts[institution] = 1
                        processed_institutions.add(institution)

        return dict(sorted(institution_counts.items(), key=lambda x: x[1], reverse=True))

    def _render_visualizations(
        self,
        pub_data: pd.Series,
        COLOR_PALETTE: Dict[str, Any],
        data_dir: str,
        has_enhanced_geo_data: bool,
    ):
        """Render all visualizations exactly as in original streamlit_app.py."""
        # Top Citing Countries Bar Chart
        countries_data = None
        if has_enhanced_geo_data:
            countries_data = pub_data["top_countries_from_affiliations"]
        elif "top_countries" in pub_data and pub_data["top_countries"]:
            countries_data = pub_data["top_countries"]

        if countries_data:
            st.markdown("### Top Citing Countries")

            # Sort by count (descending) and take top 15
            sorted_data = sorted(countries_data.items(), key=lambda x: x[1], reverse=True)[:15]
            countries, counts = zip(*sorted_data) if sorted_data else ([], [])

            fig = go.Figure()
            # Cycle through theme colors for each bar
            bar_colors = [
                COLOR_PALETTE["chart_colors"][i % len(COLOR_PALETTE["chart_colors"])]
                for i in range(len(countries))
            ]

            fig.add_trace(
                go.Bar(
                    x=list(countries),
                    y=list(counts),
                    marker_color=bar_colors,
                    text=list(counts),
                    textposition="auto",
                )
            )

            fig.update_layout(
                xaxis_title="Country",
                yaxis_title="Citations",
                height=400,
                showlegend=False,
            )

            st.plotly_chart(fig, use_container_width=True)
            st.caption(f"Citations based on available country of authors. Top {len(countries)} countries.")

        # Citation Locations - World Map
        if has_enhanced_geo_data and "top_countries_from_affiliations" in pub_data:
            st.markdown("### Citation Distribution by Country")

            country_counts = pub_data["top_countries_from_affiliations"]

            if country_counts and isinstance(country_counts, dict):
                # Convert 2-letter country codes to 3-letter codes using pycountry
                country_data = []
                for country_2letter, count in country_counts.items():
                    try:
                        country_obj = pycountry.countries.get(alpha_2=country_2letter)
                        if country_obj:
                            country_data.append(
                                {
                                    "country_2letter": country_2letter,
                                    "country_3letter": country_obj.alpha_3,
                                    "country_name": country_obj.name,
                                    "citations": count,
                                }
                            )
                    except Exception as e:
                        print(f"Could not convert country code {country_2letter}: {e}")
                        continue

                if country_data:
                    country_df = pd.DataFrame(country_data)

                    # Create choropleth map using 3-letter country codes
                    fig = px.choropleth(
                        country_df,
                        locations="country_3letter",
                        color="citations",
                        locationmode="ISO-3",
                        color_continuous_scale=COLOR_PALETTE["sequential"],
                        labels={"citations": "Number of Citing Papers"},
                        hover_name="country_name",
                        hover_data={"country_3letter": False, "citations": True},
                    )

                    fig.update_layout(
                        height=500,
                        paper_bgcolor=st.get_option("theme.backgroundColor") or "#fdfdf8",
                        plot_bgcolor=st.get_option("theme.backgroundColor") or "#fdfdf8",
                        geo=dict(
                            showframe=False,
                            showcoastlines=True,
                            projection_type="natural earth",
                            bgcolor=st.get_option("theme.backgroundColor") or "#fdfdf8",
                            showocean=True,
                            oceancolor=st.get_option("theme.backgroundColor") or "#fdfdf8",
                            showlakes=True,
                            lakecolor=st.get_option("theme.backgroundColor") or "#fdfdf8",
                            showland=True,
                            landcolor=st.get_option("theme.secondaryBackgroundColor") or "#ecebe3",
                        ),
                        coloraxis_colorbar=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=-0.15,
                            xanchor="center",
                            x=0.5,
                            title_side="top",
                        ),
                    )

                    # Enable export, fullscreen and pan options
                    config = {
                        "displayModeBar": True,
                        "displaylogo": False,
                        "modeBarButtonsToAdd": ["toImage"],
                        "modeBarButtonsToRemove": [
                            "lasso2d",
                            "select2d",
                            "zoom2d",
                            "zoomIn2d",
                            "zoomOut2d",
                            "autoScale2d",
                            "resetScale2d",
                        ],
                        "toImageButtonOptions": {
                            "format": "png",
                            "filename": "citing_papers_by_country",
                            "height": 700,
                            "width": 1200,
                            "scale": 2,
                        },
                        "scrollZoom": False,
                        "doubleClick": False,
                        "dragPan": True,
                    }

                    st.plotly_chart(fig, use_container_width=True, config=config)

                    # Summary statistics
                    total_countries = len(country_data)
                    total_papers = sum(item["citations"] for item in country_data)
                    st.caption(f"Citations distribution by available country of authors. Citations from {total_countries} countries.")

        # Citations per year chart
        if has_enhanced_geo_data:
            st.markdown("### Citations Distribution by Year")

            year_data = self._get_citations_per_year(pub_data, data_dir)

            if year_data:
                # Sort years and create the chart
                years = sorted(year_data.keys())
                counts = [year_data[year] for year in years]

                fig = go.Figure()
                fig.add_trace(
                    go.Bar(
                        x=years,
                        y=counts,
                        marker=dict(color=COLOR_PALETTE["bar_color"]),
                        text=counts,
                        textposition="auto",
                    )
                )

                fig.update_layout(
                    xaxis_title="Year",
                    yaxis_title="Number of Citations",
                    height=400,
                    showlegend=False,
                    xaxis=dict(
                        tickmode="linear",
                        tick0=min(years) if years else 2020,
                        dtick=1 if len(years) <= 10 else 2,
                    ),
                )

                st.plotly_chart(fig, use_container_width=True)

                # Summary statistics for citations per year
                total_with_years = sum(counts)
                avg_per_year = total_with_years / len(years) if years else 0
                st.caption(
                    f"Total citations with year data: {total_with_years} citations across {len(years)} years (avg: {avg_per_year:.1f} per year)"
                )
            else:
                st.info("No year information available in citation data for this article.")

        # Research Domain Analysis
        st.markdown("### Research Domain Analysis")

        domain_data = self._analyze_research_domains(pub_data, data_dir)

        if domain_data and any(domain_data.values()):
            # Create tabs for different levels of analysis
            domain_tab, field_tab, subfield_tab = st.tabs(["Domains", "Fields", "Subfields"])

            with domain_tab:
                if domain_data.get("domains"):
                    # Domain distribution pie chart
                    domains = domain_data["domains"]

                    fig = go.Figure(
                        data=[
                            go.Pie(
                                labels=list(domains.keys()),
                                values=list(domains.values()),
                                hole=0.3,
                                marker=dict(colors=COLOR_PALETTE["qualitative"][: len(domains)]),
                                textinfo="label+percent",
                                textposition="auto",
                            )
                        ]
                    )

                    fig.update_layout(
                        title="Citation Distribution by Research Domain",
                        height=400,
                        showlegend=True,
                        legend=dict(
                            orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.05
                        ),
                    )

                    st.plotly_chart(fig, use_container_width=True)

                    # Domain summary statistics
                    total_with_domains = sum(domains.values())
                    st.caption(
                        f"Papers distributed across {len(domains)} research domains (Total: {total_with_domains} papers with domain data)"
                    )
                else:
                    st.info("No domain information available in citation data.")

            with field_tab:
                if domain_data.get("fields"):
                    # Field distribution bar chart
                    fields = domain_data["fields"]
                    # Sort by count and take top 15
                    sorted_fields = dict(
                        sorted(fields.items(), key=lambda x: x[1], reverse=True)[:15]
                    )

                    # Cycle through theme colors for each bar
                    field_colors = [
                        COLOR_PALETTE["chart_colors"][i % len(COLOR_PALETTE["chart_colors"])]
                        for i in range(len(sorted_fields))
                    ]

                    fig = go.Figure(
                        [
                            go.Bar(
                                x=list(sorted_fields.values()),
                                y=list(sorted_fields.keys()),
                                orientation="h",
                                marker=dict(color=field_colors),
                                text=list(sorted_fields.values()),
                                textposition="outside",
                            )
                        ]
                    )

                    fig.update_layout(
                        title="Top Research Fields Citing This Work",
                        xaxis_title="Number of Citations",
                        yaxis_title="Research Field",
                        height=max(400, len(sorted_fields) * 30),
                        showlegend=False,
                        margin=dict(l=200),
                    )

                    st.plotly_chart(fig, use_container_width=True)

                    # Field diversity metric
                    total_fields = len(fields)
                    total_citations = sum(fields.values())
                    avg_per_field = total_citations / total_fields if total_fields > 0 else 0
                    st.caption(
                        f"Citations from {total_fields} different fields (avg: {avg_per_field:.1f} citations per field)"
                    )
                else:
                    st.info("No field information available in citation data.")

            with subfield_tab:
                if domain_data.get("subfields"):
                    # Subfield treemap
                    subfields = domain_data["subfields"]
                    # Take top 20 subfields
                    sorted_subfields = dict(
                        sorted(subfields.items(), key=lambda x: x[1], reverse=True)[:20]
                    )

                    if sorted_subfields:
                        fig = go.Figure(
                            go.Treemap(
                                labels=list(sorted_subfields.keys()),
                                values=list(sorted_subfields.values()),
                                parents=[""] * len(sorted_subfields),
                                textinfo="label+value",
                                marker=dict(
                                    colorscale=COLOR_PALETTE["sequential"],
                                    cmid=sum(sorted_subfields.values()) / len(sorted_subfields),
                                ),
                            )
                        )

                        fig.update_layout(
                            title="Research Subfields Treemap (Top 20)",
                            height=500,
                            margin=dict(t=50, l=0, r=0, b=0),
                        )

                        st.plotly_chart(fig, use_container_width=True)

                        # Subfield statistics
                        total_subfields = len(subfields)
                        st.caption(
                            f"Total of {total_subfields} unique research subfields identified"
                        )
                    else:
                        st.info("No subfield data available for visualization.")
                else:
                    st.info("No subfield information available in citation data.")

            # Interdisciplinary Impact Score
            if domain_data.get("domains") and domain_data.get("fields"):
                st.markdown("#### Interdisciplinary Impact Metrics")

                # Calculate patent citation count using highest value from available sources
                patent_count_us = self._count_patent_citations(pub_data, data_dir)  # US patents
                
                # Get Altmetric patent count (all patents)
                altmetric_patent_count = pub_data.get('altmetric_cited_by_patents_count')
                if pd.isna(altmetric_patent_count):
                    altmetric_patent_count = 0
                else:
                    altmetric_patent_count = int(altmetric_patent_count) if altmetric_patent_count else 0
                
                # Use the highest count and determine help text
                patent_count = max(patent_count_us, altmetric_patent_count)
                if altmetric_patent_count > patent_count_us:
                    patent_help_text = "Number of patents citing this work (Altmetric data)"
                else:
                    patent_help_text = "Number of US patents citing this work"

                # Create 2x2 grid for metrics
                impact_row1_col1, impact_row1_col2 = st.columns(2)
                impact_row2_col1, impact_row2_col2 = st.columns(2)

                with impact_row1_col1:
                    domain_count = len(domain_data["domains"])
                    st.metric(
                        "Research Domains",
                        domain_count,
                        border=True,
                        help="Number of distinct research domains citing this work",
                    )

                with impact_row1_col2:
                    field_count = len(domain_data["fields"])
                    st.metric(
                        "Research Fields",
                        field_count,
                        border=True,
                        help="Number of distinct research fields citing this work",
                    )

                with impact_row2_col1:
                    # Calculate diversity index (Shannon entropy)
                    import math

                    field_values = list(domain_data["fields"].values())
                    total = sum(field_values)
                    if total > 0:
                        entropy = -sum(
                            (v / total) * math.log(v / total) for v in field_values if v > 0
                        )
                        normalized_entropy = (
                            entropy / math.log(len(field_values)) if len(field_values) > 1 else 0
                        )
                        diversity_score = round(normalized_entropy * 100)
                    else:
                        diversity_score = 0

                    st.metric(
                        "Diversity Score",
                        f"{diversity_score}%",
                        border=True,
                        help="Shannon entropy-based measure of research field diversity (100% = perfectly diverse)",
                    )

                with impact_row2_col2:
                    st.metric(
                        "Patent Citations",
                        patent_count,
                        border=True,
                        help=patent_help_text,
                    )
        else:
            st.info(
                "Research domain analysis requires citation data with OpenAlex. Re-crawl with OpenAlex enabled to see this analysis."
            )
        
        # Altmetric Section
        self._render_altmetric_section(pub_data)

    def _get_citations_per_year(self, pub_data: pd.Series, data_dir: str) -> Dict[int, int]:
        """Get citations per year exactly as in original."""
        # Get the citation data for this publication
        cites_id = pub_data.get("cites_id", "")
        if not cites_id:
            return {}

        # Handle multiple cites IDs
        if "," in cites_id:
            file_cites_id = cites_id.replace(",", "_")
        else:
            file_cites_id = cites_id

        # Try to load the citation JSON file
        json_file = f"{data_dir}/cites-{file_cites_id}.json"
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                citations_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

        if not citations_data:
            return {}

        # Count citations per year
        year_counts = {}

        for citation in citations_data:
            if not isinstance(citation, dict):
                continue

            year = citation.get("citing_year", "Unknown")

            # Handle year properly - convert to int if valid
            year_value = None
            if year != "Unknown":
                if isinstance(year, int):
                    year_value = year
                elif isinstance(year, str) and year.isdigit():
                    year_value = int(year)

            if year_value is not None:
                year_counts[year_value] = year_counts.get(year_value, 0) + 1

        return year_counts

    def _analyze_research_domains(
        self, pub_data: pd.Series, data_dir: str
    ) -> Dict[str, Dict[str, int]]:
        """Analyze research domains exactly as in original."""
        # Get the citation data for this publication
        cites_id = pub_data.get("cites_id", "")
        if not cites_id:
            return {}

        # Handle multiple cites IDs
        if "," in cites_id:
            file_cites_id = cites_id.replace(",", "_")
        else:
            file_cites_id = cites_id

        # Try to load the citation JSON file
        json_file = f"{data_dir}/cites-{file_cites_id}.json"
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                citations_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

        if not citations_data:
            return {}

        # Count distributions
        domains = {}
        fields = {}
        subfields = {}
        topics = {}

        for citation in citations_data:
            if not isinstance(citation, dict):
                continue

            primary_topic = citation.get("primary_topic", {})
            if not primary_topic:
                continue

            # Extract topic
            topic_name = primary_topic.get("display_name")
            if topic_name:
                topics[topic_name] = topics.get(topic_name, 0) + 1

            # Extract domain
            domain_info = primary_topic.get("domain", {})
            if domain_info and domain_info.get("display_name"):
                domain_name = domain_info["display_name"]
                domains[domain_name] = domains.get(domain_name, 0) + 1

            # Extract field
            field_info = primary_topic.get("field", {})
            if field_info and field_info.get("display_name"):
                field_name = field_info["display_name"]
                fields[field_name] = fields.get(field_name, 0) + 1

            # Extract subfield
            subfield_info = primary_topic.get("subfield", {})
            if subfield_info and subfield_info.get("display_name"):
                subfield_name = subfield_info["display_name"]
                subfields[subfield_name] = subfields.get(subfield_name, 0) + 1

        return {"domains": domains, "fields": fields, "subfields": subfields, "topics": topics}

    def _count_patent_citations(self, pub_data: pd.Series, data_dir: str) -> int:
        """Count patent citations exactly as in original."""
        # Get the citation data for this publication
        cites_id = pub_data.get("cites_id", "")
        if not cites_id:
            return 0

        # Handle multiple IDs
        if "," in str(cites_id):
            file_cites_id = str(cites_id).replace(",", "_")
        else:
            file_cites_id = str(cites_id)

        cites_file = os.path.join(data_dir, f"cites-{file_cites_id}.json")

        patent_count = 0
        try:
            if os.path.exists(cites_file):
                with open(cites_file, "r", encoding="utf-8") as f:
                    citations_data = json.load(f)

                # Count citations where venue contains "US Patent"
                for citation in citations_data:
                    venue = citation.get("citing_venue", "")
                    if venue and "US Patent" in venue:
                        patent_count += 1

        except Exception as e:
            st.error(f"Error reading citation data: {e}")

        return patent_count

    def _create_citations_table(self, pub_data: pd.Series, data_dir: str) -> List[Dict[str, Any]]:
        """Create detailed citations table exactly as in original."""
        # Get the citation data for this publication
        cites_id = pub_data.get("cites_id", "")
        if not cites_id:
            return []

        # Handle multiple cites IDs
        if "," in cites_id:
            file_cites_id = cites_id.replace(",", "_")
        else:
            file_cites_id = cites_id

        # Try to load the citation JSON file
        json_file = f"{data_dir}/cites-{file_cites_id}.json"
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                citations_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

        if not citations_data:
            return []

        # Process each citation
        citations_table = []

        for citation in citations_data:
            if not isinstance(citation, dict):
                continue

            # Basic citation info
            paper_title = citation.get("citing_paper_title", "Unknown")
            authors = citation.get("citing_authors", "Unknown")
            year = citation.get("citing_year", "Unknown")
            venue = citation.get("citing_venue", "Unknown")
            citations_count = citation.get("citations_count", 0)

            # Skip invalid entries
            if paper_title in ["Unknown", ""] or authors in ["Unknown", ""]:
                continue

            # Collect affiliations and countries from citing_authors_details
            affiliations_list = []
            countries_list = []

            citing_authors_details = citation.get("citing_authors_details", [])
            if isinstance(citing_authors_details, list):
                for author_details in citing_authors_details:
                    if isinstance(author_details, dict):
                        affiliation = author_details.get("institution_display_name", "") or ""
                        country = author_details.get("country", "") or ""

                        # Strip whitespace if not None
                        affiliation = affiliation.strip() if affiliation else ""
                        country = country.strip() if country else ""

                        if (
                            affiliation
                            and affiliation not in ["Unknown", "Invalid", ""]
                            and affiliation not in affiliations_list
                        ):
                            affiliations_list.append(affiliation)

                        if (
                            country
                            and country not in ["Unknown", "Invalid", ""]
                            and country not in countries_list
                        ):
                            countries_list.append(country)

            # Create the table row
            # Handle year properly - convert to int if valid, otherwise use None for sorting
            year_value = None
            if year != "Unknown":
                if isinstance(year, int):
                    year_value = year
                elif isinstance(year, str) and year.isdigit():
                    year_value = int(year)

            citation_row = {
                "Paper Title": paper_title[:100] + "..." if len(paper_title) > 100 else paper_title,
                "Authors": authors[:80] + "..." if len(authors) > 80 else authors,
                "Year": year_value,  # Use None instead of empty string for missing years
                "Venue": venue[:60] + "..." if len(venue) > 60 else venue,
                "Author Affiliations": (
                    ", ".join(sorted(set(affiliations_list))) if affiliations_list else "Unknown"
                ),
                "Countries": (
                    ", ".join(sorted(set(countries_list))) if countries_list else "Unknown"
                ),
            }

            citations_table.append(citation_row)

        # Sort by year (most recent first) then alphabetically by title
        def sort_key(row):
            year_val = row["Year"]
            if year_val is None:
                year_val = 0  # Treat None/missing years as 0 for sorting
            elif not isinstance(year_val, int):
                year_val = 0

            title_val = row["Paper Title"].lower() if row["Paper Title"] else "zzz"
            return (-year_val, title_val)  # Negative year for descending, title for ascending

        citations_table.sort(key=sort_key)

        return citations_table

    def _render_altmetric_section(self, pub_data: pd.Series):
        """Render Altmetric metrics section."""
        # Check if any Altmetric data is available
        altmetric_fields = [
            'altmetric_cited_by_wikipedia_count',
            'altmetric_cited_by_posts_count',
            'altmetric_readers_count',
            'altmetric_images',
            'altmetric_details_url'
        ]
        
        has_altmetric_data = any(field in pub_data and pub_data[field] is not None for field in altmetric_fields)
        
        if has_altmetric_data:
            st.markdown("#### Altmetric Attention")
            
            # Create 2x2 grid for metrics
            altmetric_row1_col1, altmetric_row1_col2 = st.columns(2)
            altmetric_row2_col1, altmetric_row2_col2 = st.columns(2)
                
            with altmetric_row1_col1:
                wikipedia_count = pub_data.get('altmetric_cited_by_wikipedia_count')
                # Handle NaN/None values using pandas isna
                if pd.isna(wikipedia_count):
                    wikipedia_count = 0
                else:
                    wikipedia_count = int(wikipedia_count) if wikipedia_count else 0
                st.metric(
                    "Wikipedia Citations",
                    wikipedia_count,
                    border=True,
                    help="Number of times cited in Wikipedia articles"
                )
            
            with altmetric_row1_col2:
                posts_count = pub_data.get('altmetric_cited_by_posts_count')
                # Handle NaN/None values using pandas isna
                if pd.isna(posts_count):
                    posts_count = 0
                else:
                    posts_count = int(posts_count) if posts_count else 0
                st.metric(
                    "Social Media Posts",
                    posts_count,
                    border=True,
                    help="Number of social media posts mentioning this work"
                )
            
            with altmetric_row2_col1:
                readers_count = pub_data.get('altmetric_readers_count')
                # Handle NaN/None values using pandas isna
                if pd.isna(readers_count):
                    readers_count = 0
                else:
                    readers_count = int(readers_count) if readers_count else 0
                st.metric(
                    "Readers Count",
                    readers_count,
                    border=True,
                    help="Total number of readers across all platforms (Mendeley, CiteULike, etc.)"
                )
            
            with altmetric_row2_col2:
                # Display Altmetric badge as a metric card
                images = pub_data.get('altmetric_images')
                details_url = pub_data.get('altmetric_details_url')
                
                if images and details_url and isinstance(images, dict):
                    badge_image = images.get('small')
                    if badge_image:
                        # Create metric-style container for the badge
                        st.markdown(
                            f"""
                            <div style="padding: 16px; text-align: center;">
                                <a href="{details_url}" target="_blank">
                                    <img src="{badge_image}" alt="Altmetric Badge" 
                                         style="cursor: pointer; height: auto;" 
                                         title="Click to view detailed Altmetric data"/>
                                </a>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                else:
                    # Show placeholder metric if no badge available
                    st.metric(
                        "Altmetric Badge",
                        "N/A",
                        border=False,
                        help="Altmetric attention badge not available for this publication"
                    )
        else:
            # Only show section if this is likely a publication that could have Altmetric data
            # (i.e., has OpenAlex IDs indicating it was processed with enrichment)
            if 'openalex_ids' in pub_data:
                st.markdown("#### Altmetric Attention")
                st.info("No Altmetric data available for this publication.")


# Register component
ComponentRegistry.register("streamlit_app", StreamlitAppComponent)
