import os
import logging
from datetime import datetime, date as py_date, time as py_time
from flask import Flask, render_template, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user as flask_login_current_user
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
from itsdangerous import URLSafeTimedSerializer

# Import only self-contained utility functions needed for filter registration at module level
from .utils import format_date_filter, format_filesize  # These should not import 'app' themselves

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    print(f"Warning: .env file not found at {dotenv_path}.")

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()
serializer = None

# --- Constants ---
# ... (Your constants remain here) ...
MONTH_NAMES = [None, "January", "February", "March", "April", "May", "June",
               "July", "August", "September", "October", "November", "December"]
QUARTER_NAMES = [None, "Q1 (Jan-Mar)", "Q2 (Apr-Jun)",
                 "Q3 (Jul-Sep)", "Q4 (Oct-Dec)"]
SESSION_DIRECTIONS = ["None", "Long", "Short"]
SESSION_STATUSES = ["None", "True", "False"]
SESSION_MODEL_STATUSES = ["None", "Valid", "Broken"]
P12_SCENARIO_CHOICES = ["None"] + [f"{i}{ab}" for i in range(1, 6) for ab in ["A", "B"]]
P12_OUTCOMES_MAP = {
    "1A": "Between 0600 – 0830 price starts in the upper half of the P12 box...",
    "1B": "Between 0600 – 0830 price starts in the lower half of the P12 box...",
    "2A": "Between 0600 – 0830 price starts in the lower half of the P12 box...",
    "2B": "Between 0600 – 0830 price starts in the upper half of the P12 box...",
    "3A": "Between 0600 – 0830 price starts in the upper half of the P12 box...",
    "3B": "Between 0600 – 0830 price starts in the lower half of the P12 box...",
    "4A": "Between 0600 – 0830 price starts in the upper half of the P12 box...",
    "4B": "Between 0600 – 0830 price starts in the lower half of the P12 box...",
    "5A": "Between 0600 – 0830 price is in a large range...",
    "5B": "Between 0600 – 0830 price is in a small range..."
}
P12_COMMON_TARGET_INFO = "Once the confirmation is in you will target 0.5% with stop loss at 0.35%."


