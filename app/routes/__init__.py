# Routes package initialization
from app.routes.auth import auth_bp
from app.routes.dashboard import dashboard_bp
from app.routes.inventory import inventory_bp
from app.routes.analytics import analytics_bp
from app.routes.profile import profile_bp

__all__ = ['auth_bp', 'dashboard_bp', 'inventory_bp', 'analytics_bp', 'profile_bp']
