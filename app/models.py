from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, date as py_date, time as py_time
# 'dt' alias is used by some of the migrated models for utcnow
from datetime import datetime as dt
import enum
import uuid
import os
import statistics

# Import 'db' from your main 'app' package/module
# This assumes your Flask app structure has an 'app' package
# and db is initialized in app/__init__.py
from app import db

# --- Constants for Models ---
QUARTER_NAMES = [None, "Q1 (Jan-Mar)", "Q2 (Apr-Jun)", "Q3 (Jul-Sep)", "Q4 (Oct-Dec)"]


# --- Existing V3 Models (P2 Models) ---

class UserRole(enum.Enum):
    USER = 'user'
    EDITOR = 'editor'
    ADMIN = 'admin'

    def __str__(self): return self.value


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(100), nullable=True)
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.USER)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=True, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    profile_picture = db.Column(db.String(200), nullable=True) # Path relative to static/profile_pics
    bio = db.Column(db.Text, nullable=True)
    is_email_verified = db.Column(db.Boolean, nullable=False, server_default='0') # Use server_default for new DBs

    activities = db.relationship('Activity', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    files = db.relationship('File', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    settings = db.relationship('Settings', backref='user', uselist=False, cascade='all, delete-orphan')
    api_keys = db.relationship('ApiKey', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    # Relationships to models from ptg_trading_journal-original
    trading_models = db.relationship('TradingModel', backref='user', lazy='dynamic')
    trades = db.relationship('Trade', backref='user', lazy='dynamic')
    daily_journals = db.relationship('DailyJournal', backref='user', lazy='dynamic')
    weekly_journals = db.relationship('WeeklyJournal', backref='user', lazy='dynamic')
    monthly_journals = db.relationship('MonthlyJournal', backref='user', lazy='dynamic')
    quarterly_journals = db.relationship('QuarterlyJournal', backref='user', lazy='dynamic')
    yearly_journals = db.relationship('YearlyJournal', backref='user', lazy='dynamic')


    def set_password(self, password): self.password_hash = generate_password_hash(password)
    def check_password(self, password): return check_password_hash(self.password_hash, password)
    def is_admin(self): return self.role == UserRole.ADMIN
    def is_editor(self): return self.role in [UserRole.EDITOR, UserRole.ADMIN]

    def generate_api_key(self, name, expiration_days=30):
        api_key = ApiKey(user_id=self.id, name=name, key=uuid.uuid4().hex,
                         expires_at=datetime.utcnow() + timedelta(days=expiration_days))
        db.session.add(api_key)
        return api_key

    @property
    def storage_usage(self): return db.session.query(db.func.sum(File.filesize)).filter_by(user_id=self.id).scalar() or 0

    @classmethod
    def find_by_username(cls, username): return cls.query.filter_by(username=username).first()
    @classmethod
    def find_by_email(cls, email): return cls.query.filter_by(email=email.lower()).first()

    def __repr__(self): return f'<User {self.username} (ID: {self.id})>'


class Activity(db.Model):
    __tablename__ = 'activity'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_activity_user'), nullable=False, index=True)
    # user relationship defined in User model via backref
    action = db.Column(db.String(50), nullable=False, index=True)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(50), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    resource_id = db.Column(db.Integer, nullable=True)
    resource_type = db.Column(db.String(50), nullable=True)

    @classmethod
    def log(cls, user_id, action, details=None, ip_address=None, user_agent=None, resource_id=None, resource_type=None):
        activity = cls(user_id=user_id, action=action, details=details, ip_address=ip_address, user_agent=user_agent,
                       resource_id=resource_id, resource_type=resource_type)
        db.session.add(activity)
        return activity

    def __repr__(self): return f'<Activity {self.action} by User {self.user_id} at {self.timestamp.strftime("%Y-%m-%d %H:%M")}>'


class File(db.Model):
    __tablename__ = 'file'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_file_user'), nullable=False, index=True)
    # user relationship defined in User model via backref
    filename = db.Column(db.String(255), nullable=False) # Original filename
    filepath = db.Column(db.String(255), nullable=False, unique=True) # Stored filename (e.g., UUID based)
    filesize = db.Column(db.Integer, nullable=False)
    file_type = db.Column(db.String(50), nullable=True) # Extension e.g. 'pdf', 'jpg'
    mime_type = db.Column(db.String(100), nullable=True) # Full MIME type e.g. 'application/pdf'
    upload_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    last_accessed = db.Column(db.DateTime, nullable=True)
    description = db.Column(db.Text, nullable=True)
    is_public = db.Column(db.Boolean, nullable=False, default=False)
    download_count = db.Column(db.Integer, nullable=False, default=0)

    @property
    def full_disk_path(self):
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        return os.path.join(upload_folder, self.filepath)

    @property
    def extension(self):
        return os.path.splitext(self.filename)[1].lower().lstrip('.') if '.' in self.filename else ''

    @property
    def size_formatted(self):
        if not isinstance(self.filesize, (int, float)) or self.filesize < 0: return "0 B"
        if self.filesize < 1024: return f"{self.filesize} B"
        elif self.filesize < 1024**2: return f"{self.filesize/1024:.1f} KB"
        elif self.filesize < 1024**3: return f"{self.filesize/(1024**2):.1f} MB"
        return f"{self.filesize/(1024**3):.1f} GB"

    def record_access(self, commit=False):
        self.last_accessed = datetime.utcnow()
        self.download_count += 1
        if commit: db.session.commit()
        return self

    def __repr__(self): return f'<File {self.filename} (ID: {self.id}, User: {self.user_id})>'


class Settings(db.Model): # User-specific settings
    __tablename__ = 'settings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_settings_user'), nullable=False, unique=True)
    # user relationship defined in User model via backref (uselist=False)
    theme = db.Column(db.String(20), nullable=False, default='light')
    notifications_enabled = db.Column(db.Boolean, nullable=False, default=True)
    items_per_page = db.Column(db.Integer, nullable=False, default=20)
    language = db.Column(db.String(10), nullable=False, default='en')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=True, onupdate=datetime.utcnow)
    custom_settings = db.Column(db.JSON, nullable=True)

    @classmethod
    def get_for_user(cls, user_id):
        settings = cls.query.filter_by(user_id=user_id).first()
        if not settings:
            settings = cls(user_id=user_id)
            db.session.add(settings)
        return settings

    def __repr__(self): return f'<Settings for User ID: {self.user_id}>'


