# Introduction to Sports Analytics using Python — Notebooks

This repository contains the Jupyter notebooks that accompany the textbook
**Introduction to Sports Analytics using Python** by Ryan Elmore and Andrew Urbaczewski.

Each notebook corresponds to a chapter in the book and can be run independently.
They are self-contained: all data are fetched from public APIs or loaded from the
`isapy-data` package included in the requirements.

## Notebooks

| Notebook | Chapter |
|---|---|
| `intro.ipynb` | Introduction |
| `intro-to-python.ipynb` | Introduction to Python |
| `web-scraping.ipynb` | Web Scraping |
| `baseball.ipynb` | Baseball |
| `basketball.ipynb` | Basketball |
| `football.ipynb` | Football |
| `hockey.ipynb` | Hockey |
| `soccer.ipynb` | Soccer |
| `golf.ipynb` | Golf |
| `wagering.ipynb` | Sports Wagering |

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/rtelmore/isapy-code.git
cd isapy-code
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run Notebooks

You can use jupyter or VS Code (or whatever) to interact with the notebooks. 

## MLB Utility Module

The file `mlb_utils.py` provides helper functions that query the
[MLB Stats API](https://statsapi.mlb.com) for baseball data. These replace
FanGraphs-dependent functions from `pybaseball` with equivalents that work on
any machine without requiring a disk cache or API key.

```python
from mlb_utils import batting_stats_mlb, team_batting_mlb, team_pitching_mlb, pitching_stats_mlb

# Team batting totals for a season
team_batting_mlb(2025)

# Individual player batting stats (minimum 100 plate appearances)
batting_stats_mlb(2025, min_pa=100)

# Team pitching totals for a season
team_pitching_mlb(2025)

# Individual player pitching stats (minimum 20 innings pitched)
pitching_stats_mlb(2025, min_ip=20)
```

All functions return a `pandas` DataFrame with standard column names
(`HR`, `BB`, `SO`, `AVG`, `OBP`, `SLG`, etc.).

## Notes

- Data availability varies by sport and season. Some APIs may not yet have
  full data for the current season.

## License

See the textbook for licensing terms.
