from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (StringField, PasswordField, BooleanField, SubmitField,
                     TextAreaField, FloatField, SelectField, IntegerField, DateField,
                     TimeField)  # Ensured all needed fields are imported
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, NumberRange, InputRequired
from app.models import UserRole  # Import UserRole for choices in Admin forms


# --- Authentication and User-Related Forms ---
class LoginForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=4, max=80)],
                           render_kw={"placeholder": "Enter your username"})
    password = PasswordField('Password',
                             validators=[DataRequired(), Length(min=6)],
                             render_kw={"placeholder": "Enter your password"})
    remember = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(message="Username is required."),
                                       Length(min=3, max=25, message="Username must be between 3 and 25 characters.")])
    email = StringField('Email',
                        validators=[DataRequired(message="Email is required."),
                                    Email(message="Please enter a valid email address.")])
    password = PasswordField('Password',
                             validators=[DataRequired(message="Password is required."),
                                         Length(min=8, message="Password must be at least 8 characters long.")])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(message="Please confirm your password."),
                                                 EqualTo('password', message="Passwords must match.")])
    submit = SubmitField('Register')


class ResendVerificationForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(message="Email is required."),
                                    Email(message="Please enter a valid email address.")],
                        render_kw={"placeholder": "Enter your registered email address"})
    submit = SubmitField('Resend Verification Email')


class RequestPasswordResetForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(message="Email is required."),
                                    Email(message="Please enter a valid email address.")],
                        render_kw={"placeholder": "Enter your account's email address"})
    submit = SubmitField('Request Password Reset')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password',
                             validators=[DataRequired(message="Password is required."),
                                         Length(min=8, message="Password must be at least 8 characters long.")])
    confirm_password = PasswordField('Confirm New Password',
                                     validators=[DataRequired(message="Please confirm your new password."),
                                                 EqualTo('password', message="Passwords must match.")])
    submit = SubmitField('Reset Password')


class ProfileForm(FlaskForm):
    name = StringField('Full Name', validators=[Optional(), Length(max=100)])
    email = StringField('Email Address',
                        validators=[DataRequired(), Email(message="Invalid email address."), Length(max=120)])
    bio = TextAreaField('About Me (Optional)', validators=[Optional(), Length(max=500)])
    profile_picture = FileField('Update Profile Picture', validators=[
        Optional(),
        FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Images only! (jpg, jpeg, png, gif)')
    ])
    # Ensure your profile route handles distinguishing these submit buttons if they are on the same page/route
    submit = SubmitField('Save Profile Changes')


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=8,
                                                                                    message='Password must be at least 8 characters long.')])
    confirm_password = PasswordField('Confirm New Password',
                                     validators=[DataRequired(),
                                                 EqualTo('new_password', message='New passwords must match.')])
    submit = SubmitField('Update Password')


# --- File Upload Form ---
class FileUploadForm(FlaskForm):
    file = FileField('Select File', validators=[DataRequired(),
                                                FileAllowed(
                                                    ['pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx', 'xls', 'xlsx', 'txt',
                                                     'csv'],
                                                    'Allowed file types: pdf, png, jpg, jpeg, doc, docx, xls, xlsx, txt, csv')
                                                ])
    description = TextAreaField('Description (Optional)', validators=[Optional(), Length(max=500)])
    is_public = BooleanField('Make Public', default=False)
    submit = SubmitField('Upload File')


