from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework import status
from rest_framework import serializers as rf_serializers

from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db.models import Avg, Q, Count

from .models import Movie, Review
from .serializers import MovieSerializer, ReviewSerializer

@extend_schema(
        request=inline_serializer("RegisterRequest", fields={
            "username": rf_serializers.CharField(),
            "password": rf_serializers.CharField(),
        }),
        responses={201: inline_serializer("TokenResponse", fields={
            "token": rf_serializers.CharField()
        })},
        tags=["auth"]
)

@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    username = request.data.get("username")
    password = request.data.get("password")

    if not username or not password:
        return Response({"error": "username and password are required"}, status=status.HTTP_400_BAD_REQUEST)
    
    if User.objects.filter(username=username).exists():
        return Response({"error": "username already taken"}, status=status.HTTP_400_BAD_REQUEST)
    
    user = User.objects.create_user(username=username, password=password)
    token, _ = Token.objects.get_or_create(user=user)
    return Response({"token": token.key}, status=status.HTTP_201_CREATED)

@extend_schema(
    request=inline_serializer("LoginRequest", fields={
        "username": rf_serializers.CharField(),
        "password": rf_serializers.CharField(),
    }),
    responses={200: inline_serializer("TokenResponse2", fields={
        "token": rf_serializers.CharField()
    })},
    tags=["auth"]
)

@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get("username")
    password = request.data.get("password")

    user = authenticate(username=username, password=password)
    if user is None:
        return Response({"error": "invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
    
    token, _ = Token.objects.get_or_create(user=user)    
    return Response({"token": token.key})

@extend_schema(request=MovieSerializer,responses={200:MovieSerializer(many=True), 201: MovieSerializer}, tags=["movies"])
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticatedOrReadOnly])
def movie_list(request):
    if request.method == "GET":
        movies = Movie.objects.all().order_by("-created_at")
        serializer = MovieSerializer(movies, many=True)
        return Response(serializer.data)
    else:
        serializer = MovieSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(responses={200: MovieSerializer},request=MovieSerializer, tags=["movies"])
@api_view(["GET", "PUT","PATCH", "DELETE"])
@permission_classes([IsAuthenticatedOrReadOnly])
def movie_detail(request, pk):
    try:
        movie = Movie.objects.get(pk=pk)
    except Movie.DoesNotExist:
        return Response({"error": "movie not found"}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == "GET":
        serializer = MovieSerializer(movie)
        return Response(serializer.data)
    
    elif request.method in ("PUT", "PATCH"):
        partial = request.method == "PATCH"
        serializer = MovieSerializer(movie, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    elif request.method == "DELETE":
        movie.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
@extend_schema(methods=["GET"],responses={200: ReviewSerializer(many=True)}, tags=["reviews"])
@extend_schema(methods=["POST"],request=ReviewSerializer,responses={201: ReviewSerializer(many=True)}, tags=["reviews"])
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticatedOrReadOnly])
def movie_review(request, pk):
    try:
        movie = Movie.objects.get(pk=pk)
    except Movie.DoesNotExist:
        return Response({"error": "movie not found"}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == "GET":
        reviews = movie.reviews.all().order_by("-created_at")
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)
    
    elif request.method == "POST":
        data = request.data.copy()
        data["movie"] = movie.id

        serializer = ReviewSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(responses={200: ReviewSerializer},request=ReviewSerializer, tags=["reviews"])     
