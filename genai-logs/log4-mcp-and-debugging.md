## Exchange — MCP Server

**Me:**
The coursework brief mentions MCP (Model Context Protocol) as an advanced feature for the 70-79 band. What is it and how would I implement it for my movies API?

**Claude:**
Model Context Protocol (MCP) is an open standard published by Anthropic that defines a standardised interface for AI assistants to call external tools. Think of it as a plugin system for AI — instead of an AI assistant only being able to answer questions from its training data, MCP lets it call external services, query databases, run code, and take actions.

For your movies API, implementing an MCP server means wrapping your existing endpoints as callable tools. When you ask Claude Desktop "what are the top 5 rated movies?", instead of Claude guessing from its training data, it calls your top_rated_movies tool, which makes an HTTP request to your Django API, and returns real data from your database.

The FastMCP library makes this straightforward. Each tool is a Python function decorated with @mcp.tool(). The function's docstring becomes the tool description that the AI uses to decide when to call it. The function body makes the HTTP request to your API.

The server reads its base URL and auth token from environment variables — this keeps credentials out of the source code and lets different users configure it for their own deployments.

Claude Desktop is configured via a JSON file at ~/Library/Application Support/Claude/claude_desktop_config.json. You specify the Python executable, the path to your mcp_server.py, and the environment variables. After restarting Claude Desktop, a hammer icon appears confirming the tools are available.

**Me:**
Does this require an API key or any paid service?

**Claude:**
No. The MCP server just makes HTTP requests to your own Django API running locally. Claude Desktop uses its own AI model (which you already have access to via your existing Claude account) to decide which tools to call — you are not making any additional API calls. The only running cost is your existing Claude Desktop subscription or free tier, which you are already using.

---

## Exchange — Bugs Fixed with AI Assistance

**Me:**
I am getting this error when I hit the auth endpoints:
django.db.utils.OperationalError: no such table: authtoken_token

**Claude:**
This is a missing migration. You added rest_framework.authtoken to INSTALLED_APPS, but Django does not automatically create the database table — you need to run python manage.py migrate to apply the authtoken migrations. This creates the authtoken_token table.

The symptom is confusing because your other tables already exist, so it does not look like a migration issue at first glance. Run migrate and the error will resolve immediately.

**Me:**
My recommendation endpoint is returning results but none of them have genre in the reasons — only era matches. Something is wrong with the genre matching.

**Claude:**
This is almost certainly a delimiter mismatch. Check how your import_movies command stores genres — it is likely storing them as slash-separated strings like "Action/Adventure". Now check your recommendation_view.py and find the line where you split the genre string. If it reads genre.split(",") instead of genre.split("/"), the split produces a single-element list ["action/adventure"] rather than two separate genres ["action", "adventure"]. The set intersection then finds no matches.

Change both split calls — on the source movie and on each candidate — from split(",") to split("/"). Genre matching will immediately start working.

**Me:**
When I open Swagger UI I get lots of warnings like "unable to guess serializer" and endpoints show no schema. What is wrong?

**Claude:**
The @extend_schema decorator must be the outermost decorator on your view function — it needs to sit above @api_view, not below it. When the order is reversed, drf-spectacular's introspection cannot see the schema annotation because @api_view wraps the function first.

Change every view from:
```python
@api_view(["GET"])
@extend_schema(responses=MovieSerializer(many=True), tags=["movies"])
def movie_list(request):
```

To:
```python
@extend_schema(responses=MovieSerializer(many=True), tags=["movies"])
@api_view(["GET"])
def movie_list(request):
```

The Swagger UI will still load without this fix — drf-spectacular falls back gracefully — but affected endpoints show no request or response schema, which makes the documentation look incomplete.

---

**Outcome:** MCP server implemented in mcp_server.py. All three bugs resolved. These debugging experiences are documented in Section 6 of the technical report.
