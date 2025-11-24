import os
from sqlalchemy import create_engine, text
import pandas as pd
import streamlit as st
import plotly.express as px

from phi.agent import Agent
from phi.tools.sql import SQLTools
from phi.model.openai import OpenAIChat 


DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_NAME = "ncaafb_db"
DB_HOST = "localhost"
DB_USER = "root"
DB_PASS = "root"

GPT_API_KEY = "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"

st.set_page_config(page_title="NCAAFB Dash Board", layout="wide")


# Database engine factory
@st.cache_resource
def get_engine(db_name: str = None):
    if db_name:
        url = f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{db_name}?charset=utf8mb4"
    else:
        url = f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/?charset=utf8mb4"
    engine = create_engine(url, pool_pre_ping=True)
    return engine


# Utility to read SQL to DataFrame with caching
@st.cache_data(ttl=300)
def run_query(df_query: str, params: dict = None) -> pd.DataFrame:
    engine = get_engine(DB_NAME)
    with engine.connect() as conn:
        df = pd.read_sql_query(text(df_query), conn, params=params)
    return df

# --- Your function rewritten as a Streamlit page ---
def ai_query():

    st.header("AI Querier")
    st.write("Ask questions about the database in plain English. I will generate and run an SQL query to answer.")

    # --- Preserve your original variables ---
    url = f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    os.environ["OPENAI_API_KEY"] = GPT_API_KEY

    instruct = """
    You are a helpful assistant with access to a SQL database.  
    Your ONLY source of knowledge is the SQL database connected to you. 
    You must NOT use any external information, general world knowledge, 
    or assumptions beyond what is stored in the database.

    Rules:
    1. Translate the user question into an appropriate SQL query.
    2. Execute the query on the database.
    3. Use only the SQL results to generate your answer.
    4. If unable to answer, say 'sorry, could not find the proper solution.'
    """

    agent = Agent(
        tools=[SQLTools(db_url=url)],
        llm=OpenAIChat(model="gpt-4o-mini", open_api_key=GPT_API_KEY),
        instructions=instruct
    )

    user_query = st.text_input("Your question:", placeholder="Ask something about the database...")

    if st.button("Submit"):
        if user_query.strip() == "":
            st.warning("Please enter a question.")
            return
        
        # Stream response
        with st.container():
            st.write("### Response:")
            response_holder = st.empty()

            # Capture streaming output manually
            for chunk in agent.print_response(user_query, markdown=True, stream=True):
                response_holder.markdown(chunk)



def home_page():
    st.header("Home NCAAFB Overview")

    # Quick counts and tables
    col1, col2, col3 = st.columns(3)
    try:
        teams_count = run_query("SELECT COUNT(*) as cnt FROM TEAMS").iloc[0, 0]
        players_count = run_query("SELECT COUNT(*) as cnt FROM PLAYERS").iloc[0, 0]
        seasons_count = run_query("SELECT COUNT(*) as cnt FROM SEASONS").iloc[0, 0]
    except Exception:
        teams_count = players_count = seasons_count = "-"

    col1.metric("Teams", teams_count)
    col2.metric("Players", players_count)
    col3.metric("Seasons", seasons_count)

    st.subheader("Sample: Teams and Conferences")
    try:
        df = run_query(
            "SELECT t.team_id, t.market, t.name as team_name, c.name as conference FROM TEAMS t LEFT JOIN CONFERENCES c ON t.conference_id = c.conference_id LIMIT 200"
        )
        st.dataframe(df)
    except Exception as e:
        st.warning(
            "Unable to load TEAMS table yet. Make sure schema is initialized and DB contains data."
        )


