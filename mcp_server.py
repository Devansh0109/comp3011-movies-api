import os
import json
import requests
from mcp.server.fastmcp import FastMCP

# ── Config ────────────────────────────────────────────────────────────────────
BASE_URL = os.environ.get("MOVIES_API_BASE", "http://127.0.0.1:8000/api")
API_TOKEN = os.environ.get("MOVIES_API_TOKEN", "")

mcp = FastMCP("Movies API")


def _headers():
    h = {"Content-Type": "application/json"}
    if API_TOKEN:
        h["Authorization"] = f"Token {API_TOKEN}"
    return h


def _get(path, params=None):
    resp = requests.get(f"{BASE_URL}{path}", headers=_headers(), params=params)
    return resp.json()


def _post(path, data):
    resp = requests.post(f"{BASE_URL}{path}", headers=_headers(), json=data)
    return resp.json()


def _patch(path, data):
    resp = requests.patch(f"{BASE_URL}{path}", headers=_headers(), json=data)
    return resp.json()


def _delete(path):
    resp = requests.delete(f"{BASE_URL}{path}", headers=_headers())
    return {"status": resp.status_code, "success": resp.status_code == 204}


# ── Auth tools ────────────────────────────────────────────────────────────────

@mcp.tool()
def register(username: str, password: str) -> dict:
    """Register a new user and return an auth token."""
    return _post("/auth/register/", {"username": username, "password": password})


@mcp.tool()
def login(username: str, password: str) -> dict:
    """Login with existing credentials and return an auth token."""
    return _post("/auth/login/", {"username": username, "password": password})


# ── Movie tools ───────────────────────────────────────────────────────────────

@mcp.tool()
def list_movies() -> list:
    """List all movies in the catalogue with their average ratings."""
    return _get("/movies/")


@mcp.tool()
def get_movie(movie_id: int) -> dict:
    """Get full details for a single movie including average rating and review count."""
    return _get(f"/movies/{movie_id}/")


@mcp.tool()
def create_movie(title: str, genre: str, release_year: int, director: str, overview: str = "") -> dict:
    """Create a new movie entry. Requires a valid auth token set in MOVIES_API_TOKEN."""
    return _post("/movies/", {
        "title": title,
        "genre": genre,
        "release_year": release_year,
        "director": director,
        "overview": overview,
    })


@mcp.tool()
def update_movie(movie_id: int, title: str = None, genre: str = None,
                 release_year: int = None, director: str = None, overview: str = None) -> dict:
    """Partially update a movie. Only supply the fields you want to change."""
    data = {k: v for k, v in {
        "title": title, "genre": genre, "release_year": release_year,
        "director": director, "overview": overview,
    }.items() if v is not None}
    return _patch(f"/movies/{movie_id}/", data)


@mcp.tool()
def delete_movie(movie_id: int) -> dict:
    """Delete a movie and all its reviews. Requires auth."""
    return _delete(f"/movies/{movie_id}/")


# ── Review tools ──────────────────────────────────────────────────────────────

@mcp.tool()
def list_reviews(movie_id: int) -> list:
    """List all reviews for a specific movie."""
    return _get(f"/movies/{movie_id}/reviews/")


@mcp.tool()
def add_review(movie_id: int, reviewer_name: str, rating: int, comment: str = "") -> dict:
    """Add a review to a movie. Rating must be between 1 and 5. Requires auth."""
    return _post(f"/movies/{movie_id}/reviews/", {
        "reviewer_name": reviewer_name,
        "rating": rating,
        "comment": comment,
    })


@mcp.tool()
def delete_review(movie_id: int, review_id: int) -> dict:
    """Delete a specific review. Requires auth."""
    return _delete(f"/movies/{movie_id}/reviews/{review_id}/")


# ── Analytics tools ───────────────────────────────────────────────────────────

@mcp.tool()
def search_movies(query: str = None, genre: str = None,
                  year: int = None, min_rating: float = None) -> list:
    """
    Search and filter movies. All parameters are optional and combinable.
    - query: searches title, director, and overview
    - genre: filter by genre name (partial match)
    - year: filter by exact release year
    - min_rating: only return movies with average rating >= this value
    """
    params = {}
    if query:      params["q"] = query
    if genre:      params["genre"] = genre
    if year:       params["year"] = year
    if min_rating: params["min_rating"] = min_rating
    return _get("/movies/search/", params=params)


@mcp.tool()
def top_rated_movies(limit: int = 10) -> list:
    """Get the top-rated movies ranked by average review score."""
    return _get("/movies/top-rated/", params={"limit": limit})


@mcp.tool()
def most_reviewed_movies(limit: int = 10) -> list:
    """Get the most-reviewed movies ranked by total review count."""
    return _get("/movies/most-reviewed/", params={"limit": limit})


@mcp.tool()
def genre_summary() -> list:
    """Get per-genre statistics: movie count and average rating for each genre."""
    return _get("/movies/genre-summary/")


@mcp.tool()
def decade_summary() -> list:
    """Get per-decade statistics: movie count and average rating from 1920s to 2020s."""
    return _get("/movies/decade-summary/")

@mcp.tool()
def get_movie_recommendations(movie_id: int) -> dict:
    """
    Get 5 recommended movies similar to the given movie.
    Uses a weighted content-based filtering algorithm scoring on:
    genre overlap (40pts), same director (30pts), era proximity (20pts),
    and rating similarity (10pts). No external API required.
    """
    return _get(f"/movies/{movie_id}/recommendations/")

# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()