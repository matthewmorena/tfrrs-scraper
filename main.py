from fastapi import FastAPI
from api.routes import athletes, meets, teams, search

app = FastAPI(
    title="TFRRS Scraper API",
    description="FastAPI backend for scraping athlete, team, and meet data from TFRRS.org",
    version="1.0.0",
)

# Include routes
app.include_router(athletes.router, prefix="/athletes", tags=["Athletes"])
app.include_router(meets.router, prefix="/meets", tags=["Meets"])
app.include_router(teams.router, prefix="/teams", tags=["Teams"])
app.include_router(search.router, prefix="/search", tags=["Search"])


@app.get("/", tags=["Root"])
def root():
    return {"message": "Welcome to the TFRRS Scraper API"}
