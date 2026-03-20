import csv
import json
import os
from django.core.management.base import BaseCommand, CommandError
from movies.models import Movie


def parse_genres(genres_json):
    """
    genres column is a JSON array:
        [{"id": 28, "name": "Action"}, {"id": 12, "name": "Adventure"}]
    Returns first two names joined with "/" e.g. "Action/Adventure".
    """
    try:
        genres = json.loads(genres_json)
        names = [g["name"] for g in genres if "name" in g]
        return "/".join(names[:2]) if names else "Unknown"
    except (json.JSONDecodeError, TypeError):
        return "Unknown"


def parse_year(release_date):
    """release_date = "2009-12-10" -> 2009, or 0 on failure."""
    if not release_date:
        return 0
    try:
        return int(release_date[:4])
    except (ValueError, IndexError):
        return 0


def build_director_map(credits_csv_path):
    """
    Reads tmdb_5000_credits.csv and returns {movie_id: director_name}.

    The crew column is a JSON array of objects. We find the first entry
    where job == "Director".
    """
    director_map = {}
    if not os.path.exists(credits_csv_path):
        return director_map

    with open(credits_csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            movie_id = row.get("movie_id", "").strip()
            crew_json = row.get("crew", "[]")
            try:
                crew = json.loads(crew_json)
                for member in crew:
                    if member.get("job") == "Director":
                        director_map[movie_id] = member.get("name", "Unknown")
                        break
            except (json.JSONDecodeError, TypeError):
                pass

    return director_map


class Command(BaseCommand):
    help = "Import movies from TMDB Kaggle CSVs (with optional director from credits)."

    def add_arguments(self, parser):
        parser.add_argument("movies_csv", type=str, help="Path to tmdb_5000_movies.csv")
        parser.add_argument(
            "credits_csv", type=str, nargs="?", default=None,
            help="Path to tmdb_5000_credits.csv (optional — enables director names)",
        )
        parser.add_argument("--limit", type=int, default=None,
            help="Max movies to import (default: all)")
        parser.add_argument("--clear", action="store_true",
            help="Delete all existing movies and reviews before importing")

    def handle(self, *args, **options):
        cwd = os.getcwd()
        movies_csv = options["movies_csv"]
        credits_csv = options["credits_csv"]

        if not os.path.isabs(movies_csv):
            movies_csv = os.path.join(cwd, movies_csv)
        if credits_csv and not os.path.isabs(credits_csv):
            credits_csv = os.path.join(cwd, credits_csv)

        if not os.path.exists(movies_csv):
            raise CommandError(
                f"Movies CSV not found: {movies_csv}\n"
                "Download from: https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata"
            )

        # Build director lookup
        if credits_csv:
            if not os.path.exists(credits_csv):
                self.stdout.write(self.style.WARNING(
                    f"Credits CSV not found: {credits_csv} — directors will be 'Unknown'."
                ))
                director_map = {}
            else:
                self.stdout.write("Reading credits CSV...")
                director_map = build_director_map(credits_csv)
                self.stdout.write(self.style.SUCCESS(
                    f"  Director map: {len(director_map)} entries"
                ))
        else:
            self.stdout.write(self.style.WARNING(
                "No credits CSV — directors will be 'Unknown'. "
                "Pass it as a second argument to enable director names."
            ))
            director_map = {}

        if options["clear"]:
            from movies.models import Review
            Review.objects.all().delete()
            n, _ = Movie.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Cleared {n} movies."))

        limit = options["limit"]
        imported = skipped = errors = 0

        self.stdout.write("Importing movies...")

        with open(movies_csv, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if limit is not None and imported >= limit:
                    break

                movie_id    = row.get("id", "").strip()
                title       = row.get("title", "").strip()
                overview    = row.get("overview", "").strip()
                genres_raw  = row.get("genres", "[]")
                release_date = row.get("release_date", "")

                if not title or not overview:
                    skipped += 1
                    continue

                release_year = parse_year(release_date)
                if release_year == 0:
                    skipped += 1
                    continue

                genre    = parse_genres(genres_raw)
                director = director_map.get(movie_id, "Unknown")

                try:
                    Movie.objects.get_or_create(
                        title=title,
                        release_year=release_year,
                        defaults={
                            "genre": genre,
                            "director": director,
                            "overview": overview[:2000],
                        },
                    )
                    imported += 1
                except Exception as exc:
                    self.stderr.write(f"Error on '{title}': {exc}")
                    errors += 1

        self.stdout.write(self.style.SUCCESS(
            f"\nImport complete.\n"
            f"  Imported : {imported}\n"
            f"  Skipped  : {skipped}  (no overview or missing year)\n"
            f"  Errors   : {errors}\n"
            f"  Total movies in DB: {Movie.objects.count()}"
        ))
        if director_map:
            named = Movie.objects.exclude(director="Unknown").count()
            self.stdout.write(f"  Movies with named director: {named}")