def teams_explorer():
    st.header("Teams Explorer")

    # filters
    # populate options from DB
    try:
        confs = (
            run_query("SELECT DISTINCT name FROM CONFERENCES ORDER BY name")
            .squeeze()
            .tolist()
        )
    except Exception:
        confs = []
    try:
        states = (
            run_query(
                "SELECT DISTINCT v.state FROM VENUES v WHERE v.state IS NOT NULL ORDER BY v.state"
            )
            .squeeze()
            .dropna()
            .tolist()
        )
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
        placeholders = ",".join([f":conf{i}" for i in range(len(conf_sel))])
        where_clauses.append(f"c.name IN ({placeholders})")
        for i, v in enumerate(conf_sel):
            params[f"conf{i}"] = v
    if state_sel:
        placeholders = ",".join([f":state{i}" for i in range(len(state_sel))])
        where_clauses.append(f"v.state IN ({placeholders})")
        for i, v in enumerate(state_sel):
            params[f"state{i}"] = v
    if search:
        where_clauses.append("(t.name LIKE :s OR t.alias LIKE :s OR t.market LIKE :s)")
        params["s"] = f"%{search}%"

    if where_clauses:
        sql = base_sql + " WHERE " + " AND ".join(where_clauses) + " ORDER BY t.name"
    else:
        sql = base_sql + " ORDER BY t.name"

    df = run_query(sql, params)
    st.dataframe(df)

    st.markdown("---")
    st.subheader("View Team Roster")
    team_choice = st.selectbox(
        "Select a team to view roster",
        options=df["team_name"].tolist() if not df.empty else [],
    )
    if team_choice:
        team_id = df.loc[df["team_name"] == team_choice, "team_id"].iloc[0]
        roster_sql = "SELECT p.player_id, p.first_name, p.last_name, p.position, p.eligibility, p.height, p.weight, p.status FROM PLAYERS p WHERE p.team_id = :tid"
        roster_df = run_query(roster_sql, {"tid": team_id})
        st.dataframe(roster_df)


def players_explorer():
    st.header("Players Explorer")

    # Filters
    try:
        positions = (
            run_query(
                "SELECT DISTINCT position FROM PLAYERS WHERE position IS NOT NULL ORDER BY position"
            )
            .squeeze()
            .dropna()
            .tolist()
        )
    except Exception:
        positions = []
    try:
        eligs = (
            run_query(
                "SELECT DISTINCT eligibility FROM PLAYERS WHERE eligibility IS NOT NULL ORDER BY eligibility"
            )
            .squeeze()
            .dropna()
            .tolist()
        )
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
        placeholders = ",".join([f":pos{i}" for i in range(len(pos))])
        where_clauses.append(f"p.position IN ({placeholders})")
        for i, v in enumerate(pos):
            params[f"pos{i}"] = v
    if elig:
        placeholders = ",".join([f":elig{i}" for i in range(len(elig))])
        where_clauses.append(f"p.eligibility IN ({placeholders})")
        for i, v in enumerate(elig):
            params[f"elig{i}"] = v
    if name_search:
        where_clauses.append(
            "(p.first_name LIKE :q OR p.last_name LIKE :q OR t.name LIKE :q)"
        )
        params["q"] = f"%{name_search}%"

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
        col1.write(px.histogram(df, x="height", nbins=20, title="Height (inches)"))
        col2.write(px.histogram(df, x="weight", nbins=20, title="Weight (lbs)"))


def seasons_viewer():
    st.header("Seasons & Schedules")

    try:
        seasons = run_query("SELECT * FROM SEASONS ORDER BY year DESC")
    except Exception:
        st.warning("Seasons table not populated yet.")
        seasons = pd.DataFrame()

    st.dataframe(seasons)

    with st.expander("Season Filters"):
        years = seasons["year"].tolist() if not seasons.empty else []
        yr = st.selectbox("Year", options=[None] + years)
        status = st.selectbox("Status", options=[None, "active", "closed"])

    if yr or status:
        where = []
        params = {}
        if yr:
            where.append("year = :yr")
            params["yr"] = int(yr)
        if status:
            where.append("status = :st")
            params["st"] = status
        sql = (
            "SELECT * FROM SEASONS WHERE " + " AND ".join(where) + " ORDER BY year DESC"
        )
        st.dataframe(run_query(sql, params))