def create_app(config_class=None):
    global serializer
    app = Flask(__name__, instance_relative_config=True)

    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError as e:
        print(f"Error creating instance folder {app.instance_path}: {e}")

    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev_fallback_secret_key'),
        WTF_CSRF_SECRET_KEY=os.environ.get('WTF_CSRF_SECRET_KEY', 'dev_fallback_csrf_key'),
        SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL',
                                               f"sqlite:///{os.path.join(app.instance_path, 'app.db')}"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_FOLDER=os.path.join(app.instance_path, 'uploads'),
        MAX_CONTENT_LENGTH=int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)),
        ALLOWED_EXTENSIONS=set(
            os.environ.get('ALLOWED_EXTENSIONS', 'pdf,png,jpg,jpeg,doc,docx,xls,xlsx,txt,csv').split(',')),
        ALLOWED_IMAGE_EXTENSIONS={'png', 'jpg', 'jpeg', 'gif'},
        ITEMS_PER_PAGE=int(os.environ.get('ITEMS_PER_PAGE', 10)),
        PER_PAGE_TRADES=int(os.environ.get('PER_PAGE_TRADES', 25)),
        PROFILE_PICS_FOLDER_REL=os.environ.get('PROFILE_PICS_FOLDER_REL', 'profile_pics'),
        PROFILE_PICS_SAVE_PATH=os.path.join(os.path.abspath(os.path.join(app.root_path, 'static')),
                                            os.environ.get('PROFILE_PICS_FOLDER_REL', 'profile_pics')),
        MAIL_SERVER=os.environ.get('MAIL_SERVER'),
        MAIL_PORT=int(os.environ.get('MAIL_PORT', 587)),
        MAIL_USE_TLS=os.environ.get('MAIL_USE_TLS', 'True').lower() in ['true', '1', 't'],
        MAIL_USE_SSL=os.environ.get('MAIL_USE_SSL', 'False').lower() in ['true', '1', 't'],
        MAIL_USERNAME=os.environ.get('MAIL_USERNAME'),
        MAIL_PASSWORD=os.environ.get('MAIL_PASSWORD'),
        MAIL_DEFAULT_SENDER=os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@example.com'),
        MAIL_DEBUG=(os.environ.get('FLASK_DEBUG', '0') == '1')
    )

    if config_class:
        app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)

    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

    login_manager.login_view = 'auth.login'
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "info"

    # Logging, Upload folder creation (as before)
    # ... (keep your existing logging and folder creation logic) ...
    log_level = logging.DEBUG if app.debug else logging.INFO
    if not app.logger.handlers:
        log_dir = os.path.join(app.instance_path, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, 'app.log')
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(log_level)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(log_level)
    app.logger.info('Application startup')

    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        try:
            os.makedirs(app.config['UPLOAD_FOLDER'])
        except OSError as e:
            app.logger.error(f"Could not create UPLOAD_FOLDER: {e}")
    if not os.path.exists(app.config['PROFILE_PICS_SAVE_PATH']):
        try:
            os.makedirs(app.config['PROFILE_PICS_SAVE_PATH'])
        except OSError as e:
            app.logger.error(f"Could not create PROFILE_PICS_SAVE_PATH: {e}")

    # --- Register Template Filters ---
    # format_date_filter and format_filesize are imported at the top from .utils
    app.jinja_env.filters['format_date'] = format_date_filter
    app.jinja_env.filters['file_size'] = format_filesize

    # --- Context Processors ---
    @app.context_processor
    def inject_current_year():
        return {'current_year': datetime.utcnow().year}

    @app.context_processor
    def inject_theme():
        theme_to_apply = 'dark'
        if 'theme' in session:
            theme_to_apply = session['theme']
        elif flask_login_current_user.is_authenticated:
            if hasattr(flask_login_current_user, 'settings') and \
                    flask_login_current_user.settings and \
                    hasattr(flask_login_current_user.settings, 'theme') and \
                    flask_login_current_user.settings.theme:
                theme_to_apply = flask_login_current_user.settings.theme
                session['theme'] = theme_to_apply
        if theme_to_apply not in ['light', 'dark']:
            theme_to_apply = 'dark'
        return dict(theme=theme_to_apply)

    with app.app_context():
        from . import models

        @login_manager.user_loader
        def load_user(user_id):
            return models.User.query.get(int(user_id))

        # --- Register Blueprints ---
        from .blueprints.main_bp import main_bp
        app.register_blueprint(main_bp)
        from .blueprints.auth_bp import auth_bp
        app.register_blueprint(auth_bp)
        from .blueprints.trading_models_bp import trading_models_bp
        app.register_blueprint(trading_models_bp, url_prefix='/trading_models')
        from .blueprints.files_bp import files_bp
        app.register_blueprint(files_bp)
        from .blueprints.admin_bp import admin_bp
        app.register_blueprint(admin_bp)
        from .blueprints.trades_bp import trades_bp
        app.register_blueprint(trades_bp)
        from .blueprints.settings_bp import settings_bp
        app.register_blueprint(settings_bp)

        # Error Handlers (as before)
        # ... (keep your existing error handlers) ...
        @app.errorhandler(403)
        def forbidden_page(error):
            app.logger.warning(f"403 Forbidden error at {request.path}: {error}")
            return render_template("errors/403.html", error=error, title="Forbidden"), 403

        @app.errorhandler(404)
        def page_not_found(error):
            app.logger.warning(f"404 Not Found error at {request.path}: {error}")
            return render_template("errors/404.html", error=error, title="Page Not Found"), 404

        @app.errorhandler(500)
        def server_error_page(error):
            app.logger.error(f"500 Server error at {request.path}: {error}", exc_info=True)
            db.session.rollback()
            return render_template("errors/500.html", error=error, title="Server Error"), 500

        # Initial Data Setup (as before)
        # ... (keep your existing initial data setup logic) ...
        if not app.config.get('TESTING', False):
            is_flask_cli = os.environ.get('FLASK_RUN_FROM_CLI') == 'true' or \
                           ('args' in dir(request) and request.args and any(
                               arg in ['db', 'migrate', 'upgrade', 'revision'] for arg in
                               request.args)) if request else True

            if not is_flask_cli or app.extensions.get('sqlalchemy'):
                try:
                    if models.AccountSetting.query.filter_by(setting_name='current_account_size').first() is None:
                        default_account_size = models.AccountSetting(setting_name='current_account_size',
                                                                     value_str='100000')
                        db.session.add(default_account_size)
                    if models.NewsEventItem.query.count() == 0:
                        from datetime import time as py_time_init
                        default_events = [
                            models.NewsEventItem(name="FOMC Statement", default_release_time=py_time_init(14, 0)),
                            models.NewsEventItem(name="CPI", default_release_time=py_time_init(8, 30)),
                            models.NewsEventItem(name="NFP", default_release_time=py_time_init(8, 30)),
                            models.NewsEventItem(name="Other")
                        ]
                        for event in default_events: db.session.add(event)
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    app.logger.info(
                        f"Initial data setup: Could not commit initial data (may be expected if DB not fully migrated): {e}")

    return app