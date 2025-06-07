from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (StringField, PasswordField, BooleanField, SubmitField, MultipleFileField,
                     TextAreaField, FloatField, SelectField, IntegerField, DateField,
                     TimeField, FormField, FieldList)
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, NumberRange, InputRequired
from app.models import UserRole  # Assuming UserRole is used elsewhere or for consistency


# Custom coerce function for optional integer select fields
def coerce_int_optional(value):
    if value == '':
        return None
    try:
        return int(value)
    except ValueError:
        return None


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
    submit = SubmitField('Save Profile Changes')


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=8,
                                                                                    message='Password must be at least 8 characters long.')])
    confirm_password = PasswordField('Confirm New Password',
                                     validators=[DataRequired(),
                                                 EqualTo('new_password', message='New passwords must match.')])
    submit = SubmitField('Update Password')


# --- File Upload Form (General Purpose) ---
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
                       choices=[(role.value, role.name.title()) for role in UserRole],
                       validators=[DataRequired()])
    is_active = BooleanField('Account Active', default=True)
    is_email_verified = BooleanField('Email Verified by Admin', default=False)
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


# --- FORMS FOR TRADE LOGGING ---

class EntryPointForm(FlaskForm):
    # Hidden field to track existing entry ID during edit
    id = IntegerField(validators=[Optional()])
    entry_time = TimeField('Time (HH:MM NY)', format='%H:%M', validators=[DataRequired(message="Entry time required.")],
                           render_kw={"placeholder": "HH:MM"})
    contracts = IntegerField('Contracts',
                             validators=[DataRequired(message="# Contracts required."), NumberRange(min=1)],
                             render_kw={"placeholder": "e.g., 1"})
    entry_price = FloatField('Price', validators=[DataRequired(message="Entry price required.")],
                             render_kw={"placeholder": "e.g., 15000.25"})


class ExitPointForm(FlaskForm):
    # Hidden field to track existing exit ID during edit
    id = IntegerField(validators=[Optional()])
    exit_time = TimeField('Time (HH:MM NY)', format='%H:%M', validators=[Optional()],
                          render_kw={"placeholder": "HH:MM"})
    contracts = IntegerField('Contracts', validators=[Optional(), NumberRange(min=1)],
                             render_kw={"placeholder": "e.g., 1"})
    exit_price = FloatField('Price', validators=[Optional()], render_kw={"placeholder": "e.g., 15010.50"})


