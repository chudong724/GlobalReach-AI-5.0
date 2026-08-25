"""FastAPI application and routes for 文美全球AI获客系统."""

# Register Wenmei extensions onto the existing main API router early, keeping
# the upstream hunt/email architecture intact.
from api import routes as _routes
from api.crm_routes import register_crm_routes as _register_crm_routes
from api.wenmei_routes import register_wenmei_routes as _register_wenmei_routes

_register_crm_routes(_routes.router)
_register_wenmei_routes(_routes.router)
