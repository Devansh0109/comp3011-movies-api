from rest_framework import serializers
from django.db.models import Avg
from .models import Movie, Review
from drf_spectacular.utils import extend_schema_field

class MovieSerializer(serializers.ModelSerializer):
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()

    class Meta:
        model = Movie
        fields = ['id', 'title', 'genre', 'release_year', 'director', 'overview','average_rating', 'review_count', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    @extend_schema_field(serializers.FloatField(allow_null=True))
    def get_average_rating(self, obj):
        avg = obj.reviews.aggregate(avg_rating=Avg('rating'))['avg_rating']
        if avg is not None:
            return round(avg, 2)
        else:
            return None
    
    @extend_schema_field(serializers.IntegerField())
    def get_review_count(self, obj):
        return obj.reviews.count()

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'movie', 'reviewer_name', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'created_at']