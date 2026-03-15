from rest_framework import serializers
from .models import Movie, Review

class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = ['title', 'genre', 'release_year', 'director', 'overview', 'created_at']

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['movie', 'reviewer_name', 'rating', 'comment', 'created_at']