class TradeForm(FlaskForm):
    instrument_choices = [
        ('', '-- Select Instrument --'), ('NQ', 'NQ (Nasdaq 100)'), ('ES', 'ES (S&P 500)'), ('YM', 'YM (Dow Jones)'),
        ('MNQ', 'MNQ (Micro Nasdaq)'), ('MES', 'MES (Micro S&P)'), ('MYM', 'MYM (Micro Dow)'),
        ('Other', 'Other (Specify)')
    ]
    direction_choices = [('', '-- Select Direction --'), ('Long', 'Long'), ('Short', 'Short')]
    how_closed_choices = [
        ('', '-- Select How Closed --'), ('Manual', 'Closed Manually'), ('SL', 'Closed by Stop Loss'),
        ('TP', 'Closed by Take Profit'), ('Trailing SL', 'Closed by Trailing Stop Loss'),
        ('Time Exit', 'Exited by Time Rule'), ('Still Open', 'Still Open / Partially Exited')
    ]
    rating_choices = [('', '-- Rate 1-5 --')] + [(str(i), str(i)) for i in range(1, 6)]

    # Using SIMPLE_TAG_CHOICES for single select as per recent request
    SIMPLE_TAG_CHOICES = [
        ('', '-- Select Tag --'),
        ('P12-1A', 'P12 Scenario 1A'), ('P12-1B', 'P12 Scenario 1B'), ('HOD_Reversal', 'HOD Reversal'),
        ('LOD_Bounce', 'LOD Bounce'), ('Snap_0930', '0930 Snap Model'),
        ('TrendDay_Bull', 'Trend Day (Bull)'), ('TrendDay_Bear', 'Trend Day (Bear)'),
        ('RangeBound', 'Range Bound'), ('HighVol', 'High Volatility'), ('LowVol', 'Low Volatility'),
        ('FOMC_Day', 'FOMC Day'), ('CPI_Day', 'CPI Day'), ('NFP_Day', 'NFP Day'),
        ('Other_News', 'Other News Impact'), ('FOMO_Entry', 'FOMO Entry'),
        ('Good_Patience', 'Good Patience'), ('Revenge_Trade', 'Revenge Trade'),
        ('OverConfidence', 'Over Confidence'), ('Lack_Confidence', 'Lack of Confidence'),
        ('Rule_Break', 'Rule Broken'), ('Asia_Session', 'Asia Session Trade'),
        ('London_Session', 'London Session Trade'), ('NY_AM_Session', 'NY AM Session Trade'),
        ('NY_PM_Session', 'NY PM Session Trade')
    ]

    instrument = SelectField('Instrument', choices=instrument_choices, validators=[DataRequired()])
    trade_date = DateField('Trade Date', validators=[DataRequired(message="Please select a trade date.")],
                           format='%Y-%m-%d', render_kw={"placeholder": "YYYY-MM-DD"})
    direction = SelectField('Direction', choices=direction_choices, validators=[DataRequired()])

    entries = FieldList(FormField(EntryPointForm), min_entries=1, label='Entry Points')
    exits = FieldList(FormField(ExitPointForm), min_entries=0, label='Exit Points')

    initial_stop_loss = FloatField('Stop Loss Price', validators=[Optional()], render_kw={"placeholder": "Price"})
    terminus_target = FloatField('Terminus Target Price', validators=[Optional()], render_kw={"placeholder": "Price"})
    is_dca = BooleanField('Check here if this trade is a DCA entry strategy')
    mae = FloatField('MAE (In Points)', validators=[Optional()], render_kw={"placeholder": "Points against"})
    mfe = FloatField('MFE (In Points)', validators=[Optional()], render_kw={"placeholder": "Points for"})

    trading_model_id = SelectField('Trading Model', coerce=int, validators=[InputRequired(message="Select model")],
                                   choices=[(0, "-- Select Model --")])
    news_event_select = SelectField('News Event', choices=[('', '-- None --')], validators=[Optional()])
    how_closed = SelectField('How Closed?', choices=how_closed_choices, validators=[Optional()])

    rules_rating = SelectField('Rule Following', choices=rating_choices, coerce=coerce_int_optional, validators=[Optional()])
    management_rating = SelectField('Trade Management', choices=rating_choices, coerce=coerce_int_optional,
                                    validators=[Optional()])
    target_rating = SelectField('Target Placement', choices=rating_choices, coerce=coerce_int_optional, validators=[Optional()])
    entry_rating = SelectField('Entry & Execution', choices=rating_choices, coerce=coerce_int_optional, validators=[Optional()])
    preparation_rating = SelectField('Trade Preparation', choices=rating_choices, coerce=coerce_int_optional,
                                     validators=[Optional()])

    trade_notes = TextAreaField('Pre-Entry Analysis', validators=[Optional()],
                                render_kw={"rows": 4, "placeholder": "Trade context, Consider P12 analysis, 4-steps process, etc..."})
    psych_scored_highest = TextAreaField('Where did I score highest and how will I sustain this?', validators=[Optional()], render_kw={"rows": 6})
    psych_scored_lowest = TextAreaField('Where did I score lowest and how will I improve this?', validators=[Optional()], render_kw={"rows": 6})
    overall_analysis_notes = TextAreaField('Post-Trade Analysis', validators=[Optional()],
                                           render_kw={"rows": 3, "placeholder": "Post-trade reflection..."})
    trade_management_notes = TextAreaField('Trade Management Notes', validators=[Optional()],
                                           render_kw={"rows": 2, "placeholder": "Adjustments to SL/TP, partials..."})
    errors_notes = TextAreaField('Errors Noted', validators=[Optional()], render_kw={"rows": 2})
    improvements_notes = TextAreaField('Improvements Noted', validators=[Optional()], render_kw={"rows": 2})

    trade_images = MultipleFileField('Upload Images', validators=[Optional(), FileAllowed(
        ['jpg', 'png', 'jpeg', 'gif'], 'Images only!')])
    screenshot_link = StringField('TradingView Screenshot Link', validators=[Optional(), Length(max=255)],
                                  render_kw={"placeholder": "http://..."})
    tags = SelectField('Tags', choices=SIMPLE_TAG_CHOICES, validators=[Optional()])
    submit = SubmitField('Save Trade')

    def __init__(self, *args, **kwargs):
        super(TradeForm, self).__init__(*args, **kwargs)
        # Dynamic choices for trading_model_id and news_event_select are set in the route


