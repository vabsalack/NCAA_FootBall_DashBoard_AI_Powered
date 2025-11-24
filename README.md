# Sportradar NCAAFB Dashboard

<img src="artifacts/ncaa_fb.svg" width="200" alt="NCAA football logo">

## Overview
NCAA football dashboard: a compact 4-day project for ETL of API data into MySQL and a Streamlit frontend. Key features include AI-assisted data retrievals from MySQL and contextual filter/search on each page.

## API & Tech stack

### API
- [Sportradar NCAA Marketplace](https://raw.githubusercontent.com/vabsalack/NCAA_FootBall_DashBoard_AI_Powered/6db535bf53a104515f5812b09cfd1fd03a8e3c8a/artifacts/ncaa_fb.svg)

- Since it were a trial API, Extracted and Transformed data were saved under `/db_csv` directory.

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

<img src="https://raw.githubusercontent.com/vabsalack/NCAA_FootBall_DashBoard_AI_Powered/47e876bafe7d76e746361db2d0be3cdb3f91b1d3/artifacts/schema.svg" width="600" alt="ER diagram">

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

