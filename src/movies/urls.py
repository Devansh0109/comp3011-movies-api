from django.urls import path
from .views import movie_list, movie_detail, movie_review, movie_search

urlpatterns = [
    path("movies/", movie_list, name="movie-list"),
    path("movies/<int:pk>/", movie_detail, name="movie-detail"),
    path("movies/<int:pk>/reviews/", movie_review, name="movie-reviews"),
    path("movies/search/", movie_search, name="movie-search"),
]