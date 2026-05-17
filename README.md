# Chicago HIV Incidence Dashboard

Streamlit dashboard for Chicago HIV incidence data transcribed from the provided PDF.

The data files in `data/` transcribe the values printed in the PDF only. `No data` is preserved as `No data` and is not treated as zero.

`data/chicago_community_areas.geojson` is the official City of Chicago community-area boundary layer from the City of Chicago Data Portal. It is used only to draw the map geometry; it does not add or modify HIV incidence values.

Run locally:

```bash
streamlit run app.py
```

Deploy for free with Streamlit Community Cloud. See `DEPLOYMENT.md`.
