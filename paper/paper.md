---
title: 'ScholarImpact: A Python tool to analyse, visualise, and share your research impact, output and scholarly influence using bibliometric data'
tags:
  - Python
  - bibliometrics
  - research impact
  - citation analysis
  - scholarly communication
  - OpenAlex
  - Google Scholar
authors:
  - name: Abhishek Tiwari
    orcid: 0000-0003-2222-2395
    affiliation: 1
affiliations:
  - name: D3ML
    index: 1
date: 6 October 2025
bibliography: paper.bib
---

# Summary

ScholarImpact is a Python-based bibliometric analysis tool designed to help researchers analyse, visualise, and share their research impact, output and scholarly influence. The software extracts initial data from a given Google Scholar profile and performs enrichment using OpenAlex [@priem2022openalex] and Altmetric [@adie2013altmetric] to provide multidimensional insights into citation patterns, geographic distribution, institutional reach, patent citations, and interdisciplinary influence. Unlike traditional citation metrics that provide only aggregate counts, ScholarImpact enables researchers to understand who is citing their work, where citations originate geographically and institutionally, and how their research impacts different domains and disciplines.

The tool features an interactive Streamlit-based dashboard that visualizes key metrics including total citations, unique citing authors, institutional diversity, country distribution, temporal citation trends, research domain analysis, and alternative metrics such as patent citations and Wikipedia mentions. ScholarImpact is distributed as a pip-installable package with a command-line interface that automates data extraction, enrichment, and visualization, making sophisticated bibliometric analysis accessible to researchers without specialized technical expertise.

# Statement of Need

While numerous bibliometric tools exist, most focus exclusively on citation counts and h-indices, providing limited insight into the breadth and diversity of research impact [@hirsch2005index]. Individual researchers increasingly need to demonstrate and communicate their impact beyond traditional metrics, including geographic reach, interdisciplinary influence, and societal engagement [@bornmann2014alternative]. Existing commercial platforms like Web of Science, Dimension AI, and Scopus offer some geographic and institutional analysis but require expensive institutional subscriptions, lack personalization, and do not provide researchers with shareable visualizations of their own impact [@archambault2009comparison].

ScholarImpact addresses these gaps by providing an open-source, accessible solution that combines data from multiple sources to deliver comprehensive impact analysis. The tool is designed for individual researchers seeking to understand and communicate their research impact for grant applications, tenure reviews, and personal career development.

# Brief Overview
For data extraction, ScholarImpact uses publicly available APIs and web scraping techniques that respect rate limits and terms of service. The modular design separates data collection (`extract-author` and `crawl-citations` commands), enrichment (OpenAlex and Altmetric integration), and visualization (Streamlit dashboard), allowing researchers to customize workflows. The `generate-dashboard` command creates standalone deployable projects suitable for sharing via Streamlit Cloud, enabling researchers to publicly showcase their impact.

ScholarImpact leverages the scholarly-python library [@cholewiak2021scholarly] for Google Scholar data extraction and integrates with OpenAlex's comprehensive open bibliographic database to enrich citation data with institutional affiliations, country codes, and research domain classifications [@priem2022openalex]. Altmetric integration provides alternative impact indicators including social media mentions, policy document citations, and patent references [@adie2013altmetric]. The visualization framework uses Plotly [@plotly] for interactive charts and maps, allowing dynamic exploration of citation patterns across time, geography, and research domains.

![Example dashboard showing research domains analysis, interdisciplinary impact metrics including patents and wikipedia mentions, and alternative metrics.](https://static.abhishek-tiwari.com/scholarimpact/research-domains-v4.png)

The tool fills a critical niche by democratizing access to sophisticated bibliometric analysis. By combining open data sources with an intuitive interface and deployment-ready architecture, ScholarImpact enables researchers across disciplines and career stages to gain actionable insights into their scholarly influence. The software has been used to analyze citation patterns across computer science, social sciences, and interdisciplinary research, demonstrating its flexibility and broad applicability.

Future development roadmap includes enhanced citation network analysis, co-authorship visualization, comparative benchmarking against field averages, and integration with additional data sources such as ORCID [@haak2012orcid] and CrossRef [@hendricks2020crossref]. Community contributions are welcome via the project's GitHub repository.

# Acknowledgements

The author acknowledges the open-source communities behind scholarly-python, OpenAlex, Streamlit, and the broader Python scientific computing ecosystem. This work builds upon the foundations established by these projects to advance open science and reproducible research.

# References
