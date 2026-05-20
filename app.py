import json
from copy import deepcopy

import branca.colormap as cm
import folium
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from streamlit_folium import st_folium


st.set_page_config(
    page_title="Chicago HIV Incidence Dashboard",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
)

YEAR_COLUMNS = ["2019", "2020", "2021", "2022", "2023"]
CORRELATION_SIGNAL_THRESHOLD = 0.15
ACCENT_BLUE = "#2563eb"
ACCENT_TEAL = "#0f766e"
ACCENT_GREEN = "#16a34a"
ACCENT_RED = "#dc2626"
ACCENT_AMBER = "#d97706"
BG = "#f8fafc"
PANEL_BG = "#ffffff"
TEXT = "#0f172a"
MUTED = "#64748b"
GENDER_COLORS = {
    "Cisgender Male": "#2563eb",
    "Cisgender Female": "#db2777",
}
RACE_COLORS = {
    "White non-hispanic": "#60a5fa",
    "Black Non Hispanic": "#1d4ed8",
    "Asian or pacific islander non-hispanic": "#14b8a6",
    "Hispanic or Latino": "#f59e0b",
}
AGE_COLORS = {
    "13-19": "#bfdbfe",
    "20-29": "#93c5fd",
    "30-39": "#60a5fa",
    "40-49": "#2563eb",
    "50-59": "#1d4ed8",
    "60+": "#0f172a",
}
DETERMINANT_COLORS = {
    "Economic factors": ACCENT_TEAL,
    "Healthcare access": ACCENT_BLUE,
    "Housing & neighborhood": ACCENT_AMBER,
}
MAP_MODES = {
    "Current": {
        "value_column": "current_value",
        "display_column": "current_display",
        "caption": "Current HIV incidence",
        "palette": ["#dbeafe", "#93c5fd", "#2563eb", "#1e3a8a"],
    },
    "Potential": {
        "value_column": "potential_value",
        "display_column": "potential_display",
        "caption": "Potential target incidence",
        "palette": ["#ccfbf1", "#5eead4", "#0f766e", "#134e4a"],
    },
    "Improvement opportunities": {
        "value_column": "opportunity_value",
        "display_column": "opportunity_display",
        "caption": "Improvement opportunity",
        "palette": ["#fef3c7", "#fbbf24", "#f97316", "#b91c1c"],
    },
}
PROTECTIVE_DETERMINANTS = [
    {
        "key": "owner_occupied",
        "label": "Owner occupied housing",
        "field": "HUO_2020-2024",
        "favorable": "higher",
        "value_type": "percent",
        "why": "Housing stability can support continuity in prevention, testing, and care.",
    },
    {
        "key": "primary_care",
        "label": "Primary care provider access",
        "field": "HCSPCPP_2023-2024",
        "favorable": "higher",
        "value_type": "percent",
        "why": "Regular care access can improve screening, PrEP referral, STI treatment, and linkage to HIV care.",
    },
    {
        "key": "uninsured",
        "label": "Uninsured rate",
        "field": "UNS_2020-2024",
        "favorable": "lower",
        "value_type": "percent",
        "why": "Lower uninsured rates can make prevention visits, testing, medication, and follow-up easier to sustain.",
    },
    {
        "key": "income",
        "label": "Median household income",
        "field": "INC_2020-2024",
        "favorable": "higher",
        "value_type": "currency",
        "why": "Higher household resources can reduce barriers to transportation, care access, and consistent prevention.",
    },
    {
        "key": "routine_checkup",
        "label": "Routine checkup",
        "field": "HCSRCP_2023-2024",
        "favorable": "higher",
        "value_type": "percent",
        "why": "Preventive visits create more opportunities for HIV testing, PrEP conversations, and earlier care connection.",
    },
]