def rankings_page():
    st.header("Rankings — Weekly AP Poll")

    try:
        seasons = run_query("SELECT season_id, year FROM SEASONS ORDER BY year DESC")
    except Exception:
        seasons = pd.DataFrame()

    season_map = (
        {row["year"]: row["season_id"] for _, row in seasons.iterrows()}
        if not seasons.empty
        else {}
    )
    years = list(season_map.keys())

    col1, col2, col3 = st.columns(3)
    season_sel = col1.selectbox("Season", options=[None] + years)
    week_sel = col2.number_input("Week (number)", min_value=1, max_value=30, value=1)
    rank_range = col3.slider("Rank range", 1, 25, (1, 25))

    params = {}
    where = []
    if season_sel:
        where.append("r.season_id = :sid")
        params["sid"] = season_map[season_sel]
    if week_sel:
        where.append("r.week = :w")
        params["w"] = int(week_sel)
    where.append("r.rank BETWEEN :r1 AND :r2")
    params["r1"] = int(rank_range[0])
    params["r2"] = int(rank_range[1])

    sql = "SELECT r.week, t.name as team_name, r.rank, r.points, r.fp_votes, r.wins, r.losses FROM RANKINGS r LEFT JOIN TEAMS t ON r.team_id = t.team_id"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY r.week, r.rank"

    df = run_query(sql, params)
    st.dataframe(df)

    # Team ranking history
    st.subheader("Search team ranking history")
    team_list = (
        run_query("SELECT team_id, name FROM TEAMS ORDER BY name")
        if df is not None
        else pd.DataFrame()
    )
    team_choice = (
        st.selectbox("Team", options=([""] + team_list["name"].tolist()))
        if not team_list.empty
        else None
    )
    if team_choice:
        tid = team_list.loc[team_list["name"] == team_choice, "team_id"].iloc[0]
        hist = run_query(
            "SELECT s.year, r.week, r.rank, r.points FROM RANKINGS r JOIN seasons s ON r.season_id = s.season_id WHERE r.team_id = :tid ORDER BY s.year, r.week",
            {"tid": tid},
        )
        if not hist.empty:
            fig = px.line(
                hist.sort_values(["year", "week"]),
                x="week",
                y="rank",
                color="year",
                markers=True,
                title=f"Ranking history for {team_choice} (lower is better)",
            )
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No ranking history found for this team.")


def venues_page():
    st.header("Venues Directory")
    try:
        states = (
            run_query(
                "SELECT DISTINCT state FROM VENUES WHERE state IS NOT NULL ORDER BY state"
            )
            .squeeze()
            .dropna()
            .tolist()
        )
    except Exception:
        states = []
    with st.sidebar.expander("Venues Filters"):
        state_sel = st.multiselect("State", options=states)
        roof_sel = st.selectbox("Roof Type", options=[None, "Indoor", "Outdoor"])

    base_sql = "SELECT * FROM VENUES"
    where = []
    params = {}
    if state_sel:
        placeholders = ",".join([f":st{i}" for i in range(len(state_sel))])
        where.append(f"state IN ({placeholders})")
        for i, v in enumerate(state_sel):
            params[f"st{i}"] = v
    if roof_sel:
        where.append("roof_type = :roof")
        params["roof"] = roof_sel
    if where:
        base_sql += " WHERE " + " AND ".join(where)
    base_sql += " ORDER BY city, name"
    df = run_query(base_sql, params)
    st.dataframe(df)


def coaches_page():
    st.header("Coaches")
    try:
        df = run_query(
            "SELECT coach_id, full_name, position, t.name as team_name FROM COACHES c LEFT JOIN TEAMS t ON c.team_id = t.team_id ORDER BY full_name"
        )
    except Exception:
        df = pd.DataFrame()
    st.dataframe(df)


PAGES = {
    "AI Query": ai_query,
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

    PAGES[page]()


if __name__ == "__main__":
    main()
