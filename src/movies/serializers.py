from rest_framework import serializers
from django.db.models import Avg
from .models import Movie, Review

class MovieSerializer(serializers.ModelSerializer):
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    class Meta:
        model = Movie
        fields = ['title', 'genre', 'release_year', 'director', 'overview','average_rating', 'review_count', 'created_at']
    
    def get_average_rating(self, obj):
        avg = obj.reviews.aggregate(avg_rating=Avg('rating'))['avg_rating']
        if avg is None:
            return None
        else:
            return round(avg, 2)
    
    def get_review_count(self, obj):
        return obj.reviews.count()

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['movie', 'reviewer_name', 'rating', 'comment', 'created_at']