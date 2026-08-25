"""FastAPI application and routes for 文美全球AI获客系统."""

from api import routes as _routes
from api.commercial_ops_routes import register_commercial_ops_routes as _register_commercial_ops_routes
from api.crm_routes import register_crm_routes as _register_crm_routes
from api.knowledge_routes import register_knowledge_routes as _register_knowledge_routes
from api.sales_ops_routes import register_sales_ops_routes as _register_sales_ops_routes
from api.wenmei_routes import register_wenmei_routes as _register_wenmei_routes

_register_crm_routes(_routes.router)
_register_knowledge_routes(_routes.router)
_register_sales_ops_routes(_routes.router)
_register_commercial_ops_routes(_routes.router)
_register_wenmei_routes(_routes.router)