# --- Trading Model Form ---
class TradingModelForm(FlaskForm):
    name = StringField('Model Name', validators=[DataRequired(), Length(max=150)])
    version = StringField('Version', validators=[Optional(), Length(max=50)])
    is_active = BooleanField('Is Active', default=True)
    overview_logic = TextAreaField('Overview & Logic', validators=[Optional()])
    primary_chart_tf = StringField('Primary Chart TF (Analysis/Setup)', validators=[Optional(), Length(max=50)])
    execution_chart_tf = StringField('Execution Chart TF (Entry/Fine-tuning)', validators=[Optional(), Length(max=50)])
    context_chart_tf = StringField('Higher Timeframe (Context/Trend)', validators=[Optional(), Length(max=50)])
    technical_indicators_used = TextAreaField('Technical Indicators Used (and settings)', validators=[Optional()])
    chart_patterns_used = TextAreaField('Chart Patterns Used', validators=[Optional()])
    price_action_signals = TextAreaField('Price Action Signals', validators=[Optional()])
    key_levels_identification = TextAreaField('Key Levels Identification', validators=[Optional()])
    volume_analysis_notes = TextAreaField('Volume Analysis (if applicable)', validators=[Optional()])
    fundamental_analysis_notes = TextAreaField('Fundamental Analysis Considerations (if applicable)',
                                               validators=[Optional()])
    instrument_applicability = TextAreaField('Instrument Applicability (e.g., NQ, ES, specific stocks)',
                                             validators=[Optional()])
    session_applicability = TextAreaField('Session Applicability (e.g., London Open, NY Open)', validators=[Optional()])
    optimal_market_conditions = TextAreaField('Optimal Market Conditions for this Model', validators=[Optional()])
    sub_optimal_market_conditions = TextAreaField('Sub-optimal Market Conditions (or when to avoid)',
                                                  validators=[Optional()])
    entry_trigger_description = TextAreaField('Entry Trigger Description (Specific conditions for entry)',
                                              validators=[DataRequired()])
    stop_loss_strategy = TextAreaField('Stop-Loss Strategy (e.g., ATR-based, fixed points, structure)',
                                       validators=[DataRequired()])
    take_profit_strategy = TextAreaField('Take-Profit Strategy (e.g., fixed R:R, key levels, trailing)',
                                         validators=[DataRequired()])
    min_risk_reward_ratio = FloatField('Minimum Acceptable Risk:Reward Ratio', validators=[Optional(),
                                                                                           NumberRange(min=0.0,
                                                                                                       message="R:R must be a positive number or zero.")])
    position_sizing_rules = TextAreaField('Position Sizing Rules (e.g., % of account, fixed lot)',
                                          validators=[Optional()])
    scaling_in_out_rules = TextAreaField('Scaling In/Out Rules (if applicable)', validators=[Optional()])
    trade_management_breakeven_rules = TextAreaField('Trade Management: Breakeven Rules', validators=[Optional()])
    trade_management_trailing_stop_rules = TextAreaField('Trade Management: Trailing Stop Rules',
                                                         validators=[Optional()])
    trade_management_partial_profit_rules = TextAreaField('Trade Management: Partial Profit Taking Rules',
                                                          validators=[Optional()])
    trade_management_adverse_price_action = TextAreaField('Trade Management: Handling Adverse Price Action',
                                                          validators=[Optional()])
    model_max_loss_per_trade = StringField('Max Risk per Trade for this Model (e.g., 1% or $X)',
                                           validators=[Optional(), Length(max=100)])
    model_max_daily_loss = StringField('Max Daily Loss when using this Model (e.g., 3% or $Y)',
                                       validators=[Optional(), Length(max=100)])
    model_max_weekly_loss = StringField('Max Weekly Loss when using this Model',
                                        validators=[Optional(), Length(max=100)])
    model_consecutive_loss_limit = StringField('Consecutive Loss Limit for this Model (e.g., 3 trades)',
                                               validators=[Optional(), Length(max=100)])
    model_action_on_max_drawdown = TextAreaField('Action if Max Drawdown (for this model) is Hit',
                                                 validators=[Optional()])
    pre_trade_checklist = TextAreaField('Pre-Trade Routine Checklist (Model Specific - one item per line)',
                                        validators=[Optional()])
    order_types_used = TextAreaField('Order Types Primarily Used (e.g., Market, Limit, Stop)', validators=[Optional()])
    broker_platform_notes = TextAreaField('Broker/Platform Specific Notes', validators=[Optional()])
    execution_confirmation_notes = TextAreaField('Confirmation after Execution Notes', validators=[Optional()])
    post_trade_routine_model = TextAreaField('Post-Trade Routine (Model Specific)', validators=[Optional()])
    strengths = TextAreaField('Perceived Strengths of this Model', validators=[Optional()])
    weaknesses = TextAreaField('Perceived Weaknesses of this Model', validators=[Optional()])
    backtesting_forwardtesting_notes = TextAreaField('Backtesting/Forward-Testing Notes & Results',
                                                     validators=[Optional()])
    refinements_learnings = TextAreaField('Refinements & Learnings Over Time', validators=[Optional()])
    submit = SubmitField('Save Trading Model')


