
import requests
headers = {
    "accept": "application/json",
    "x-api-key": "RlviAZ2p1C6LEiOHHW0e9AIuhCEUBxxBcKETm1M9"
}
####################### get all teams info
def api_teams():
    """
    get all the teams
    """
    url = "https://api.sportradar.com/ncaafb/trial/v7/en/league/teams.json"
    response = requests.get(url, headers=headers)
    # return response.json()
    return response.json()

#################### rankding current week
def api_ranking():
    """
    returns current week rankings, top 25
    """
    url = "https://api.sportradar.com/ncaafb/trial/v7/en/polls/AP25/2025/rankings.json"
    response = requests.get(url, headers=headers)
    return response.json()
######################### team roaster details by team id

def api_team_roasters(team_id):
    # url = "https://api.sportradar.com/ncaafb/trial/v7/en/teams/19775492-f1eb-4bc5-9e15-078ebd689c0f/full_roster.json"
    url = f"https://api.sportradar.com/ncaafb/trial/v7/en/teams/{team_id}/full_roster.json"
    response = requests.get(url, headers=headers)
    return response.json()

###################### player profile by player id

def api_player_profile(player_id):
    # url = "https://api.sportradar.com/ncaafb/trial/v7/en/players/3992e590-8f40-11ec-9f33-1965c9c46e44/profile.json"
    url = "https://api.sportradar.com/ncaafb/trial/v7/en/players/{player_id}/profile.json"
    response = requests.get(url, headers=headers)
    return response.json()

#######################  all season detials
def api_season_details():
    "all season details"
    url = "https://api.sportradar.com/ncaafb/trial/v7/en/league/seasons.json"
    response = requests.get(url, headers=headers)
    return response.json()

##################  season schedule by year
def api_season_schedule(year):
    # url = "https://api.sportradar.com/ncaafb/trial/v7/en/games/2025/REG/schedule.json"
    url = "https://api.sportradar.com/ncaafb/trial/v7/en/games/{year}/REG/schedule.json"
    response = requests.get(url, headers=headers)
    return response.json()

