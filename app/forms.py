from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed  # Used for profile_picture and new trade_images
from wtforms import (StringField, PasswordField, BooleanField, SubmitField,
                     MultipleFileField,  # Added MultipleFileField
                     TextAreaField, FloatField, SelectField, IntegerField, DateField,
                     TimeField, FormField, FieldList)
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, NumberRange, InputRequired
from app.models import UserRole


# Custom coerce function for optional integer select fields
def coerce_int_optional(value):
    if value == '':
        return None
    try:
        return int(value)
    except ValueError:
        return None


# --- Auth, User, FileUpload, TradingModel, Admin forms remain the same ---
# For brevity, I'll skip re-listing them here, but assume they are present
# as in your original smitty1021/combined_trading_journal/Combined_Trading_Journal-0f4f944ecae8022b68b0343942d1cb40d73402a0/app/forms.py file.

class LoginForm(FlaskForm):  # ... (as before)
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=80)],
                           render_kw={"placeholder": "Enter your username"})
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)],
                             render_kw={"placeholder": "Enter your password"})
    remember = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):  # ... (as before)
    username = StringField('Username', validators=[DataRequired(message="Username is required."), Length(min=3, max=25,
                                                                                                         message="Username must be between 3 and 25 characters.")])
    email = StringField('Email', validators=[DataRequired(message="Email is required."),
                                             Email(message="Please enter a valid email address.")])
    password = PasswordField('Password', validators=[DataRequired(message="Password is required."), Length(min=8,
                                                                                                           message="Password must be at least 8 characters long.")])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(message="Please confirm your password."),
                                                 EqualTo('password', message="Passwords must match.")])
    submit = SubmitField('Register')


class ResendVerificationForm(FlaskForm):  # ... (as before)
    email = StringField('Email', validators=[DataRequired(message="Email is required."),
                                             Email(message="Please enter a valid email address.")],
                        render_kw={"placeholder": "Enter your registered email address"})
    submit = SubmitField('Resend Verification Email')


class RequestPasswordResetForm(FlaskForm):  # ... (as before)
    email = StringField('Email', validators=[DataRequired(message="Email is required."),
                                             Email(message="Please enter a valid email address.")],
                        render_kw={"placeholder": "Enter your account's email address"})
    submit = SubmitField('Request Password Reset')


class ResetPasswordForm(FlaskForm):  # ... (as before)
    password = PasswordField('New Password', validators=[DataRequired(message="Password is required."), Length(min=8,
                                                                                                               message="Password must be at least 8 characters long.")])
    confirm_password = PasswordField('Confirm New Password',
                                     validators=[DataRequired(message="Please confirm your new password."),
                                                 EqualTo('password', message="Passwords must match.")])
    submit = SubmitField('Reset Password')


class ProfileForm(FlaskForm):  # ... (as before)
    name = StringField('Full Name', validators=[Optional(), Length(max=100)])
    email = StringField('Email Address',
                        validators=[DataRequired(), Email(message="Invalid email address."), Length(max=120)])
    bio = TextAreaField('About Me (Optional)', validators=[Optional(), Length(max=500)])
    profile_picture = FileField('Update Profile Picture', validators=[Optional(),
                                                                      FileAllowed(['jpg', 'png', 'jpeg', 'gif'],
                                                                                  'Images only! (jpg, jpeg, png, gif)')])
    submit = SubmitField('Save Profile Changes')


class ChangePasswordForm(FlaskForm):  # ... (as before)
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=8,
                                                                                    message='Password must be at least 8 characters long.')])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password',
                                                                                                 message='New passwords must match.')])
    submit = SubmitField('Update Password')


class FileUploadForm(FlaskForm):  # ... (as before) General file upload
    file = FileField('Select File', validators=[DataRequired(), FileAllowed(
        ['pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx', 'xls', 'xlsx', 'txt', 'csv'],
        'Allowed file types: pdf, png, jpg, jpeg, doc, docx, xls, xlsx, txt, csv')])
    description = TextAreaField('Description (Optional)', validators=[Optional(), Length(max=500)])
    is_public = BooleanField('Make Public', default=False)
    submit = SubmitField('Upload File')


class TradingModelForm(FlaskForm):  # ... (as before)
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


