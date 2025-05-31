from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, current_app)
from flask_login import login_required, current_user
from datetime import date as py_date, time as py_time, datetime as py_datetime

from app import db
from app.models import Trade, EntryPoint, ExitPoint, TradingModel, NewsEventItem
from app.forms import TradeForm # Assuming EntryPointForm & ExitPointForm are not directly used here yet
from app.utils import (_parse_form_float, _parse_form_int, _parse_form_time,
                       get_news_event_options, record_activity) # Ensure these are in utils

trades_bp = Blueprint('trades', __name__,
                      template_folder='../templates/trades', # We'll create this folder
                      url_prefix='/trades')

def populate_trade_form_choices(form):
    """Helper function to populate dynamic choices for the TradeForm."""
    # Populate Trading Models
    form.trading_model_id.choices = [(0, '-- Select Model --')] + \
                                    [(tm.id, tm.name) for tm in TradingModel.query.filter_by(
                                        user_id=current_user.id, is_active=True
                                    ).order_by(TradingModel.name).all()]

    # Populate News Events
    news_choices = [('', '-- None --')] + \
                   [(event, event) for event in get_news_event_options() if event.lower() != 'none']
    form.news_event_select.choices = news_choices
    return form

@trades_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_trade():
    form = TradeForm()
    form = populate_trade_form_choices(form) # Populate dynamic choices

    if form.validate_on_submit():
        try:
            new_trade = Trade(
                user_id=current_user.id,
                instrument=form.instrument.data,
                trade_date=form.trade_date.data,
                direction=form.direction.data,
                point_value=_parse_form_float(form.point_value.data), # Ensure this is float
                initial_stop_loss=_parse_form_float(form.initial_stop_loss.data),
                terminus_target=_parse_form_float(form.terminus_target.data),
                is_dca=form.is_dca.data,
                mae=_parse_form_float(form.mae.data),
                mfe=_parse_form_float(form.mfe.data),
                trading_model_id=form.trading_model_id.data if form.trading_model_id.data != 0 else None,
                entry_model_legacy=form.entry_model_legacy.data,
                news_event=form.news_event_select.data if form.news_event_select.data else form.news_event.data, # Prioritize select
                how_closed=form.how_closed.data if form.how_closed.data else None,
                rules_rating=_parse_form_int(form.rules_rating.data),
                management_rating=_parse_form_int(form.management_rating.data),
                target_rating=_parse_form_int(form.target_rating.data),
                entry_rating=_parse_form_int(form.entry_rating.data),
                preparation_rating=_parse_form_int(form.preparation_rating.data),
                trade_notes=form.trade_notes.data,
                psych_scored_highest=form.psych_scored_highest.data,
                psych_scored_lowest=form.psych_scored_lowest.data,
                overall_analysis_notes=form.overall_analysis_notes.data,
                trade_management_notes=form.trade_management_notes.data,
                errors_notes=form.errors_notes.data,
                improvements_notes=form.improvements_notes.data,
                screenshot_link=form.screenshot_link.data,
                tags=form.tags.data
            )
            db.session.add(new_trade)
            # Important: Flush to get new_trade.id before adding entries/exits
            db.session.flush()

            # --- Handle Simplified Single Entry ---
            if form.entry_time_1.data and form.entry_contracts_1.data and form.entry_price_1.data:
                entry1 = EntryPoint(
                    trade_id=new_trade.id,
                    entry_time=form.entry_time_1.data,
                    contracts=_parse_form_int(form.entry_contracts_1.data),
                    entry_price=_parse_form_float(form.entry_price_1.data)
                )
                db.session.add(entry1)
            else:
                # If primary entry is not valid, this trade might be problematic.
                # For now, we assume DataRequired on form ensures this.
                # If not, you might want to flash an error and not save the trade.
                pass

            # --- Handle Simplified Single Exit ---
            # Check if at least one exit field has data, indicating an attempt to log an exit
            if form.exit_time_1.data or form.exit_contracts_1.data or form.exit_price_1.data:
                # An exit requires all three to be valid for a complete log
                if form.exit_time_1.data and form.exit_contracts_1.data and form.exit_price_1.data:
                    exit1 = ExitPoint(
                        trade_id=new_trade.id,
                        exit_time=form.exit_time_1.data,
                        contracts=_parse_form_int(form.exit_contracts_1.data),
                        exit_price=_parse_form_float(form.exit_price_1.data)
                    )
                    db.session.add(exit1)
                else:
                    # Partial exit data was provided, flash a warning or handle as incomplete.
                    # For now, we only add if all three parts of the exit are there.
                    flash("Exit 1 was partially filled and not saved. Please provide time, contracts, and price for an exit.", "warning")

            db.session.commit()
            record_activity('trade_logged', f"Logged new trade ID: {new_trade.id} for {new_trade.instrument}")
            flash(f'Trade for {new_trade.instrument} on {new_trade.trade_date.strftime("%Y-%m-%d")} logged successfully!', 'success')
            # We'll create 'trades.view_trades_list' route next
            return redirect(url_for('trades.view_trades_list'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error logging new trade for user {current_user.username}: {e}", exc_info=True)
            flash(f'An error occurred while logging the trade: {str(e)}', 'danger')

    elif request.method == 'POST': # Form submitted but was not valid
        flash('Please correct the errors in the form and try again.', 'warning')
        # Re-populate choices as they are lost on a failed POST validation if not explicit
        form = populate_trade_form_choices(form)


    return render_template('add_trade.html', title='Log New Trade', form=form,
                           default_trade_date=py_date.today().strftime('%Y-%m-%d'))

# --- Placeholder for other trade routes ---
@trades_bp.route('/')
@login_required
def view_trades_list():
    # This will be the main page to view all trades
    # We'll implement this fully later
    # For now, just so the redirect from add_trade works:
    flash("Trade list page is under construction. Your trade should be logged.", "info")
    # Redirect to dashboard or a simple placeholder page
    return render_template("view_trades_list_placeholder.html", title="Trades List")
    # Or: return redirect(url_for('main.index'))