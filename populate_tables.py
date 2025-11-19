from api_endpoints import api_teams

teams = api_teams()
teams_id = []
for team in teams["teams"]:
    teams_id.append(team["id"])

print(len(teams_id), len(teams_id[0]))
print(*teams_id, sep="\n")

