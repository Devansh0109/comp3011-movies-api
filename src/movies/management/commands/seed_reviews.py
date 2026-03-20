import csv
import json
import math
import os
import random
from django.core.management.base import BaseCommand
from movies.models import Movie, Review


# ── Reviewer name pool ────────────────────────────────────────────────────────

REVIEWER_NAMES = [
    "Alex T.", "Priya K.", "Jordan M.", "Sam W.", "Chris B.",
    "Taylor R.", "Morgan L.", "Casey P.", "Riley H.", "Dana F.",
    "Quinn A.", "Avery S.", "Blake N.", "Drew C.", "Emerson V.",
    "Sage D.", "Parker J.", "Reese O.", "Logan E.", "Hayden G.",
    "Rowan X.", "Finley Z.", "Skylar U.", "Cameron I.", "Peyton Y.",
]

# ── Comment templates keyed by star rating ────────────────────────────────────
# Each entry is a list of comment strings. We randomly pick one per review.

COMMENTS = {
    5: [
        "An absolute masterpiece. One of the finest films I have ever seen.",
        "Flawless from start to finish. The direction and performances are exceptional.",
        "A cinematic triumph. Left me speechless.",
        "Genuinely outstanding. Every scene is purposeful and beautifully crafted.",
        "A landmark film. Essential viewing — I cannot recommend it highly enough.",
        "Stunning visuals and a powerful story. Easily a five-star experience.",
        "One of those rare films that stays with you long after the credits roll.",
        "Perfect pacing, incredible performances, and a story that resonates deeply.",
    ],
    4: [
        "Really enjoyed this. Minor pacing issues aside, it is a very strong film.",
        "Impressive on almost every level. A few scenes drag but the overall result is excellent.",
        "Very well made with standout performances. Highly recommended.",
        "Great film with a compelling story. Falls just short of perfect but not by much.",
        "Thoroughly entertaining and well-crafted. A solid four stars.",
        "Strong direction and great writing. One or two moments feel slightly off but mostly superb.",
        "Engaging from the first scene. Great work all round.",
        "A very good film with a lot to admire. Would definitely watch again.",
    ],
    3: [
        "Decent enough. Has its moments but does not fully deliver on its potential.",
        "Watchable but unremarkable. Some good ideas that could have been developed further.",
        "Fine for what it is. Not something I would rush to recommend but not bad either.",
        "Mixed feelings on this one. The first half is strong but it loses its way later on.",
        "Competent filmmaking with a few standout scenes. Ultimately forgettable.",
        "There is a good film in here somewhere. As it stands, just okay.",
        "Middle of the road. Neither disappointing nor particularly impressive.",
        "Has some real highlights but also some significant weaknesses.",
    ],
    2: [
        "Disappointing. The premise is interesting but the execution falls flat.",
        "A weak script lets down what could have been a much better film.",
        "Not much to recommend here. The pacing is off and the story goes nowhere interesting.",
        "Struggled to stay engaged. Too slow and the payoff is not worth the wait.",
        "Below average. Some decent moments but they are few and far between.",
        "Overhyped and underdelivered. Expected considerably more.",
        "The performances are fine but the material they are working with is poor.",
        "Would not bother watching this again.",
    ],
    1: [
        "A real disappointment. Poorly made and difficult to sit through.",
        "Genuinely bad. Hard to find anything positive to say.",
        "Wasted a promising premise entirely. One star is generous.",
        "Tedious, incoherent, and poorly executed throughout.",
        "One of the worst films I have seen in a long time.",
        "I struggled to finish this. Not recommended at all.",
    ],
}


def tmdb_to_five_star(vote_average):
    """
    Convert a TMDB vote_average (0-10) to a 1-5 star scale.

    TMDB scores cluster between 5 and 8 for most films. We use a simple
    linear mapping but clamp to valid range:
        TMDB 10 -> 5 stars
        TMDB 5  -> 2.5 stars (rounds to 3)
        TMDB 0  -> 1 star (minimum)
    """
    converted = vote_average / 2.0  # e.g. 7.4 -> 3.7
    return max(1.0, min(5.0, converted))


def generate_rating_around(target, sigma=0.7):
    """
    Draw a random integer rating (1-5) from a normal distribution
    centred on `target` with standard deviation `sigma`.
    This produces a realistic spread of opinions around the film's true quality.
    """
    raw = random.gauss(target, sigma)
    return max(1, min(5, round(raw)))


