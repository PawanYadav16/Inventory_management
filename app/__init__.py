import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from config import Config

# Initialize Flask extensions
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'
migrate = Migrate()
csrf = CSRFProtect()


def create_app(config_class=Config):
    """Application factory for creating and configuring the Flask app instance."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure instance directory exists for SQLite db file
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    # Bind extensions to app
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Ensure SQLite database schema contains currency column if database file exists
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if db_uri.startswith('sqlite:///'):
        db_path = db_uri.replace('sqlite:///', '')
        if os.path.exists(db_path):
            try:
                import sqlite3
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
                if cursor.fetchone():
                    cursor.execute("PRAGMA table_info(users)")
                    columns = [row[1] for row in cursor.fetchall()]
                    if 'currency' not in columns:
                        cursor.execute("ALTER TABLE users ADD COLUMN currency VARCHAR(10) NOT NULL DEFAULT 'INR'")
                        conn.commit()
                conn.close()
            except Exception:
                pass

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.inventory import inventory_bp
    from app.routes.analytics import analytics_bp
    from app.routes.profile import profile_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(profile_bp)

    # Register Jinja Template Filter for Currency Formatting
    @app.template_filter('currency')
    def format_currency_filter(amount, currency_code=None):
        from flask_login import current_user
        if not currency_code:
            if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
                currency_code = getattr(current_user, 'currency', 'INR')
            else:
                currency_code = 'INR'

        symbols = {'INR': '₹', 'USD': '$', 'EUR': '€', 'GBP': '£'}
        symbol = symbols.get(currency_code, '₹')
        try:
            val = float(amount or 0.0)
            return f"{symbol}{val:,.2f}"
        except (ValueError, TypeError):
            return f"{symbol}0.00"

    # Custom Error Handlers
    @app.after_request
    def set_no_cache_headers(response):
        from flask_login import current_user
        if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        return response

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    return app
