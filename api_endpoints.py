
import requests
headers = {
    "accept": "application/json",
    "x-api-key": "JNApRuJmXopQGGiqZ11OjdKBgIVUWJtoCPV1PQXJ"
}

def api_teams():
    """
    get all the teams
    """
    url = "https://api.sportradar.com/ncaafb/trial/v7/en/league/teams.json"
    response = requests.get(url, headers=headers)
    return response.json()

def api_ranking():
    """
    returns current week rankings, top 25
    """
    url = "https://api.sportradar.com/ncaafb/trial/v7/en/polls/AP25/2025/rankings.json"
    response = requests.get(url, headers=headers)
    return response.json()

def api_team_roasters(team_id):
    url = f"https://api.sportradar.com/ncaafb/trial/v7/en/teams/{team_id}/full_roster.json"
    response = requests.get(url, headers=headers)
    return response.json()

def api_player_profile(player_id):
    url = f"https://api.sportradar.com/ncaafb/trial/v7/en/players/{player_id}/profile.json"
    response = requests.get(url, headers=headers)
    return response.json()

def api_season_details():
    "all season details"
    url = "https://api.sportradar.com/ncaafb/trial/v7/en/league/seasons.json"
    response = requests.get(url, headers=headers)
    return response.json()

def api_season_schedule(year):
    url = f"https://api.sportradar.com/ncaafb/trial/v7/en/games/{year}/REG/schedule.json"
    response = requests.get(url, headers=headers)
    return response.json()

