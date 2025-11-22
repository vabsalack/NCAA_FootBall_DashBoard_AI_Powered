"""
Streamlit app for NCAAFB Data Explorer

Files provided by user (already referenced in this project):
- /mnt/data/schema.sql    <-- SQL schema file (used to create DB tables)
- /mnt/data/NCAAFB API_ Data Analysis.pdf  <-- Project requirements & notes

How this app works (high-level):
- Connects to a MySQL server using SQLAlchemy + PyMySQL
- If the target database does not exist, it will create it and run the schema.sql file
- Provides multipage Streamlit frontend: Home, Teams, Players, Seasons, Rankings, Venues, Coaches
- Each page includes filters built from the database and returns results as interactive tables and charts

Usage:
1. Install dependencies:
   pip install streamlit sqlalchemy pymysql pandas plotly python-dotenv

2. Create a .env file (in the same folder as this script) with these variables:
   DB_HOST=localhost
   DB_PORT=3306
   DB_USER=root
   DB_PASS=your_password
   DB_NAME=ncaafb_db

3. Place the provided schema at: /mnt/data/schema.sql (already present)

4. Run the app:
   streamlit run NCAAFB_streamlit_app.py

Notes & Caveats:
- This script assumes the MySQL server is reachable and the credentials are correct.
- For production or team sharing, use secrets manager for DB credentials (Streamlit secrets or env manager).
- The schema runner will execute the schema.sql only once (if tables are missing).

"""

import os
import textwrap
import sqlalchemy
from sqlalchemy import create_engine, text
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
import plotly.express as px

# ---------------------------
# Config & Helpers
# ---------------------------

# load_dotenv()

# DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
# DB_USER = os.getenv("DB_USER", "root")
# DB_PASS = os.getenv("DB_PASS", "")
# DB_NAME = os.getenv("DB_NAME", "ncaafb_db")
# SCHEMA_PATH = "/mnt/data/schema.sql"  # path provided by user

DB_NAME = "ncaafb_db"
DB_HOST = "localhost"
DB_USER = "root"
DB_PASS = "root"

st.set_page_config(page_title="NCAAFB Data Explorer", layout="wide")

# Database engine factory
@st.cache_resource
def get_engine(db_name: str = None):
    """Return SQLAlchemy engine. If db_name is None, connect to server without selecting DB."""
    if db_name:
        url = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{db_name}?charset=utf8mb4"
    else:
        url = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/?charset=utf8mb4"
    engine = create_engine(url, pool_pre_ping=True)
    return engine


# def ensure_database_and_schema():
#     """Ensure database exists and schema is applied. Executes schema.sql if necessary."""
#     # Connect to server (no DB)
#     engine = get_engine(None)
#     with engine.connect() as conn:
#         # create database if not exists
#         conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"))
#         conn.commit()

#     # Connect to target DB and check if tables exist; if not, run schema
#     engine_db = get_engine(DB_NAME)
#     with engine_db.connect() as conn:
#         # check for any table
#         result = conn.execute(text("SELECT COUNT(*) as c FROM information_schema.tables WHERE table_schema = :schema"), {"schema": DB_NAME})
#         count = result.mappings().first()["c"]
#         if count == 0:
#             # load schema file and execute
#             if not os.path.exists(SCHEMA_PATH):
#                 st.error(f"Schema file not found at {SCHEMA_PATH}")
#                 return False
#             with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
#                 schema_sql = f.read()
#             # naive split by ; to execute statements safely; preserve DELIMITER statements
#             statements = [s.strip() for s in schema_sql.split(';') if s.strip()]
#             for stmt in statements:
#                 try:
#                     conn.execute(text(stmt))
#                 except Exception as e:
#                     # ignore statements that cannot run alone (e.g., DELIMITER-related or comments)
#                     print("Schema execution error for statement chunk:", e)
#             conn.commit()
#             st.info("Database schema initialized from schema.sql")
#         else:
#             st.info("Database already contains tables - skipping schema initialization")
#     return True


# Utility to read SQL to DataFrame with caching
@st.cache_data(ttl=300)
def run_query(df_query: str, params: dict = None) -> pd.DataFrame:
    engine = get_engine(DB_NAME)
    with engine.connect() as conn:
        df = pd.read_sql_query(text(df_query), conn, params=params)
    return df


# ---------------------------
# Page Components
# ---------------------------

def home_page():
    st.header("Home — NCAAFB Overview")

    # Quick counts and tables
    col1, col2, col3 = st.columns(3)
    try:
        teams_count = run_query("SELECT COUNT(*) as cnt FROM TEAMS").iloc[0,0]
        players_count = run_query("SELECT COUNT(*) as cnt FROM PLAYERS").iloc[0,0]
        seasons_count = run_query("SELECT COUNT(*) as cnt FROM SEASONS").iloc[0,0]
    except Exception:
        teams_count = players_count = seasons_count = "-"

    col1.metric("Teams", teams_count)
    col2.metric("Players", players_count)
    col3.metric("Seasons", seasons_count)

    st.subheader("Sample: Teams and Conferences")
    try:
        df = run_query("SELECT t.team_id, t.market, t.name as team_name, c.name as conference FROM TEAMS t LEFT JOIN CONFERENCES c ON t.conference_id = c.conference_id LIMIT 200")
        st.dataframe(df)
    except Exception as e:
        st.warning("Unable to load TEAMS table yet. Make sure schema is initialized and DB contains data.")


