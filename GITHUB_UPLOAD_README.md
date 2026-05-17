# HIV Chicago Dashboard GitHub Updates

Upload these files to the same paths in the GitHub repository.

## Dashboard Code

- `app.py`  
  Streamlit dashboard with the updated Social Determinants section, three toggleable correlation heatmaps, filtered indicators, and explanatory hover text.

## Data Files

- `data/hiv_priority_factor_correlations.csv`  
  Correlations for the main city-action priority factors, including housing, healthcare access, economic hardship, race/structural inequity, and education/opportunity.

- `data/hiv_community_stress_correlations.csv`  
  Correlations for community stress and structural-risk indicators, including crime proxies, youth justice, substance use, mental health, food access, and clinical access.

- `data/chicago_acs_community_demographics_2023.csv`  
  2023 community-area race/ethnicity percentages from the City of Chicago ACS community-area data.

## Reports

- `reports/hiv_indicator_selection_report.pdf`  
  PDF explanation of which indicators were included or excluded from the heatmaps and why.

- `reports/hiv_indicator_selection_audit.csv`  
  CSV audit table behind the PDF report.

## Notes

- Heatmaps only show indicators with average absolute correlation `>= 0.15`.
- Correlations are exploratory and should not be presented as proof of causation.
- Crime and legal-system indicators should be interpreted as community stress, reporting, enforcement, and structural-risk proxies.
- Race variables should be framed as structural context around segregation and disinvestment, not individual-level or biological risk.
