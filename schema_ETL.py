from api_endpoints import api_teams
from api_endpoints import api_team_roasters
from api_endpoints import api_season_details
from api_endpoints import api_player_profile
from api_endpoints import api_ranking

from util import obj_to_file
from util import file_to_obj
from util import df_to_file
from util import file_to_df

import time

from util import to_mysql_timestamp

import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import os, time, random

DB_NAME = "ncaafb_db"
SCHEMA_FILE = "schema.sql"
HOST_ID = "localhost"
USER_NAME = "root"
USER_PASSWORD = "root"

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


def _get(d, keys, default=None):
    """Safe nested dict getter: _get(d, ['a','b']) -> d['a']['b'] or default."""
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def get_all_just_teams_id_list():
    print("fetching all teams id's..")
    teams = api_teams()
    teams_id = [team["id"] for team in teams["teams"]]
    obj_to_file(teams_id, "./db_csv/teams_id_list")
    return teams_id


def get_all_seasons_list():
    print("fetching all season's detail..")
    season_details = api_season_details()
    season_list = season_details["seasons"]
    obj_to_file(season_list, "./db_csv/seasons_list")
    return season_list


def db_populate_seasons(season_list, engine):
    seasons_df = pd.DataFrame(
        columns=["season_id", "year", "start_date", "end_date", "status", "type_code"]
    )
    for season in season_list:
        season_dict = {
            "season_id": _get(season, ["id"]),
            "year": _get(season, ["year"]),
            "start_date": _get(season, ["start_date"]),
            "end_date": _get(season, ["end_date"]),
            "status": _get(season, ["status"]),
            "type_code": _get(season, ["type", "code"]),
        }

        if (
            season_dict["season_id"] is not None
            and season_dict["season_id"] not in seasons_df["season_id"].values
        ):
            seasons_df.loc[len(seasons_df)] = season_dict

    seasons_df.to_sql("SEASONS", engine, index=False, if_exists="append")
    df_to_file(seasons_df, "./db_csv/SEASONS.csv")
    print("db updated: seasons.")


def get_all_teams_roaster_list(teams_id):
    def _fetch_roaster(tid, max_retries=1, base_backoff=1.0):
        backoff = base_backoff
        for attempt in range(1, max_retries + 1):
            try:
                res = api_team_roasters(tid)
            except Exception as e:
                msg = str(e)
                # treat typical rate-limit errors as retryable
                if "Too Many Requests" in msg or "429" in msg:
                    print(f"Too Many Requests: {tid}")
                    wait = backoff + random.uniform(0, 0.5)
                    time.sleep(wait)
                    backoff *= 2
                    continue
                return {"id": tid, "_error": msg}

            # api wrapper may return a dict with a 'message' or '_error'
            if isinstance(res, dict) and (
                res.get("message") == "Too Many Requests"
                or "Too Many Requests" in str(res.get("_error", ""))
            ):
                # if the API returned Retry-After in headers, use that (needs wrapper change to expose headers)
                wait = backoff + random.uniform(0, 0.5)
                time.sleep(wait)
                backoff *= 2
                continue

            return res

        return {"id": tid, "_error": "TooManyRequests_after_retries"}

    # lower concurrency to avoid bursts
    max_workers = min(10, (os.cpu_count() or 1) * 2, len(teams_id))
    roasters_list = []
    print("fetching all team's roaster detail..")
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = [ex.submit(_fetch_roaster, tid) for tid in teams_id]
        for i, fut in enumerate(as_completed(futures), 1):
            roasters_list.append(fut.result())
            if i % 50 == 0 or i == len(teams_id):
                print(f"Fetched {i}/{len(teams_id)}")

    obj_to_file(roasters_list, "./db_csv/roasters_list")
    return roasters_list