def teams_explorer():
    st.header("Teams Explorer")

    # filters
    # populate options from DB
    try:
        confs = run_query("SELECT DISTINCT name FROM CONFERENCES ORDER BY name").squeeze().tolist()
    except Exception:
        confs = []
    try:
        states = run_query("SELECT DISTINCT v.state FROM VENUES v WHERE v.state IS NOT NULL ORDER BY v.state").squeeze().dropna().tolist()
    except Exception:
        states = []

    with st.sidebar.expander("Filters - Teams"):
        conf_sel = st.multiselect("Conference", options=confs)
        state_sel = st.multiselect("Venue state", options=states)
        search = st.text_input("Search team by name or alias or market")

    base_sql = "SELECT t.team_id, t.market, t.name as team_name, t.alias, c.name as conference, v.name as venue, v.city, v.state FROM TEAMS t LEFT JOIN CONFERENCES c ON t.conference_id = c.conference_id LEFT JOIN VENUES v ON t.venue_id = v.venue_id"
    where_clauses = []
    params = {}
    if conf_sel:
        placeholders = ','.join([f':conf{i}' for i in range(len(conf_sel))])
        where_clauses.append(f"c.name IN ({placeholders})")
        for i, v in enumerate(conf_sel):
            params[f'conf{i}'] = v
    if state_sel:
        placeholders = ','.join([f':state{i}' for i in range(len(state_sel))])
        where_clauses.append(f"v.state IN ({placeholders})")
        for i, v in enumerate(state_sel):
            params[f'state{i}'] = v
    if search:
        where_clauses.append("(t.name LIKE :s OR t.alias LIKE :s OR t.market LIKE :s)")
        params['s'] = f"%{search}%"

    if where_clauses:
        sql = base_sql + " WHERE " + " AND ".join(where_clauses) + " ORDER BY t.name"
    else:
        sql = base_sql + " ORDER BY t.name"

    df = run_query(sql, params)
    st.dataframe(df)

    st.markdown("---")
    st.subheader("View Team Roster")
    team_choice = st.selectbox("Select a team to view roster", options=df['team_name'].tolist() if not df.empty else [])
    if team_choice:
        team_id = df.loc[df['team_name'] == team_choice, 'team_id'].iloc[0]
        roster_sql = "SELECT p.player_id, p.first_name, p.last_name, p.position, p.eligibility, p.height, p.weight, p.status FROM PLAYERS p WHERE p.team_id = :tid"
        roster_df = run_query(roster_sql, {'tid': team_id})
        st.dataframe(roster_df)


def players_explorer():
    st.header("Players Explorer")

    # Filters
    try:
        positions = run_query("SELECT DISTINCT position FROM PLAYERS WHERE position IS NOT NULL ORDER BY position").squeeze().dropna().tolist()
    except Exception:
        positions = []
    try:
        eligs = run_query("SELECT DISTINCT eligibility FROM PLAYERS WHERE eligibility IS NOT NULL ORDER BY eligibility").squeeze().dropna().tolist()
    except Exception:
        eligs = []

    with st.sidebar.expander("Filters - Players"):
        pos = st.multiselect("Position", options=positions)
        elig = st.multiselect("Eligibility", options=eligs)
        name_search = st.text_input("Search player name or team")

    base_sql = "SELECT p.player_id, p.first_name, p.last_name, p.position, p.eligibility, p.height, p.weight, p.status, t.name as team_name FROM PLAYERS p LEFT JOIN TEAMS t ON p.team_id = t.team_id"
    where_clauses = []
    params = {}

    if pos:
        placeholders = ','.join([f':pos{i}' for i in range(len(pos))])
        where_clauses.append(f"p.position IN ({placeholders})")
        for i, v in enumerate(pos):
            params[f'pos{i}'] = v
    if elig:
        placeholders = ','.join([f':elig{i}' for i in range(len(elig))])
        where_clauses.append(f"p.eligibility IN ({placeholders})")
        for i, v in enumerate(elig):
            params[f'elig{i}'] = v
    if name_search:
        where_clauses.append("(p.first_name LIKE :q OR p.last_name LIKE :q OR t.name LIKE :q)")
        params['q'] = f"%{name_search}%"

    if where_clauses:
        sql = base_sql + " WHERE " + " AND ".join(where_clauses)
    else:
        sql = base_sql

    sql += " ORDER BY p.last_name LIMIT 1000"
    df = run_query(sql, params)
    st.dataframe(df)

    # Simple histograms
    st.subheader("Height and Weight distribution")
    if not df.empty:
        col1, col2 = st.columns(2)
        col1.write(px.histogram(df, x='height', nbins=20, title='Height (inches)'))
        col2.write(px.histogram(df, x='weight', nbins=20, title='Weight (lbs)'))


