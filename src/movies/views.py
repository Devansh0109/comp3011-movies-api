from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import Movie
from .serializers import MovieSerializer

@api_view(["GET", "POST"])
def movie_list(request):
    if request.method == "GET":
        movies = Movie.objects.all()
        serializer = MovieSerializer(movies, many=True)
        return Response(serializer.data)
    else:
        serializer = MovieSerializer(data = request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["GET"])
def movie_detail(request, pk):
    try:
        movie = Movie.objects.get(pk=pk)
    except Movie.DoesNotExist:
        return Response({"error: movie not found"}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = MovieSerializer(movie)
    return Response(serializer.data)