def db_populate_venues_divisons_confs_teams_coaches_players(roasters_list, engine):
    venue_df = pd.DataFrame(
        columns=[
            "venue_id",
            "name",
            "city",
            "state",
            "country",
            "zip",
            "address",
            "capacity",
            "surface",
            "roof_type",
            "latitude",
            "longitude",
        ]
    )
    conferene_df = pd.DataFrame(columns=["conference_id", "name", "alias"])
    divison_df = pd.DataFrame(columns=["division_id", "name", "alias"])
    teams_df = pd.DataFrame(
        columns=[
            "team_id",
            "market",
            "name",
            "alias",
            "founded",
            "mascot",
            "fight_song",
            "championships_won",
            "conference_id",
            "division_id",
            "venue_id",
        ]
    )
    players_df = pd.DataFrame(
        columns=[
            "player_id",
            "first_name",
            "last_name",
            "abbr_name",
            "birth_place",
            "position",
            "height",
            "weight",
            "status",
            "eligibility",
            "team_id",
        ]
    )
    coaches_df = pd.DataFrame(columns=["coach_id", "full_name", "position", "team_id"])

    for roaster in roasters_list:
        print(roaster)
        if not isinstance(roaster, dict) or "id" not in roaster:
            continue

        venue_dict = {
            "venue_id": _get(roaster, ["venue", "id"]),
            "name": _get(roaster, ["venue", "name"]),
            "city": _get(roaster, ["venue", "city"]),
            "state": _get(roaster, ["venue", "state"]),
            "country": _get(roaster, ["venue", "country"]),
            "zip": _get(roaster, ["venue", "zip"]),
            "address": _get(roaster, ["venue", "address"]),
            "capacity": _get(roaster, ["venue", "capacity"]),
            "surface": _get(roaster, ["venue", "surface"]),
            "roof_type": _get(roaster, ["venue", "roof_type"]),
            "latitude": _get(roaster, ["venue", "location", "lat"]),
            "longitude": _get(roaster, ["venue", "location", "lng"]),
        }

        conference_dict = {
            "conference_id": _get(roaster, ["conference", "id"]),
            "name": _get(roaster, ["conference", "name"]),
            "alias": _get(roaster, ["conference", "alias"]),
        }

        division_dict = {
            "division_id": _get(roaster, ["division", "id"]),
            "name": _get(roaster, ["division", "name"]),
            "alias": _get(roaster, ["division", "alias"]),
        }

        teams_dict = {
            "team_id": _get(roaster, ["id"]),
            "market": _get(roaster, ["market"]),
            "name": _get(roaster, ["name"]),
            "alias": _get(roaster, ["alias"]),
            "founded": _get(roaster, ["founded"]),
            "mascot": _get(roaster, ["mascot"]),
            "fight_song": _get(roaster, ["fight_song"]),
            "championships_won": _get(roaster, ["championships_won"]),
            "conference_id": _get(roaster, ["conference", "id"]),
            "division_id": _get(roaster, ["division", "id"]),
            "venue_id": _get(roaster, ["venue", "id"]),
        }

        # Replacements to avoid FutureWarning:
        if (
            venue_dict["venue_id"] is not None
            and venue_dict["venue_id"] not in venue_df["venue_id"].values
        ):
            venue_df = pd.concat(
                [venue_df, pd.DataFrame([venue_dict])], ignore_index=True
            )

        if (
            conference_dict["conference_id"] is not None
            and conference_dict["conference_id"]
            not in conferene_df["conference_id"].values
        ):
            conferene_df = pd.concat(
                [conferene_df, pd.DataFrame([conference_dict])], ignore_index=True
            )

        if (
            division_dict["division_id"] is not None
            and division_dict["division_id"] not in divison_df["division_id"].values
        ):
            divison_df = pd.concat(
                [divison_df, pd.DataFrame([division_dict])], ignore_index=True
            )

        if (
            teams_dict["team_id"] is not None
            and teams_dict["team_id"] not in teams_df["team_id"].values
        ):
            teams_df = pd.concat(
                [teams_df, pd.DataFrame([teams_dict])], ignore_index=True
            )

        print("v|d|c|t done")

        # Coaches
        for coach in roaster.get("coaches", []) or []:
            c = {
                "coach_id": _get(coach, ["id"]),
                "full_name": _get(coach, ["full_name"]),
                "position": _get(coach, ["position"]),
                "team_id": teams_dict["team_id"],
            }
            if (
                c["coach_id"] is not None
                and c["coach_id"] not in coaches_df["coach_id"].values
            ):
                coaches_df = pd.concat(
                    [coaches_df, pd.DataFrame([c])], ignore_index=True
                )
            print("c done")

        # Players
        for player in roaster.get("players", []) or []:
            p = {
                "player_id": _get(player, ["id"]),
                "first_name": _get(player, ["first_name"]),
                "last_name": _get(player, ["last_name"]),
                "abbr_name": _get(player, ["abbr_name"]),
                "birth_place": _get(player, ["birth_place"]),
                "position": _get(player, ["position"]),
                "height": _get(player, ["height"]),
                "weight": _get(player, ["weight"]),
                "status": _get(player, ["status"]),
                "eligibility": _get(player, ["eligibility"]),
                "team_id": teams_dict["team_id"],
            }
            if (
                p["player_id"] is not None
                and p["player_id"] not in players_df["player_id"].values
            ):
                players_df = pd.concat(
                    [players_df, pd.DataFrame([p])], ignore_index=True
                )
            print(" pdone")

    print("uploading to sql")

    tables = [
        (conferene_df, "CONFERENCES"),
        (venue_df, "VENUES"),
        (divison_df, "DIVISIONS"),
        (teams_df, "TEAMS"),
        (players_df, "PLAYERS"),
        (coaches_df, "COACHES"),
    ]

    for df, table_name in tables:
        csv_path = f"./db_csv/{table_name}.csv"
        try:
            df.to_csv(csv_path, index=False)
        except Exception as e:
            print(f"Failed to write CSV {csv_path}: {e}")
        try:
            df.to_sql(table_name, engine, index=False, if_exists="append")
        except Exception as e:
            print(f"Failed to write SQL table {table_name}: {e}")

    print("db updated: " + ", ".join([t for _, t in tables]))

    # preserve previous behavior of saving player ids and returning them
    obj_to_file(players_df["player_id"].values, "./db_csv/players_ids")
    print("file player_id saved")
    # return players_df["player_id"].values


