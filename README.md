# 🎬 Movies API

A production-ready RESTful Web API for managing a curated movie catalogue, built with **Django REST Framework**. Integrates ~4,800 real films from the TMDB dataset, exposes analytical endpoints for genre and decade trends, implements a content-based recommendation engine, and ships an MCP server for natural language querying via Claude Desktop.

**Module:** COMP3011 Web Services and Web Data — University of Leeds  
**Live API:** https://devanshsinghal0109.pythonanywhere.com/api/  
**Swagger UI:** https://devanshsinghal0109.pythonanywhere.com/api/docs/  
**API Schema:** https://devanshsinghal0109.pythonanywhere.com/api/schema/

---

## Features

- **Full CRUD** for movies and reviews with input validation and correct HTTP status codes
- **Token authentication** — register/login to obtain a token; all write operations are protected
- **5 analytical endpoints** — top-rated, most-reviewed, genre summary, decade trends, advanced search
- **Content-based recommendation engine** — scores films on genre, director, era, and rating similarity
- **MCP server** — exposes all endpoints as tools for AI assistants (Claude Desktop)
- **4,800+ real movies** imported from the TMDB Kaggle dataset with director names from credits data
- **14,000+ synthetic reviews** calibrated to TMDB vote statistics
- **47 tests** covering auth, CRUD, analytics, recommendations, and serialiser structure
- **OpenAPI 3 documentation** auto-generated via drf-spectacular

---

## Tech Stack

| Layer | Choice | Reason |
|-------|--------|--------|
| Language | Python 3.12 | Ecosystem, DRF support |
| Framework | Django 6 + DRF 3.16 | Serialisers, ORM, permissions built-in |
| Database | SQLite (dev) / PostgreSQL-ready | ORM-only access; portable schema |
| Auth | DRF Token Authentication | Stateless, no additional dependencies |
| API Docs | drf-spectacular (OpenAPI 3) | Auto-generated, always in sync with code |
| Recommender | Content-based filtering | No cost, offline, explainable results |
| AI Interface | MCP server (FastMCP) | Natural language tool calls via Claude Desktop |
| Deployment | PythonAnywhere | Free tier, Python-native hosting |

---

## Project Structure

```
comp3011-movies-api/
├── src/
│   ├── movies/
│   │   ├── management/
│   │   │   └── commands/
│   │   │       ├── import_movies.py     # Import TMDB dataset (merges 2 CSVs)
│   │   │       ├── seed_reviews.py      # Generate calibrated synthetic reviews
│   │   ├── migrations/
│   │   ├── models.py                    # Movie and Review models
│   │   ├── serializers.py               # MovieSerializer, ReviewSerializer
│   │   ├── views.py                     # All CRUD and analytics views
│   │   ├── recommendation_view.py       # Content-based recommendation engine
│   │   ├── urls.py                      # URL routing
│   │   └── tests.py                     # 47 tests across 8 test classes
│   ├── movies_api/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   └── manage.py
├── mcp_server.py                        # MCP server for Claude Desktop
├── requirements.txt
├── docs/
│   └── api-documentation.pdf           # Swagger UI exported as PDF
├── screenshots/
├── genai-logs/
└── README.md
```

---

## Setup Instructions

### Prerequisites

- Python 3.12+
- pip

### 1. Clone the repository

```bash
git clone https://github.com/Devansh0109/comp3011-movies-api.git
cd comp3011-movies-api
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate        # macOS/Linux
.venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run migrations

```bash
cd src
python manage.py migrate
```

### 5. Import the TMDB dataset

Download both CSV files from [Kaggle — TMDB Movie Metadata](https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata) and place them in `src/data/`:

```
src/data/tmdb_5000_movies.csv
src/data/tmdb_5000_credits.csv
```

Then run:

```bash
python manage.py import_movies data/tmdb_5000_movies.csv data/tmdb_5000_credits.csv
python manage.py seed_reviews --votes-csv data/tmdb_5000_movies.csv
```

This imports ~4,800 films with director names extracted from the credits CSV, then generates calibrated synthetic reviews.

### 6. Start the development server

```bash
python manage.py runserver
```

The API is now available at `http://127.0.0.1:8000/api/`  
Swagger UI is available at `http://127.0.0.1:8000/api/docs/`

---

## Running Tests

```bash
cd src
python manage.py test movies.tests
```

Expected output:
```
Ran 47 tests in X.Xs
OK
```

---

## API Endpoints

### Authentication

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/auth/register/` | Register a new user, returns token | No |
| POST | `/api/auth/login/` | Login with credentials, returns token | No |

### Movies

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/movies/` | List all movies (paginated) | No |
| POST | `/api/movies/` | Create a movie | Yes |
| GET | `/api/movies/<id>/` | Retrieve a movie | No |
| PUT | `/api/movies/<id>/` | Full update | Yes |
| PATCH | `/api/movies/<id>/` | Partial update | Yes |
| DELETE | `/api/movies/<id>/` | Delete movie and all reviews | Yes |