st.markdown(
    f"""
<style>
    .stApp {{
        background-color: {BG};
        color: {TEXT};
    }}
    .main .block-container {{
        padding-top: 1.5rem;
        padding-bottom: 2.5rem;
        max-width: 1220px;
    }}
    section[data-testid="stSidebar"] {{
        background-color: {PANEL_BG};
        border-right: 1px solid #e2e8f0;
    }}
    h1, h2, h3, h4, h5, h6, p, label, .stMarkdown {{
        color: {TEXT} !important;
    }}
    .main-header {{
        font-size: 2.35rem;
        color: {TEXT};
        text-align: left;
        margin-bottom: 0.2rem;
        font-weight: 750;
        letter-spacing: 0;
    }}
    .sub-header {{
        font-size: 1.02rem;
        color: {MUTED} !important;
        text-align: left;
        margin-bottom: 1.5rem;
        max-width: 760px;
    }}
    .nav-summary-gap {{
        height: 1.3rem;
    }}
    .summary-section-gap {{
        height: 2rem;
    }}
    .metric-card,
    .insight-box {{
        background: {PANEL_BG};
        padding: 0.9rem;
        border-radius: 8px;
        height: 160px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 10px 28px rgba(15, 23, 42, 0.06);
        overflow: hidden;
    }}
    .metric-card h3,
    .insight-box h3 {{
        font-size: 0.82rem;
        color: {MUTED} !important;
        margin: 0 0 0.45rem 0;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0;
    }}
    .metric-card .value {{
        font-size: 1.75rem;
        line-height: 1;
        color: {TEXT};
        font-weight: 800;
    }}
    .metric-card .note {{
        font-size: 0.82rem;
        color: {MUTED} !important;
        margin-top: 0.55rem;
        line-height: 1.32;
    }}
    .trend-up {{
        color: {ACCENT_RED};
        font-weight: 800;
    }}
    .trend-down {{
        color: {ACCENT_GREEN};
        font-weight: 800;
    }}
    .trend-flat {{
        color: {MUTED};
        font-weight: 800;
    }}
    .insight-box p {{
        margin: 0;
        color: {MUTED} !important;
        line-height: 1.34;
        font-size: 0.84rem;
    }}
    .selected-community-tile {{
        background: linear-gradient(135deg, #0f172a 0%, #164e63 100%);
        border: 1px solid rgba(20, 184, 166, 0.36);
        border-radius: 8px;
        box-shadow: 0 18px 40px rgba(15, 23, 42, 0.22);
        padding: 1.1rem;
        margin-top: 1rem;
    }}
    .selected-community-tile h3 {{
        margin: 0 0 0.9rem 0;
        font-size: 1.25rem;
        color: #ffffff !important;
    }}
    .selected-community-grid {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.9rem;
    }}
    .selected-community-stat {{
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.18);
        border-radius: 8px;
        padding: 0.9rem;
    }}
    .selected-community-stat .label {{
        color: #a7f3d0;
        font-size: 0.78rem;
        font-weight: 750;
        text-transform: uppercase;
    }}
    .selected-community-stat .value {{
        color: #ffffff;
        font-size: 1.45rem;
        font-weight: 800;
        line-height: 1.1;
        margin-top: 0.4rem;
    }}
    .selected-community-stat .note {{
        color: #d1fae5;
        font-size: 0.86rem;
        margin-top: 0.4rem;
    }}
    div[data-testid="stDataFrame"] {{
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        overflow: hidden;
    }}
    .community-table {{
        width: 100%;
        border-collapse: collapse;
        background: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
    }}
    .community-table th {{
        background: #0f172a;
        color: #ffffff;
        font-weight: 750;
        padding: 0.7rem 0.8rem;
        text-align: left;
    }}
    .community-table td {{
        color: {TEXT};
        padding: 0.65rem 0.8rem;
        border-top: 1px solid #e2e8f0;
    }}
    .community-table tr:nth-child(even) td {{
        background: #eff6ff;
    }}
    .determinants-table {{
        width: 100%;
        border-collapse: collapse;
        background: #ffffff;
        border: 1px solid #94a3b8;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
        margin: 0.85rem 0 1rem 0;
    }}
    .determinants-table th {{
        background: #0f766e;
        color: #ffffff;
        font-weight: 800;
        padding: 0.78rem 0.85rem;
        text-align: left;
        border: 1px solid #0f766e;
    }}
    .determinants-table td {{
        color: {TEXT};
        padding: 0.72rem 0.85rem;
        border: 1px solid #cbd5e1;
        vertical-align: top;
    }}
    .determinants-table tbody tr:nth-child(odd) td {{
        background: #f0fdfa;
    }}
    .determinants-table tbody tr:nth-child(even) td {{
        background: #ffffff;
    }}
    .determinants-table .section-cell {{
        background: #164e63 !important;
        color: #ffffff;
        font-weight: 800;
        width: 24%;
    }}
    .indicator-explainer {{
        background: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        padding: 1rem;
        margin-top: 1rem;
        box-shadow: 0 12px 28px rgba(15, 23, 42, 0.08);
    }}
    .indicator-explainer h3 {{
        margin: 0 0 0.75rem 0;
        color: {TEXT} !important;
        font-size: 1.15rem;
        font-weight: 850;
    }}
    .indicator-explainer .determinants-table {{
        margin-bottom: 0.85rem;
    }}
    .community-summary-card {{
        background: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        box-shadow: 0 16px 36px rgba(15, 23, 42, 0.12);
        padding: 1rem;
        margin: 0.5rem 0 1rem 0;
    }}
    .community-summary-card h3 {{
        margin: 0;
        color: {TEXT} !important;
        font-size: 1.45rem;
        font-weight: 850;
    }}
    .community-summary-card .geoid {{
        color: {MUTED};
        font-size: 0.95rem;
        margin-top: 0.35rem;
        font-weight: 700;
    }}
    .summary-stat-grid {{
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.8rem;
        margin: 1rem 0;
    }}
    .summary-stat {{
        background: #f0fdfa;
        border: 1px solid #99f6e4;
        border-radius: 8px;
        padding: 0.85rem;
    }}
    .summary-stat.current {{
        background: #eff6ff;
        border-color: #bfdbfe;
    }}
    .summary-stat.opportunity {{
        background: #fff7ed;
        border-color: #fed7aa;
    }}
    .summary-stat .value {{
        color: {TEXT};
        font-size: 2rem;
        line-height: 1;
        font-weight: 900;
    }}
    .summary-stat .label {{
        color: {MUTED};
        font-size: 0.78rem;
        margin-top: 0.45rem;
        text-transform: uppercase;
        font-weight: 800;
    }}
    .opportunity-list {{
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 0.9rem 1rem;
        margin-top: 0.8rem;
    }}
    .opportunity-list h4 {{
        margin: 0 0 0.65rem 0;
        color: {TEXT} !important;
        font-size: 1rem;
        font-weight: 850;
    }}
    .opportunity-list ol {{
        margin: 0;
        padding-left: 1.35rem;
    }}
    .opportunity-list li {{
        color: {TEXT};
        margin: 0.35rem 0;
        font-weight: 750;
    }}
    .opportunity-list span {{
        color: {MUTED};
        font-weight: 650;
    }}
    .stTabs [data-baseweb="tab-list"] {{
        gap: 1.35rem;
        margin-top: 1.65rem;
        margin-bottom: 1.5rem;
    }}
    .stTabs [data-baseweb="tab"] {{
        background: #e2e8f0;
        border-radius: 8px;
        color: {TEXT};
        padding: 0.72rem 1.35rem;
        min-width: 150px;
        justify-content: center;
    }}
    div[role="radiogroup"] {{
        display: grid !important;
        grid-template-columns: repeat(5, minmax(0, 1fr));
        gap: 0.9rem;
        margin: 1.6rem 0 0 0;
        background: #ffffff;
        border: 1px solid #dbe3ef;
        border-radius: 10px;
        padding: 0.45rem;
        box-shadow: 0 10px 26px rgba(15, 23, 42, 0.05);
    }}
    div[role="radiogroup"] label {{
        background: #f8fafc;
        border: 1px solid transparent;
        border-radius: 8px;
        padding: 0.82rem 1rem;
        min-width: 0;
        justify-content: center;
        text-align: center;
        transition: all 160ms ease;
    }}
    div[role="radiogroup"] label:hover {{
        background: #e0f2fe;
        border-color: #93c5fd;
    }}
    div[role="radiogroup"] label:has(input:checked) {{
        background: #0f172a;
        border-color: #0f172a;
        box-shadow: 0 8px 18px rgba(15, 23, 42, 0.16);
    }}
    div[role="radiogroup"] label:has(input:checked) p {{
        color: #ffffff !important;
        font-weight: 750;
    }}
    div[role="radiogroup"] label p {{
        color: {TEXT} !important;
        font-weight: 700;
    }}
    .js-plotly-plot .plotly .main-svg text {{
        fill: {TEXT} !important;
    }}
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_data
def load_data():
    community_raw = pd.read_csv("data/community_hiv_incidence.csv", dtype=str)
    gender = pd.read_csv("data/citywide_gender.csv")
    race = pd.read_csv("data/citywide_race_ethnicity.csv")
    age = pd.read_csv("data/citywide_age.csv")
    with open("data/chicago_community_areas.geojson", encoding="utf-8") as geojson_file:
        geography = json.load(geojson_file)

    community_numeric = community_raw.copy()
    for year in YEAR_COLUMNS:
        community_numeric[year] = pd.to_numeric(community_numeric[year], errors="coerce")
    community_numeric["Map key"] = community_numeric["Place"].str.upper().str.replace("'", "", regex=False)
    community_raw["Map key"] = community_raw["Place"].str.upper().str.replace("'", "", regex=False)

    community_long = community_numeric.melt(
        id_vars=["Place", "Map key"],
        value_vars=YEAR_COLUMNS,
        var_name="Year",
        value_name="HIV incidence",
    )
    community_long["Year"] = community_long["Year"].astype(int)
    return community_raw, community_numeric, community_long, gender, race, age, geography


@st.cache_data
def load_social_determinants_data():
    analysis = pd.read_csv("data/hiv_coc_selected_analysis.csv")
    master_indicators = pd.read_excel(
        "data/hiv_coc_master_from_zip.xlsx",
        sheet_name="All ZIP fields",
        usecols=[
            "Map key",
            "HUO_2020-2024",
            "HCSPCPP_2023-2024",
            "UNS_2020-2024",
            "INC_2020-2024",
            "HCSRCP_2023-2024",
        ],
    )
    analysis = analysis.merge(master_indicators, on="Map key", how="left")
    correlations = pd.read_csv("data/hiv_coc_correlations.csv")
    priority_correlations = pd.read_csv("data/hiv_priority_factor_correlations.csv")
    stress_correlations = pd.read_csv("data/hiv_community_stress_correlations.csv")
    for year in YEAR_COLUMNS:
        correlations[year] = pd.to_numeric(correlations[year], errors="coerce")
        correlations[f"n_{year}"] = pd.to_numeric(correlations[f"n_{year}"], errors="coerce")
        priority_correlations[year] = pd.to_numeric(priority_correlations[year], errors="coerce")
        priority_correlations[f"n_{year}"] = pd.to_numeric(priority_correlations[f"n_{year}"], errors="coerce")
        stress_correlations[year] = pd.to_numeric(stress_correlations[year], errors="coerce")
        stress_correlations[f"n_{year}"] = pd.to_numeric(stress_correlations[f"n_{year}"], errors="coerce")
    priority_correlations["Average absolute correlation"] = pd.to_numeric(
        priority_correlations["Average absolute correlation"],
        errors="coerce",
    )
    stress_correlations["Average absolute correlation"] = pd.to_numeric(
        stress_correlations["Average absolute correlation"],
        errors="coerce",
    )
    return analysis, correlations, priority_correlations, stress_correlations


def plot_template(fig):
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor=PANEL_BG,
        plot_bgcolor=PANEL_BG,
        font=dict(color=TEXT, size=13),
        margin=dict(l=24, r=24, t=54, b=46),
        colorway=[ACCENT_BLUE, ACCENT_TEAL, ACCENT_AMBER, ACCENT_RED],
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.15,
            xanchor="left",
            x=0,
            font=dict(color=TEXT, size=12),
            bgcolor="rgba(255,255,255,0.9)",
        ),
        hoverlabel=dict(
            bgcolor="#ffffff",
            bordercolor="#cbd5e1",
            font=dict(color=TEXT, size=12),
        ),
        title=dict(font=dict(color=TEXT, size=17)),
    )
    fig.update_xaxes(gridcolor="#e2e8f0", zerolinecolor="#e2e8f0", color=TEXT, title_font=dict(color=TEXT), tickfont=dict(color=TEXT))
    fig.update_yaxes(gridcolor="#e2e8f0", zerolinecolor="#e2e8f0", color=TEXT, title_font=dict(color=TEXT), tickfont=dict(color=TEXT))
    return fig


def trend_details(current_value, previous_value):
    delta = current_value - previous_value
    if delta > 0:
        return "up", "↑", f"+{delta:,.0f} vs prior year"
    if delta < 0:
        return "down", "↓", f"{delta:,.0f} vs prior year"
    return "flat", "→", "No change vs prior year"


def metric_card(title, value, note, trend=None):
    trend_markup = ""
    if trend:
        direction, symbol, text = trend
        trend_markup = f'<span class="trend-{direction}">{symbol}</span> {text}'
    note_markup = trend_markup or note
    st.markdown(
        f"""
        <div class="metric-card">
            <h3>{title}</h3>
            <div class="value">{value}</div>
            <div class="note">{note_markup}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def insight_box(title, body):
    st.markdown(
        f"""
        <div class="insight-box">
            <h3>{title}</h3>
            <p>{body}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def selected_community_tile(place, max_increase, max_decrease):
    if max_increase is None:
        increase_value = "No increase"
        increase_note = "Across available years"
    else:
        increase_value = f"{int(max_increase['Year'])}"
        increase_note = f"↑ +{int(max_increase['Delta'])} cases"

    if max_decrease is None:
        decrease_value = "No reduction"
        decrease_note = "Across available years"
    else:
        decrease_value = f"{int(max_decrease['Year'])}"
        decrease_note = f"↓ {abs(int(max_decrease['Delta']))} fewer cases"

    st.markdown(
        f"""
        <div class="selected-community-tile">
            <h3>{place}</h3>
            <div class="selected-community-grid">
                <div class="selected-community-stat">
                    <div class="label">Largest Increase</div>
                    <div class="value">{increase_value}</div>
                    <div class="note">{increase_note}</div>
                </div>
                <div class="selected-community-stat">
                    <div class="label">Largest Reduction</div>
                    <div class="value">{decrease_value}</div>
                    <div class="note">{decrease_note}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def selected_community_map_details(properties):
    if not properties:
        return

    previous_label = properties.get("previous_label", "Previous year")
    current_label = f"{properties.get('map_year', 'Selected year')} current"
    opportunity_items = []
    for determinant in PROTECTIVE_DETERMINANTS:
        value = properties.get(f"determinant_{determinant['key']}", "No data")
        action = "Increase" if determinant["favorable"] == "higher" else "Reduce"
        icon = "📈" if determinant["favorable"] == "higher" else "📉"
        opportunity_items.append(
            f"<li>{icon} {action} {determinant['label']} <span>{value}</span></li>"
        )

    st.markdown(
        f"""
        <div class="community-summary-card">
            <h3>📍 {properties.get('display_community', 'Selected community')}</h3>
            <div class="geoid">GEOID: {properties.get('geoid', 'No data')}</div>
            <div class="summary-stat-grid">
                <div class="summary-stat current">
                    <div class="value">{properties.get('current_display', 'No data')}</div>
                    <div class="label">Current</div>
                </div>
                <div class="summary-stat">
                    <div class="value">{properties.get('potential_display', 'No data')}</div>
                    <div class="label">Potential</div>
                </div>
                <div class="summary-stat opportunity">
                    <div class="value">{properties.get('opportunity_display', 'No data')}</div>
                    <div class="label">Improvement opportunity</div>
                </div>
            </div>
            <div class="opportunity-list">
                <h4>🎯 Improvement Opportunities</h4>
                <ol>
                    {''.join(opportunity_items)}
                </ol>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    detail_rows = [
        ("Current", properties.get("mode_display", "No data")),
        (current_label, properties.get("current_display", "No data")),
        ("Potential target", properties.get("potential_display", "No data")),
        ("Improvement opportunity", properties.get("opportunity_display", "No data")),
        (f"{previous_label} incidence", properties.get("previous_display", "No data")),
        ("Change", properties.get("growth_display", "N/A")),
        ("Opportunity note", properties.get("opportunity_note", "No current data")),
        ("Owner occupied housing", properties.get("determinant_owner_occupied", "No data")),
        ("Primary care provider access", properties.get("determinant_primary_care", "No data")),
        ("Uninsured rate", properties.get("determinant_uninsured", "No data")),
        ("Median household income", properties.get("determinant_income", "No data")),
        ("Routine checkup", properties.get("determinant_routine_checkup", "No data")),
    ]
    rows = "".join(
        f"""
        <tr>
            <td>{label}</td>
            <td>{value}</td>
        </tr>
        """
        for label, value in detail_rows
    )
    st.markdown(
        f"""
        <table class="determinants-table">
            <thead>
                <tr>
                    <th>Measure</th>
                    <th>Value</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
        """,
        unsafe_allow_html=True,
    )


@st.dialog("Community Summary", width="large")
def selected_community_dialog(place, trend_df, max_increase, max_decrease, map_properties=None):
    selected_community_map_details(map_properties)
    selected_community_tile(place, max_increase, max_decrease)
    fig = community_trend_chart(trend_df, f"{place} 5-Year Trend")
    st.plotly_chart(fig, width='stretch')


def melt_breakdown(df, label):
    value_cols = [c for c in df.columns if c not in ["Year", "Total"]]
    long = df.melt(id_vars="Year", value_vars=value_cols, var_name=label, value_name="Cases")
    return long


def format_change(current_value, previous_value):
    if pd.isna(current_value) or pd.isna(previous_value):
        return "N/A"
    delta = int(current_value - previous_value)
    if delta > 0:
        return f"↑ +{delta}"
    if delta < 0:
        return f"↓ {delta}"
    return "→ 0"


def format_determinant_value(value, value_type):
    if pd.isna(value):
        return "No data"
    if value_type == "currency":
        return f"${float(value):,.0f}"
    if value_type == "percent":
        return f"{float(value):.1f}%"
    if value_type == "number":
        return f"{float(value):,.0f}"
    return f"{float(value):,.1f}"


def community_trend_frame(community_raw, map_key):
    selected_row = community_raw.loc[community_raw["Map key"].eq(map_key)].iloc[0]
    trend_df = pd.DataFrame(
        {"Year": [int(year) for year in YEAR_COLUMNS], "Cases": [selected_row[year] for year in YEAR_COLUMNS]}
    )
    trend_df["Cases"] = pd.to_numeric(trend_df["Cases"], errors="coerce")
    trend_df["Delta"] = trend_df["Cases"].diff()
    trend_df["Change"] = [
        "N/A" if index == 0 else format_change(row["Cases"], trend_df.loc[index - 1, "Cases"])
        for index, row in trend_df.iterrows()
    ]
    return trend_df


def trend_extremes(trend_df):
    changes = trend_df.dropna(subset=["Delta"])
    increases = changes.loc[changes["Delta"] > 0]
    decreases = changes.loc[changes["Delta"] < 0]
    max_increase = None if increases.empty else increases.loc[increases["Delta"].idxmax()]
    max_decrease = None if decreases.empty else decreases.loc[decreases["Delta"].idxmin()]
    return max_increase, max_decrease


def community_insight_text(place, trend_df):
    available = trend_df.dropna(subset=["Cases"])
    if available.empty:
        return f"{place} has no available yearly case values in the current dataset."

    latest = available.iloc[-1]
    max_increase, max_decrease = trend_extremes(trend_df)
    direction = "no year-over-year change"
    if not pd.isna(latest["Delta"]):
        if latest["Delta"] > 0:
            direction = f"an increase of {int(latest['Delta'])} cases from the prior year"
        elif latest["Delta"] < 0:
            direction = f"a reduction of {abs(int(latest['Delta']))} cases from the prior year"

    increase_text = "no increase year"
    if max_increase is not None:
        increase_text = f"the largest increase was in {int(max_increase['Year'])} (+{int(max_increase['Delta'])})"

    decrease_text = "no reduction year"
    if max_decrease is not None:
        decrease_text = f"the largest reduction was in {int(max_decrease['Year'])} ({abs(int(max_decrease['Delta']))} fewer)"

    return (
        f"{place} recorded {int(latest['Cases'])} cases in {int(latest['Year'])}, showing {direction}. "
        f"Across the five-year trend, {increase_text}, while {decrease_text}."
    )


def community_trend_chart(trend_df, title, selected_year=None):
    plot_points = trend_df.dropna(subset=["Cases"]).copy()
    plot_points["Change Label"] = plot_points["Delta"].apply(
        lambda value: "" if pd.isna(value) else ("↑" if value > 0 else "↓" if value < 0 else "→")
    )
    fig = px.line(plot_points, x="Year", y="Cases", markers=True, title=title)
    fig.update_traces(line=dict(color=ACCENT_AMBER, width=4), marker=dict(size=10, color=ACCENT_TEAL))
    fig.update_xaxes(type="linear", tickmode="array", tickvals=[int(year) for year in YEAR_COLUMNS])
    for _, row in plot_points.iterrows():
        if row["Change Label"]:
            fig.add_annotation(
                x=row["Year"],
                y=row["Cases"],
                text=row["Change Label"],
                showarrow=False,
                yshift=18,
                font=dict(color=ACCENT_RED if row["Delta"] > 0 else ACCENT_GREEN if row["Delta"] < 0 else MUTED, size=18),
            )

    if selected_year is not None:
        selected_year_int = int(selected_year)
        selected_point = plot_points.loc[plot_points["Year"].eq(selected_year_int)]
        if not selected_point.empty:
            selected_case = int(selected_point["Cases"].iloc[0])
            fig.add_annotation(
                x=selected_year_int,
                y=selected_case,
                text=f"{selected_year}: {selected_case:,}",
                showarrow=True,
                arrowcolor=ACCENT_BLUE,
                arrowwidth=1.5,
                ay=-46,
                font=dict(color=TEXT, size=12),
                bgcolor="#ffffff",
                bordercolor=ACCENT_BLUE,
                borderpad=4,
            )
    plot_template(fig)
    return fig


def correlation_strength(value):
    if pd.isna(value):
        return "No signal", "Insufficient paired data to interpret this year."
    magnitude = abs(value)
    if magnitude >= 0.50:
        level = "High"
    elif magnitude >= 0.30:
        level = "Medium"
    elif magnitude >= CORRELATION_SIGNAL_THRESHOLD:
        level = "Low"
    else:
        level = "Below threshold"

    direction = "positive" if value > 0 else "negative"
    if value > 0:
        explanation = "Communities with higher values for this indicator tend to have more HIV cases in this year."
    elif value < 0:
        explanation = "Communities with higher values for this indicator tend to have fewer HIV cases in this year."
    else:
        explanation = "This indicator shows no linear relationship with HIV cases in this year."
    return f"{level} {direction} association", explanation


def combined_correlation_data(*frames):
    prepared_frames = []
    for frame in frames:
        prepared = frame.copy()
        if "Average absolute correlation" not in prepared.columns:
            prepared["Average absolute correlation"] = prepared[YEAR_COLUMNS].abs().mean(axis=1)
        if "Direction" not in prepared.columns:
            prepared["Direction"] = prepared[YEAR_COLUMNS].mean(axis=1).map(
                lambda value: "Positive" if value > 0 else "Negative"
            )
        if "Analyst note" not in prepared.columns:
            prepared["Analyst note"] = prepared.get("Source", "Curated social determinant indicator")
        prepared_frames.append(prepared)

    combined = pd.concat(prepared_frames, ignore_index=True, sort=False)
    combined = combined.loc[
        ~combined["Category"].astype(str).str.contains("Behavioral", case=False, na=False)
    ].copy()
    combined = combined.sort_values("Average absolute correlation", ascending=False)
    combined = combined.drop_duplicates(subset=["Field"], keep="first")
    combined = combined.sort_values(["Category", "Average absolute correlation"], ascending=[True, False])
    return combined


def social_determinants_heatmap(correlations, title="", height=760):
    plot_df = correlations.copy()
    if "Average absolute correlation" not in plot_df.columns:
        plot_df["Average absolute correlation"] = plot_df[YEAR_COLUMNS].abs().mean(axis=1)
    plot_df = plot_df.loc[
        plot_df["Average absolute correlation"].ge(CORRELATION_SIGNAL_THRESHOLD)
    ].copy()
    if plot_df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text=f"No indicators meet the |r| threshold of {CORRELATION_SIGNAL_THRESHOLD:.2f}.",
            showarrow=False,
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            font=dict(size=15, color=MUTED),
        )
        plot_template(fig)
        fig.update_layout(title=title, height=260)
        return fig
    plot_df = plot_df.reset_index(drop=True)
    plot_df["Indicator label"] = plot_df["Category"] + " | " + plot_df["Indicator"]
    z_values = plot_df[YEAR_COLUMNS].to_numpy()
    sample_sizes = plot_df[[f"n_{year}" for year in YEAR_COLUMNS]].to_numpy()
    hover_text = []
    for row_index, row in plot_df.iterrows():
        source = row["Source"] if "Source" in row and pd.notna(row["Source"]) else row.get("Analyst note", "Chicago Health Atlas")
        row_hover = []
        for year_index, year in enumerate(YEAR_COLUMNS):
            value = row[year]
            strength, explanation = correlation_strength(value)
            row_hover.append(
                (
                    f"<b>{row['Indicator']}</b><br>"
                    f"Section: {row['Category']}<br>"
                    f"HIV year: {year}<br>"
                    f"Correlation: {value:+.3f}<br>"
                    f"Association strength: <b>{strength}</b><br>"
                    f"Interpretation: {explanation}<br>"
                    f"Average |r| across years: {row['Average absolute correlation']:.3f}<br>"
                    f"Communities compared: {int(sample_sizes[row_index][year_index])}<br>"
                    f"Note: correlation does not prove causation.<br>"
                    f"Source: {source}"
                )
            )
        hover_text.append(row_hover)

    fig = go.Figure(
        data=go.Heatmap(
            z=z_values,
            x=YEAR_COLUMNS,
            y=plot_df["Indicator label"],
            zmin=-1,
            zmax=1,
            colorscale=[
                [0, "#2563eb"],
                [0.5, "#ffffff"],
                [1, ACCENT_RED],
            ],
            colorbar=dict(title="Pearson r", tickvals=[-1, -0.5, 0, 0.5, 1]),
            text=[[f"{value:+.2f}" if pd.notna(value) else "N/A" for value in row] for row in z_values],
            texttemplate="%{text}",
            textfont=dict(color=TEXT, size=12),
            hoverinfo="text",
            hovertext=hover_text,
            hoverlabel=dict(
                bgcolor="#ffffff",
                bordercolor="#cbd5e1",
                font=dict(color=TEXT, size=12),
            ),
        )
    )
    for index in range(len(plot_df) - 1):
        if plot_df.loc[index, "Category"] != plot_df.loc[index + 1, "Category"]:
            fig.add_hline(y=index + 0.5, line_width=1, line_color="#cbd5e1")

    plot_template(fig)
    fig.update_layout(
        title=title,
        height=height,
        xaxis_title="HIV cases by year",
        yaxis_title="Section | Indicator",
        yaxis=dict(autorange="reversed", tickfont=dict(size=10), automargin=True),
        xaxis=dict(side="top"),
        margin=dict(l=330, r=28, t=40 if not title else 86, b=34),
    )
    return fig


def derive_map_opportunity_metrics(community_numeric, year):
    selected_years = [column for column in YEAR_COLUMNS if int(column) <= int(year)]
    metrics = community_numeric[["Place", "Map key"] + selected_years].copy()
    metrics["current_value"] = metrics[year]
    metrics["potential_value"] = metrics[selected_years].min(axis=1, skipna=True)
    metrics.loc[metrics["current_value"].isna(), "potential_value"] = pd.NA
    metrics["opportunity_value"] = metrics["current_value"] - metrics["potential_value"]
    metrics["opportunity_value"] = metrics["opportunity_value"].clip(lower=0)

    if len(selected_years) > 1:
        previous_year = selected_years[-2]
        metrics["previous_value"] = metrics[previous_year]
    else:
        metrics["previous_value"] = pd.NA

    def format_count(value):
        if pd.isna(value):
            return "No data"
        return str(int(value))

    metrics["current_display"] = metrics["current_value"].apply(format_count)
    metrics["potential_display"] = metrics["potential_value"].apply(format_count)
    metrics["opportunity_display"] = metrics["opportunity_value"].apply(format_count)
    metrics["potential_note"] = metrics.apply(
        lambda row: "No current data"
        if pd.isna(row["current_value"])
        else f"Recent low from {YEAR_COLUMNS[0]}-{year}",
        axis=1,
    )
    metrics["opportunity_note"] = metrics.apply(
        lambda row: "No current data"
        if pd.isna(row["current_value"])
        else (
            "At recent low"
            if row["opportunity_value"] == 0
            else f"{int(row['opportunity_value'])} cases above recent low"
        ),
        axis=1,
    )
    return metrics[
        [
            "Map key",
            "current_value",
            "previous_value",
            "potential_value",
            "opportunity_value",
            "current_display",
            "potential_display",
            "opportunity_display",
            "potential_note",
            "opportunity_note",
        ]
    ]


def build_map_data(community_numeric, geography, year, determinants_analysis):
    map_values = community_numeric[["Place", "Map key", year]].rename(columns={year: "HIV incidence"})
    opportunity_metrics = derive_map_opportunity_metrics(community_numeric, year)
    determinant_fields = (
        ["Map key", "GEOID"]
        + [determinant["field"] for determinant in PROTECTIVE_DETERMINANTS]
    )
    determinant_fields = list(dict.fromkeys(determinant_fields))
    determinant_values = determinants_analysis[determinant_fields].copy()
    boundary_names = pd.DataFrame(
        {
            "Map key": [feature["properties"]["community"] for feature in geography["features"]],
            "Boundary community": [feature["properties"]["community"].title() for feature in geography["features"]],
        }
    )
    map_df = boundary_names.merge(map_values, on="Map key", how="left")
    map_df = map_df.merge(opportunity_metrics, on="Map key", how="left")
    map_df = map_df.merge(determinant_values, on="Map key", how="left")
    map_df["Display community"] = map_df["Place"].fillna(map_df["Boundary community"])
    map_df["Status"] = map_df["HIV incidence"].apply(lambda value: "Missing" if pd.isna(value) else "Available")
    centroids = []
    for feature in geography["features"]:
        lon, lat = feature_label_point(feature)
        centroids.append({"Map key": feature["properties"]["community"], "lon": lon, "lat": lat})
    map_df = map_df.merge(pd.DataFrame(centroids), on="Map key", how="left")
    return map_df


def feature_label_point(feature):
    geometry = feature.get("geometry") or {}
    coordinates = geometry.get("coordinates") or []
    polygons = coordinates if geometry.get("type") == "MultiPolygon" else [coordinates]
    rings = []
    for polygon in polygons:
        if polygon:
            rings.append(polygon[0])
    if not rings:
        return None, None

    ring = max(rings, key=lambda points: len(points))
    lon_values = [point[0] for point in ring]
    lat_values = [point[1] for point in ring]
    return (min(lon_values) + max(lon_values)) / 2, (min(lat_values) + max(lat_values)) / 2


def geography_bounds(geography):
    lon_values = []
    lat_values = []
    for feature in geography["features"]:
        geometry = feature.get("geometry") or {}
        coordinates = geometry.get("coordinates") or []
        polygons = coordinates if geometry.get("type") == "MultiPolygon" else [coordinates]
        for polygon in polygons:
            for ring in polygon:
                for lon, lat in ring:
                    lon_values.append(lon)
                    lat_values.append(lat)

    return [[min(lat_values), min(lon_values)], [max(lat_values), max(lon_values)]]


def create_chicago_map(map_df, geography, year, community_numeric):
    chicago_bounds = geography_bounds(geography)
    year_index = YEAR_COLUMNS.index(year)
    previous_year = YEAR_COLUMNS[year_index - 1] if year_index > 0 else None
    map_mode = "Current"
    mode_config = MAP_MODES[map_mode]
    mode_value_column = mode_config["value_column"]
    mode_display_column = mode_config["display_column"]
    value_columns = [
        "Map key",
        "Display community",
        "current_value",
        "previous_value",
        "potential_value",
        "opportunity_value",
        "current_display",
        "potential_display",
        "opportunity_display",
        "potential_note",
        "opportunity_note",
        "GEOID",
        *[determinant["field"] for determinant in PROTECTIVE_DETERMINANTS],
    ]
    value_columns = list(dict.fromkeys(value_columns))
    map_values = map_df[value_columns].copy()
    if previous_year:
        previous_values = community_numeric[["Map key", previous_year]].rename(columns={previous_year: "previous_value"})
        map_values = map_values.drop(columns=["previous_value"], errors="ignore")
        map_values = map_values.merge(previous_values, on="Map key", how="left")
    else:
        map_values["previous_value"] = None

    value_lookup = map_values.set_index("Map key").to_dict("index")
    mapped_geo = deepcopy(geography)
    max_value = max(float(map_values[mode_value_column].max(skipna=True) or 1), 1)
    color_scale = cm.LinearColormap(
        colors=mode_config["palette"],
        vmin=0,
        vmax=max_value,
        caption=f"{mode_config['caption']}, {year}",
    )

    for feature in mapped_geo["features"]:
        key = feature["properties"]["community"]
        values = value_lookup.get(key, {})
        current_value = values.get("current_value")
        previous_value = values.get("previous_value")
        potential_value = values.get("potential_value")
        opportunity_value = values.get("opportunity_value")
        mode_value = values.get(mode_value_column)
        display_name = values.get("Display community") or key.title()

        current_numeric = None if pd.isna(current_value) else float(current_value)
        previous_numeric = None if pd.isna(previous_value) else float(previous_value)
        potential_numeric = None if pd.isna(potential_value) else float(potential_value)
        opportunity_numeric = None if pd.isna(opportunity_value) else float(opportunity_value)
        mode_numeric = None if pd.isna(mode_value) else float(mode_value)
        current_display = values.get("current_display") or "No data"
        potential_display = values.get("potential_display") or "No data"
        opportunity_display = values.get("opportunity_display") or "No data"
        potential_note = values.get("potential_note") or "No current data"
        opportunity_note = values.get("opportunity_note") or "No current data"
        determinant_properties = {}
        for determinant in PROTECTIVE_DETERMINANTS:
            value = values.get(determinant["field"])
            formatted_value = format_determinant_value(value, determinant["value_type"])
            favorable_text = "higher is favorable" if determinant["favorable"] == "higher" else "lower is favorable"
            determinant_properties[f"determinant_{determinant['key']}"] = f"{formatted_value} ({favorable_text})"

        if previous_year is None:
            previous_display = "N/A"
            growth_display = "N/A"
        elif previous_numeric is None:
            previous_display = "No data"
            growth_display = "N/A"
        else:
            previous_display = str(int(previous_numeric))
            if current_numeric is None:
                growth_display = "N/A"
            elif previous_numeric == 0 and current_numeric == 0:
                growth_display = "0.0%"
            elif previous_numeric == 0:
                growth_display = "N/A; previous year was 0"
            else:
                growth_display = f"{((current_numeric - previous_numeric) / previous_numeric) * 100:.1f}%"

        feature["properties"].update(
            {
                "map_key": key,
                "display_community": display_name,
                "geoid": "No data" if pd.isna(values.get("GEOID")) else str(int(values.get("GEOID"))),
                "current_display": current_display,
                "potential_display": potential_display,
                "opportunity_display": opportunity_display,
                "potential_note": potential_note,
                "opportunity_note": opportunity_note,
                "mode_label": map_mode,
                "mode_display": values.get(mode_display_column) or "No data",
                "map_year": year,
                "previous_label": previous_year or "Previous year",
                "previous_display": previous_display,
                "growth_display": growth_display,
                "current_value": current_numeric,
                "potential_value": potential_numeric,
                "opportunity_value": opportunity_numeric,
                "mode_value": mode_numeric,
                **determinant_properties,
            }
        )

    def style_function(feature):
        value = feature["properties"].get("mode_value")
        if value is None:
            return {
                "fillColor": "#64748b",
                "color": "#ffffff",
                "weight": 1,
                "fillOpacity": 0.28,
            }
        return {
            "fillColor": color_scale(value),
            "color": "#ffffff",
            "weight": 1,
            "fillOpacity": 0.74,
        }

    chicago_map = folium.Map(
        location=[41.83, -87.73],
        zoom_start=11,
        min_zoom=10,
        max_zoom=12,
        tiles=None,
        control_scale=False,
        prefer_canvas=True,
        max_bounds=True,
        min_lat=chicago_bounds[0][0],
        max_lat=chicago_bounds[1][0],
        min_lon=chicago_bounds[0][1],
        max_lon=chicago_bounds[1][1],
        zoom_control=False,
        dragging=True,
        scrollWheelZoom=False,
        doubleClickZoom=False,
        boxZoom=False,
        keyboard=False,
        touchZoom=False,
    )
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
        attr="&copy; OpenStreetMap &copy; CARTO",
        name="Muted city context",
        control=False,
        opacity=0.58,
    ).add_to(chicago_map)
    chicago_map.fit_bounds(chicago_bounds)

    folium.GeoJson(
        mapped_geo,
        name="Community areas",
        style_function=style_function,
        highlight_function=lambda feature: {
            "weight": 3,
            "color": ACCENT_AMBER,
            "fillOpacity": 0.88,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["display_community"],
            aliases=["Community"],
            sticky=True,
            style=(
                "background-color: #ffffff; color: #0f172a; border: 1px solid #cbd5e1; "
                "border-radius: 6px; padding: 6px 10px; font-weight: 700;"
            ),
        ),
    ).add_to(chicago_map)

    color_scale.add_to(chicago_map)
    map_name = chicago_map.get_name()
    chicago_map.get_root().html.add_child(
        folium.Element(
            f"""
            <script>
            const mapContainer = {map_name}.getContainer();
            mapContainer.style.background = "#f8fafc";
            const style = document.createElement("style");
            style.innerHTML = `
                #{map_name} .leaflet-tile-pane {{
                    filter: blur(1.4px) grayscale(0.55) saturate(0.7);
                    opacity: 0.62;
                }}
                #{map_name} .leaflet-overlay-pane {{
                    filter: drop-shadow(0 8px 18px rgba(15, 23, 42, 0.18));
                }}
            `;
            document.head.appendChild(style);
            {map_name}.setView([41.83, -87.73], 11);
            {map_name}.setMaxBounds({chicago_bounds});
            {map_name}.scrollWheelZoom.disable();
            {map_name}.doubleClickZoom.disable();
            {map_name}.boxZoom.disable();
            {map_name}.keyboard.disable();
            if ({map_name}.touchZoom) {{
                {map_name}.touchZoom.disable();
            }}
            {map_name}.on('drag', function() {{
                {map_name}.panInsideBounds({chicago_bounds}, {{ animate: false }});
            }});
            </script>
            """
        )
    )
    return chicago_map


def map_summary_values(map_df):
    current_total = int(map_df["current_value"].sum(skipna=True))
    potential_total = int(map_df["potential_value"].sum(skipna=True))
    opportunity_total = int(map_df["opportunity_value"].sum(skipna=True))
    opportunity_communities = int(map_df["opportunity_value"].fillna(0).gt(0).sum())
    top_rows = map_df.dropna(subset=["opportunity_value"]).sort_values(
        ["opportunity_value", "current_value"],
        ascending=False,
    )
    if top_rows.empty or top_rows.iloc[0]["opportunity_value"] <= 0:
        top_community = "None"
    else:
        top_community = top_rows.iloc[0]["Display community"]
    return current_total, potential_total, opportunity_total, opportunity_communities, top_community


community_raw, community_numeric, community_long, gender, race, age, geography = load_data()
determinants_analysis, determinants_correlations, priority_correlations, stress_correlations = load_social_determinants_data()
reported_long = community_long.dropna(subset=["HIV incidence"])
latest_year = max(YEAR_COLUMNS)
previous_year = YEAR_COLUMNS[YEAR_COLUMNS.index(latest_year) - 1]
latest_numeric = community_numeric[["Place", latest_year]].dropna(subset=[latest_year])
latest_citywide = int(gender.loc[gender["Year"].eq(int(latest_year)), "Total"].iloc[0])
previous_citywide = int(gender.loc[gender["Year"].eq(int(previous_year)), "Total"].iloc[0])
latest_community_total = int(latest_numeric[latest_year].sum())
top_community_row = latest_numeric.sort_values(latest_year, ascending=False).iloc[0]
top_community = top_community_row["Place"]
top_community_value = int(top_community_row[latest_year])
citywide_trend = trend_details(latest_citywide, previous_citywide)
race_latest = race.loc[race["Year"].eq(int(latest_year))].drop(columns=["Year", "Total"]).T.reset_index()
race_latest.columns = ["Race / Ethnicity", "Cases"]
largest_ethnicity = race_latest.sort_values("Cases", ascending=False).iloc[0]
top_share = (top_community_value / latest_community_total) * 100 if latest_community_total else 0

st.markdown('<h1 class="main-header">Chicago HIV Incidence Dashboard</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="sub-header">A focused view of citywide HIV incidence patterns, demographics, and Chicago community trends.</p>',
    unsafe_allow_html=True,
)

active_section = st.radio(
    "Dashboard section",
    ["Overview", "Chicago Demography", "Community Trends", "Social Determinants", "Chicago Map"],
    horizontal=True,
    label_visibility="collapsed",
    key="dashboard_section",
)

st.markdown('<div class="nav-summary-gap"></div>', unsafe_allow_html=True)

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    metric_card("Citywide Total", f"{latest_citywide:,}", latest_year, citywide_trend)
with col2:
    metric_card("Years Tracked", f"{YEAR_COLUMNS[0]}-{latest_year}", "Citywide and community views")
with col3:
    insight_box(
        "Citywide Direction",
        f"{latest_year} is {citywide_trend[2].lower()}, with {latest_citywide:,} total incidence.",
    )
with col4:
    insight_box(
        "Community Concentration",
        f"{top_community} has the highest community value in {latest_year}, representing {top_share:.1f}% of the community total.",
    )
with col5:
    insight_box(
        "Largest Demographic Segment",
        f"{largest_ethnicity['Race / Ethnicity']} is the largest race or ethnicity segment in {latest_year}.",
    )

st.markdown('<div class="summary-section-gap"></div>', unsafe_allow_html=True)

if active_section == "Overview":
    citywide = gender[["Year", "Total"]].copy()
    gender_latest = gender.loc[gender["Year"].eq(int(latest_year))].drop(columns=["Year", "Total"]).T.reset_index()
    gender_latest.columns = ["Category", "Cases"]

    left, right = st.columns([1.15, 1])
    with left:
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=citywide["Year"],
                y=citywide["Total"],
                mode="lines+markers",
                name="Citywide total",
                line=dict(color=ACCENT_TEAL, width=4),
                marker=dict(size=9),
            )
        )
        fig.update_layout(title="Citywide Trend")
        plot_template(fig)
        st.plotly_chart(fig, width='stretch')

    with right:
        fig = px.pie(
            gender_latest,
            names="Category",
            values="Cases",
            hole=0.58,
            color="Category",
            color_discrete_map=GENDER_COLORS,
            title=f"Male vs Female Distribution, {latest_year}",
        )
        fig.update_traces(textposition="outside", textinfo="percent+label", marker=dict(line=dict(color="#ffffff", width=2)))
        plot_template(fig)
        st.plotly_chart(fig, width='stretch')

    fig = px.bar(
        race_latest.sort_values("Cases", ascending=True),
        x="Cases",
        y="Race / Ethnicity",
        orientation="h",
        color="Race / Ethnicity",
        color_discrete_map=RACE_COLORS,
        title=f"Ethnicity Division, {latest_year}",
    )
    fig.update_layout(showlegend=False)
    plot_template(fig)
    st.plotly_chart(fig, width='stretch')

if active_section == "Chicago Demography":
    c1, c2 = st.columns(2)

    with c1:
        age_long = melt_breakdown(age, "Age group")
        fig = px.line(
            age_long,
            x="Year",
            y="Cases",
            color="Age group",
            markers=True,
            color_discrete_map=AGE_COLORS,
            title="Age Group Trend",
        )
        plot_template(fig)
        st.plotly_chart(fig, width='stretch')

    with c2:
        fig = px.line(gender, x="Year", y="Total", markers=True, title="Citywide Total")
        fig.update_traces(line=dict(color=ACCENT_TEAL, width=4), marker=dict(size=10, color=ACCENT_AMBER))
        plot_template(fig)
        st.plotly_chart(fig, width='stretch')

    c3, c4 = st.columns(2)

    with c3:
        race_long = melt_breakdown(race, "Race / Ethnicity")
        fig = px.bar(
            race_long,
            x="Year",
            y="Cases",
            color="Race / Ethnicity",
            color_discrete_map=RACE_COLORS,
            barmode="group",
            title="By Race and Ethnicity",
        )
        plot_template(fig)
        st.plotly_chart(fig, width='stretch')

    with c4:
        gender_long = melt_breakdown(gender, "Category")
        fig = px.area(
            gender_long,
            x="Year",
            y="Cases",
            color="Category",
            color_discrete_map=GENDER_COLORS,
            title="By Gender",
        )
        plot_template(fig)
        st.plotly_chart(fig, width='stretch')

if active_section == "Community Trends":
    filters_left, filters_right = st.columns([1, 1.4])
    with filters_left:
        selected_year = st.selectbox("Year", YEAR_COLUMNS, index=len(YEAR_COLUMNS) - 1, key="community_year")
    with filters_right:
        places = community_raw["Place"].tolist()
        selected_place = st.selectbox(
            "Community area",
            places,
            index=places.index("Uptown") if "Uptown" in places else 0,
            key="community_area",
        )

    selected_map_key = community_raw.loc[community_raw["Place"].eq(selected_place), "Map key"].iloc[0]
    selected_plot = community_trend_frame(community_raw, selected_map_key)
    selected_table = selected_plot[["Year", "Cases", "Change"]].copy()
    selected_table["Cases"] = selected_table["Cases"].apply(lambda value: "No data" if pd.isna(value) else f"{int(value):,}")

    left, right = st.columns([1.05, 1.35])
    with left:
        st.markdown(selected_table.to_html(index=False, classes="community-table"), unsafe_allow_html=True)
        insight_box("Community Insight", community_insight_text(selected_place, selected_plot))

    with right:
        fig = community_trend_chart(selected_plot, f"{selected_place} Trend", selected_year=selected_year)
        st.plotly_chart(fig, width='stretch')

    if st.toggle("Show heatmap", value=False):
        heatmap_df = community_numeric.set_index("Place")[YEAR_COLUMNS]
        heatmap_hover = heatmap_df.astype(object).apply(
            lambda column: column.map(lambda value: "No data" if pd.isna(value) else f"{int(value):,}")
        )
        fig = px.imshow(
            heatmap_df,
            aspect="auto",
            color_continuous_scale=["#f8fafc", "#dbeafe", ACCENT_BLUE, ACCENT_TEAL, ACCENT_AMBER, ACCENT_RED],
            title="Community Heatmap",
            labels=dict(color="Incidence"),
        )
        fig.update_traces(
            customdata=heatmap_hover.values,
            hovertemplate="Community: %{y}<br>Year: %{x}<br>Cases: %{customdata}<extra></extra>",
        )
        fig.update_layout(
            height=940,
            coloraxis_colorbar=dict(title="Incidence"),
            yaxis=dict(tickfont=dict(size=9), automargin=True),
            xaxis=dict(tickfont=dict(size=12), automargin=True),
        )
        plot_template(fig)
        st.plotly_chart(fig, width='stretch')

if active_section == "Social Determinants":
    st.markdown("### HIV Cases and Social Determinants")

    if st.toggle("Show priority factors heatmap", value=True, key="show_priority_heatmap"):
        priority_rows = priority_correlations["Average absolute correlation"].ge(CORRELATION_SIGNAL_THRESHOLD).sum()
        priority_fig = social_determinants_heatmap(
            priority_correlations,
            title="Priority Factor Correlations with HIV Incidence",
            height=max(760, int(priority_rows) * 30 + 170),
        )
        st.plotly_chart(priority_fig, width='stretch')

    if st.toggle("Show community stress heatmap", value=True, key="show_stress_heatmap"):
        stress_rows = stress_correlations["Average absolute correlation"].ge(CORRELATION_SIGNAL_THRESHOLD).sum()
        stress_fig = social_determinants_heatmap(
            stress_correlations,
            title="Community Stress & Structural Risk Correlations with HIV Incidence",
            height=max(760, int(stress_rows) * 30 + 170),
        )
        st.plotly_chart(stress_fig, width='stretch')

    category_options = ["All categories"] + list(determinants_correlations["Category"].drop_duplicates())
    selected_category = st.selectbox("Selected indicator category", category_options, key="determinants_category")
    if selected_category == "All categories":
        filtered_correlations = determinants_correlations.copy()
    else:
        filtered_correlations = determinants_correlations.loc[
            determinants_correlations["Category"].eq(selected_category)
        ].copy()

    if st.toggle("Show selected indicator heatmap", value=True, key="show_selected_indicator_heatmap"):
        if "Average absolute correlation" not in filtered_correlations.columns:
            selected_rows = filtered_correlations[YEAR_COLUMNS].abs().mean(axis=1).ge(CORRELATION_SIGNAL_THRESHOLD).sum()
        else:
            selected_rows = filtered_correlations["Average absolute correlation"].ge(CORRELATION_SIGNAL_THRESHOLD).sum()
        heatmap_fig = social_determinants_heatmap(
            filtered_correlations,
            title="Selected Indicator Correlations with HIV Incidence",
            height=max(600, int(selected_rows) * 34 + 170),
        )
        st.plotly_chart(heatmap_fig, width='stretch')

if active_section == "Chicago Map":
    map_year = st.selectbox(
        "Map year",
        YEAR_COLUMNS,
        index=len(YEAR_COLUMNS) - 1,
        key="map_year",
    )

    map_df = build_map_data(community_numeric, geography, map_year, determinants_analysis)
    map_fig = create_chicago_map(map_df, geography, map_year, community_numeric)
    map_result = st_folium(
        map_fig,
        height=760,
        returned_objects=["last_active_drawing"],
        use_container_width=True,
        center=(41.83, -87.73),
        zoom=11,
        key=f"chicago_map_{map_year}",
    )

    active_drawing = (map_result or {}).get("last_active_drawing") or {}
    clicked_properties = active_drawing.get("properties", {})
    clicked_map_key = clicked_properties.get("map_key")
    if clicked_map_key in set(community_raw["Map key"]):
        clicked_place = community_raw.loc[community_raw["Map key"].eq(clicked_map_key), "Place"].iloc[0]
        map_trend = community_trend_frame(community_raw, clicked_map_key)
        max_increase, max_decrease = trend_extremes(map_trend)

        selected_community_dialog(clicked_place, map_trend, max_increase, max_decrease, clicked_properties)
    else:
        insight_box("Select a Community", "Choose a community area on the Chicago map to open its trend and increase/reduction summary.")