def get_player_profiles_list(players_id):
    def _fetch_player_profile(pid, max_retries=5):
        for attempt in range(max_retries):
            try:
                return api_player_profile(pid)
            except Exception as e:
                msg = str(e)
                # backoff on rate limit-ish errors
                if "Too Many Requests" in msg or "429" in msg:
                    time.sleep((2**attempt) * 0.1 + 0.1)
                    continue
                return {"player_id": pid, "_error": msg}
        return {"player_id": pid, "_error": "TooManyRequests_after_retries"}

    max_workers = min(50, (os.cpu_count() or 1) * 5, len(players_id))
    playerprof_list = []
    print("fetching all player's stats..")
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(_fetch_player_profile, pid): pid for pid in players_id}
        for i, fut in enumerate(as_completed(futures), 1):
            playerprof_list.append(fut.result())
            if i % 100 == 0 or i == len(players_id):
                print(f"Fetched {i}/{len(players_id)}")

    obj_to_file(playerprof_list, "./db_csv/players_profiles_list")
    return playerprof_list


def db_populate_players_statistics(playerprof_list, engine):
    playerstat_df = pd.DataFrame(
        columns=[
            "player_id",
            "team_id",
            "season_id",
            "games_played",
            "games_started",
            "rushing_yards",
            "rushing_touchdowns",
            "receiving_yards",
            "receiving_touchdowns",
            "kick_return_yards",
            "fumbles",
        ]
    )
    for player in playerprof_list:
        playerstat_dict = {key: None for key in playerstat_df.columns}
        playerstat_dict["player_id"] = _get(player, ["id"])
        playerstat_dict["team_id"] = _get(player, ["team", "id"])
        if _get(player, ["seasons"]) in [None, []]:
            playerstat_df.loc[len(playerstat_df)] = playerstat_dict
            continue

        for season in player["seasons"]:
            playerstat_dict["season_id"] = _get(season, ["id"])
            if _get(season, ["teams"]) in [None, []]:
                playerstat_df.loc[len(playerstat_df)] = playerstat_dict
                continue

            for team in season["teams"]:
                if (
                    playerstat_dict["team_id"] is not None
                    and _get(team, ["id"]) == playerstat_dict["team_id"]
                ):
                    playerstat_dict["team_id"] = _get(team, ["id"])
                    playerstat_dict["games_played"] = _get(
                        team, ["statistics", "games_played"]
                    )
                    playerstat_dict["games_started"] = _get(
                        team, ["statistics", "games_started"]
                    )
                    playerstat_dict["rushing_yards"] = _get(
                        team, ["statistics", "rushing", "yards"]
                    )
                    playerstat_dict["rushing_touchdowns"] = _get(
                        team, ["statistics", "rushing", "touchdowns"]
                    )
                    playerstat_dict["receiving_yards"] = _get(
                        team, ["statistics", "receiving", "yards"]
                    )
                    playerstat_dict["receiving_touchdowns"] = _get(
                        team, ["statistics", "receiving", "touchdowns"]
                    )
                    playerstat_dict["kick_return_yards"] = _get(
                        team, ["statistics", "kick_returns", "yards"]
                    )
                    playerstat_dict["fumbles"] = _get(
                        team, ["statistics", "fumbles", "fumbles"]
                    )

                    playerstat_df.loc[len(playerstat_df)] = playerstat_dict

        df_to_file(playerstat_df, "./db_csv/PLAYER_STATISTICS.csv")
        playerstat_df.to_sql(
            "PLAYER_STATISTICS", engine, index=False, if_exists="append"
        )

    print("db updated: player_statistics.")


def get_current_week_rankings():
    return [api_ranking()]


