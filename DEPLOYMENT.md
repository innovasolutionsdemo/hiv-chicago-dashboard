# Free Deployment Guide

Use Streamlit Community Cloud for a free public deployment.

## Files To Push

Push this repository exactly as-is, including:

- `app.py`
- `requirements.txt`
- `README.md`
- `data/community_hiv_incidence.csv`
- `data/citywide_gender.csv`
- `data/citywide_race_ethnicity.csv`
- `data/citywide_age.csv`
- `data/chicago_community_areas.geojson`

Do not push the local `reference-ai/` folder. It is ignored by `.gitignore`.

## Deploy On Streamlit Community Cloud

1. Create a new GitHub repository, for example `chicago-hiv-dashboard`.
2. Push this folder to that repository.
3. Go to https://share.streamlit.io.
4. Click **Create app**.
5. Select your GitHub repository and branch.
6. Set the main file path to `app.py`.
7. Click **Deploy**.

The app will receive a public URL like:

```text
https://your-app-name.streamlit.app
```

## Data Note

The HIV incidence values are transcribed from the provided PDF only. `No data` values are preserved and are not converted to zero. The Chicago community-area GeoJSON is used only as a geography boundary layer.