# Form for filtering trades list
class TradeFilterForm(FlaskForm):
    start_date = DateField('Start Date', format='%Y-%m-%d', validators=[Optional()])
    end_date = DateField('End Date', format='%Y-%m-%d', validators=[Optional()])
    instrument = SelectField('Instrument', choices=[('', 'All Instruments')] + TradeForm.instrument_choices[1:],
                             validators=[Optional()])
    direction = SelectField('Direction', choices=[('', 'All Directions')] + TradeForm.direction_choices[1:],
                            validators=[Optional()])
    trading_model_id = SelectField('Trading Model', coerce=int, choices=[(0, 'All Models')],
                                   validators=[Optional()])  # Choices populated in route
    tags = SelectField('Tag', choices=[('', 'All Tags')] + TradeForm.SIMPLE_TAG_CHOICES[1:],
                       validators=[Optional()])  # For single tag filter
    # You can add more fields like P&L range, R-value range, etc.
    submit = SubmitField('Filter Trades')
    clear = SubmitField('Clear Filters', render_kw={'formnovalidate': True, 'class': 'btn btn-outline-secondary'})


# Form for importing trades
class ImportTradesForm(FlaskForm):
    csv_file = FileField('CSV File to Import',
                         validators=[DataRequired(), FileAllowed(['csv'], 'Only CSV files are allowed!')])
    submit = SubmitField('Upload and Import Trades')

