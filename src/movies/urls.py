from django.urls import path
from .views import (
    register,
    login_view,
    movie_list, 
    movie_detail, 
    movie_review,
    review_detail, 
    movie_search,
    top_rated_movies,
    most_reviewed_movies,
    genre_summary,
    )

urlpatterns = [
    path("auth/register/", register, name="register"),
    path("auth/login/", login_view, name="login"),    
    path("movies/", movie_list, name="movie-list"),
    path("movies/<int:pk>/", movie_detail, name="movie-detail"),
    path("movies/<int:pk>/reviews/", movie_review, name="movie-reviews"),
    path("movies/<int:pk>/reviews/<int:review_pk>/", review_detail, name="review-detail"),
    path("movies/search/", movie_search, name="movie-search"),
    path("movies/top-rated/", top_rated_movies, name="top-rated-movies"),
    path("movies/most-reviewed/", most_reviewed_movies, name="most-reviewed-movies"),
    path("movies/genre-summary/", genre_summary, name="genre-summary"),
]