from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token
from rest_framework import status
from .models import Movie, Review


# Helper mixin

class AuthMixin:
    """Creates a test user and sets the auth header on the client."""

    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.token = Token.objects.create(user=self.user)
        self.auth_header = {"HTTP_AUTHORIZATION": f"Token {self.token.key}"}

    def _movie(self, **kwargs):
        defaults = {
            "title": "Inception",
            "genre": "Sci-Fi",
            "release_year": 2010,
            "director": "Christopher Nolan",
            "overview": "A thief who steals secrets through dreams.",
        }
        defaults.update(kwargs)
        return Movie.objects.create(**defaults)

    def _review(self, movie, **kwargs):
        defaults = {
            "reviewer_name": "Alice",
            "rating": 4,
            "comment": "Great film.",
        }
        defaults.update(kwargs)
        return Review.objects.create(movie=movie, **defaults)

# Auth endpoint tests

class RegisterTests(APITestCase):
    def test_register_success(self):
        response = self.client.post("/api/auth/register/", {
            "username": "newuser", "password": "securepass"
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("token", response.data)

    def test_register_duplicate_username(self):
        User.objects.create_user(username="existing", password="pass")
        response = self.client.post("/api/auth/register/", {
            "username": "existing", "password": "other"
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_fields(self):
        response = self.client.post("/api/auth/register/", {"username": "x"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="loginuser", password="loginpass")

    def test_login_success(self):
        response = self.client.post("/api/auth/login/", {
            "username": "loginuser", "password": "loginpass"
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)

    def test_login_wrong_password(self):
        response = self.client.post("/api/auth/login/", {
            "username": "loginuser", "password": "wrong"
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# Movie CRUD tests

class MovieListTests(AuthMixin, APITestCase):
    def test_list_movies_public(self):
        self._movie()
        response = self.client.get("/api/movies/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_list_empty(self):
        response = self.client.get("/api/movies/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_create_movie_authenticated(self):
        payload = {
            "title": "The Matrix",
            "genre": "Sci-Fi",
            "release_year": 1999,
            "director": "The Wachowskis",
        }
        response = self.client.post("/api/movies/", payload, **self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "The Matrix")
        self.assertIn("id", response.data)

    def test_create_movie_unauthenticated(self):
        payload = {
            "title": "Dune",
            "genre": "Sci-Fi",
            "release_year": 2021,
            "director": "Denis Villeneuve",
        }
        response = self.client.post("/api/movies/", payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_movie_missing_required_field(self):
        payload = {"title": "Nameless"}  # missing genre, release_year, director
        response = self.client.post("/api/movies/", payload, **self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class MovieDetailTests(AuthMixin, APITestCase):
    def test_retrieve_movie(self):
        movie = self._movie()
        response = self.client.get(f"/api/movies/{movie.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], movie.title)

    def test_retrieve_nonexistent_movie(self):
        response = self.client.get("/api/movies/9999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_full_update_movie(self):
        movie = self._movie()
        payload = {
            "title": "Inception Updated",
            "genre": "Thriller",
            "release_year": 2010,
            "director": "Christopher Nolan",
        }
        response = self.client.put(f"/api/movies/{movie.id}/", payload, **self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Inception Updated")
        self.assertEqual(response.data["genre"], "Thriller")

    def test_partial_update_movie(self):
        movie = self._movie()
        response = self.client.patch(
            f"/api/movies/{movie.id}/", {"genre": "Drama"}, **self.auth_header
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["genre"], "Drama")
        self.assertEqual(response.data["title"], movie.title)  # unchanged

    def test_delete_movie_authenticated(self):
        movie = self._movie()
        response = self.client.delete(f"/api/movies/{movie.id}/", **self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Movie.objects.filter(pk=movie.id).exists())

    def test_delete_movie_unauthenticated(self):
        movie = self._movie()
        response = self.client.delete(f"/api/movies/{movie.id}/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(Movie.objects.filter(pk=movie.id).exists())

# Review CRUD tests

class ReviewListTests(AuthMixin, APITestCase):
    def test_list_reviews_public(self):
        movie = self._movie()
        self._review(movie)
        response = self.client.get(f"/api/movies/{movie.id}/reviews/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_review_authenticated(self):
        movie = self._movie()
        payload = {"reviewer_name": "Bob", "rating": 5, "comment": "Masterpiece"}
        response = self.client.post(
            f"/api/movies/{movie.id}/reviews/", payload, **self.auth_header
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["rating"], 5)

    def test_create_review_invalid_rating(self):
        movie = self._movie()
        payload = {"reviewer_name": "Bob", "rating": 10}  # max is 5
        response = self.client.post(
            f"/api/movies/{movie.id}/reviews/", payload, **self.auth_header
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_review_nonexistent_movie(self):
        payload = {"reviewer_name": "Bob", "rating": 3}
        response = self.client.post("/api/movies/9999/reviews/", payload, **self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ReviewDetailTests(AuthMixin, APITestCase):
    def test_retrieve_review(self):
        movie = self._movie()
        review = self._review(movie)
        response = self.client.get(f"/api/movies/{movie.id}/reviews/{review.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["reviewer_name"], "Alice")

    def test_partial_update_review(self):
        movie = self._movie()
        review = self._review(movie)
        response = self.client.patch(
            f"/api/movies/{movie.id}/reviews/{review.id}/",
            {"rating": 5},
            **self.auth_header,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["rating"], 5)

    def test_delete_review(self):
        movie = self._movie()
        review = self._review(movie)
        response = self.client.delete(
            f"/api/movies/{movie.id}/reviews/{review.id}/", **self.auth_header
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Review.objects.filter(pk=review.id).exists())

    def test_review_not_found_on_wrong_movie(self):
        movie1 = self._movie()
        movie2 = self._movie(title="Other Film")
        review = self._review(movie1)
        response = self.client.get(f"/api/movies/{movie2.id}/reviews/{review.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# Analytics endpoint tests

class AnalyticsTests(AuthMixin, APITestCase):
    def setUp(self):
        super().setUp()
        self.scifi = self._movie(title="Interstellar", genre="Sci-Fi", release_year=2014)
        self.drama = self._movie(title="The Shawshank Redemption", genre="Drama", release_year=1994)
        self._review(self.scifi, rating=5)
        self._review(self.scifi, rating=4)
        self._review(self.drama, rating=5)

    def test_top_rated(self):
        response = self.client.get("/api/movies/top-rated/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)

    def test_top_rated_limit(self):
        response = self.client.get("/api/movies/top-rated/?limit=1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_most_reviewed(self):
        response = self.client.get("/api/movies/most-reviewed/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Interstellar has 2 reviews so should come first
        self.assertEqual(response.data[0]["title"], "Interstellar")

    def test_genre_summary(self):
        response = self.client.get("/api/movies/genre-summary/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        genres = [item["genre"] for item in response.data]
        self.assertIn("Sci-Fi", genres)
        self.assertIn("Drama", genres)

    def test_search_by_title(self):
        response = self.client.get("/api/movies/search/?q=Interstellar")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Interstellar")

    def test_search_by_genre(self):
        response = self.client.get("/api/movies/search/?genre=Drama")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_search_by_year(self):
        response = self.client.get("/api/movies/search/?year=2014")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Interstellar")

    def test_search_invalid_year(self):
        response = self.client.get("/api/movies/search/?year=notanumber")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_search_by_min_rating(self):
        response = self.client.get("/api/movies/search/?min_rating=4.5")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Interstellar avg=4.5, Shawshank avg=5.0 — both should return
        self.assertEqual(len(response.data), 2)

    def test_search_invalid_min_rating(self):
        response = self.client.get("/api/movies/search/?min_rating=abc")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

# Serializer / response structure tests

class SerializerStructureTests(AuthMixin, APITestCase):
    def test_movie_response_includes_id_and_computed_fields(self):
        movie = self._movie()
        self._review(movie, rating=4)
        response = self.client.get(f"/api/movies/{movie.id}/")
        self.assertIn("id", response.data)
        self.assertIn("average_rating", response.data)
        self.assertIn("review_count", response.data)
        self.assertEqual(response.data["average_rating"], 4.0)
        self.assertEqual(response.data["review_count"], 1)

    def test_movie_with_no_reviews_has_null_average(self):
        movie = self._movie()
        response = self.client.get(f"/api/movies/{movie.id}/")
        self.assertIsNone(response.data["average_rating"])
        self.assertEqual(response.data["review_count"], 0)

# recommender

class RecommendationTests(AuthMixin, APITestCase):
    def setUp(self):
        super().setUp()
        # Create source movie
        self.inception = self._movie(
            title="Inception",
            genre="Sci-Fi/Thriller",
            release_year=2010,
            director="Christopher Nolan"
        )
        # Same genre, same director — should score highest
        self.dark_knight = self._movie(
            title="The Dark Knight",
            genre="Action/Thriller",
            release_year=2008,
            director="Christopher Nolan"
        )
        # Same genre, different director, similar era
        self.interstellar = self._movie(
            title="Interstellar",
            genre="Sci-Fi/Drama",
            release_year=2014,
            director="Christopher Nolan"
        )
        # Completely different — should not appear
        self.comedy = self._movie(
            title="Some Comedy",
            genre="Comedy/Romance",
            release_year=1970,
            director="Unknown"
        )

    def test_recommendations_returns_200(self):
        response = self.client.get(f"/api/movies/{self.inception.id}/recommendations/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_recommendations_response_structure(self):
        response = self.client.get(f"/api/movies/{self.inception.id}/recommendations/")
        self.assertIn("movie", response.data)
        self.assertIn("recommendations", response.data)
        self.assertIn("algorithm", response.data)

    def test_recommendations_source_movie_correct(self):
        response = self.client.get(f"/api/movies/{self.inception.id}/recommendations/")
        self.assertEqual(response.data["movie"]["title"], "Inception")

    def test_recommendations_excludes_source_movie(self):
        response = self.client.get(f"/api/movies/{self.inception.id}/recommendations/")
        titles = [r["title"] for r in response.data["recommendations"]]
        self.assertNotIn("Inception", titles)

    def test_recommendations_returns_at_most_5(self):
        response = self.client.get(f"/api/movies/{self.inception.id}/recommendations/")
        self.assertLessEqual(len(response.data["recommendations"]), 5)

    def test_recommendations_result_has_required_fields(self):
        response = self.client.get(f"/api/movies/{self.inception.id}/recommendations/")
        if response.data["recommendations"]:
            rec = response.data["recommendations"][0]
            self.assertIn("title", rec)
            self.assertIn("match_score", rec)
            self.assertIn("reasons", rec)
            self.assertIn("review_count", rec)

    def test_same_director_scores_higher(self):
        response = self.client.get(f"/api/movies/{self.inception.id}/recommendations/")
        titles = [r["title"] for r in response.data["recommendations"]]
        # Dark Knight and Interstellar share director — should appear
        self.assertIn("The Dark Knight", titles)
        self.assertIn("Interstellar", titles)

    def test_unrelated_movie_excluded(self):
        response = self.client.get(f"/api/movies/{self.inception.id}/recommendations/")
        titles = [r["title"] for r in response.data["recommendations"]]
        self.assertNotIn("Some Comedy", titles)

    def test_recommendations_nonexistent_movie(self):
        response = self.client.get("/api/movies/9999/recommendations/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_recommendations_public_no_auth_required(self):
        # Should work without any auth token
        response = self.client.get(f"/api/movies/{self.inception.id}/recommendations/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)