class DailyJournalForm(FlaskForm):
    journal_date = DateField('Journal Date', format='%Y-%m-%d', validators=[DataRequired()])

    # Part 1: Pre-market Preparation
    key_events_today = TextAreaField('Key Economic Events/News Today', validators=[Optional()], render_kw={"rows": 2,
                                                                                                           "placeholder": "List major news, speeches, data releases..."})
    key_tasks_today = TextAreaField('Key Personal Tasks for Today', validators=[Optional()], render_kw={"rows": 2,
                                                                                                        "placeholder": "Important non-trading tasks impacting your day..."})

    on_my_mind = TextAreaField('On My Mind (from yesterday / for today)', validators=[Optional()],
                               render_kw={"rows": 2, "placeholder": "Lingering thoughts, reflections, expectations..."})
    important_focus_today = TextAreaField('Most Important Things to Focus On In My Trading Today',
                                          validators=[Optional()], render_kw={"rows": 2,
                                                                              "placeholder": "Key principles, rules, or behaviors..."})

    mental_rating_choices = [('', '-- Rate --')] + [(str(i), str(i)) for i in range(1, 6)]  # 1-5
    mental_feeling_rating = SelectField('Mental Feeling (Overall Mood)', choices=mental_rating_choices,
                                        coerce=coerce_int_optional, validators=[Optional()])
    mental_mind_rating = SelectField('Mental Mind (Clarity/Focus)', choices=mental_rating_choices,
                                     coerce=coerce_int_optional, validators=[Optional()])
    mental_energy_rating = SelectField('Mental Energy (Physical)', choices=mental_rating_choices,
                                       coerce=coerce_int_optional, validators=[Optional()])
    mental_motivation_rating = SelectField('Mental Motivation (Drive)', choices=mental_rating_choices,
                                           coerce=coerce_int_optional, validators=[Optional()])

    # Part 2: Pre-market Analysis
    p12_scenario_choices = [("None", "-- Select P12 --")] + [(f"{i}{ab}", f"P12 {i}{ab}") for i in range(1, 6) for ab in
                                                             ["A", "B"]]  # From __init__.py constants
    p12_scenario_selected = SelectField('P12 Scenario Selected', choices=p12_scenario_choices, validators=[Optional()])
    p12_expected_outcomes = TextAreaField('P12 Expected Outcomes/Notes', validators=[Optional()], render_kw={"rows": 3})

    session_direction_choices = [("None", "N/A")] + [(d, d) for d in ["Long", "Short"]]
    session_status_choices = [("None", "N/A")] + [(s, s) for s in
                                                  ["True", "False"]]  # True for normal, False for retrace
    session_model_choices = [("None", "N/A")] + [(m, m) for m in ["Valid", "Broken"]]  # For OU Midline

    # Asia Session
    asia_direction = SelectField('ASN Direction', choices=session_direction_choices, validators=[Optional()])
    asia_session_status = SelectField('ASN Session Status', choices=session_status_choices, validators=[Optional()])
    asia_model_status = SelectField('ASN Model (OU) Status', choices=session_model_choices, validators=[Optional()])
    asia_actual_range_points = FloatField('ASN Actual Range (Points)', validators=[Optional()])
    asia_median_range_input_note = TextAreaField('ASN Median Range Notes/Input', validators=[Optional()],
                                                 render_kw={"rows": 2,
                                                            "placeholder": "e.g., manual input for median range expectation"})

    # London Session
    london_direction = SelectField('LDN Direction', choices=session_direction_choices, validators=[Optional()])
    london_session_status = SelectField('LDN Session Status', choices=session_status_choices, validators=[Optional()])
    london_model_status = SelectField('LDN Model (OU) Status', choices=session_model_choices, validators=[Optional()])
    london_actual_range_points = FloatField('LDN Actual Range (Points)', validators=[Optional()])
    london_median_range_input_note = TextAreaField('LDN Median Range Notes/Input', validators=[Optional()],
                                                   render_kw={"rows": 2})

    # NY1 Session
    ny1_direction = SelectField('NY1 Direction', choices=session_direction_choices, validators=[Optional()])
    ny1_session_status = SelectField('NY1 Session Status', choices=session_status_choices, validators=[Optional()])
    ny1_model_status = SelectField('NY1 Model (OU) Status', choices=session_model_choices, validators=[Optional()])
    ny1_actual_range_points = FloatField('NY1 Actual Range (Points)', validators=[Optional()])
    ny1_median_range_input_note = TextAreaField('NY1 Median Range Notes/Input', validators=[Optional()],
                                                render_kw={"rows": 2})

    # NY1 HOD/LOD Projections (wg_ fields) - Example for one set (Long/True HOD)
    wg_ny1_lt_notes = TextAreaField('NY1 Long/True Projection Notes', validators=[Optional()], render_kw={"rows": 2})
    wg_ny1_lt_hod_pct_l = FloatField('NY1 L/T HOD Low %', validators=[Optional()])
    wg_ny1_lt_hod_pct_h = FloatField('NY1 L/T HOD High %', validators=[Optional()])
    wg_ny1_lt_hod_ts = TimeField('NY1 L/T HOD Time Start', format='%H:%M', validators=[Optional()])
    wg_ny1_lt_hod_te = TimeField('NY1 L/T HOD Time End', format='%H:%M', validators=[Optional()])

    wg_ny1_lf_notes = TextAreaField('NY1 Long/True Projection Notes', validators=[Optional()], render_kw={"rows": 2})
    wg_ny1_lf_hod_pct_l = FloatField('NY1 L/T HOD Low %', validators=[Optional()])
    wg_ny1_lf_hod_pct_h = FloatField('NY1 L/T HOD High %', validators=[Optional()])
    wg_ny1_lf_hod_ts = TimeField('NY1 L/T HOD Time Start', format='%H:%M', validators=[Optional()])
    wg_ny1_lf_hod_te = TimeField('NY1 L/T HOD Time End', format='%H:%M', validators=[Optional()])

    wg_ny1_st_notes = TextAreaField('NY1 Long/True Projection Notes', validators=[Optional()], render_kw={"rows": 2})
    wg_ny1_st_hod_pct_l = FloatField('NY1 L/T HOD Low %', validators=[Optional()])
    wg_ny1_st_hod_pct_h = FloatField('NY1 L/T HOD High %', validators=[Optional()])
    wg_ny1_st_hod_ts = TimeField('NY1 L/T HOD Time Start', format='%H:%M', validators=[Optional()])
    wg_ny1_st_hod_te = TimeField('NY1 L/T HOD Time End', format='%H:%M', validators=[Optional()])

    wg_ny1_sf_notes = TextAreaField('NY1 Long/True Projection Notes', validators=[Optional()], render_kw={"rows": 2})
    wg_ny1_sf_hod_pct_l = FloatField('NY1 L/T HOD Low %', validators=[Optional()])
    wg_ny1_sf_hod_pct_h = FloatField('NY1 L/T HOD High %', validators=[Optional()])
    wg_ny1_sf_hod_ts = TimeField('NY1 L/T HOD Time Sfart', format='%H:%M', validators=[Optional()])
    wg_ny1_sf_hod_te = TimeField('NY1 L/T HOD Time End', format='%H:%M', validators=[Optional()])

    wg_ny1_lt_notes = TextAreaField('NY1 Long/True Projection Notes', validators=[Optional()], render_kw={"rows": 2})
    wg_ny1_lt_lod_pct_l = FloatField('NY1 L/T LOD Low %', validators=[Optional()])
    wg_ny1_lt_lod_pct_h = FloatField('NY1 L/T LOD High %', validators=[Optional()])
    wg_ny1_lt_lod_ts = TimeField('NY1 L/T LOD Time Start', format='%H:%M', validators=[Optional()])
    wg_ny1_lt_lod_te = TimeField('NY1 L/T LOD Time End', format='%H:%M', validators=[Optional()])

    wg_ny1_lf_notes = TextAreaField('NY1 Long/True Projection Notes', validators=[Optional()], render_kw={"rows": 2})
    wg_ny1_lf_lod_pct_l = FloatField('NY1 L/T LOD Low %', validators=[Optional()])
    wg_ny1_lf_lod_pct_h = FloatField('NY1 L/T LOD High %', validators=[Optional()])
    wg_ny1_lf_lod_ts = TimeField('NY1 L/T LOD Time Start', format='%H:%M', validators=[Optional()])
    wg_ny1_lf_lod_te = TimeField('NY1 L/T LOD Time End', format='%H:%M', validators=[Optional()])

    wg_ny1_st_notes = TextAreaField('NY1 Long/True Projection Notes', validators=[Optional()], render_kw={"rows": 2})
    wg_ny1_st_lod_pct_l = FloatField('NY1 L/T LOD Low %', validators=[Optional()])
    wg_ny1_st_lod_pct_h = FloatField('NY1 L/T LOD High %', validators=[Optional()])
    wg_ny1_st_lod_ts = TimeField('NY1 L/T LOD Time Start', format='%H:%M', validators=[Optional()])
    wg_ny1_st_lod_te = TimeField('NY1 L/T LOD Time End', format='%H:%M', validators=[Optional()])

    wg_ny1_sf_notes = TextAreaField('NY1 Long/True Projection Notes', validators=[Optional()], render_kw={"rows": 2})
    wg_ny1_sf_lod_pct_l = FloatField('NY1 L/T LOD Low %', validators=[Optional()])
    wg_ny1_sf_lod_pct_h = FloatField('NY1 L/T LOD High %', validators=[Optional()])
    wg_ny1_sf_lod_ts = TimeField('NY1 L/T LOD Time Sfart', format='%H:%M', validators=[Optional()])
    wg_ny1_sf_lod_te = TimeField('NY1 L/T LOD Time End', format='%H:%M', validators=[Optional()])

    wg_ny2_lt_notes = TextAreaField('NY2 Long/True Projection Notes', validators=[Optional()], render_kw={"rows": 2})
    wg_ny2_lt_hod_pct_l = FloatField('NY2 L/T HOD Low %', validators=[Optional()])
    wg_ny2_lt_hod_pct_h = FloatField('NY2 L/T HOD High %', validators=[Optional()])
    wg_ny2_lt_hod_ts = TimeField('NY2 L/T HOD Time Start', format='%H:%M', validators=[Optional()])
    wg_ny2_lt_hod_te = TimeField('NY2 L/T HOD Time End', format='%H:%M', validators=[Optional()])

    wg_ny2_lf_notes = TextAreaField('NY2 Long/True Projection Notes', validators=[Optional()], render_kw={"rows": 2})
    wg_ny2_lf_hod_pct_l = FloatField('NY2 L/T HOD Low %', validators=[Optional()])
    wg_ny2_lf_hod_pct_h = FloatField('NY2 L/T HOD High %', validators=[Optional()])
    wg_ny2_lf_hod_ts = TimeField('NY2 L/T HOD Time Start', format='%H:%M', validators=[Optional()])
    wg_ny2_lf_hod_te = TimeField('NY2 L/T HOD Time End', format='%H:%M', validators=[Optional()])

    wg_ny2_st_notes = TextAreaField('NY2 Long/True Projection Notes', validators=[Optional()], render_kw={"rows": 2})
    wg_ny2_st_hod_pct_l = FloatField('NY2 L/T HOD Low %', validators=[Optional()])
    wg_ny2_st_hod_pct_h = FloatField('NY2 L/T HOD High %', validators=[Optional()])
    wg_ny2_st_hod_ts = TimeField('NY2 L/T HOD Time Start', format='%H:%M', validators=[Optional()])
    wg_ny2_st_hod_te = TimeField('NY2 L/T HOD Time End', format='%H:%M', validators=[Optional()])

    wg_ny2_sf_notes = TextAreaField('NY2 Long/True Projection Notes', validators=[Optional()], render_kw={"rows": 2})
    wg_ny2_sf_hod_pct_l = FloatField('NY2 L/T HOD Low %', validators=[Optional()])
    wg_ny2_sf_hod_pct_h = FloatField('NY2 L/T HOD High %', validators=[Optional()])
    wg_ny2_sf_hod_ts = TimeField('NY2 L/T HOD Time Sfart', format='%H:%M', validators=[Optional()])
    wg_ny2_sf_hod_te = TimeField('NY2 L/T HOD Time End', format='%H:%M', validators=[Optional()])

    wg_ny2_lt_notes = TextAreaField('NY2 Long/True Projection Notes', validators=[Optional()], render_kw={"rows": 2})
    wg_ny2_lt_lod_pct_l = FloatField('NY2 L/T LOD Low %', validators=[Optional()])
    wg_ny2_lt_lod_pct_h = FloatField('NY2 L/T LOD High %', validators=[Optional()])
    wg_ny2_lt_lod_ts = TimeField('NY2 L/T LOD Time Start', format='%H:%M', validators=[Optional()])
    wg_ny2_lt_lod_te = TimeField('NY2 L/T LOD Time End', format='%H:%M', validators=[Optional()])

    wg_ny2_lf_notes = TextAreaField('NY2 Long/True Projection Notes', validators=[Optional()], render_kw={"rows": 2})
    wg_ny2_lf_lod_pct_l = FloatField('NY2 L/T LOD Low %', validators=[Optional()])
    wg_ny2_lf_lod_pct_h = FloatField('NY2 L/T LOD High %', validators=[Optional()])
    wg_ny2_lf_lod_ts = TimeField('NY2 L/T LOD Time Start', format='%H:%M', validators=[Optional()])
    wg_ny2_lf_lod_te = TimeField('NY2 L/T LOD Time End', format='%H:%M', validators=[Optional()])

    wg_ny2_st_notes = TextAreaField('NY2 Long/True Projection Notes', validators=[Optional()], render_kw={"rows": 2})
    wg_ny2_st_lod_pct_l = FloatField('NY2 L/T LOD Low %', validators=[Optional()])
    wg_ny2_st_lod_pct_h = FloatField('NY2 L/T LOD High %', validators=[Optional()])
    wg_ny2_st_lod_ts = TimeField('NY2 L/T LOD Time Start', format='%H:%M', validators=[Optional()])
    wg_ny2_st_lod_te = TimeField('NY2 L/T LOD Time End', format='%H:%M', validators=[Optional()])

    wg_ny2_sf_notes = TextAreaField('NY2 Long/True Projection Notes', validators=[Optional()], render_kw={"rows": 2})
    wg_ny2_sf_lod_pct_l = FloatField('NY2 L/T LOD Low %', validators=[Optional()])
    wg_ny2_sf_lod_pct_h = FloatField('NY2 L/T LOD High %', validators=[Optional()])
    wg_ny2_sf_lod_ts = TimeField('NY2 L/T LOD Time Sfart', format='%H:%M', validators=[Optional()])
    wg_ny2_sf_lod_te = TimeField('NY2 L/T LOD Time End', format='%H:%M', validators=[Optional()])

    # NY2 Session
    ny2_direction = SelectField('NY2 Direction', choices=session_direction_choices, validators=[Optional()])
    ny2_session_status = SelectField('NY2 Session Status', choices=session_status_choices, validators=[Optional()])
    ny2_model_status = SelectField('NY2 Model (OU) Status', choices=session_model_choices, validators=[Optional()])
    ny2_actual_range_points = FloatField('NY2 Actual Range (Points)', validators=[Optional()])
    ny2_median_range_input_note = TextAreaField('NY2 Median Range Notes/Input', validators=[Optional()],
                                                render_kw={"rows": 2})

    # Step 3: Realistic Expectance
    adr_10_day_median_range_value = FloatField('10-Day Median Range (ADR/MDR Value)', validators=[Optional()])
    todays_total_range_points = FloatField("Today's Total Range (Points)", validators=[Optional()])
    realistic_expectance_notes = TextAreaField('Step 3: Realistic Expectance Notes (RTE for images)',
                                               validators=[Optional()], render_kw={"rows": 4,
                                                                                   "placeholder": "Compare current range to historical, extension analysis..."})

    # Step 4: Engagement Structure
    engagement_structure_notes = TextAreaField('Step 4: Engagement Structure Notes (RTE for images)',
                                               validators=[Optional()], render_kw={"rows": 4,
                                                                                   "placeholder": "Highest statistical structure, entry types..."})

    key_levels_notes = TextAreaField('Key Levels Identified (Pre-Market)', validators=[Optional()],
                                     render_kw={"rows": 3, "placeholder": "Support, Resistance, Pivots, Fibs..."})
    pre_market_news_notes = TextAreaField('Pre-Market News Impact Analysis', validators=[Optional()],
                                          render_kw={"rows": 3, "placeholder": "How might today's news affect setups?"})

    pre_market_screenshots = MultipleFileField('Pre-Market Analysis Screenshots', validators=[Optional(), FileAllowed(
        ['jpg', 'png', 'jpeg', 'gif'], 'Images only!')])

    # Part 4: Post Market Analysis
    market_observations = TextAreaField('Post-Market Analysis / Market Observations (RTE for images)',
                                        validators=[Optional()], render_kw={"rows": 5,
                                                                            "placeholder": "How did the market actually behave? Key observations..."})
    self_observations = TextAreaField('Self-Observations / Re-engineering Notes (RTE for images)',
                                      validators=[Optional()], render_kw={"rows": 5,
                                                                          "placeholder": "Reflection on personal performance, decision-making..."})
    eod_chart_screenshots = MultipleFileField('End-of-Day Chart Screenshots', validators=[Optional(), FileAllowed(
        ['jpg', 'png', 'jpeg', 'gif'], 'Images only!')])

    # Part 5: Daily Review and Reflection
    did_well_today = TextAreaField('What I Did Well Today (RTE for images)', validators=[Optional()],
                                   render_kw={"rows": 3})
    did_not_go_well_today = TextAreaField('What Did Not Go So Well Today (RTE for images)', validators=[Optional()],
                                          render_kw={"rows": 3})
    learned_today = TextAreaField('Something I Learned About the Market or Myself Today (RTE for images)',
                                  validators=[Optional()], render_kw={"rows": 3})
    improve_action_next_day = TextAreaField('Action(s) I Can Take to Improve My Trading Performance Going Forward',
                                            validators=[Optional()], render_kw={"rows": 3})

    # Daily Psych Review scores (will be filled from model if editing)
    review_psych_discipline_rating = SelectField('Psych Review: Discipline', choices=mental_rating_choices,
                                                 coerce=coerce_int_optional, validators=[Optional()])
    review_psych_motivation_rating = SelectField('Psych Review: Motivation', choices=mental_rating_choices,
                                                 coerce=coerce_int_optional, validators=[Optional()])
    review_psych_focus_rating = SelectField('Psych Review: Focus', choices=mental_rating_choices,
                                            coerce=coerce_int_optional, validators=[Optional()])
    review_psych_mastery_rating = SelectField('Psych Review: Mastery', choices=mental_rating_choices,
                                              coerce=coerce_int_optional, validators=[Optional()])
    review_psych_composure_rating = SelectField('Psych Review: Composure', choices=mental_rating_choices,
                                                coerce=coerce_int_optional, validators=[Optional()])
    review_psych_resilience_rating = SelectField('Psych Review: Resilience', choices=mental_rating_choices,
                                                 coerce=coerce_int_optional, validators=[Optional()])
    review_psych_mind_rating = SelectField('Psych Review: Mind Clarity', choices=mental_rating_choices,
                                           coerce=coerce_int_optional, validators=[Optional()])
    review_psych_energy_rating = SelectField('Psych Review: Physical Energy', choices=mental_rating_choices,
                                             coerce=coerce_int_optional, validators=[Optional()])

    submit = SubmitField('Save Daily Journal')