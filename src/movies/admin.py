from django.contrib import admin
from .models import Movie

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ("title", "genre", "release_year", "director", "created_at")
    search_fields = ("title","genre", "director")
    list_filter = ("genre", "release_year")