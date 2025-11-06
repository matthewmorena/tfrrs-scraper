
# TFRRS Scraper API

A FastAPI-based web service for scraping structured data from [TFRRS.org](https://www.tfrrs.org), including athletes, meets, teams, and rosters.
Built for reliable programmatic access to collegiate track & field and cross country results.

---

## Features

* **Search endpoints** for athletes, teams, and meets
* **Detailed meet results** (Track & Field & Cross Country)
* **Gender-aware TF scraping** (`/m` or `/f`)
* **Full athlete history** (team changes, performances, non-relay filtering)
* **Team roster & conference info**
* **Logging & error handling** for reliable scraping
* Modular design with reusable **utils** and **scrapers**

---

## Project Structure

```
tfrrs-scraper/
├── scrapers/
│   ├── getSearchResults.py
│   ├── getAthleteDetails.py
│   ├── getMeetDetails.py
│   ├── getTeamRoster.py
│
├── utils/
│   ├── common.py
│   ├── logging_config.py
│
├── api/
│   ├── main.py
│   ├── routes/
│   │   ├── athletes.py
│   │   ├── meets.py
│   │   ├── teams.py
│
├── logs/
│   ├── *.log
│
├── Dockerfile
├── .dockerignore
├── requirements.txt
├── README.md
└── .gitignore
```

---

## Setup

### Local (Python)

```bash
# Clone repo
git clone https://github.com/yourusername/tfrrs-scraper.git
cd tfrrs-scraper

# Create virtual environment
python -m venv venv
source venv/bin/activate   # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Run FastAPI
uvicorn api.main:app --reload
```

---

### Docker

Build and run the containerized API:

```bash
docker build -t tfrrs-scraper .
docker run -d -p 8000:8000 tfrrs-scraper
```

Visit the interactive API docs at
- [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Example API Calls

**Search for a team:**

```
GET /search?query_type=team&query_value=Northern Arizona
```

**Get meet results:**

```
GET /meets/92668?sport=tf&gender=f
```

**Fetch athlete details:**

```
GET /athletes/7929458
```

---

## Environment Variables

You can define these in a `.env` file (optional):

```
LOG_LEVEL=INFO
PORT=8000
```

---

## Tech Stack

* **Python 3.11+**
* **FastAPI**
* **BeautifulSoup4**
* **Requests**
* **Docker**
* **RotatingFileHandler logging**

---

## Notes

* All scrapers are designed for **read-only public data** on TFRRS.
* The API is stateless and does **not** persist data — integrate it with your own DB if needed.
* Relay, para, and field events are automatically filtered out from athlete and meet scrapes.
* Logs are stored in `/logs` and rotated automatically.

---

## License

MIT License © 2025 — You are free to modify and distribute with attribution.
