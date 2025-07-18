import streamlit as st
import datetime
import pandas as pd
import os

from astrophotography_planner import main

import plotly.express as px


@st.cache_resource
def main_planner(config):
    return main(config)


# Set up the page configuration
st.set_page_config(
    page_title="Astrophotography Planner",
    page_icon=":milky_way:",
    layout="wide",
)

st.title("Astrophotography Planner")

# variables
# get the current year
current_year = datetime.datetime.now().year

# labels for the target multiselect from a list of possible targets
possible_targets = pd.read_csv("targets.csv")["target"].tolist()

# declare all session state variables
# location_name (default to empty string)
if "location_name" not in st.session_state:
    st.session_state["location_name"] = ""

# calendar_year (current year by default)
if "calendar_year" not in st.session_state:
    st.session_state["calendar_year"] = current_year

# min_altitude_deg (default to 20 degrees)
min_altitude_deg_default = 20
if "min_altitude_deg" not in st.session_state:
    st.session_state["min_altitude_deg"] = min_altitude_deg_default

# max_altitude_deg (default to 90 degrees)
max_altitude_deg_default = 90
if "max_altitude_deg" not in st.session_state:
    st.session_state["max_altitude_deg"] = max_altitude_deg_default

# moon_sep_deg (default to 30 degrees)
moon_sep_deg_default = 30
if "moon_sep_deg" not in st.session_state:
    st.session_state["moon_sep_deg"] = moon_sep_deg_default

# max_moon_illum (default to 50%)
max_moon_illum_default = 0.5
if "max_moon_illum" not in st.session_state:
    st.session_state["max_moon_illum"] = max_moon_illum_default

# min_minutes_observable (default to 180 minutes)
min_minutes_observable_default = 180
if "min_minutes_observable" not in st.session_state:
    st.session_state["min_minutes_observable"] = min_minutes_observable_default

# targets list (default to empty list)
if "targets" not in st.session_state:
    st.session_state["targets"] = []

if "make_ics" not in st.session_state:
    st.session_state["make_ics"] = True

if "make_calendar" not in st.session_state:
    st.session_state["make_calendar"] = False

# Interface for user inputs

col_1_1, col_1_2 = st.columns([3, 1], gap="medium")

with col_1_1:
    st.session_state["location_name"] = st.text_input("Enter your location name")

with col_1_2:
    st.session_state["calendar_year"] = st.number_input(
        "Select the year",
        min_value=2000,
        max_value=current_year + 50,
        value=datetime.datetime.now().year,
        step=1,
    )

col_2_1, col_2_2, col_2_3, col_2_4 = st.columns([1, 1, 1, 1], gap="medium")

with col_2_1:
    min_val = st.session_state["min_altitude_deg"]
    max_val = st.session_state["max_altitude_deg"]
    min_alt, max_alt = st.slider(
        "Altitude range (degrees)",
        min_value=0,
        max_value=90,
        value=(min_val, max_val),
        step=1,
    )
    st.session_state["min_altitude_deg"] = min_alt
    st.session_state["max_altitude_deg"] = max_alt
with col_2_2:
    st.session_state["moon_sep_deg"] = st.slider(
        "Moon separation (degrees)",
        min_value=0,
        max_value=180,
        value=moon_sep_deg_default,
        step=1,
    )

with col_2_3:
    st.session_state["max_moon_illum"] = st.slider(
        "Maximum moon illumination (%)",
        min_value=0,
        max_value=100,
        value=int(max_moon_illum_default * 100),
        step=1,
    )
    st.session_state["max_moon_illum"] = st.session_state["max_moon_illum"] / 100

with col_2_4:
    st.session_state["min_minutes_observable"] = st.number_input(
        "Minimum observable minutes",
        min_value=0,
        max_value=1440,  # 24 hours in minutes
        value=min_minutes_observable_default,
        step=1,
    )

col_3_1, col_3_2, col_3_3 = st.columns(
    [4, 1, 1], vertical_alignment="bottom", gap="medium"
)
with col_3_1:
    st.session_state["targets"] = st.multiselect(
        "Select your targets", options=possible_targets
    )

with col_3_2:
    st.session_state["make_ics"] = st.checkbox("Create ICS file", value=True)

with col_3_3:
    st.session_state["make_calendar"] = st.checkbox("Create Calendar", value=False)

config_file = {
    "location_name": st.session_state["location_name"],
    "calendar_year": st.session_state["calendar_year"],
    "min_altitude_deg": st.session_state["min_altitude_deg"],
    "max_altitude_deg": st.session_state["max_altitude_deg"],
    "moon_sep_deg": st.session_state["moon_sep_deg"],
    "max_moon_illum": st.session_state["max_moon_illum"],
    "min_minutes_observable": st.session_state["min_minutes_observable"],
    "targets": st.session_state["targets"],
    "make_ics": st.session_state["make_ics"],
    "make_calendar": st.session_state["make_calendar"],
}


# execute the main logic if the location name and targets are set

if st.button(
    "Plan Astrophotography",
    use_container_width=True,
    type="primary",
    help="Click to generate the astrophotography plan based on your inputs.",
    disabled=not (
        st.session_state["location_name"].strip() and st.session_state["targets"]
    ),
):
    results = main_planner(config_file)

    # check if a astro_planner_targets.ics file was created and button to download it

    if st.session_state["make_ics"] and os.path.exists("astro_planner_targets.ics"):
        with open("astro_planner_targets.ics", "rb") as file:
            st.download_button(
                label="Download ICS file",
                data=file,
                file_name="astro_planner_targets.ics",
                mime="text/calendar",
                help="Download the ICS file with your targets.",
            )

    df = pd.DataFrame(results)

    # st.write(df)

    # Prepare data
    df["date"] = pd.to_datetime(df["date"])
    df["end"] = df["date"] + pd.to_timedelta(df["observable_hours"], unit="h")

    fig = px.timeline(
        df,
        x_start="date",
        x_end="end",
        y="target",
        color="observable_hours",
        hover_data=["date", "target", "observable_hours"],
        title="Astrophotography Observable Hours Gantt Chart",
        color_continuous_scale="viridis",
    )
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Target",
        height=max(400, len(df["target"].unique()) * 30),
    )

    st.plotly_chart(fig, use_container_width=True)