@api_view(["GET", "PUT", "PATCH", "DELETE"])
@permission_classes([IsAuthenticatedOrReadOnly])
def review_detail(request, pk, review_pk):
    try:
        movie = Movie.objects.get(pk=pk)
    except Movie.DoesNotExist:
        return Response({"error": "movie not found"}, status=status.HTTP_404_NOT_FOUND)
    
    try:
        review = movie.reviews.get(pk=review_pk)
    except Review.DoesNotExist:
        return Response({"error": "review not found"}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == "GET":
        serializer = ReviewSerializer(review)
        return Response(serializer.data)
    
    if request.method in ("PUT", "PATCH"):
        partial = request.method == "PATCH"
        serializer = ReviewSerializer(review, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    if request.method == "DELETE":
        movie.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
        
@extend_schema(
    parameters=[
        OpenApiParameter(name="q", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY,
            description="Search by title, director, or overview", required=False),
        OpenApiParameter(name="genre", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY,
            description="Filter by genre (partial match)", required=False),
        OpenApiParameter(name="year", type=OpenApiTypes.INT, location=OpenApiParameter.QUERY,
            description="Filter by exact release year", required=False),
        OpenApiParameter(name="min_rating", type=OpenApiTypes.FLOAT, location=OpenApiParameter.QUERY,
            description="Minimum average rating (1.0 - 5.0)", required=False),
    ],
    responses=MovieSerializer(many=True),
    tags=["analytics"]
)
@api_view(["GET"])
def movie_search(request):
    query = request.GET.get("q")
    genre = request.GET.get("genre")
    year = request.GET.get("year")
    min_rating = request.GET.get("min_rating")

    movies = Movie.objects.all().annotate(avg_rating=Avg("reviews__rating"))

    if query:
        movies = movies.filter(Q(title__icontains=query) | Q(director__icontains=query) | Q(overview__icontains=query))

    if genre:
        movies = movies.filter(genre__icontains=genre)

    if year:
        try:
            movies = movies.filter(release_year=year)
        except ValueError:
            return Response({"error": "year must be an integer"}, status=status.HTTP_400_BAD_REQUEST)

    if min_rating:
        try:
            movies = movies.filter(avg_rating__gte=float(min_rating))
        except ValueError:
            return Response({"error": "min_rating must be a number"}, status=status.HTTP_400_BAD_REQUEST)
        
    serializer = MovieSerializer(movies, many=True)
    return Response(serializer.data)

@extend_schema(
    parameters=[
        OpenApiParameter(name="limit", type=OpenApiTypes.INT, location=OpenApiParameter.QUERY,
            description="Number of results to return (default: 10)", required=False),
    ],
    responses=MovieSerializer(many=True),
    tags=["analytics"]
)
@api_view(["GET"])
def top_rated_movies(request):
    try:
        limit = int(request.GET.get("limit", 10))
    except ValueError:
        return Response({"error": "limit must be an integer"}, status=status.HTTP_400_BAD_REQUEST)
    movies = Movie.objects.annotate(avg_rating=Avg("reviews__rating"))
    movies = movies.filter(avg_rating__isnull=False)
    movies = movies.order_by("-avg_rating")[:limit]

    serializer = MovieSerializer(movies, many=True)
    return Response(serializer.data)

@extend_schema(
    parameters=[
        OpenApiParameter(name="limit", type=OpenApiTypes.INT, location=OpenApiParameter.QUERY,
            description="Number of results to return (default: 10)", required=False),
    ],
    responses=MovieSerializer(many=True),
    tags=["analytics"]
)
@api_view(["GET"])
def most_reviewed_movies(request):
    try:
        limit = int(request.GET.get("limit", 10))
    except ValueError:
        return Response({"error": "limit must be an integer"}, status=status.HTTP_400_BAD_REQUEST)
    movies = Movie.objects.annotate(review_total=Count("reviews"))
    movies = movies.filter(review_total__gt=0)
    movies = movies.order_by("-review_total", "title")[:limit]

    serializer = MovieSerializer(movies, many=True)
    return Response(serializer.data)

@extend_schema(
        responses=inline_serializer("GenreSummary", fields={
            "genre": rf_serializers.CharField(),
            "movie_count": rf_serializers.IntegerField(),
            "average_rating": rf_serializers.FloatField(),
        }, many=True),
        tags=["analytics"]
)
@api_view(["GET"])
def genre_summary(request):
    summary = Movie.objects.values("genre").annotate(movie_count=Count("id"), average_rating=Avg("reviews__rating"))
    summary = summary.order_by("genre")

    return Response(list(summary))

@extend_schema(exclude=True)
@api_view(["GET"])
@permission_classes([AllowAny])
def api_root(request):
    """API root — lists all available endpoint groups."""
    return Response({
        "movies": request.build_absolute_uri("/api/movies/"),
        "search": request.build_absolute_uri("/api/movies/search/"),
        "top_rated": request.build_absolute_uri("/api/movies/top-rated/"),
        "most_reviewed": request.build_absolute_uri("/api/movies/most-reviewed/"),
        "genre_summary": request.build_absolute_uri("/api/movies/genre-summary/"),
        "documentation": request.build_absolute_uri("/api/docs/"),
        "auth": {
            "register": request.build_absolute_uri("/api/auth/register/"),
            "login": request.build_absolute_uri("/api/auth/login/"),
        }
    })