### Reviews

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/movies/<id>/reviews/` | List reviews for a movie | No |
| POST | `/api/movies/<id>/reviews/` | Add a review (rating 1–5) | Yes |
| PATCH | `/api/movies/<id>/reviews/<rid>/` | Update a review | Yes |
| DELETE | `/api/movies/<id>/reviews/<rid>/` | Delete a review | Yes |

### Analytics

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/movies/search/` | Filter by `q`, `genre`, `year`, `min_rating` | No |
| GET | `/api/movies/top-rated/` | Ranked by average rating (`?limit=N`) | No |
| GET | `/api/movies/most-reviewed/` | Ranked by review count (`?limit=N`) | No |
| GET | `/api/movies/genre-summary/` | Per-genre movie count and average rating | No |
| GET | `/api/movies/decade-summary/` | Per-decade movie count and average rating | No |

### AI-Powered

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/movies/<id>/recommendations/` | 5 similar films with match scores and reasons | No |

---

## Authentication

All write operations require a token in the `Authorization` header:

```
Authorization: Token <your-token>
```

**Obtain a token:**

```bash
curl -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your-username", "password": "your-password"}'
```

Response:
```json
{
  "token": "abc123your-token-here"
}
```

**Use the token:**

```bash
curl -X POST http://127.0.0.1:8000/api/movies/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token abc123your-token-here" \
  -d '{"title": "Inception", "genre": "Sci-Fi/Thriller", "release_year": 2010, "director": "Christopher Nolan"}'
```

---

## Recommendation Engine

The recommendations endpoint uses a weighted content-based filtering algorithm — no external API or user history required.

**Scoring factors (max 100 points):**

| Factor | Points | Logic |
|--------|--------|-------|
| Genre overlap | 0–40 | Proportional to shared genres |
| Director match | 30 | Exact match, ignores 'Unknown' |
| Era proximity | 20 or 10 | Within 5 years = 20pts, within 15 years = 10pts |
| Rating similarity | 10 | Average rating within 0.5 stars |

**Example response:**

```bash
curl https://devanshsinghal0109.pythonanywhere.com/api/movies/1/recommendations/
```

```json
{
  "movie": {
    "id": 1,
    "title": "Avatar",
    "year": 2009,
    "genre": "Action/Adventure"
  },
  "recommendations": [
    {
      "title": "Dune",
      "year": 2021,
      "genre": "Action/Adventure",
      "match_score": 58,
      "reasons": ["Similar genres (Action, Adventure)", "From a similar era"]
    }
  ],
  "algorithm": "Weighted Heuristic (Content-Based Filtering)"
}
```

---

## MCP Server (Claude Desktop Integration)

The project includes an MCP server that exposes all API endpoints as callable tools for AI assistants.

### Setup

**1. Install dependencies:**
```bash
pip install mcp requests
```

**2. Get your auth token:**
```bash
curl -s -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"your-username","password":"your-password"}'
```

**3. Configure Claude Desktop** — edit `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "movies-api": {
      "command": "python",
      "args": ["path/to/comp3011-movies-api/mcp_server.py"],
      "env": {
        "MOVIES_API_BASE": "http://127.0.0.1:8000/api",
        "MOVIES_API_TOKEN": "your-token-here"
      }
    }
  }
}
```

Replace `path/to/comp3011-movies-api/mcp_server.py` with the absolute path to the file on your machine. On macOS this is typically `/Users/your-username/Documents/comp3011-movies-api/mcp_server.py`. Use the full path to your virtual environment Python if `python` is not found — e.g. `/path/to/.venv/bin/python`.

**4. Restart Claude Desktop.** The hammer icon (🔨) confirms the server is connected or you can check by visiting developer section in the claude desktop and if it says API connected , it works.

**5. Try it:**
```
What are the top 5 rated movies in the database?
Search for sci-fi movies with a rating above 4
Find movies similar to Inception
What are the genre statistics?
```

---

## Data Sources

- **TMDB Movie Metadata** — [Kaggle](https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata) — CC0 Public Domain
  - `tmdb_5000_movies.csv` — movie metadata (title, genres, release date, overview)
  - `tmdb_5000_credits.csv` — cast and crew data (director extracted from JSON crew array)

The dataset files are not committed to this repository. Download them from Kaggle and place in `src/data/` before running the import command.

---

## API Documentation

Full interactive documentation is available via Swagger UI:

- **Live:** https://devanshsinghal0109.pythonanywhere.com/api/docs/
- **PDF:** [docs/api-documentation.pdf](docs/api-documentation.pdf)

---

## Generative AI Declaration

This project was built with Claude (Anthropic) as the primary GenAI tool. AI was used for architecture design, dataset discovery, import script generation, recommendation algorithm design, test strategy, MCP server implementation, and debugging. All uses are declared in the technical report and conversation logs are available in `genai-logs/`.

This is a Green Light Assessment — GenAI use is permitted and encouraged.

---

## Deliverables

- [x] Public GitHub repository with commit history
- [x] README.md with setup instructions
- [x] API documentation PDF (`docs/api-documentation.pdf`)
- [x] Technical report (`report/technical-report.pdf`)
- [x] Presentation slides (`slides/`)
- [x] GenAI conversation logs (`genai-logs/`)
- [x] Live deployment on PythonAnywhere
- [x] 47 passing tests

---

## License

This project was developed for academic purposes as part of COMP3011 at the University of Leeds.