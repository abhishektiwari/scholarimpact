# ScholarImpact Data Files

This directory contains data files used by ScholarImpact for citation analysis and visualization.

## Scimago Institutions Ranking

The Scimago Institutions Ranking dataset is used to identify and rank institutions based on their research output and impact.

### Citation

When using ScholarImpact with Scimago rankings data, please cite:

> SCImago, (n.d.). SJR—SCImago Journal Country & Rank [Portal]. Retrieved from https://www.scimagojr.com

### Data Source

- **Source**: Scimago Research Group
- **Portal**: https://www.scimagojr.com
- **Coverage**: Global research institutions across multiple sectors
- **Update Frequency**: Annual

### Usage

The rankings data is automatically downloaded or bundled with ScholarImpact and used by the `add-rankings` command to enrich citation data with institutional prestige information.

### Data Format

The Scimago rankings CSV contains the following fields:
- **Global Rank**: Numerical ranking (1 = most prominent)
- **Institution**: Name of the research institution
- **Country**: Country code or name
- **Sector**: Type of institution (Universities, Government, Companies, Health, Non-Profit)
- **Best Country Quartile**: Performance quartile within the country

## License and Attribution

Please ensure proper attribution when using ScholarImpact data and analysis in your research or publications.
