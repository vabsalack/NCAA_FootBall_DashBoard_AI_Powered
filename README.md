# Sportradar Dashboard

<img src="artifacts/ncaa_fb.svg" width="200" alt="NCAA football logo">

## Overview
NCAA football dashboard: a compact 4-day project for ETL of API data into MySQL and a Streamlit frontend. Key features include AI-assisted data retrievals from MySQL and contextual filter/search on each page.

## Tools, APIs and Libraries

### API
- [Sportradar NCAA Marketplace](https://marketplace.sportradar.com/leagues/687fea148de93a6971154c99)

### Language / Runtime
- Python >= 3.11 (streamlit compatible version on linux)

### Package manager
- uv (astral)

### Libraries (requirements)
- mysql-connector-python>=9.5.0
- pandas>=2.3.3
- plotly>=6.5.0
- requests>=2.32.5
- ruff>=0.14.6
- sqlalchemy>=2.0.44
- streamlit>=1.51.0


## ETL data and ER diagram
- All teams id's were collected from /teams end point and rest were derived from it.

<img src="artifacts/schema.svg" width="600" alt="ER diagram">

## Core pages
1. AI-assisted search  
2. Home  
3. Team Explorer  
4. Players Explorer  
5. Season Viewer  
6. Rankings  
7. Venues  
8. Coaches

## Getting started
1. Create virtual environment:  
     - `uv init`
2. Activate and install:  
     - copy paste './pyproject.toml`
     - `uv sync`
3. Run the app:  
     - `streamlit run frontend_st.py`

