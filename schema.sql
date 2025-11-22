CREATE DATABASE ncaafb_db;
USE ncaafb_db;

CREATE TABLE VENUES
(
    venue_id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100),
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),
    zip VARCHAR(100),
    address VARCHAR(100),
    capacity INT,
    surface VARCHAR(100),
    roof_type VARCHAR(100),
    latitude DECIMAL(10, 5),
    longitude DECIMAL(10, 5)
);

CREATE TABLE CONFERENCES
(
    conference_id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100),
    alias VARCHAR(100)
);

CREATE TABLE DIVISIONS
(
    division_id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100),
    alias VARCHAR(100)
);

CREATE TABLE TEAMS
(
    team_id VARCHAR(36) PRIMARY KEY,
    market VARCHAR(100),
    name VARCHAR(100),
    alias VARCHAR(100),
    founded SMALLINT,
    mascot VARCHAR(100),
    fight_song VARCHAR(100),
    championships_won INT,
    conference_id VARCHAR(36),
    division_id VARCHAR(36),
    venue_id VARCHAR(36),

    FOREIGN KEY (venue_id) REFERENCES VENUES(venue_id),
    FOREIGN KEY (conference_id) REFERENCES CONFERENCES(conference_id),
    FOREIGN KEY (division_id) REFERENCES DIVISIONS(division_id)
    
);

CREATE TABLE SEASONS
(
    season_id VARCHAR(36) PRIMARY KEY,
    year SMALLINT,
    start_date DATE,
    end_date DATE,
    status VARCHAR(100),
    type_code VARCHAR(100)
);

CREATE TABLE RANKINGS
(
    ranking_id INT AUTO_INCREMENT PRIMARY KEY,
    poll_id VARCHAR(36),
    poll_name VARCHAR(100),
    season_id VARCHAR(36),
    week INT,
    effective_time TIMESTAMP,
    team_id VARCHAR(36),
    rank_position INT,
    prev_rank INT,
    points INT,
    fp_votes INT,
    wins INT,
    losses INT,
    ties INT,

    FOREIGN KEY (team_id) REFERENCES TEAMS(team_id),
    FOREIGN KEY (season_id) REFERENCES SEASONS(season_id)

);

CREATE TABLE PLAYERS
(
    player_id VARCHAR(36) PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    abbr_name VARCHAR(100),
    birth_place VARCHAR(100),
    position VARCHAR(100),
    height INT,
    weight INT,
    status VARCHAR(100),
    eligibility VARCHAR(100),
    team_id VARCHAR(36),

    FOREIGN KEY (team_id) REFERENCES TEAMS(team_id)

);

CREATE TABLE COACHES
(
    coach_id VARCHAR(100) PRIMARY KEY,
    full_name VARCHAR(100),
    position VARCHAR(100),
    team_id VARCHAR(36),

    FOREIGN KEY (team_id) REFERENCES TEAMS(team_id)
);

CREATE TABLE PLAYER_STATISTICS
(
    stat_id INT AUTO_INCREMENT PRIMARY KEY,
    player_id VARCHAR(36),
    team_id VARCHAR(36),
    season_id VARCHAR(36),
    games_played INT,
    games_started INT,
    rushing_yards INT,
    rushing_touchdowns INT,
    receiving_yards INT,
    receiving_touchdowns INT,
    kick_return_yards INT,
    fumbles INT,

    FOREIGN KEY (team_id) REFERENCES TEAMS(team_id),
    FOREIGN KEY (player_id) REFERENCES PLAYERS(player_id),
    FOREIGN KEY (season_id) REFERENCES SEASONS(season_id)
);






