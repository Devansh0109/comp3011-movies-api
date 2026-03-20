## Exchange

**Me:**
I am building a RESTful API for a movie catalogue as part of my COMP3011 coursework. I need to choose between Django REST Framework, FastAPI, and Flask. Which should I use and why?

**Claude:**
All three are solid choices, but they serve different needs. Here is an honest comparison:

**FastAPI** is the most performant of the three and uses Python type hints for automatic validation and documentation generation. It is excellent for microservices where speed matters. However, it requires more manual wiring for authentication, serialisation, and permissions — concerns you would need to build from scratch or find third-party packages for.

**Flask** is the most minimal. It gives you routing and not much else. For a project that needs database models, authentication, and schema generation, you end up assembling a lot of pieces yourself. It is a reasonable choice for very simple APIs but adds overhead for your use case.

**Django REST Framework (DRF)** is the most batteries-included. Its serialiser layer handles input validation, nested relationship serialisation, and computed fields declaratively. The permission system integrates natively with token authentication. The ORM means you write no raw SQL. The trade-off is that Django's convention-heavy structure can feel like overhead if you only need a few endpoints, but for a data-driven project with auth, relationships, and documentation requirements, it is the strongest choice.

My recommendation: DRF. The serialiser layer alone will save you significant time — computed fields like average_rating can be defined in one method, validation is automatic, and the permission system handles auth guards without any additional packages.

**Me:**
What about GraphQL vs REST? The brief says I can use either but I need to justify the choice.

**Claude:**
GraphQL solves a specific problem: over-fetching and under-fetching when clients have varying data needs. If you had a mobile client that only needed title and genre and a web client that needed the full movie object with reviews, GraphQL would let each client request exactly what it needs.

For your use case — a coursework API demonstrating CRUD and analytics — REST is the stronger choice for two reasons. First, your data model is simple and predictable. Clients querying /api/movies/top-rated/ always want the same fields; there is no varied client consuming pattern that GraphQL's flexibility would benefit. Second, REST is significantly easier to document with tools like Swagger UI. GraphQL documentation requires a different toolchain (GraphiQL, GraphQL Playground) and the auto-generated schema is less immediately readable to an examiner.

The justification to write in your report: REST was chosen because the API's data access patterns are uniform and predictable, making GraphQL's query flexibility unnecessary overhead. REST's tooling ecosystem (drf-spectacular, Swagger UI) produces cleaner, more accessible documentation for a CRUD and analytics use case.

**Me:**
For authentication, what are the trade-offs between JWT, session auth, and DRF token auth?

**Claude:**
**Session authentication** is stateful — the server stores session data and the client stores a cookie. It works well for browser-based apps but is poorly suited to API clients (mobile apps, Postman, other services) that may not maintain a cookie jar. It also creates problems with horizontal scaling since sessions need to be shared across server instances.

**JWT (JSON Web Tokens)** is self-contained — the token encodes the user's identity and the server validates it cryptographically without a database lookup. This sounds ideal for APIs. The problem is token invalidation: if you want to log a user out or revoke access, you cannot — the token is valid until it expires. Solving this properly requires a token blacklist (database lookup on every request, which defeats the stateless benefit) or short expiry times with refresh tokens. The djangorestframework-simplejwt library adds register, login, refresh, and verify endpoints, plus blacklist management. That is meaningful complexity for a project where token revocation is not a requirement.

**DRF TokenAuthentication** is the simplest model: one token per user, stored in the database, submitted in the Authorization header. It is stateless from the client's perspective, works with any HTTP client, and requires zero additional packages. The trade-off is that tokens do not expire automatically — but for a coursework API where you control both the client and the server, this is not a meaningful limitation.

My recommendation: DRF TokenAuthentication. It satisfies the authentication requirement cleanly with no additional dependencies and is trivial to demonstrate in Swagger UI.

---

**Outcome:** Chose Django REST Framework with Token Authentication and REST architecture. These decisions are justified in the technical report Section 2.
