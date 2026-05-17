# Institution Rankings and Top Citing Institutions

## Overview

ScholarImpact now adds Scimago institution rankings to your citation data, allowing the dashboard to display top citing institutions sorted by prominence.

## Features

- **Institution Rankings**: Scimago 2026 global rankings (15,000+ institutions)
- **Top Citing Institutions Table**: Dashboard displays institutions sorted by prominence
- **Smart Matching**: Fuzzy matching for institution name variations
- **Persistent Data**: Rankings stored in citations JSON for reuse

## Workflow

### 1. Add Institution Rankings to Citations

After crawling citations, add institution ranking data:

```bash
scholarimpact add-rankings data/cites-XXXXX.json
```

This command:
- Reads the citations JSON file
- Matches each institution against Scimago rankings
- Adds `institution_rank` and `institution_rank_weight` to each author
- Updates the file in place
- Displays enrichment summary

**Output:**
```
File: data/cites-12862953873024122861.json
Enriched entries: 145
Ranked institutions: 78
Total citations: 156
```

### 2. View in Dashboard

The enriched data is automatically displayed in the Streamlit dashboard:

```bash
scholarimpact generate-dashboard data/
```

For each article, scroll to the "Top Citing Institutions" section to see a table of institutions sorted by Scimago ranking.

## Dashboard Display

### Top Citing Institutions Table

Shows all institutions citing your work, sorted by Scimago prominence ranking:

| Institution | Citations | Scimago Rank |
|---|---|---|
| Arizona State University | 12 | #357 |
| Institute for Development... | 5 | N/A |
| University of Münster | 2 | N/A |

- **Institution**: Name of the citing institution
- **Citations**: Number of citing papers from that institution
- **Scimago Rank**: Global research ranking (1 = most prominent)

## Data Structure

After enrichment, each citing author includes:

```json
{
  "citing_authors_details": [
    {
      "name": "Oliver Meyer",
      "institution_display_name": "Arizona State University",
      "institution_rank": 186,           // Scimago global rank
      "institution_rank_weight": 0.74,   // Normalized 0-1
      "country": "US",
      "openalex_author_id": "..."
    }
  ]
}
```

## Institution Ranking Details

### Scimago Ranking System

- **Global Rank**: 1-15,000+ institutions worldwide
- **Sectors**: Universities, Government, Companies, Health, etc.
- **Countries**: All countries represented
- **Weight Calculation**:
  - Top 100 institutions: weight 0.3-1.0 (linear scale)
  - Ranked 101-5000: weight 0.1-0.3
  - Beyond 5000: weight 0.0

### Matching Algorithm

1. **Exact match**: Direct name lookup
2. **Normalized match**: Case-insensitive match
3. **Partial match**: >70% word overlap

## Installation

Rankings feature requires optional dependencies:

```bash
pip install "scholarimpact[network]"
```

This installs:
- `networkx>=3.0.0` - Network analysis
- `pyvis>=0.3.0` - Data processing

## Data Distribution

The Scimago rankings file is bundled with the package:
- Location: `src/scholarimpact/data/ScimagoIR2026-OverallRank.csv`
- Automatically loaded by the InstitutionRankings class
- Can be customized by passing a different file path

## Examples

### Basic Usage

```bash
# 1. Extract
scholarimpact extract-author 4HhfAe0AAAAJ

# 2. Crawl
scholarimpact crawl-citations data/author.json

# 3. Add rankings
scholarimpact add-rankings data/cites-*.json

# 4. View in dashboard
scholarimpact generate-dashboard data/
```

### Bulk Processing

```bash
# Add rankings to all citations files
for file in data/cites-*.json; do
  scholarimpact add-rankings "$file"
done
```

## Troubleshooting

### Institutions not being ranked

**Problem**: Institution names don't match Scimago database

**Solutions**:
1. Check institution name spelling
2. Use the exact name from Scimago CSV
3. The fuzzy matcher should catch most variations (>70% match)
4. Update Scimago file if very new institutions

### Low enrichment percentage

**Problem**: Only a few entries have rankings

**Possible causes**:
- Institution names are abbreviated differently
- Institutions are very new (not yet in Scimago)
- Institutions have non-English names

The system gracefully handles unranked institutions - they display as "N/A" in the dashboard table.

## Future Enhancements

Potential improvements:
- Real-time institution ranking updates from Scimago API
- Custom institution rankings per user
- Filtering table by rank range or country
- Export rankings data as CSV