class AdminCreateUserForm(FlaskForm):  # ... (as before)
    username = StringField('Username', validators=[DataRequired(message="Username is required."), Length(min=3, max=25,
                                                                                                         message="Username must be between 3 and 25 characters.")])
    email = StringField('Email', validators=[DataRequired(message="Email is required."),
                                             Email(message="Please enter a valid email address.")])
    name = StringField('Full Name (Optional)', validators=[Optional(), Length(max=100)])
    password = PasswordField('Password', validators=[DataRequired(message="Password is required."), Length(min=8,
                                                                                                           message="Password must be at least 8 characters long.")])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(message="Please confirm your password."),
                                                 EqualTo('password', message="Passwords must match.")])
    role = SelectField('Role', choices=[(role.value, role.name.title()) for role in UserRole],
                       validators=[DataRequired()])
    is_active = BooleanField('Account Active', default=True)
    is_email_verified = BooleanField('Email Verified by Admin', default=False)
    submit = SubmitField('Create User')


class AdminEditUserForm(FlaskForm):  # ... (as before)
    username = StringField('Username', validators=[DataRequired(message="Username is required."), Length(min=3, max=25,
                                                                                                         message="Username must be between 3 and 25 characters.")])
    email = StringField('Email', validators=[DataRequired(message="Email is required."),
                                             Email(message="Please enter a valid email address.")])
    name = StringField('Full Name (Optional)', validators=[Optional(), Length(max=100)])
    role = SelectField('Role', choices=[(role.value, role.name.title()) for role in UserRole],
                       validators=[DataRequired()])
    is_active = BooleanField('Account Active')
    is_email_verified = BooleanField('Email Verified by Admin')
    new_password = PasswordField('New Password (leave blank to keep current)', validators=[Optional(), Length(min=8,
                                                                                                              message="If changing, password must be at least 8 characters long.")])
    confirm_new_password = PasswordField('Confirm New Password',
                                         validators=[EqualTo('new_password', message="New passwords must match.")])
    submit = SubmitField('Update User Details')


# --- FORMS FOR TRADE LOGGING ---

class EntryPointForm(FlaskForm):
    entry_time = TimeField('Time (HH:MM NY)', format='%H:%M', validators=[DataRequired(message="Entry time required.")],
                           render_kw={"placeholder": "HH:MM"})
    contracts = IntegerField('Contracts',
                             validators=[DataRequired(message="# Contracts required."), NumberRange(min=1)],
                             render_kw={"placeholder": "e.g., 1"})
    entry_price = FloatField('Price', validators=[DataRequired(message="Entry price required.")],
                             render_kw={"placeholder": "e.g., 15000.25"})


