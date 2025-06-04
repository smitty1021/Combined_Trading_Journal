from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, current_app)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import uuid

from datetime import date as py_date, time as py_time, datetime as py_datetime

from app import db
from app.models import Trade, EntryPoint, ExitPoint, TradingModel, NewsEventItem, TradeImage
from app.forms import TradeForm, EntryPointForm, ExitPointForm  # Ensure these are correctly imported if used
from app.utils import (_parse_form_float, _parse_form_int, _parse_form_time,
                       get_news_event_options, record_activity)  # Removed unused allowed_file from here

trades_bp = Blueprint('trades', __name__,
                      template_folder='../templates/trades',
                      url_prefix='/trades')

INSTRUMENT_POINT_VALUES = {
    'NQ': 20.0, 'ES': 50.0, 'YM': 5.0,
    'MNQ': 2.0, 'MES': 5.0, 'MYM': 0.5,
    'Other': 1.0
}


def populate_trade_form_choices(form):
    form.trading_model_id.choices = [(0, '-- Select Model --')] + \
                                    [(tm.id, tm.name) for tm in TradingModel.query.filter_by(
                                        user_id=current_user.id, is_active=True
                                    ).order_by(TradingModel.name).all()]
    news_choices = [('', '-- None --')] + \
                   [(event, event) for event in get_news_event_options() if event and event.lower() != 'none']
    form.news_event_select.choices = news_choices
    return form


def _is_allowed_image(filename):
    """Checks if the filename has an allowed image extension."""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in current_app.config.get('ALLOWED_IMAGE_EXTENSIONS',
                                                                     {'png', 'jpg', 'jpeg', 'gif'})


@trades_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_trade():
    form = TradeForm()
    if request.method == 'GET':
        if not form.entries.entries:
            form.entries.append_entry()
        if not form.exits.entries:
            form.exits.append_entry()

    form = populate_trade_form_choices(form)

    if form.validate_on_submit():
        try:
            instrument = form.instrument.data
            point_value_for_trade = INSTRUMENT_POINT_VALUES.get(instrument, 1.0)
            tag_value = form.tags.data if form.tags.data else None

            new_trade = Trade(
                user_id=current_user.id,
                instrument=instrument,
                trade_date=form.trade_date.data,
                direction=form.direction.data,
                point_value=point_value_for_trade,
                initial_stop_loss=_parse_form_float(form.initial_stop_loss.data),
                terminus_target=_parse_form_float(form.terminus_target.data),
                is_dca=form.is_dca.data,
                mae=_parse_form_float(form.mae.data),
                mfe=_parse_form_float(form.mfe.data),
                trading_model_id=form.trading_model_id.data if form.trading_model_id.data and form.trading_model_id.data != 0 else None,
                news_event=form.news_event_select.data if form.news_event_select.data else None,
                how_closed=form.how_closed.data if form.how_closed.data else None,
                rules_rating=form.rules_rating.data,
                management_rating=form.management_rating.data,
                target_rating=form.target_rating.data,
                entry_rating=form.entry_rating.data,
                preparation_rating=form.preparation_rating.data,
                trade_notes=form.trade_notes.data,
                psych_scored_highest=form.psych_scored_highest.data,
                psych_scored_lowest=form.psych_scored_lowest.data,
                overall_analysis_notes=form.overall_analysis_notes.data,
                trade_management_notes=form.trade_management_notes.data,
                errors_notes=form.errors_notes.data,
                improvements_notes=form.improvements_notes.data,
                screenshot_link=form.screenshot_link.data,
                tags=tag_value
            )
            db.session.add(new_trade)
            db.session.flush()

            for entry_data in form.entries.data:
                if entry_data.get('entry_time') and entry_data.get('contracts') is not None and entry_data.get(
                        'entry_price') is not None:
                    entry = EntryPoint(trade_id=new_trade.id, entry_time=entry_data['entry_time'],
                                       contracts=entry_data['contracts'], entry_price=entry_data['entry_price'])
                    db.session.add(entry)
                elif any(entry_data.values()):
                    current_app.logger.warning(f"Incomplete entry data for trade {new_trade.id}: {entry_data}")

            for exit_data in form.exits.data:
                if exit_data.get('exit_time') and exit_data.get('contracts') is not None and exit_data.get(
                        'exit_price') is not None:
                    exit_point = ExitPoint(trade_id=new_trade.id, exit_time=exit_data['exit_time'],
                                           contracts=exit_data['contracts'], exit_price=exit_data['exit_price'])
                    db.session.add(exit_point)
                elif any(val is not None for val in exit_data.values() if val != ''):
                    current_app.logger.warning(f"Incomplete exit data for trade {new_trade.id}: {exit_data}")
                    flash(
                        f"An exit for trade {new_trade.instrument} was partially filled and not saved. Please provide time, contracts, and price for a complete exit log.",
                        "warning")

            if form.trade_images.data:
                for image_file in form.trade_images.data:
                    if image_file and _is_allowed_image(image_file.filename):
                        original_filename = secure_filename(image_file.filename)
                        file_ext = os.path.splitext(original_filename)[1].lower()
                        unique_filename = f"{uuid.uuid4().hex}{file_ext}"
                        upload_folder = current_app.config['UPLOAD_FOLDER']
                        file_path = os.path.join(upload_folder, unique_filename)
                        try:
                            image_file.save(file_path)
                            trade_image = TradeImage(
                                trade_id=new_trade.id, user_id=current_user.id, filename=original_filename,
                                filepath=unique_filename, filesize=os.path.getsize(file_path),
                                mime_type=image_file.mimetype
                            )
                            db.session.add(trade_image)
                        except Exception as e_save:
                            current_app.logger.error(
                                f"Failed to save image {original_filename} for trade {new_trade.id}: {e_save}",
                                exc_info=True)
                            flash(f"Could not save image: {original_filename}", "warning")
                    elif image_file:
                        flash(f"Image type not allowed for file: {image_file.filename}", "warning")

            db.session.commit()
            record_activity('trade_logged', f"Logged new trade ID: {new_trade.id} for {new_trade.instrument}")
            flash(
                f'Trade for {new_trade.instrument} on {new_trade.trade_date.strftime("%Y-%m-%d")} logged successfully!',
                'success')
            return redirect(url_for('trades.view_trades_list'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error logging new trade for user {current_user.username}: {e}", exc_info=True)
            flash(f'An error occurred while logging the trade: {str(e)}', 'danger')

    elif request.method == 'POST':
        flash('Please correct the errors in the form and try again.', 'warning')

    return render_template('add_trade.html', title='Log New Trade', form=form,
                           default_trade_date=py_date.today().strftime('%Y-%m-%d'))


@trades_bp.route('/')
@login_required
def view_trades_list():
    # MODIFIED: Fetch trades and render a new template
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('PER_PAGE_TRADES', 25)  # Get per_page from config

    trades_pagination = Trade.query.filter_by(user_id=current_user.id) \
        .order_by(Trade.trade_date.desc(), Trade.id.desc()) \
        .paginate(page=page, per_page=per_page, error_out=False)

    trades_on_page = trades_pagination.items

    return render_template("trades/view_trades_list.html",
                           title="Trades List",
                           trades=trades_on_page,
                           pagination=trades_pagination)