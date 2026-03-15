from django.contrib import admin
from .models import Movie, Review

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ("title", "genre", "release_year", "director", "created_at")
    search_fields = ("title","genre", "director")
    list_filter = ("genre", "release_year")

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("movie", "reviewer_name", "rating", "created_at")
    search_fields = ("movie__title", "reviewer_name")
    list_filter = ("rating", "created_at")