def seasons_viewer():
    st.header("Seasons & Schedules")

    try:
        seasons = run_query("SELECT * FROM SEASONS ORDER BY year DESC")
    except Exception:
        st.warning("Seasons table not populated yet.")
        seasons = pd.DataFrame()

    st.dataframe(seasons)

    with st.expander("Season Filters"):
        years = seasons['year'].tolist() if not seasons.empty else []
        yr = st.selectbox("Year", options=[None] + years)
        status = st.selectbox("Status", options=[None, 'active', 'closed'])

    if yr or status:
        where = []
        params = {}
        if yr:
            where.append("year = :yr")
            params['yr'] = int(yr)
        if status:
            where.append("status = :st")
            params['st'] = status
        sql = "SELECT * FROM SEASONS WHERE " + " AND ".join(where) + " ORDER BY year DESC"
        st.dataframe(run_query(sql, params))


def rankings_page():
    st.header("Rankings — Weekly AP Poll")

    try:
        seasons = run_query("SELECT season_id, year FROM SEASONS ORDER BY year DESC")
    except Exception:
        seasons = pd.DataFrame()

    season_map = {row['year']: row['season_id'] for _, row in seasons.iterrows()} if not seasons.empty else {}
    years = list(season_map.keys())

    col1, col2, col3 = st.columns(3)
    season_sel = col1.selectbox("Season", options=[None] + years)
    week_sel = col2.number_input("Week (number)", min_value=1, max_value=30, value=1)
    rank_range = col3.slider("Rank range", 1, 25, (1, 25))

    params = {}
    where = []
    if season_sel:
        where.append("r.season_id = :sid")
        params['sid'] = season_map[season_sel]
    if week_sel:
        where.append("r.week = :w")
        params['w'] = int(week_sel)
    where.append("r.rank BETWEEN :r1 AND :r2")
    params['r1'] = int(rank_range[0])
    params['r2'] = int(rank_range[1])

    sql = "SELECT r.week, t.name as team_name, r.rank, r.points, r.fp_votes, r.wins, r.losses FROM RANKINGS r LEFT JOIN TEAMS t ON r.team_id = t.team_id"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY r.week, r.rank"

    df = run_query(sql, params)
    st.dataframe(df)

    # Team ranking history
    st.subheader("Search team ranking history")
    team_list = run_query("SELECT team_id, name FROM TEAMS ORDER BY name") if df is not None else pd.DataFrame()
    team_choice = st.selectbox("Team", options=([""] + team_list['name'].tolist())) if not team_list.empty else None
    if team_choice:
        tid = team_list.loc[team_list['name'] == team_choice, 'team_id'].iloc[0]
        hist = run_query("SELECT s.year, r.week, r.rank, r.points FROM RANKINGS r JOIN seasons s ON r.season_id = s.season_id WHERE r.team_id = :tid ORDER BY s.year, r.week", {'tid': tid})
        if not hist.empty:
            fig = px.line(hist.sort_values(['year', 'week']), x='week', y='rank', color='year', markers=True, title=f"Ranking history for {team_choice} (lower is better)")
            fig.update_yaxes(autorange='reversed')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No ranking history found for this team.")


def venues_page():
    st.header("Venues Directory")
    try:
        states = run_query("SELECT DISTINCT state FROM VENUES WHERE state IS NOT NULL ORDER BY state").squeeze().dropna().tolist()
    except Exception:
        states = []
    with st.sidebar.expander("Venues Filters"):
        state_sel = st.multiselect("State", options=states)
        roof_sel = st.selectbox("Roof Type", options=[None, 'Indoor', 'Outdoor'])

    base_sql = "SELECT * FROM VENUES"
    where = []
    params = {}
    if state_sel:
        placeholders = ','.join([f':st{i}' for i in range(len(state_sel))])
        where.append(f"state IN ({placeholders})")
        for i, v in enumerate(state_sel):
            params[f'st{i}'] = v
    if roof_sel:
        where.append("roof_type = :roof")
        params['roof'] = roof_sel
    if where:
        base_sql += " WHERE " + " AND ".join(where)
    base_sql += " ORDER BY city, name"
    df = run_query(base_sql, params)
    st.dataframe(df)


def coaches_page():
    st.header("Coaches")
    try:
        df = run_query("SELECT coach_id, full_name, position, t.name as team_name FROM COACHES c LEFT JOIN TEAMS t ON c.team_id = t.team_id ORDER BY full_name")
    except Exception:
        df = pd.DataFrame()
    st.dataframe(df)


PAGES = {
    "Home": home_page,
    "Teams Explorer": teams_explorer,
    "Players Explorer": players_explorer,
    "Seasons": seasons_viewer,
    "Rankings": rankings_page,
    "Venues": venues_page,
    "Coaches": coaches_page,
}


def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", list(PAGES.keys()))

    # Ensure DB and schema
    # with st.spinner("Checking database and schema..."):
    #     ok = ensure_database_and_schema()
    #     if not ok:
    #         st.stop()

    # Run selected page
    PAGES[page]()


if __name__ == '__main__':
    main()
