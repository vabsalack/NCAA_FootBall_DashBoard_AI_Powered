[
sportradar server
-------------------------------
curl --request GET \
     --url https://api.sportradar.com/ncaafb/trial/v7/en/polls/AP25/2025/01/rankings.json \
     --header 'accept: application/json' \
     --header 'x-api-key: RlviAZ2p1C6LEiOHHW0e9AIuhCEUBxxBcKETm1M9'
-------------------------------
some api endpoint
requeset api endpiont with api_key
download raw json data
]

[
preprocess the data before storing it in sql db
extract json to dict if necessary or convert json into dict and pass dict values to sql table
define sql schema
store the data in schema as per requirement
]

-- total 9 tables
-- 1.TEAMS, 2.VENUES, 3.CONFERENCES, 4.SEASONS, 5.PLAYERS, 6.PLAYER_STATISTICS, 7.RANKINGS, 8.COACHES, 9.DIVISIONS

-- importants
-- 1. terminate each command with ;, since it act as delimiter in python handling;


parents of teams: 1. venues, 2. divisions, 3. conferences
-- first
1. extract all team id from /teams ep
2. extract team roaster info from team_id
3. from each team roaster, extract conferences, divisions, venues

teams id fetch by teams/ then to team_roaster/
level1: conf, venue, division (team_roaster/)
level2: season, teams (season/, team_roaster/)
level3: ranks, players, coaches (rankings_byweek/, team_roaster/, team_roaster/)
level4: player_stats (player_profile/)
