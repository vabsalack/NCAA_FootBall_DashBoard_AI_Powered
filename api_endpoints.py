GLOBAL_API_KEY = "JNApRuJmXopQGGiqZ11OjdKBgIVUWJtoCPV1PQXJ"

import requests


def api_teams(local_api_key=None):
    """
    get all the teams
    """

    api_key = GLOBAL_API_KEY if local_api_key is None else local_api_key

    headers = {"accept": "application/json", "x-api-key": f"{api_key}"}

    url = "https://api.sportradar.com/ncaafb/trial/v7/en/league/teams.json"
    response = requests.get(url, headers=headers)
    return response.json()


def api_ranking(local_api_key=None):
    """
    returns current week rankings, top 25
    """
    api_key = GLOBAL_API_KEY if local_api_key is None else local_api_key

    headers = {"accept": "application/json", "x-api-key": f"{api_key}"}

    url = "https://api.sportradar.com/ncaafb/trial/v7/en/polls/AP25/2025/rankings.json"
    response = requests.get(url, headers=headers)
    return response.json()


def api_team_roasters(team_id, local_api_key=None):
    api_key = GLOBAL_API_KEY if local_api_key is None else local_api_key

    headers = {"accept": "application/json", "x-api-key": f"{api_key}"}

    url = f"https://api.sportradar.com/ncaafb/trial/v7/en/teams/{team_id}/full_roster.json"
    response = requests.get(url, headers=headers)
    return response.json()


def api_player_profile(player_id, local_api_key=None):
    api_key = GLOBAL_API_KEY if local_api_key is None else local_api_key

    headers = {"accept": "application/json", "x-api-key": f"{api_key}"}

    url = f"https://api.sportradar.com/ncaafb/trial/v7/en/players/{player_id}/profile.json"
    response = requests.get(url, headers=headers)
    return response.json()


def api_season_details(local_api_key=None):
    "all season details"

    api_key = GLOBAL_API_KEY if local_api_key is None else local_api_key

    headers = {"accept": "application/json", "x-api-key": f"{api_key}"}

    url = "https://api.sportradar.com/ncaafb/trial/v7/en/league/seasons.json"
    response = requests.get(url, headers=headers)
    return response.json()


def api_season_schedule(year, local_api_key=None):
    api_key = GLOBAL_API_KEY if local_api_key is None else local_api_key

    headers = {"accept": "application/json", "x-api-key": f"{api_key}"}

    url = (
        f"https://api.sportradar.com/ncaafb/trial/v7/en/games/{year}/REG/schedule.json"
    )
    response = requests.get(url, headers=headers)
    return response.json()
