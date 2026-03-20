## Exchange — Test Strategy

**Me:**
I need to write tests for my movies API. I have the basic CRUD tests covered — create, read, update, delete. What else should I test that I might be missing?

**Claude:**
The obvious CRUD tests are a good start, but several non-obvious edge cases are worth adding — these are the ones that catch real bugs and demonstrate thorough testing to an examiner.

**Authentication guard tests:** For every write endpoint (POST, PUT, PATCH, DELETE), write a test that sends the request without an Authorization header and asserts a 401 Unauthorized response. This is easy to miss but critical — it proves your auth protection is actually working, not just present.

**Cross-movie review 404:** Create a review on Movie A, then request that review under Movie B's URL (/api/movies/B/reviews/review_id/). It should return 404, not the review. This tests that reviews are properly scoped to their parent movie, which is a common REST design error.

**Serialiser structure tests:** Write a test that calls GET /api/movies/<id>/ and explicitly asserts that "id" is in the response data. This sounds trivial but catches a real bug — the id field was accidentally omitted from the MovieSerializer fields list in an early version, which would make it impossible for clients to construct update or delete URLs. Also assert that average_rating is None when a movie has no reviews, and a correct float when it does.

**Validation boundary tests:** Test that a review with rating=6 returns 400 Bad Request. The validator is defined on the model but you want to confirm it fires through the full serialiser layer.

**404 on nonexistent resources:** Test GET /api/movies/9999/ returns 404, not 500. This catches cases where you forgot to handle the DoesNotExist exception.

**Me:**
Should I test the recommendation endpoint too? What are the key cases?

**Claude:**
Yes — the recommendation endpoint has several specific cases worth testing beyond a basic 200 response.

The most important: assert that the source movie itself does not appear in the recommendations. This is easy to miss in the implementation and immediately obvious to an examiner who tries the endpoint.

Test that the response never returns more than 5 results regardless of how many candidates exist.

Test that an unrelated movie — completely different genre, different era, unknown director — does not appear in recommendations. This validates that the scoring algorithm is actually filtering, not just returning random films.

Test that a movie sharing the director does appear in recommendations. This is a positive assertion on the scoring logic itself.

Test a 404 on a nonexistent movie ID.

Test that the endpoint is public (no auth required) — call it without a token and assert 200, not 401.

---

## Exchange — Synthetic Reviews

**Me:**
I have 4,800 movies imported but no reviews. The TMDB dataset does not have individual review text — just vote_average and vote_count aggregate numbers. How should I generate realistic review data?

**Claude:**
The TMDB vote data gives you everything you need to generate statistically realistic synthetic reviews. Here is the approach:

**Rating calibration:** Convert vote_average (0–10 scale) to a 1–5 scale by dividing by 2. A film with vote_average of 7.4 becomes a target rating of 3.7. Then for each synthetic review, sample a rating from a normal distribution centred on that target with a standard deviation of 0.7. This produces a realistic spread of opinions — most reviewers rate near the average, but some rate higher or lower. Round to the nearest integer and clamp to 1–5.

**Review count calibration:** vote_count tells you how popular the film is. Use a logarithmic scale: log base 10 of the vote_count, scaled to your maximum reviews per film. Avatar with 11,800 votes gets the maximum (say 6 reviews). An obscure film with 80 votes gets 1 or 2. This means your analytics endpoints will return blockbusters at the top of most-reviewed, which is exactly what you would expect from a real dataset.

**Comment realism:** Create a pool of comment strings split by star rating — 5-star comments use language like "a cinematic masterpiece", 2-star comments say "the execution falls flat". Pick randomly from the appropriate pool based on the generated rating. This makes the reviews readable rather than obviously random.

**Me:**
Is it academically acceptable to use synthetic data for a coursework project?

**Claude:**
Yes, and it is actually the expected approach here. The brief specifically says to use AI to help generate import scripts and populate the database. Real review text from sites like Letterboxd or IMDb is not available in free public datasets — those companies do not publish individual review data. Generating synthetic data calibrated to real statistical properties (TMDB vote data) is standard practice in data science and API development when real data is unavailable or restricted.

The key is to declare it clearly in your technical report — which the report already does in Section 3.1. Describing the calibration methodology (normal distribution, log-scaled counts) demonstrates genuine statistical thinking rather than just making up random numbers.

---

**Outcome:** Test suite expanded to 47 tests across 8 classes. Seed_reviews management command generates 14,322 synthetic reviews calibrated to TMDB vote_average and vote_count. See src/movies/tests.py and src/movies/management/commands/seed_reviews.py.