def db_populate_rankings(week_rankings, engine):
    rank_curr_week_df = pd.DataFrame(columns=["ranking_id", 
                                             "poll_id", 
                                             "poll_name",
                                             "season_id",
                                             "week",
                                             "effective_time",
                                             "team_id",
                                             "rank_position",
                                             "prev_rank",
                                             "points",
                                             "fp_votes",
                                             "wins",
                                             "losses",
                                             "ties"])
    # 754e4990-efc7-11ef-bb2a-5d2d22b9215e
    rank_dict = {key:None for key in rank_curr_week_df.columns}
    rank_dict["season_id"] = "754e4990-efc7-11ef-bb2a-5d2d22b9215e"

    for week_rank in week_rankings:
        for team_rank in _get(week_rank, ["rankings"]):
            rank_dict["poll_id"] = _get(week_rank, ["poll", "id"])
            rank_dict["poll_name"] = _get(week_rank, ["poll", "name"])
            rank_dict["week"] = _get(week_rank, ["week"])
            rank_dict["effective_time"] = to_mysql_timestamp(_get(week_rank, ["effective_time"]))
            rank_dict["team_id"] = _get(team_rank, ["id"])
            rank_dict["rank_position"] = _get(team_rank, ["rank"])
            rank_dict["prev_rank"] = _get(team_rank, ["prev_rank"])
            rank_dict["points"] = _get(team_rank, ["points"])
            rank_dict["fp_votes"] = _get(team_rank, ["fp_votes"])
            rank_dict["wins"] = _get(team_rank, ["wins"])
            rank_dict["losses"] = _get(team_rank, ["losses"])
            rank_dict["ties"] = _get(team_rank, ["ties"])
            rank_curr_week_df.loc[len(rank_curr_week_df)] = rank_dict
    
    df_to_file(rank_curr_week_df, "./db_csv/RANKINGS.csv")
    print("RANKINGS.csv file saved")
    rank_curr_week_df.to_sql("RANKINGS", engine, index=False, if_exists="append")
    print("db updated: rankings")


def _apply_schema(engine_db):
    """Apply schema only if not already applied."""
    with engine_db.connect() as conn:
        # Check if schema version table exists
        result = conn.execute(
            text("""
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = :db
              AND table_name = 'schema_version'
        """),
            {"db": DB_NAME},
        ).scalar()

        if result == 1:
            print("Schema already applied — skipping.")
            return

    print(
        f"Applying schema to {DB_NAME}",
        f"Loading schema file from ./{SCHEMA_FILE}",
        sep="\n",
    )

    try:
        with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
            sql_content = f.read()
    except FileNotFoundError:
        print(f"ERROR: Schema file '{SCHEMA_FILE}' not found.")
        return

    # Split into SQL statements
    statements = [stmt.strip() for stmt in sql_content.split(";") if stmt.strip()]

    with engine_db.connect() as conn:
        for stmt in statements:
            try:
                conn.execute(text(stmt))
            except SQLAlchemyError as e:
                print(f"Error executing statement:\n{stmt}\n{e}")

        # Mark schema as applied
        conn.execute(
            text("""
            CREATE TABLE IF NOT EXISTS schema_version (
                id INT PRIMARY KEY AUTO_INCREMENT,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        )

        conn.execute(text("INSERT INTO schema_version () VALUES ()"))

    print("Schema applied successfully.")


def ensure_database():
    """Ensure the database exists and return an engine bound to it."""
    server_url = f"mysql+mysqlconnector://{USER_NAME}:{USER_PASSWORD}@{HOST_ID}"

    server_engine = create_engine(server_url)

    with server_engine.connect() as conn:
        conn.execute(
            text(
                f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        )

    # Now return engine bound to the database
    engine_db = create_engine(server_url + f"/{DB_NAME}")
    return engine_db


def main():
    # create sql engine with creditianls applied and schema applied
    engine = ensure_database()
    _apply_schema(engine)

    # get all team's ids & save it to file
    get_all_just_teams_id_list()
    time.sleep(5)
    # get all seasons detail save it to file
    get_all_seasons_list()

    # load seaons details from file and upload to database
    seasons_list = file_to_obj("./db_csv/seasons_list")
    db_populate_seasons(seasons_list, engine)

    # load teams's ids from file and get all team's roaster details
    teams_id = file_to_obj("./db_csv/teams_id_list")
    get_all_teams_roaster_list(teams_id)

    # load all teams roasters from file and upload to database
    roasters_list = file_to_obj("./db_csv/roasters_list")
    db_populate_venues_divisons_confs_teams_coaches_players(roasters_list, engine)

    # load player's ids from file and get player stats
    players_ids = file_to_obj("./db_csv/players_ids")
    get_player_profiles_list(players_ids)

    # load playear stats from file and upload to database
    players_stats = file_to_obj("./db_csv/players_profiles_list")
    db_populate_players_statistics(players_stats, engine)


if __name__ == "__main__":
    main()


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

# Ensure DB and schema
# with st.spinner("Checking database and schema..."):
#     ok = ensure_database_and_schema()
#     if not ok:
#         st.stop()
