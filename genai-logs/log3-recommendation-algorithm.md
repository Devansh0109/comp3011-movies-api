## Exchange

**Me:**
I want to add a recommendation endpoint to my movies API. My initial idea was to call the Claude API or Gemini API — pass the movie details and get recommendations back. Is this a good approach?

**Claude:**
It is a valid approach and would produce high-quality natural language recommendations with nuanced reasoning. However, there are practical problems worth considering before committing to it.

The main issue is cost and availability. The Anthropic API requires credits — even with a free tier, each recommendation request makes a paid API call. If your university does not provide credits and you do not want to spend your own money, every demo during your oral exam becomes a potential cost. If the API is rate-limited or your credits run out during the presentation, the endpoint simply fails.

There is also a reliability dependency: your API's recommendation feature stops working if the external service has an outage or if your API key is revoked.

The alternative — a database-driven content-based filtering algorithm — has none of these drawbacks. It runs entirely within your Django application, requires no external dependencies, works offline, and is actually more impressive from a software engineering perspective because you designed and implemented the scoring logic yourself.

More importantly: for your oral examination, being able to explain exactly how your recommendation algorithm works — "genre overlap scores up to 40 points proportionally, director match adds 30, era proximity adds 20 tiered by 5-year windows, rating similarity adds 10" — is a much stronger answer than "it calls Claude and Claude decides." The examiner can ask you to justify every design choice in the in-house algorithm.

My recommendation: build the content-based filter. Use the TMDB vote data you already have (vote_average, vote_count) to make the scoring statistically meaningful.

**Me:**
Okay I like that idea. How should I design the scoring? What factors make two movies similar?

**Claude:**
Content-based filtering for films traditionally uses four factors. Here is how to weight them for your dataset:

**Genre overlap (up to 40 points):** This is the strongest similarity signal. Two Action/Adventure films are more similar than an Action film and a Drama. Score proportionally — if the source film has two genres and the candidate shares one, award 20 points (50% overlap). If it shares both, award 40 points. This handles slash-separated genre strings cleanly.

**Director match (30 points):** Same director is a strong signal — Christopher Nolan films have a distinctive style regardless of genre. Use exact string matching after lowercasing both values. Exclude "Unknown" from matching to avoid false positives across the ~400 films where the credits CSV had no match.

**Era proximity (20 or 10 points):** Films from the same decade share cultural context, visual style, and production conventions. A tiered approach works better than a continuous decay here: within 5 years = 20 points (near-contemporaries), within 15 years = 10 points (same broad era), beyond 15 years = 0. This is easier to explain than a decay formula.

**Rating similarity (10 points):** Films with similar average ratings appeal to the same audience tolerance for quality. Award 10 points if the average ratings are within 0.5 stars of each other. This is a lightweight tiebreaker rather than a primary factor.

**Performance consideration:** With 4,800 films, scoring every candidate for every request would be slow. Pre-filter using Django Q objects to only load films sharing at least one genre OR the same director. This reduces the candidate pool dramatically and avoids a full table scan.

**Me:**
Should I use collaborative filtering instead? I've seen that recommended for recommendation systems.

**Claude:**
Collaborative filtering would be more powerful with real user data, but it is the wrong choice here for a specific reason: it requires persistent user history. The model works by finding users with similar taste and recommending what they liked — "users who rated Inception highly also rated Interstellar highly."

Your API has no user model with viewing history. The Review model has reviewer_name as a plain string, not a foreign key to an authenticated user, so you cannot build a user-item matrix. Implementing collaborative filtering properly would require redesigning the Review model, collecting real viewing history, and building a matrix factorisation or nearest-neighbour model — far beyond the coursework scope.

Content-based filtering is the academically correct choice for cold-start data (a dataset with no user history). It is used in exactly this situation — new recommendation systems before they have enough user interaction data to do collaborative filtering. Mentioning this in your report actually strengthens the write-up: you evaluated both approaches and chose content-based for well-reasoned technical reasons.

---

**Outcome:** Implemented content-based filtering with four weighted factors. The algorithm is fully offline, requires no external API, and produces explainable results with a reasons array. See src/movies/recommendation_view.py.