class ExitPointForm(FlaskForm):
    exit_time = TimeField('Time (HH:MM NY)', format='%H:%M', validators=[Optional()],
                          render_kw={"placeholder": "HH:MM"})
    contracts = IntegerField('Contracts', validators=[Optional(), NumberRange(min=1)],
                             render_kw={"placeholder": "e.g., 1"})
    exit_price = FloatField('Price', validators=[Optional()], render_kw={"placeholder": "e.g., 15010.50"})


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
        ('Manual', 'Closed Manually'), ('SL', 'Closed by Stop Loss'), ('TP', 'Closed by Take Profit'),
        ('Trailing SL', 'Closed by Trailing Stop Loss'), ('Time Exit', 'Exited by Time Rule'),
        ('Still Open', 'Still Open / Partially Exited')
    ]
    rating_choices = [('', '-- Rate 1-5 --')] + [(str(i), str(i)) for i in range(1, 6)]

    SIMPLE_TAG_CHOICES = [
        ('', '-- Select Tag --'),
        ('P12-1A', 'P12 Scenario 1A'), ('P12-1B', 'P12 Scenario 1B'), ('HOD_Reversal', 'HOD Reversal'),
        ('TrendDay_Bull', 'Trend Day (Bull)'), ('RangeBound', 'Range Bound'), ('FOMC_Day', 'FOMC Day'),
        ('FOMO_Entry', 'FOMO Entry'), ('Good_Patience', 'Good Patience'), ('Rule_Break', 'Rule Broken'),
        ('NY_AM_Session', 'NY AM Session Trade')
    ]  # Simplified list for single SelectField

    instrument = SelectField('Instrument', choices=instrument_choices,
                             validators=[DataRequired(message="Please select an instrument.")])
    trade_date = DateField('Trade Date', validators=[DataRequired(message="Please select a trade date.")],
                           format='%Y-%m-%d', render_kw={"placeholder": "YYYY-MM-DD"})
    direction = SelectField('Direction', choices=direction_choices,
                            validators=[DataRequired(message="Please select trade direction.")])

    entries = FieldList(FormField(EntryPointForm), min_entries=1, label='Entry Points')
    exits = FieldList(FormField(ExitPointForm), min_entries=0, label='Exit Points')

    initial_stop_loss = FloatField('Initial Stop Loss Price', validators=[Optional()],
                                   render_kw={"placeholder": "Price level"})
    terminus_target = FloatField('Terminus Target Price (Final TP)', validators=[Optional()],
                                 render_kw={"placeholder": "Final TP price level"})
    is_dca = BooleanField('DCA Entry Strategy?')
    mae = FloatField('MAE (Points against you)', validators=[Optional()],
                     render_kw={"placeholder": "Max points against"})
    mfe = FloatField('MFE (Points in your favor)', validators=[Optional()], render_kw={"placeholder": "Max points for"})

    trading_model_id = SelectField('Trading Model Used', coerce=int,
                                   validators=[InputRequired(message="Please select a trading model.")],
                                   choices=[(0, "-- Select Model --")])
    news_event_select = SelectField('News Event (if any)', choices=[('', '-- None --')], validators=[Optional()])
    how_closed = SelectField('How Was Position Finalized?', choices=how_closed_choices, validators=[Optional()])

    rules_rating = SelectField('Rules Rating', choices=rating_choices, coerce=coerce_int_optional,
                               validators=[Optional()])
    management_rating = SelectField('Management Rating', choices=rating_choices, coerce=coerce_int_optional,
                                    validators=[Optional()])
    target_rating = SelectField('Target Rating', choices=rating_choices, coerce=coerce_int_optional,
                                validators=[Optional()])
    entry_rating = SelectField('Entry Rating', choices=rating_choices, coerce=coerce_int_optional,
                               validators=[Optional()])
    preparation_rating = SelectField('Preparation Rating', choices=rating_choices, coerce=coerce_int_optional,
                                     validators=[Optional()])

    trade_notes = TextAreaField('Trade Setup & Execution Notes', validators=[Optional()],
                                render_kw={"rows": 3, "placeholder": "Trade context, P12, 4-steps, etc."})
    psych_scored_highest = TextAreaField('Psych: Scored Highest & How to Sustain?', validators=[Optional()],
                                         render_kw={"rows": 2})
    psych_scored_lowest = TextAreaField('Psych: Scored Lowest & How to Improve?', validators=[Optional()],
                                        render_kw={"rows": 2})
    overall_analysis_notes = TextAreaField('Overall Trade Analysis', validators=[Optional()],
                                           render_kw={"rows": 3, "placeholder": "Post-trade reflection..."})
    trade_management_notes = TextAreaField('Trade Management Notes', validators=[Optional()],
                                           render_kw={"rows": 2, "placeholder": "Adjustments to SL/TP, partials..."})
    errors_notes = TextAreaField('Errors Noted', validators=[Optional()], render_kw={"rows": 2})
    improvements_notes = TextAreaField('Potential Improvements', validators=[Optional()], render_kw={"rows": 2})

    # ADDED: Field for trade-specific image uploads
    trade_images = MultipleFileField('Upload Screenshots/Images (Optional)',
                                     validators=[Optional(),
                                                 FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Images only!')])

    screenshot_link = StringField('External Screenshot Link (Optional)', validators=[Optional(), Length(max=255)],
                                  render_kw={"placeholder": "https://www.tradingview.com/chart/..."})

    tags = SelectField('Tag (Optional)', choices=SIMPLE_TAG_CHOICES,
                       validators=[Optional()])  # Kept as single select as per last request

    submit = SubmitField('Log This Trade')

    def __init__(self, *args, **kwargs):
        super(TradeForm, self).__init__(*args, **kwargs)