# --- Admin Forms ---
class AdminCreateUserForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(message="Username is required."),
                                       Length(min=3, max=25, message="Username must be between 3 and 25 characters.")])
    email = StringField('Email',
                        validators=[DataRequired(message="Email is required."),
                                    Email(message="Please enter a valid email address.")])
    name = StringField('Full Name (Optional)', validators=[Optional(), Length(max=100)])
    password = PasswordField('Password',
                             validators=[DataRequired(message="Password is required."),
                                         Length(min=8, message="Password must be at least 8 characters long.")])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(message="Please confirm your password."),
                                                 EqualTo('password', message="Passwords must match.")])
    role = SelectField('Role',
                       choices=[(role.value, role.name.title()) for role in UserRole],  # Populates from UserRole enum
                       validators=[DataRequired()])
    is_active = BooleanField('Account Active', default=True)
    is_email_verified = BooleanField('Email Verified by Admin', default=False)  # Admin can choose to pre-verify
    submit = SubmitField('Create User')


class AdminEditUserForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(message="Username is required."),
                                       Length(min=3, max=25, message="Username must be between 3 and 25 characters.")])
    email = StringField('Email',
                        validators=[DataRequired(message="Email is required."),
                                    Email(message="Please enter a valid email address.")])
    name = StringField('Full Name (Optional)', validators=[Optional(), Length(max=100)])
    role = SelectField('Role',
                       choices=[(role.value, role.name.title()) for role in UserRole],
                       validators=[DataRequired()])
    is_active = BooleanField('Account Active')
    is_email_verified = BooleanField('Email Verified by Admin')
    new_password = PasswordField('New Password (leave blank to keep current)',
                                 validators=[Optional(),
                                             Length(min=8,
                                                    message="If changing, password must be at least 8 characters long.")])
    confirm_new_password = PasswordField('Confirm New Password',
                                         validators=[EqualTo('new_password', message="New passwords must match.")])
    submit = SubmitField('Update User Details')


# --- FORMS FOR TRADE LOGGING (Initial Simple Version) ---
# Sub-forms for entry and exit points
class EntryPointForm(FlaskForm):
    entry_time = TimeField('Entry Time (HH:MM NY)', validators=[DataRequired(message="Entry time required.")],
                           format='%H:%M')
    contracts = IntegerField('Contracts', validators=[DataRequired(message="Number of contracts required."),
                                                      NumberRange(min=1, message="Contracts must be at least 1.")])
    entry_price = FloatField('Entry Price', validators=[DataRequired(message="Entry price required.")])
    # No submit button in sub-form


class ExitPointForm(FlaskForm):
    exit_time = TimeField('Exit Time (HH:MM NY)', validators=[Optional()], format='%H:%M')
    contracts = IntegerField('Contracts', validators=[Optional(), NumberRange(min=1,
                                                                              message="If exiting, contracts must be at least 1.")])
    exit_price = FloatField('Exit Price', validators=[Optional()])
    # No submit button in sub-form


