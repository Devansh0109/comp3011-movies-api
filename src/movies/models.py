from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Movie(models.Model):
    title = models.CharField(max_length=200)
    genre = models.CharField(max_length=100)
    release_year = models.PositiveBigIntegerField()
    director = models.CharField(max_length=150)
    overview = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title}({self.release_year})"
    
class Review(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="reviews")
    reviewer_name = models.CharField(max_length=100)
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review for {self.movie.title} by {self.reviewer_name}"