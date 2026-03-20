from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status, serializers as rf_serializers
from drf_spectacular.utils import extend_schema, inline_serializer
from django.db.models import Avg, Q, Count

from .models import Movie


@extend_schema(
    responses=inline_serializer("RecommendationResponse", fields={
        "movie": rf_serializers.DictField(),
        "recommendations": rf_serializers.ListField(),
        "algorithm": rf_serializers.CharField(),
    }),
    tags=["ai"]
)
@api_view(["GET"])
@permission_classes([AllowAny])
def movie_recommendations(request, pk):
    """

    Returns the 5 most similar movies using a weighted content-based
    filtering algorithm.

    Scoring breakdown (max 100 points):
      - Genre match    : up to 40 pts (proportional to overlapping genres)
      - Director match : 30 pts (exact match, ignores 'Unknown')
      - Era proximity  : 20 pts (within 5 years) or 10 pts (within 15 years)
      - Rating quality : 10 pts (average rating within 0.5 stars)

    Performance: candidates are pre-filtered by genre or director before
    scoring, avoiding a full table scan of 4800+ movies.
    """

    # ── 1. Source movie ───────────────────────────────────────────────────────
    movie = get_object_or_404(Movie, pk=pk)

    # ── 2. Source attributes ─────────────────────────────────────────────────
    # Genres are stored as slash-separated strings e.g. "Action/Adventure"
    source_genres = [g.strip().lower() for g in movie.genre.split("/") if g.strip()]
    source_director = movie.director.strip().lower()
    source_year = movie.release_year
    source_avg = movie.reviews.aggregate(a=Avg("rating"))["a"] or 3.0

    # ── 3. Pre-filter candidates (performance optimisation) ──────────────────
    # Only consider movies sharing at least one genre OR the same director.
    # This avoids iterating the full 4800-row table for every request.
    genre_query = Q()
    for g in source_genres:
        genre_query |= Q(genre__icontains=g)

    candidates = (
        Movie.objects.exclude(pk=pk)
        .filter(Q(director__iexact=source_director) | genre_query)
        .annotate(
            avg_rating=Avg("reviews__rating"),
            review_count=Count("reviews"),
        )
    )

    # ── 4. Scoring engine ────────────────────────────────────────────────────
    scored_results = []

    for candidate in candidates:
        score = 0
        reasons = []

        # A. Genre match — up to 40 points
        candidate_genres = [g.strip().lower() for g in candidate.genre.split("/") if g.strip()]
        common = set(source_genres) & set(candidate_genres)
        if common:
            genre_score = int(40 * (len(common) / max(len(source_genres), 1)))
            score += genre_score
            display = ", ".join(g.title() for g in list(common)[:2])
            reasons.append(f"Similar genres ({display})")

        # B. Director match — 30 points
        if candidate.director.strip().lower() == source_director and source_director != "unknown":
            score += 30
            reasons.append(f"Also directed by {candidate.director}")

        # C. Era proximity — 20 or 10 points
        year_diff = abs(candidate.release_year - source_year)
        if year_diff <= 5:
            score += 20
            reasons.append("Released around the same time")
        elif year_diff <= 15:
            score += 10
            reasons.append("From a similar era")

        # D. Rating similarity — 10 points
        cand_avg = candidate.avg_rating or 3.0
        if abs(cand_avg - source_avg) <= 0.5:
            score += 10

        if score > 0:
            scored_results.append({
                "id": candidate.id,
                "title": candidate.title,
                "year": candidate.release_year,
                "genre": candidate.genre,
                "director": candidate.director,
                "average_rating": round(cand_avg, 1),
                "review_count": candidate.review_count,
                "match_score": min(score, 100),
                "reasons": reasons,
            })

    # ── 5. Return top 5 ──────────────────────────────────────────────────────
    scored_results.sort(key=lambda x: x["match_score"], reverse=True)

    return Response({
        "movie": {
            "id": movie.id,
            "title": movie.title,
            "year": movie.release_year,
            "genre": movie.genre,
            "director": movie.director,
        },
        "recommendations": scored_results[:5],
        "algorithm": "Weighted Heuristic (Content-Based Filtering)",
    })