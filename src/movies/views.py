from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from django.db.models import Avg, Q, Count

from .models import Movie, Review
from .serializers import MovieSerializer, ReviewSerializer

@api_view(["GET", "POST"])
def movie_list(request):
    if request.method == "GET":
        movies = Movie.objects.all()
        serializer = MovieSerializer(movies, many=True)
        return Response(serializer.data)
    else:
        serializer = MovieSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["GET", "PUT", "DELETE"])
def movie_detail(request, pk):
    try:
        movie = Movie.objects.get(pk=pk)
    except Movie.DoesNotExist:
        return Response({"error: movie not found"}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == "GET":
        serializer = MovieSerializer(movie)
        return Response(serializer.data)
    
    elif request.method == "PUT":
        serializer = MovieSerializer(movie, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    elif request.method == "DELETE":
        movie.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
@api_view(["GET", "POST"])
def movie_review(request, pk):
    try:
        movie = Movie.objects.get(pk=pk)
    except Movie.DoesNotExist:
        return Response({"error: movie not found"}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == "GET":
        reviews = movie.reviews.all()
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
        
@api_view(["GET"])
def movie_search(request):
    query = request.GET.get("q")
    genre = request.GET.get("genre")
    year = request.GET.get("year")
    min_rating = request.GET.get("min_rating")

    movies = Movie.objects.all().annotate(avg_rating=Avg("reviews__rating"))
    movies = list(movies)

    if query:
        movies = [
            movie for movie in movies
            if query.lower() in movie.title.lower()
            or query.lower() in movie.director.lower()
            or query.lower() in movie.overview.lower()
        ]

    if genre:
        movies = [
            movie for movie in movies
            if genre.lower() in movie.genre.lower()
        ]

    if year:
        movies = [
            movie for movie in movies
            if str(movie.release_year) == year
        ]

    if min_rating:
        try:
            min_rating = float(min_rating)
            movies = [
                movie for movie in movies
                if movie.avg_rating is not None and movie.avg_rating >= min_rating
            ]
        except ValueError:
            return Response({"error": "min_rating must be a number"}, status=status.HTTP_400_BAD_REQUEST)
        
    serializer = MovieSerializer(movies, many=True)
    return Response(serializer.data)

@api_view(["GET"])
def top_rated_movies(request):
    movies = Movie.objects.annotate(avg_rating=Avg("reviews__rating"))
    movies = movies.filter(avg_rating__isnull=False)
    movies = movies.order_by("-avg_rating")

    serializer = MovieSerializer(movies, many=True)
    return Response(serializer.data)

@api_view(["GET"])
def most_reviewed_movies(request):
    movies = Movie.objects.annotate(review_total=Count("reviews"))
    movies = movies.filter(review_total__gt=0)
    movies = movies.order_by("-review_total", "title")

    serializer = MovieSerializer(movies, many=True)
    return Response(serializer.data)

@api_view(["GET"])
def genre_summary(request):
    summary = Movie.objects.values("genre").annotate(movie_count=Count("id"), average_rating=Avg("reviews__rating"))
    summary = summary.order_by("genre")

    return Response(summary)