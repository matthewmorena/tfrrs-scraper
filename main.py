from fastapi import FastAPI, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from api.routes import athletes, meets, teams, search

# -------------------------
# Initialize FastAPI
# -------------------------
app = FastAPI(
    title="TFRRS Scraper API",
    description="FastAPI backend for scraping athlete, team, and meet data from TFRRS.org",
    version="1.0.0",
)

# -------------------------
# Global Rate Limiter Setup
# -------------------------
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Instead of calling a private method (_check_request_limit),
# just decorate the entire app router using limiter.limit()
@app.middleware("http")
@limiter.limit("5/second")  # limit applied globally
async def global_rate_limiter(request: Request, call_next):
    response = await call_next(request)
    return response

# -------------------------
# Include Routers
# -------------------------
app.include_router(athletes.router, prefix="/athletes", tags=["Athletes"])
app.include_router(meets.router, prefix="/meets", tags=["Meets"])
app.include_router(teams.router, prefix="/teams", tags=["Teams"])
app.include_router(search.router, prefix="/search", tags=["Search"])

# -------------------------
# Root Endpoint
# -------------------------
@app.get("/", tags=["Root"])
async def root():
    return {"message": "Welcome to the TFRRS Scraper API"}
