"""FastAPI application and routes for 文美全球AI获客系统."""

# Register CRM endpoints onto the existing main API router early, so app.py does
# not need invasive changes and the original hunt/email architecture stays intact.
from api import routes as _routes
from api.crm_routes import register_crm_routes as _register_crm_routes

_register_crm_routes(_routes.router)