class TradeForm(FlaskForm):
    instrument_choices = [
        ('', '-- Select Instrument --'),
        ('NQ', 'NQ (Nasdaq 100)'), ('ES', 'ES (S&P 500)'), ('YM', 'YM (Dow Jones)'),
        ('MNQ', 'MNQ (Micro Nasdaq)'), ('MES', 'MES (Micro S&P)'), ('MYM', 'MYM (Micro Dow)'),
        ('Other', 'Other (Specify)')
    ]
    direction_choices = [('', '-- Select Direction --'), ('Long', 'Long'), ('Short', 'Short')]
    how_closed_choices = [
        ('', '-- Select How Closed --'),
        ('Manual', 'Closed Manually'),
        ('SL', 'Closed by Stop Loss'),
        ('TP', 'Closed by Take Profit'),
        ('Trailing SL', 'Closed by Trailing Stop Loss'),
        ('Time Exit', 'Exited by Time Rule'),
        ('Still Open', 'Still Open / Partially Exited')
    ]
    rating_choices = [('', '-- Rate 1-5 --')] + [(str(i), str(i)) for i in range(1, 6)]

    # --- Basic Trade Details ---
    instrument = SelectField('Instrument', choices=instrument_choices,
                             validators=[DataRequired(message="Please select an instrument.")])
    trade_date = DateField('Trade Date', validators=[DataRequired(message="Please select a trade date.")],
                           format='%Y-%m-%d', render_kw={"placeholder": "YYYY-MM-DD"})
    direction = SelectField('Direction', choices=direction_choices,
                            validators=[DataRequired(message="Please select trade direction.")])
    point_value = FloatField('Point Value ($)', validators=[DataRequired(message="Enter the dollar value per point.")],
                             description="e.g., NQ=20, ES=50, MNQ=2, MES=5")

    # --- Entry/Exit Points (Simplified for now - single entry/exit) ---
    # We will enhance this for multiple entries/exits with FieldList and JavaScript later
    entry_time_1 = TimeField('Entry 1 Time (HH:MM NY)', validators=[DataRequired(message="Entry time required.")],
                             format='%H:%M', render_kw={"placeholder": "HH:MM"})
    entry_contracts_1 = IntegerField('Entry 1 Contracts',
                                     validators=[DataRequired(message="Contracts required."), NumberRange(min=1)],
                                     render_kw={"placeholder": "e.g., 1"})
    entry_price_1 = FloatField('Entry 1 Price', validators=[DataRequired(message="Entry price required.")],
                               render_kw={"placeholder": "e.g., 15000.25"})

    exit_time_1 = TimeField('Exit 1 Time (HH:MM NY)', validators=[Optional()], format='%H:%M',
                            render_kw={"placeholder": "HH:MM"})
    exit_contracts_1 = IntegerField('Exit 1 Contracts', validators=[Optional(), NumberRange(min=1)],
                                    render_kw={"placeholder": "e.g., 1"})
    exit_price_1 = FloatField('Exit 1 Price', validators=[Optional()], render_kw={"placeholder": "e.g., 15010.50"})

    # --- Risk/Reward & Management ---
    initial_stop_loss = FloatField('Initial Stop Loss Price', validators=[Optional()])
    terminus_target = FloatField('Terminus Target Price (Final TP)', validators=[Optional()])
    is_dca = BooleanField('DCA Entry Strategy?')
    mae = FloatField('MAE (Points against you)', validators=[Optional()])
    mfe = FloatField('MFE (Points in your favor)', validators=[Optional()])

    # --- Model & Context ---
    trading_model_id = SelectField('Trading Model Used', coerce=int,
                                   validators=[InputRequired(message="Please select a trading model.")],
                                   choices=[(0, "-- Select Model --")])  # Choices populated in route
    entry_model_legacy = StringField('Legacy Entry Model (if any)', validators=[Optional(), Length(max=50)])

    # You would populate news_event_select choices from get_news_event_options() in the route
    news_event_select = SelectField('News Event (if any)', choices=[('', '-- None --')], validators=[Optional()])

    how_closed = SelectField('How Was Position Finalized?', choices=how_closed_choices, validators=[Optional()])

    # --- Psychological & Performance Ratings ---
    rules_rating = SelectField('Rules Rating', choices=rating_choices, coerce=int, validators=[Optional()])
    management_rating = SelectField('Management Rating', choices=rating_choices, coerce=int, validators=[Optional()])
    target_rating = SelectField('Target Rating', choices=rating_choices, coerce=int, validators=[Optional()])
    entry_rating = SelectField('Entry Rating', choices=rating_choices, coerce=int, validators=[Optional()])
    preparation_rating = SelectField('Preparation Rating', choices=rating_choices, coerce=int, validators=[Optional()])

    # --- Notes & Analysis ---
    trade_notes = TextAreaField('Trade Setup & Execution Notes', validators=[Optional()], render_kw={"rows": 3})
    psych_scored_highest = TextAreaField('Psych: Scored Highest & How to Sustain?', validators=[Optional()],
                                         render_kw={"rows": 2})
    psych_scored_lowest = TextAreaField('Psych: Scored Lowest & How to Improve?', validators=[Optional()],
                                        render_kw={"rows": 2})
    overall_analysis_notes = TextAreaField('Overall Trade Analysis', validators=[Optional()], render_kw={"rows": 3})
    trade_management_notes = TextAreaField('Trade Management Notes', validators=[Optional()], render_kw={"rows": 2})
    errors_notes = TextAreaField('Errors Noted', validators=[Optional()], render_kw={"rows": 2})
    improvements_notes = TextAreaField('Potential Improvements', validators=[Optional()], render_kw={"rows": 2})

    screenshot_link = StringField('Screenshot Link', validators=[Optional(), Length(max=255)])
    tags = StringField('Tags (comma-separated)', validators=[Optional(), Length(max=255)])

    submit = SubmitField('Log This Trade')

    def __init__(self, *args, **kwargs):
        super(TradeForm, self).__init__(*args, **kwargs)
        # Note: Dynamic choices for trading_model_id and news_event_select
        # should be set in the route that instantiates this form.
        # Example (in route):
        # form.trading_model_id.choices = [(0,"-- Select Model --")] + [(tm.id, tm.name) for tm in TradingModel.query.filter_by(user_id=current_user.id, is_active=True).order_by(TradingModel.name).all()]
        # form.news_event_select.choices = [('','-- None --')] + [(event, event) for event in get_news_event_options() if event != 'None']