def reviews_for_vote_count(vote_count, max_per_movie):
    """
    Scale the number of synthetic reviews to the film's real TMDB popularity.
    We use a logarithmic scale so blockbusters get more reviews than obscure films,
    but not so many that the database becomes enormous.

    vote_count 0-50    -> 1-2 reviews
    vote_count 50-500  -> 2-5 reviews
    vote_count 500+    -> 5-max_per_movie reviews
    """
    if vote_count <= 0:
        return 1
    # log base 10: count=10->1, count=100->2, count=1000->3, count=10000->4
    log_val = math.log10(max(1, vote_count))
    scaled = int(log_val * (max_per_movie / 4))
    return max(1, min(max_per_movie, scaled))


class Command(BaseCommand):
    help = "Seed synthetic reviews for all movies, using TMDB vote data for realism."

    def add_arguments(self, parser):
        parser.add_argument(
            "--votes-csv",
            type=str,
            default=None,
            help=(
                "Path to tmdb_5000_movies.csv. If provided, vote_average and "
                "vote_count are read to calibrate ratings and review counts. "
                "If omitted, a random rating distribution is used instead."
            ),
        )
        parser.add_argument(
            "--max-per-movie",
            type=int,
            default=6,
            help="Maximum reviews to generate per movie (default: 6)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all existing reviews before seeding",
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=42,
            help="Random seed for reproducibility (default: 42)",
        )

    def handle(self, *args, **options):
        random.seed(options["seed"])
        max_per_movie = options["max_per_movie"]

        if options["clear"]:
            deleted, _ = Review.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Cleared {deleted} existing reviews."))

        # ── Build vote lookup from TMDB CSV (if provided) ─────────────────
        vote_data = {}  # title -> {"average": float, "count": int}

        votes_csv = options["votes_csv"]
        if votes_csv:
            if not os.path.isabs(votes_csv):
                votes_csv = os.path.join(os.getcwd(), votes_csv)

            if not os.path.exists(votes_csv):
                self.stdout.write(self.style.WARNING(
                    f"Votes CSV not found: {votes_csv} — using random ratings."
                ))
            else:
                self.stdout.write("Reading vote data from TMDB CSV...")
                with open(votes_csv, newline="", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        title = row.get("title", "").strip()
                        try:
                            avg   = float(row.get("vote_average", 0) or 0)
                            count = int(row.get("vote_count", 0) or 0)
                            vote_data[title] = {"average": avg, "count": count}
                        except ValueError:
                            pass
                self.stdout.write(self.style.SUCCESS(
                    f"  Vote data loaded for {len(vote_data)} titles."
                ))

        # ── Generate reviews for every movie in DB ────────────────────────
        movies = Movie.objects.all()
        total_movies   = movies.count()
        total_reviews  = 0
        skipped        = 0

        self.stdout.write(f"Generating reviews for {total_movies} movies...")

        for movie in movies.iterator():
            # Skip if movie already has reviews
            if movie.reviews.exists():
                skipped += 1
                continue

            # Get TMDB vote data for this movie (matched by exact title)
            vdata = vote_data.get(movie.title)

            if vdata and vdata["average"] > 0:
                target_rating = tmdb_to_five_star(vdata["average"])
                num_reviews   = reviews_for_vote_count(vdata["count"], max_per_movie)
            else:
                # No TMDB data: use a mild positive skew (most films are average-to-good)
                target_rating = random.uniform(2.5, 4.2)
                num_reviews   = random.randint(1, max_per_movie)

            used_names = set()
            for _ in range(num_reviews):
                # Pick a unique reviewer name per movie
                available = [n for n in REVIEWER_NAMES if n not in used_names]
                if not available:
                    available = REVIEWER_NAMES  # reset if exhausted
                reviewer = random.choice(available)
                used_names.add(reviewer)

                rating  = generate_rating_around(target_rating)
                comment = random.choice(COMMENTS[rating])

                Review.objects.create(
                    movie=movie,
                    reviewer_name=reviewer,
                    rating=rating,
                    comment=comment,
                )
                total_reviews += 1

        self.stdout.write(self.style.SUCCESS(
            f"\nReview seeding complete.\n"
            f"  Reviews created : {total_reviews}\n"
            f"  Movies skipped  : {skipped}  (already had reviews)\n"
            f"  Total reviews in DB: {Review.objects.count()}"
        ))

        # Summary stats
        from django.db.models import Avg, Count
        stats = Review.objects.aggregate(
            avg_rating=Avg("rating"),
            total=Count("id"),
        )
        self.stdout.write(
            f"  Overall avg rating: {round(stats['avg_rating'] or 0, 2)} / 5.0"
        )