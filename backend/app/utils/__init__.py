"""Small, dependency-free helper functions shared across layers.

Kept intentionally minimal: anything that needs a database session or FastAPI
request context belongs in services/dependencies, not here.
"""