class ApiKey(db.Model):
    __tablename__ = 'api_key'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_apikey_user'), nullable=False, index=True)
    # user relationship defined in User model via backref
    name = db.Column(db.String(100), nullable=False)
    key = db.Column(db.String(64), nullable=False, unique=True, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    last_used_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    permissions = db.Column(db.String(255), nullable=True)

    @property
    def is_expired(self): return self.expires_at and datetime.utcnow() > self.expires_at
    @property
    def is_valid(self): return self.is_active and not self.is_expired
    def use(self): self.last_used_at = datetime.utcnow()

    @classmethod
    def find_by_key(cls, key_value): return cls.query.filter_by(key=key_value).first()

    def __repr__(self): return f'<ApiKey {self.name} (User: {self.user_id})>'


user_group_association = db.Table('user_group_association',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id', name='fk_user_group_assoc_user'), primary_key=True),
    db.Column('group_id', db.Integer, db.ForeignKey('group.id', name='fk_user_group_assoc_group'), primary_key=True)
)


class Group(db.Model):
    __tablename__ = 'group'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_group_created_by_user'), nullable=True)
    creator = db.relationship('User', foreign_keys=[created_by_user_id])
    members = db.relationship('User', secondary=user_group_association,
                              backref=db.backref('member_of_groups', lazy='dynamic'))

    def __repr__(self): return f'<Group {self.name} (ID: {self.id})>'


class PasswordReset(db.Model):
    __tablename__ = 'password_reset'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_passwordreset_user'), nullable=False, index=True)
    token = db.Column(db.String(100), nullable=False, unique=True, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, nullable=False, default=False)
    user = db.relationship('User', backref=db.backref('password_resets', lazy='dynamic', cascade='all, delete-orphan'))

    @property
    def is_expired(self): return datetime.utcnow() > self.expires_at
    @property
    def is_valid(self): return not self.used and not self.is_expired

    @classmethod
    def generate_token(cls, user_id, expiration_hours=24):
        token_value = uuid.uuid4().hex
        reset = cls(user_id=user_id, token=token_value,
                    expires_at=datetime.utcnow() + timedelta(hours=expiration_hours))
        db.session.add(reset)
        return reset

    @classmethod
    def find_by_token(cls, token_value): return cls.query.filter_by(token=token_value).first()
    def use(self): self.used = True

    def __repr__(self): return f'<PasswordReset for User ID: {self.user_id} (Token: {self.token[:10]}...)>'


# --- Models from P1 (ptg_trading_journal-original) ---

class TradingModel(db.Model):
    __tablename__ = 'trading_model'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    version = db.Column(db.String(50), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    overview_logic = db.Column(db.Text, nullable=True)
    primary_chart_tf = db.Column(db.String(50), nullable=True)
    execution_chart_tf = db.Column(db.String(50), nullable=True)
    context_chart_tf = db.Column(db.String(50), nullable=True)
    technical_indicators_used = db.Column(db.Text, nullable=True)
    chart_patterns_used = db.Column(db.Text, nullable=True)
    price_action_signals = db.Column(db.Text, nullable=True)
    key_levels_identification = db.Column(db.Text, nullable=True)
    volume_analysis_notes = db.Column(db.Text, nullable=True)
    fundamental_analysis_notes = db.Column(db.Text, nullable=True)
    instrument_applicability = db.Column(db.Text, nullable=True)
    session_applicability = db.Column(db.Text, nullable=True)
    optimal_market_conditions = db.Column(db.Text, nullable=True)
    sub_optimal_market_conditions = db.Column(db.Text, nullable=True)
    entry_trigger_description = db.Column(db.Text, nullable=True)
    stop_loss_strategy = db.Column(db.Text, nullable=True)
    take_profit_strategy = db.Column(db.Text, nullable=True)
    min_risk_reward_ratio = db.Column(db.Float, nullable=True)
    position_sizing_rules = db.Column(db.Text, nullable=True)
    scaling_in_out_rules = db.Column(db.Text, nullable=True)
    trade_management_breakeven_rules = db.Column(db.Text, nullable=True)
    trade_management_trailing_stop_rules = db.Column(db.Text, nullable=True)
    trade_management_partial_profit_rules = db.Column(db.Text, nullable=True)
    trade_management_adverse_price_action = db.Column(db.Text, nullable=True)
    model_max_loss_per_trade = db.Column(db.String(100), nullable=True)
    model_max_daily_loss = db.Column(db.String(100), nullable=True)
    model_max_weekly_loss = db.Column(db.String(100), nullable=True)
    model_consecutive_loss_limit = db.Column(db.String(100), nullable=True)
    model_action_on_max_drawdown = db.Column(db.Text, nullable=True)
    pre_trade_checklist = db.Column(db.Text, nullable=True)
    order_types_used = db.Column(db.Text, nullable=True)
    broker_platform_notes = db.Column(db.Text, nullable=True)
    execution_confirmation_notes = db.Column(db.Text, nullable=True)
    post_trade_routine_model = db.Column(db.Text, nullable=True)
    strengths = db.Column(db.Text, nullable=True)
    weaknesses = db.Column(db.Text, nullable=True)
    backtesting_forwardtesting_notes = db.Column(db.Text, nullable=True)
    refinements_learnings = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=dt.utcnow)
    updated_at = db.Column(db.DateTime, default=dt.utcnow, onupdate=dt.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_tradingmodel_user'), nullable=False, index=True)
    # user relationship defined in User model via backref
    __table_args__ = (db.UniqueConstraint('user_id', 'name', name='uq_user_tradingmodel_name'),)

    def __repr__(self): return f"<TradingModel '{self.name}' (User: {self.user_id})>"


class Trade(db.Model):
    __tablename__ = 'trade'
    id = db.Column(db.Integer, primary_key=True)
    instrument = db.Column(db.String(10), nullable=False)
    trade_date = db.Column(db.Date, nullable=False, default=py_date.today)
    direction = db.Column(db.String(5), nullable=False)
    initial_stop_loss = db.Column(db.Float, nullable=True)
    terminus_target = db.Column(db.Float, nullable=True)
    is_dca = db.Column(db.Boolean, default=False)
    mae = db.Column(db.Float, nullable=True)
    mfe = db.Column(db.Float, nullable=True)
    entry_model_legacy = db.Column(db.String(50), nullable=True)
    trade_notes = db.Column(db.Text, nullable=True)
    how_closed = db.Column(db.String(20), nullable=True)
    news_event = db.Column(db.String(100), nullable=True)
    rules_rating = db.Column(db.Integer, nullable=True)
    management_rating = db.Column(db.Integer, nullable=True)
    target_rating = db.Column(db.Integer, nullable=True)
    entry_rating = db.Column(db.Integer, nullable=True)
    preparation_rating = db.Column(db.Integer, nullable=True)
    psych_scored_highest = db.Column(db.Text, nullable=True)
    psych_scored_lowest = db.Column(db.Text, nullable=True)
    overall_analysis_notes = db.Column(db.Text, nullable=True)
    screenshot_link = db.Column(db.String(255), nullable=True)
    trade_management_notes = db.Column(db.Text, nullable=True)
    errors_notes = db.Column(db.Text, nullable=True)
    improvements_notes = db.Column(db.Text, nullable=True)
    tags = db.Column(db.String(255), nullable=True)
    point_value = db.Column(db.Float, nullable=True)

    trading_model_id = db.Column(db.Integer, db.ForeignKey('trading_model.id', name='fk_trade_trading_model'), nullable=True)
    trading_model = db.relationship('TradingModel', backref=db.backref('trades', lazy='dynamic'))

    entries = db.relationship('EntryPoint', backref='trade', lazy='dynamic', cascade="all, delete-orphan")
    exits = db.relationship('ExitPoint', backref='trade', lazy='dynamic', cascade="all, delete-orphan")

    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_trade_user'), nullable=False, index=True)
    # user relationship defined in User model via backref

    @property
    def total_contracts_entered(self):
        if not self.entries: return 0
        return sum(entry.contracts for entry in self.entries if entry.contracts is not None)

    @property
    def average_entry_price(self):
        total_contracts = self.total_contracts_entered
        if not total_contracts or total_contracts == 0: return None
        total_value = sum(entry.contracts * entry.entry_price for entry in self.entries if
                          entry.contracts is not None and entry.entry_price is not None)
        return total_value / total_contracts

    @property
    def total_contracts_exited(self):
        if not self.exits: return 0
        return sum(exit_point.contracts for exit_point in self.exits if exit_point.contracts is not None)

    @property
    def average_exit_price(self):
        total_exited = self.total_contracts_exited
        if not total_exited or total_exited == 0: return None
        total_exit_value = sum(exit_point.contracts * exit_point.exit_price for exit_point in self.exits if
                               exit_point.contracts is not None and exit_point.exit_price is not None)
        return total_exit_value / total_exited

    @property
    def gross_pnl(self):
        avg_entry = self.average_entry_price
        avg_exit = self.average_exit_price
        contracts_exited = self.total_contracts_exited
        pv = self.point_value
        if avg_entry is None or avg_exit is None or contracts_exited == 0 or pv is None or pv == 0:
            return 0.0
        pnl_per_contract_in_points = 0.0
        if self.direction == "Long": pnl_per_contract_in_points = avg_exit - avg_entry
        elif self.direction == "Short": pnl_per_contract_in_points = avg_entry - avg_exit
        return pnl_per_contract_in_points * contracts_exited * pv

    @property
    def risk_reward_ratio(self):
        avg_entry = self.average_entry_price
        sl = self.initial_stop_loss
        tp = self.terminus_target
        if avg_entry is None or sl is None or tp is None: return None
        potential_risk_per_contract = 0.0
        potential_reward_per_contract = 0.0
        if self.direction == "Long":
            potential_risk_per_contract = abs(avg_entry - sl)
            potential_reward_per_contract = abs(tp - avg_entry)
        elif self.direction == "Short":
            potential_risk_per_contract = abs(sl - avg_entry)
            potential_reward_per_contract = abs(avg_entry - tp)
        return potential_reward_per_contract / potential_risk_per_contract if potential_risk_per_contract > 0 and potential_reward_per_contract > 0 else None

    @property
    def time_in_trade(self):
        if not self.entries: return "Open"
        first_entry_obj = self.entries.order_by(EntryPoint.entry_time).first()
        if not first_entry_obj or not first_entry_obj.entry_time: return "Open"
        min_entry_datetime = datetime.combine(self.trade_date, first_entry_obj.entry_time)
        last_exit_obj = self.exits.order_by(ExitPoint.exit_time.desc()).first()
        if not last_exit_obj or not last_exit_obj.exit_time: return "Open"
        max_exit_datetime = datetime.combine(self.trade_date, last_exit_obj.exit_time)
        if max_exit_datetime >= min_entry_datetime:
            duration = max_exit_datetime - min_entry_datetime
            total_seconds = int(duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{hours:02d}:{minutes:02d}"
        return "N/A"

    @property
    def dollar_risk(self):
        avg_entry = self.average_entry_price
        sl = self.initial_stop_loss
        contracts = self.total_contracts_entered
        pv = self.point_value
        if avg_entry is None or sl is None or contracts == 0 or pv is None or pv == 0: return None
        risk_per_contract_in_points = 0.0
        if self.direction == "Long": risk_per_contract_in_points = avg_entry - sl
        elif self.direction == "Short": risk_per_contract_in_points = sl - avg_entry
        return risk_per_contract_in_points * contracts * pv if risk_per_contract_in_points > 0 else 0.0

    @property
    def pnl_in_r(self):
        initial_risk = self.dollar_risk
        pnl = self.gross_pnl
        if initial_risk is None or initial_risk == 0 or pnl is None: return None
        if self.total_contracts_exited > 0 and self.how_closed not in ["Still Open", None] and initial_risk > 0:
            return pnl / initial_risk
        return None

    def __repr__(self): return f"<Trade {self.id} {self.instrument} on {self.trade_date} (User: {self.user_id})>"


class EntryPoint(db.Model):
    __tablename__ = 'entry_point'
    id = db.Column(db.Integer, primary_key=True)
    entry_time = db.Column(db.Time, nullable=False)
    contracts = db.Column(db.Integer, nullable=False)
    entry_price = db.Column(db.Float, nullable=False)
    trade_id = db.Column(db.Integer, db.ForeignKey('trade.id', name='fk_entrypoint_trade'), nullable=False)
    # trade relationship defined in Trade model via backref

    def __repr__(self): return f"<EntryPoint ID: {self.id} for Trade ID: {self.trade_id} ({self.contracts} @ {self.entry_price})>"


class ExitPoint(db.Model):
    __tablename__ = 'exit_point'
    id = db.Column(db.Integer, primary_key=True)
    exit_time = db.Column(db.Time, nullable=True)
    contracts = db.Column(db.Integer, nullable=True)
    exit_price = db.Column(db.Float, nullable=True)
    trade_id = db.Column(db.Integer, db.ForeignKey('trade.id', name='fk_exitpoint_trade'), nullable=False)
    # trade relationship defined in Trade model via backref

    def __repr__(self): return f"<ExitPoint ID: {self.id} for Trade ID: {self.trade_id} ({self.contracts} @ {self.exit_price})>"


class DailyJournal(db.Model):
    __tablename__ = 'daily_journal'
    id = db.Column(db.Integer, primary_key=True)
    journal_date = db.Column(db.Date, nullable=False)
    key_events = db.Column(db.Text, nullable=True)
    key_tasks = db.Column(db.Text, nullable=True)
    on_my_mind = db.Column(db.Text, nullable=True)
    important_focus = db.Column(db.Text, nullable=True)
    key_strengths = db.Column(db.Text, nullable=True)
    mental_feeling_rating = db.Column(db.Integer, nullable=True)
    mental_mind_rating = db.Column(db.Integer, nullable=True)
    mental_energy_rating = db.Column(db.Integer, nullable=True)
    mental_motivation_rating = db.Column(db.Integer, nullable=True)
    asia_direction = db.Column(db.String(10), default="None")
    asia_session_status = db.Column(db.String(10), default="None")
    asia_model_status = db.Column(db.String(10), default="None")
    asia_actual_range_points = db.Column(db.Float, nullable=True)
    asia_actual_range_percentage = db.Column(db.Float, nullable=True)
    asia_median_range_input_note = db.Column(db.Text, nullable=True)
    london_direction = db.Column(db.String(10), default="None")
    london_session_status = db.Column(db.String(10), default="None")
    london_model_status = db.Column(db.String(10), default="None")
    london_actual_range_points = db.Column(db.Float, nullable=True)
    london_actual_range_percentage = db.Column(db.Float, nullable=True)
    london_median_range_input_note = db.Column(db.Text, nullable=True)
    ny1_direction = db.Column(db.String(10), default="None")
    ny1_session_status = db.Column(db.String(10), default="None")
    ny1_model_status = db.Column(db.String(10), default="None")
    ny1_actual_range_points = db.Column(db.Float, nullable=True)
    ny1_actual_range_percentage = db.Column(db.Float, nullable=True)
    ny1_median_range_input_note = db.Column(db.Text, nullable=True)
    ny2_direction = db.Column(db.String(10), default="None")
    ny2_session_status = db.Column(db.String(10), default="None")
    ny2_model_status = db.Column(db.String(10), default="None")
    ny2_actual_range_points = db.Column(db.Float, nullable=True)
    ny2_actual_range_percentage = db.Column(db.Float, nullable=True)
    ny2_median_range_input_note = db.Column(db.Text, nullable=True)
    adr_10_day_median_range_value = db.Column(db.Float, nullable=True)
    todays_total_range_points = db.Column(db.Float, nullable=True)
    todays_total_range_percentage = db.Column(db.Float, nullable=True)
    p12_scenario_selected = db.Column(db.String(10), default="None")
    p12_expected_outcomes = db.Column(db.Text, nullable=True)
    realistic_expectance_notes = db.Column(db.Text, nullable=True)
    engagement_structure_notes = db.Column(db.Text, nullable=True)
    did_well_today = db.Column(db.Text, nullable=True)
    did_not_go_well_today = db.Column(db.Text, nullable=True)
    learned_today = db.Column(db.Text, nullable=True)
    improve_action_next_day = db.Column(db.Text, nullable=True)
    market_observations = db.Column(db.Text, nullable=True)
    self_observations = db.Column(db.Text, nullable=True)
    review_psych_discipline_rating = db.Column(db.Integer, nullable=True)
    review_psych_motivation_rating = db.Column(db.Integer, nullable=True)
    review_psych_focus_rating = db.Column(db.Integer, nullable=True)
    review_psych_mastery_rating = db.Column(db.Integer, nullable=True)
    review_psych_composure_rating = db.Column(db.Integer, nullable=True)
    review_psych_resilience_rating = db.Column(db.Integer, nullable=True)
    review_psych_mind_rating = db.Column(db.Integer, nullable=True)
    review_psych_energy_rating = db.Column(db.Integer, nullable=True)

    wg_ny1_lt_notes = db.Column(db.Text, nullable=True)
    wg_ny1_lt_hod_pct_l = db.Column(db.Float, nullable=True)
    wg_ny1_lt_hod_pct_h = db.Column(db.Float, nullable=True)
    wg_ny1_lt_hod_ts = db.Column(db.Time, nullable=True)
    wg_ny1_lt_hod_te = db.Column(db.Time, nullable=True)
    wg_ny1_lt_lod_pct_l = db.Column(db.Float, nullable=True)
    wg_ny1_lt_lod_pct_h = db.Column(db.Float, nullable=True)
    wg_ny1_lt_lod_ts = db.Column(db.Time, nullable=True)
    wg_ny1_lt_lod_te = db.Column(db.Time, nullable=True)
    wg_ny1_lf_notes = db.Column(db.Text, nullable=True)
    wg_ny1_lf_hod_pct_l = db.Column(db.Float, nullable=True)
    wg_ny1_lf_hod_pct_h = db.Column(db.Float, nullable=True)
    wg_ny1_lf_hod_ts = db.Column(db.Time, nullable=True)
    wg_ny1_lf_hod_te = db.Column(db.Time, nullable=True)
    wg_ny1_lf_lod_pct_l = db.Column(db.Float, nullable=True)
    wg_ny1_lf_lod_pct_h = db.Column(db.Float, nullable=True)
    wg_ny1_lf_lod_ts = db.Column(db.Time, nullable=True)
    wg_ny1_lf_lod_te = db.Column(db.Time, nullable=True)
    wg_ny1_st_notes = db.Column(db.Text, nullable=True)
    wg_ny1_st_hod_pct_l = db.Column(db.Float, nullable=True)
    wg_ny1_st_hod_pct_h = db.Column(db.Float, nullable=True)
    wg_ny1_st_hod_ts = db.Column(db.Time, nullable=True)
    wg_ny1_st_hod_te = db.Column(db.Time, nullable=True)
    wg_ny1_st_lod_pct_l = db.Column(db.Float, nullable=True)
    wg_ny1_st_lod_pct_h = db.Column(db.Float, nullable=True)
    wg_ny1_st_lod_ts = db.Column(db.Time, nullable=True)
    wg_ny1_st_lod_te = db.Column(db.Time, nullable=True)
    wg_ny1_sf_notes = db.Column(db.Text, nullable=True)
    wg_ny1_sf_hod_pct_l = db.Column(db.Float, nullable=True)
    wg_ny1_sf_hod_pct_h = db.Column(db.Float, nullable=True)
    wg_ny1_sf_hod_ts = db.Column(db.Time, nullable=True)
    wg_ny1_sf_hod_te = db.Column(db.Time, nullable=True)
    wg_ny1_sf_lod_pct_l = db.Column(db.Float, nullable=True)
    wg_ny1_sf_lod_pct_h = db.Column(db.Float, nullable=True)
    wg_ny1_sf_lod_ts = db.Column(db.Time, nullable=True)
    wg_ny1_sf_lod_te = db.Column(db.Time, nullable=True)
    wg_ny2_lt_notes = db.Column(db.Text, nullable=True)
    wg_ny2_lt_hod_pct_l = db.Column(db.Float, nullable=True)
    wg_ny2_lt_hod_pct_h = db.Column(db.Float, nullable=True)
    wg_ny2_lt_hod_ts = db.Column(db.Time, nullable=True)
    wg_ny2_lt_hod_te = db.Column(db.Time, nullable=True)
    wg_ny2_lt_lod_pct_l = db.Column(db.Float, nullable=True)
    wg_ny2_lt_lod_pct_h = db.Column(db.Float, nullable=True)
    wg_ny2_lt_lod_ts = db.Column(db.Time, nullable=True)
    wg_ny2_lt_lod_te = db.Column(db.Time, nullable=True)
    wg_ny2_lf_notes = db.Column(db.Text, nullable=True)
    wg_ny2_lf_hod_pct_l = db.Column(db.Float, nullable=True)
    wg_ny2_lf_hod_pct_h = db.Column(db.Float, nullable=True)
    wg_ny2_lf_hod_ts = db.Column(db.Time, nullable=True)
    wg_ny2_lf_hod_te = db.Column(db.Time, nullable=True)
    wg_ny2_lf_lod_pct_l = db.Column(db.Float, nullable=True)
    wg_ny2_lf_lod_pct_h = db.Column(db.Float, nullable=True)
    wg_ny2_lf_lod_ts = db.Column(db.Time, nullable=True)
    wg_ny2_lf_lod_te = db.Column(db.Time, nullable=True)
    wg_ny2_st_notes = db.Column(db.Text, nullable=True)
    wg_ny2_st_hod_pct_l = db.Column(db.Float, nullable=True)
    wg_ny2_st_hod_pct_h = db.Column(db.Float, nullable=True)
    wg_ny2_st_hod_ts = db.Column(db.Time, nullable=True)
    wg_ny2_st_hod_te = db.Column(db.Time, nullable=True)
    wg_ny2_st_lod_pct_l = db.Column(db.Float, nullable=True)
    wg_ny2_st_lod_pct_h = db.Column(db.Float, nullable=True)
    wg_ny2_st_lod_ts = db.Column(db.Time, nullable=True)
    wg_ny2_st_lod_te = db.Column(db.Time, nullable=True)
    wg_ny2_sf_notes = db.Column(db.Text, nullable=True)
    wg_ny2_sf_hod_pct_l = db.Column(db.Float, nullable=True)
    wg_ny2_sf_hod_pct_h = db.Column(db.Float, nullable=True)
    wg_ny2_sf_hod_ts = db.Column(db.Time, nullable=True)
    wg_ny2_sf_hod_te = db.Column(db.Time, nullable=True)
    wg_ny2_sf_lod_pct_l = db.Column(db.Float, nullable=True)
    wg_ny2_sf_lod_pct_h = db.Column(db.Float, nullable=True)
    wg_ny2_sf_lod_ts = db.Column(db.Time, nullable=True)
    wg_ny2_sf_lod_te = db.Column(db.Time, nullable=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_dailyjournal_user'), nullable=False, index=True)
    # user relationship defined in User model via backref
    __table_args__ = (db.UniqueConstraint('user_id', 'journal_date', name='uq_user_journal_date'),)

    @property
    def average_review_psych_rating(self):
        ratings = [
            self.review_psych_discipline_rating, self.review_psych_motivation_rating,
            self.review_psych_focus_rating, self.review_psych_mastery_rating,
            self.review_psych_composure_rating, self.review_psych_resilience_rating,
            self.review_psych_mind_rating, self.review_psych_energy_rating
        ]
        valid_ratings = [r for r in ratings if r is not None and isinstance(r, (int, float)) and 1 <= r <= 5]
        return statistics.mean(valid_ratings) if valid_ratings else None

    def __repr__(self): return f"<DailyJournal for {self.journal_date} (User: {self.user_id})>"


class WeeklyJournal(db.Model):
    __tablename__ = 'weekly_journal'
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    week_number = db.Column(db.Integer, nullable=False)
    know_traded_well_if = db.Column(db.Text, nullable=True)
    key_actions_for_excellence = db.Column(db.Text, nullable=True)
    potential_challenge_and_response = db.Column(db.Text, nullable=True)
    improvement_area_and_approach = db.Column(db.Text, nullable=True)
    weekly_did_well_more_of = db.Column(db.Text, nullable=True)
    weekly_could_do_differently = db.Column(db.Text, nullable=True)
    weekly_challenge_overcame_learned = db.Column(db.Text, nullable=True)
    weekly_improve_action_next_week = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_weeklyjournal_user'), nullable=False, index=True)
    # user relationship defined in User model via backref
    __table_args__ = (db.UniqueConstraint('user_id', 'year', 'week_number', name='uq_user_year_week'),)

    @property
    def week_start_date_display(self):
        try: return py_date.fromisocalendar(self.year, self.week_number, 1).strftime('%d %b %Y')
        except ValueError: return "Invalid Week/Year"

    def __repr__(self): return f"<WeeklyJournal {self.year}-W{self.week_number:02d} (User: {self.user_id})>"


class MonthlyJournal(db.Model):
    __tablename__ = 'monthly_journal'
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False) # 1-12
    long_term_trading_goal = db.Column(db.Text, nullable=True)
    reason_for_trading = db.Column(db.Text, nullable=True)
    monthly_goals = db.Column(db.Text, nullable=True)
    monthly_actions_to_achieve_goals = db.Column(db.Text, nullable=True)
    coach_advice_for_month_ahead = db.Column(db.Text, nullable=True)
    monthly_did_well_more_of = db.Column(db.Text, nullable=True)
    monthly_could_do_differently = db.Column(db.Text, nullable=True)
    monthly_challenge_overcame_learned = db.Column(db.Text, nullable=True)
    monthly_action_taken_and_progress = db.Column(db.Text, nullable=True)
    coach_feedback_on_month = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_monthlyjournal_user'), nullable=False, index=True)
    # user relationship defined in User model via backref
    __table_args__ = (db.UniqueConstraint('user_id', 'year', 'month', name='uq_user_year_month'),)

    @property
    def month_year_display(self):
        try: return py_date(self.year, self.month, 1).strftime('%B %Y')
        except ValueError: return f"Invalid Date {self.year}-{self.month}"

    def __repr__(self): return f"<MonthlyJournal {self.year}-{self.month:02d} (User: {self.user_id})>"


class QuarterlyJournal(db.Model):
    __tablename__ = 'quarterly_journal'
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    quarter = db.Column(db.Integer, nullable=False) # 1-4
    key_goals_for_quarter = db.Column(db.Text, nullable=True)
    major_focus_areas_strategies = db.Column(db.Text, nullable=True)
    anticipated_challenges_mitigation = db.Column(db.Text, nullable=True)
    quarterly_achievements_progress = db.Column(db.Text, nullable=True)
    what_went_well_quarter = db.Column(db.Text, nullable=True)
    what_did_not_go_well_quarter = db.Column(db.Text, nullable=True)
    key_lessons_learned_quarter = db.Column(db.Text, nullable=True)
    adjustments_for_next_quarter = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_quarterlyjournal_user'), nullable=False, index=True)
    # user relationship defined in User model via backref
    __table_args__ = (db.UniqueConstraint('user_id', 'year', 'quarter', name='uq_user_year_quarter'),)

    @property
    def quarter_display_name(self): return QUARTER_NAMES[self.quarter] if self.quarter and 1 <= self.quarter <= 4 else "Invalid Quarter"

    def __repr__(self): return f"<QuarterlyJournal {self.year}-Q{self.quarter} (User: {self.user_id})>"


class YearlyJournal(db.Model):
    __tablename__ = 'yearly_journal'
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    yearly_long_term_vision = db.Column(db.Text, nullable=True)
    yearly_key_goals = db.Column(db.Text, nullable=True)
    yearly_major_focus_areas = db.Column(db.Text, nullable=True)
    yearly_coach_advice_for_year_ahead = db.Column(db.Text, nullable=True)
    yearly_achievements = db.Column(db.Text, nullable=True)
    yearly_challenges_overcome = db.Column(db.Text, nullable=True)
    yearly_lessons_learned = db.Column(db.Text, nullable=True)
    yearly_goals_for_next_year = db.Column(db.Text, nullable=True)
    yearly_coach_feedback_on_year = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_yearlyjournal_user'), nullable=False, index=True)
    # user relationship defined in User model via backref
    __table_args__ = (db.UniqueConstraint('user_id', 'year', name='uq_user_year'),)

    def __repr__(self): return f"<YearlyJournal for {self.year} (User: {self.user_id})>"


class NewsEventItem(db.Model):
    __tablename__ = 'news_event_item'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    default_release_time = db.Column(db.Time, nullable=True)

    def __repr__(self): return f"<NewsEventItem '{self.name}'>"


class AccountSetting(db.Model):
    __tablename__ = 'account_setting'
    id = db.Column(db.Integer, primary_key=True)
    setting_name = db.Column(db.String(100), unique=True, nullable=False)
    value_str = db.Column(db.String(255), nullable=True)
    value_int = db.Column(db.Integer, nullable=True)
    value_float = db.Column(db.Float, nullable=True)
    value_bool = db.Column(db.Boolean, nullable=True)
    description = db.Column(db.Text, nullable=True)

    def __repr__(self): return f"<AccountSetting '{self.setting_name}'>"