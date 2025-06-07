from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, current_app, Response, abort)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import uuid
import csv
import io
from datetime import date as py_date, datetime as py_datetime, time as py_time

from app import db
from app.models import Trade, EntryPoint, ExitPoint, TradingModel, NewsEventItem, TradeImage
from app.forms import TradeForm, EntryPointForm, ExitPointForm, TradeFilterForm, ImportTradesForm
from app.utils import (_parse_form_float, _parse_form_int, _parse_form_time,
                       get_news_event_options, record_activity)

trades_bp = Blueprint('trades', __name__,
                      template_folder='../templates/trades',
                      url_prefix='/trades')

# --- Helper Functions and Constants (as before) ---
INSTRUMENT_POINT_VALUES = {
    'NQ': 20.0, 'ES': 50.0, 'YM': 5.0,
    'MNQ': 2.0, 'MES': 5.0, 'MYM': 0.5,
    'Other': 1.0
}


def _is_allowed_image(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in current_app.config.get('ALLOWED_IMAGE_EXTENSIONS',
                                                                     {'png', 'jpg', 'jpeg', 'gif'})


def _populate_trade_form_choices(form):
    form.trading_model_id.choices = [(0, '-- Select Model --')] + \
                                    [(tm.id, tm.name) for tm in
                                     TradingModel.query.filter_by(user_id=current_user.id, is_active=True).order_by(
                                         TradingModel.name).all()]
    if hasattr(form, 'news_event_select'):
        form.news_event_select.choices = [('', '-- None --')] + [(event, event) for event in get_news_event_options() if
                                                                 event and event.lower() != 'none']
    return form


def _populate_filter_form_choices(filter_form):
    filter_form.trading_model_id.choices = [(0, 'All Models')] + \
                                           [(tm.id, tm.name) for tm in
                                            TradingModel.query.filter_by(user_id=current_user.id,
                                                                         is_active=True).order_by(
                                                TradingModel.name).all()]
    if hasattr(TradeForm, 'instrument_choices'):
        filter_form.instrument.choices = [('', 'All Instruments')] + TradeForm.instrument_choices[1:]
    if hasattr(TradeForm, 'direction_choices'):
        filter_form.direction.choices = [('', 'All Directions')] + TradeForm.direction_choices[1:]
    if hasattr(TradeForm, 'SIMPLE_TAG_CHOICES'):
        filter_form.tags.choices = [('', 'All Tags')] + TradeForm.SIMPLE_TAG_CHOICES[1:]
    return filter_form


# --- VIEW TRADES LIST ---
@trades_bp.route('/', methods=['GET'])
@login_required
def view_trades_list():
    # MODIFIED: Removed meta={'csrf': False} to enable the CSRF field on this form
    filter_form = TradeFilterForm(request.args)
    _populate_filter_form_choices(filter_form)

    query = Trade.query.filter_by(user_id=current_user.id)

    # This validation is for GET requests so it's a bit different, but WTForms can handle it.
    if filter_form.validate():
        if filter_form.start_date.data:
            query = query.filter(Trade.trade_date >= filter_form.start_date.data)
        if filter_form.end_date.data:
            query = query.filter(Trade.trade_date <= filter_form.end_date.data)
        if filter_form.instrument.data:
            query = query.filter(Trade.instrument == filter_form.instrument.data)
        if filter_form.direction.data:
            query = query.filter(Trade.direction == filter_form.direction.data)
        if filter_form.trading_model_id.data and filter_form.trading_model_id.data != 0:
            query = query.filter(Trade.trading_model_id == filter_form.trading_model_id.data)
        if filter_form.tags.data:
            query = query.filter(Trade.tags == filter_form.tags.data)

    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('PER_PAGE_TRADES', 10)

    trades_pagination = query.order_by(Trade.trade_date.desc(), Trade.id.desc()).paginate(page=page, per_page=per_page,
                                                                                          error_out=False)

    # MODIFIED: No longer need to generate and pass the CSRF token manually
    return render_template("trades/view_trades_list.html",
                           title="Trades List",
                           trades=trades_pagination.items,
                           pagination=trades_pagination,
                           filter_form=filter_form)  # Pass the filter_form which contains the CSRF token


# ... (The rest of your routes: add_trade, edit_trade, etc. can remain unchanged) ...


# --- ADD TRADE ---
@trades_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_trade():
    form = TradeForm()
    if request.method == 'GET':
        if not form.entries.entries:
            form.entries.append_entry(None)
        if not form.exits.entries:
            form.exits.append_entry(None)

    _populate_trade_form_choices(form)

    if form.validate_on_submit():
        try:
            instrument = form.instrument.data
            point_value_for_trade = INSTRUMENT_POINT_VALUES.get(instrument, 1.0)
            tag_value = form.tags.data if form.tags.data and form.tags.data != '' else None

            new_trade = Trade(user_id=current_user.id)

            # Populate trade object from form data where names match
            new_trade.instrument = instrument
            new_trade.trade_date = form.trade_date.data
            new_trade.direction = form.direction.data
            new_trade.initial_stop_loss = _parse_form_float(form.initial_stop_loss.data)
            new_trade.terminus_target = _parse_form_float(form.terminus_target.data)
            new_trade.is_dca = form.is_dca.data
            new_trade.mae = _parse_form_float(form.mae.data)
            new_trade.mfe = _parse_form_float(form.mfe.data)
            new_trade.how_closed = form.how_closed.data if form.how_closed.data else None
            new_trade.rules_rating = form.rules_rating.data
            new_trade.management_rating = form.management_rating.data
            new_trade.target_rating = form.target_rating.data
            new_trade.entry_rating = form.entry_rating.data
            new_trade.preparation_rating = form.preparation_rating.data
            new_trade.trade_notes = form.trade_notes.data
            new_trade.psych_scored_highest = form.psych_scored_highest.data
            new_trade.psych_scored_lowest = form.psych_scored_lowest.data
            new_trade.overall_analysis_notes = form.overall_analysis_notes.data
            new_trade.trade_management_notes = form.trade_management_notes.data
            new_trade.errors_notes = form.errors_notes.data
            new_trade.improvements_notes = form.improvements_notes.data
            new_trade.screenshot_link = form.screenshot_link.data

            # Set specific fields
            new_trade.point_value = point_value_for_trade
            new_trade.tags = tag_value
            new_trade.trading_model_id = form.trading_model_id.data if form.trading_model_id.data and form.trading_model_id.data != 0 else None
            new_trade.news_event = form.news_event_select.data if form.news_event_select.data else None

            db.session.add(new_trade)
            db.session.flush()

            for entry_data in form.entries.data:
                if entry_data.get('entry_time') and entry_data.get('contracts') is not None and entry_data.get(
                        'entry_price') is not None:
                    entry = EntryPoint(
                        trade_id=new_trade.id,
                        entry_time=entry_data['entry_time'],
                        contracts=entry_data['contracts'],
                        entry_price=entry_data['entry_price']
                    )
                    db.session.add(entry)

            for exit_data in form.exits.data:
                if exit_data.get('exit_time') and exit_data.get('contracts') is not None and exit_data.get(
                        'exit_price') is not None:
                    exit_point = ExitPoint(
                        trade_id=new_trade.id,
                        exit_time=exit_data['exit_time'],
                        contracts=exit_data['contracts'],
                        exit_price=exit_data['exit_price']
                    )
                    db.session.add(exit_point)
                elif any(val for key, val in exit_data.items() if key != 'id' and val is not None and val != ''):
                    flash(
                        f"An exit for trade was partially filled and not saved. Please provide all of time, contracts, and price for a complete exit log.",
                        "warning")

            if form.trade_images.data:
                for image_file in form.trade_images.data:
                    if image_file and _is_allowed_image(image_file.filename):
                        original_filename = secure_filename(image_file.filename)
                        file_ext = os.path.splitext(original_filename)[1].lower()
                        unique_filename = f"{uuid.uuid4().hex}{file_ext}"
                        upload_folder = current_app.config['UPLOAD_FOLDER']
                        if not os.path.exists(upload_folder): os.makedirs(upload_folder)
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
        if not form.entries.entries: form.entries.append_entry(None)
        if not form.exits.entries and len(form.exits.data) == 0: form.exits.append_entry(None)

    return render_template('trades/add_trade.html', title='Log New Trade', form=form,
                           default_trade_date=py_date.today().strftime('%Y-%m-%d'))

# --- VIEW TRADE DETAIL ---
@trades_bp.route('/<int:trade_id>/view')
@login_required
def view_trade_detail(trade_id):
    trade = db.get_or_404(Trade, trade_id)
    if trade.user_id != current_user.id:
        abort(403)
    return render_template('trades/view_trade_detail.html', title="Trade Details", trade=trade)


# --- EDIT TRADE ---
@trades_bp.route('/<int:trade_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_trade(trade_id):
    trade_to_edit = db.get_or_404(Trade, trade_id)
    if trade_to_edit.user_id != current_user.id:
        abort(403)

    form = TradeForm(obj=trade_to_edit)
    _populate_trade_form_choices(form)

    if request.method == 'GET':
        while len(form.entries) > 0: form.entries.pop_entry()
        for entry in trade_to_edit.entries.all():
            entry_form_data = {
                'id': entry.id, 'entry_time': entry.entry_time,
                'contracts': entry.contracts, 'entry_price': entry.entry_price
            }
            form.entries.append_entry(data=entry_form_data)
        if not form.entries.entries: form.entries.append_entry(None)

        while len(form.exits) > 0: form.exits.pop_entry()
        for exit_item in trade_to_edit.exits.all():
            exit_form_data = {
                'id': exit_item.id, 'exit_time': exit_item.exit_time,
                'contracts': exit_item.contracts, 'exit_price': exit_item.exit_price
            }
            form.exits.append_entry(data=exit_form_data)
        if not form.exits.entries: form.exits.append_entry(None)

    if form.validate_on_submit():
        try:
            # Populate main trade object fields from the form
            trade_to_edit.instrument = form.instrument.data
            trade_to_edit.trade_date = form.trade_date.data
            trade_to_edit.direction = form.direction.data
            trade_to_edit.point_value = INSTRUMENT_POINT_VALUES.get(form.instrument.data, 1.0)
            trade_to_edit.initial_stop_loss = _parse_form_float(form.initial_stop_loss.data)
            trade_to_edit.terminus_target = _parse_form_float(form.terminus_target.data)
            trade_to_edit.is_dca = form.is_dca.data
            trade_to_edit.mae = _parse_form_float(form.mae.data)
            trade_to_edit.mfe = _parse_form_float(form.mfe.data)
            trade_to_edit.trading_model_id = form.trading_model_id.data if form.trading_model_id.data and form.trading_model_id.data != 0 else None
            trade_to_edit.news_event = form.news_event_select.data if form.news_event_select.data else None
            trade_to_edit.how_closed = form.how_closed.data if form.how_closed.data else None
            trade_to_edit.rules_rating = form.rules_rating.data
            trade_to_edit.management_rating = form.management_rating.data
            trade_to_edit.target_rating = form.target_rating.data
            trade_to_edit.entry_rating = form.entry_rating.data
            trade_to_edit.preparation_rating = form.preparation_rating.data
            trade_to_edit.trade_notes = form.trade_notes.data
            trade_to_edit.psych_scored_highest = form.psych_scored_highest.data
            trade_to_edit.psych_scored_lowest = form.psych_scored_lowest.data
            trade_to_edit.overall_analysis_notes = form.overall_analysis_notes.data
            trade_to_edit.trade_management_notes = form.trade_management_notes.data
            trade_to_edit.errors_notes = form.errors_notes.data
            trade_to_edit.improvements_notes = form.improvements_notes.data
            trade_to_edit.screenshot_link = form.screenshot_link.data
            trade_to_edit.tags = form.tags.data if form.tags.data and form.tags.data != '' else None

            # Handle Entries: Update existing, Add new, Delete removed
            current_entry_ids_in_db = {entry.id for entry in trade_to_edit.entries}
            submitted_entry_ids = set()
            new_entries_to_add = []

            for entry_form_data in form.entries.data:
                entry_id = entry_form_data.get('id')
                if entry_form_data.get('entry_time') and entry_form_data.get(
                        'contracts') is not None and entry_form_data.get('entry_price') is not None:
                    if entry_id:
                        entry_to_update = EntryPoint.query.get(entry_id)
                        if entry_to_update and entry_to_update.trade_id == trade_to_edit.id:
                            entry_to_update.entry_time = entry_form_data['entry_time']
                            entry_to_update.contracts = entry_form_data['contracts']
                            entry_to_update.entry_price = entry_form_data['entry_price']
                            submitted_entry_ids.add(entry_id)
                    else:
                        new_entries_to_add.append(EntryPoint(
                            trade_id=trade_to_edit.id, entry_time=entry_form_data['entry_time'],
                            contracts=entry_form_data['contracts'], entry_price=entry_form_data['entry_price']
                        ))
            for id_to_delete in current_entry_ids_in_db - submitted_entry_ids:
                entry_to_delete = EntryPoint.query.get(id_to_delete)
                if entry_to_delete: db.session.delete(entry_to_delete)
            for new_entry in new_entries_to_add:
                db.session.add(new_entry)

            # Handle Exits: Update existing, Add new, Delete removed
            current_exit_ids_in_db = {exit_item.id for exit_item in trade_to_edit.exits}
            submitted_exit_ids = set()
            new_exits_to_add = []
            for exit_form_data in form.exits.data:
                exit_id = exit_form_data.get('id')
                if exit_form_data.get('exit_time') and exit_form_data.get(
                        'contracts') is not None and exit_form_data.get('exit_price') is not None:
                    if exit_id:
                        exit_to_update = ExitPoint.query.get(exit_id)
                        if exit_to_update and exit_to_update.trade_id == trade_to_edit.id:
                            exit_to_update.exit_time = exit_form_data['exit_time']
                            exit_to_update.contracts = exit_form_data['contracts']
                            exit_to_update.exit_price = exit_form_data['exit_price']
                            submitted_exit_ids.add(exit_id)
                    else:
                        new_exits_to_add.append(ExitPoint(
                            trade_id=trade_to_edit.id, exit_time=exit_form_data['exit_time'],
                            contracts=exit_form_data['contracts'], exit_price=exit_form_data['exit_price']
                        ))
            for id_to_delete in current_exit_ids_in_db - submitted_exit_ids:
                exit_to_delete = ExitPoint.query.get(id_to_delete)
                if exit_to_delete: db.session.delete(exit_to_delete)
            for new_exit in new_exits_to_add:
                db.session.add(new_exit)

            # Handle image deletion
            for image in trade_to_edit.images:  # Iterate over a copy if modifying the list
                if request.form.get(f'delete_image_{image.id}'):
                    image_path_to_delete = os.path.join(current_app.config['UPLOAD_FOLDER'], image.filepath)
                    if os.path.exists(image_path_to_delete):
                        try:
                            os.remove(image_path_to_delete)
                        except OSError:
                            current_app.logger.warning(f"Could not delete image file on disk: {image.filepath}")
                    db.session.delete(image)

            # Handle new image uploads
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
                                trade_id=trade_to_edit.id, user_id=current_user.id, filename=original_filename,
                                filepath=unique_filename, filesize=os.path.getsize(file_path),
                                mime_type=image_file.mimetype)
                            db.session.add(trade_image)
                        except Exception as e_save:
                            current_app.logger.error(
                                f"Failed to save new image during edit {original_filename} for trade {trade_to_edit.id}: {e_save}",
                                exc_info=True)

            db.session.commit()
            flash('Trade updated successfully!', 'success')
            return redirect(url_for('trades.view_trade_detail', trade_id=trade_to_edit.id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error editing trade {trade_id}: {e}", exc_info=True)
            flash(f'An error occurred while updating the trade: {str(e)}', 'danger')

    return render_template('trades/edit_trade.html', title="Edit Trade", form=form, trade=trade_to_edit)


# --- DELETE TRADE (Single) ---
@trades_bp.route('/<int:trade_id>/delete', methods=['POST'])
@login_required
def delete_trade(trade_id):
    trade_to_delete = db.get_or_404(Trade, trade_id)
    if trade_to_delete.user_id != current_user.id:
        abort(403)
    try:
        for img in trade_to_delete.images:
            if img.filepath:
                try:
                    os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], img.filepath))
                except OSError:
                    current_app.logger.warning(f"Could not delete image file: {img.filepath}")
        db.session.delete(trade_to_delete)  # Cascades should handle entries, exits, images in DB
        db.session.commit()
        flash('Trade deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting trade {trade_id}: {e}", exc_info=True)
        flash('Error deleting trade. Please try again.', 'danger')
    return redirect(url_for('trades.view_trades_list'))


# --- BULK DELETE TRADES ---
@trades_bp.route('/bulk_delete', methods=['POST'])
@login_required
def bulk_delete_trades():
    trade_ids_to_delete = request.form.getlist('trade_ids')
    if not trade_ids_to_delete:
        flash('No trades selected for deletion.', 'warning')
        return redirect(url_for('trades.view_trades_list'))

    deleted_count = 0
    error_count = 0
    for trade_id_str in trade_ids_to_delete:
        try:
            trade_id = int(trade_id_str)
            trade = Trade.query.get(trade_id)
            if trade and trade.user_id == current_user.id:
                for img in trade.images:
                    if img.filepath:
                        try:
                            os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], img.filepath))
                        except OSError:
                            pass
                db.session.delete(trade)
                deleted_count += 1
            else:
                error_count += 1
        except ValueError:
            error_count += 1
        except Exception as e:
            error_count += 1
            current_app.logger.error(f"Error during bulk delete of trade ID {trade_id_str}: {e}", exc_info=True)

    if deleted_count > 0:
        try:
            db.session.commit()
            flash(f'Successfully deleted {deleted_count} trade(s).', 'success')
        except Exception as e_commit:
            db.session.rollback()
            flash('An error occurred during bulk deletion commit.', 'danger')
            current_app.logger.error(f"Error committing bulk delete: {e_commit}", exc_info=True)
    if error_count > 0:
        flash(f'Could not delete {error_count} selected item(s) due to errors or permissions.', 'warning')

    return redirect(url_for('trades.view_trades_list'))


# --- EXPORT TRADES ---
@trades_bp.route('/export_csv', methods=['GET'])
@login_required
def export_trades_csv():
    filter_form = TradeFilterForm(request.args, meta={'csrf': False})
    _populate_filter_form_choices(filter_form)

    query = Trade.query.filter_by(user_id=current_user.id)
    if filter_form.start_date.data: query = query.filter(Trade.trade_date >= filter_form.start_date.data)
    if filter_form.end_date.data: query = query.filter(Trade.trade_date <= filter_form.end_date.data)
    if filter_form.instrument.data: query = query.filter(Trade.instrument == filter_form.instrument.data)
    if filter_form.direction.data: query = query.filter(Trade.direction == filter_form.direction.data)
    if filter_form.trading_model_id.data and filter_form.trading_model_id.data != 0:
        query = query.filter(Trade.trading_model_id == filter_form.trading_model_id.data)
    if filter_form.tags.data: query = query.filter(Trade.tags == filter_form.tags.data)

    trades_to_export = query.order_by(Trade.trade_date.asc()).all()

    if not trades_to_export:
        flash('No trades found matching current filters to export.', 'warning')
        return redirect(url_for('trades.view_trades_list', **request.args))

    output = io.StringIO()
    writer = csv.writer(output)
    headers = [
        'ID', 'Date', 'Instrument', 'Direction', 'Point Value',
        'Total Entry Contracts', 'Avg Entry Price', 'Total Exit Contracts', 'Avg Exit Price',
        'Gross P&L', 'R-Value (Initial)', 'Dollar Risk (Initial)',
        'Initial SL', 'Terminus Target', 'MAE', 'MFE', 'How Closed',
        'Trading Model', 'Tags', 'Trade Notes', 'Overall Analysis', 'Management Notes',
        'Errors', 'Improvements', 'External Screenshot Link'
        # Detailed entries/exits would require a more complex CSV or separate export
    ]
    writer.writerow(headers)
    for trade in trades_to_export:
        writer.writerow([
            trade.id, trade.trade_date.strftime('%Y-%m-%d'), trade.instrument, trade.direction, trade.point_value,
            trade.total_contracts_entered, trade.average_entry_price,
            trade.total_contracts_exited, trade.average_exit_price,
            trade.gross_pnl, trade.pnl_in_r, trade.dollar_risk,
            trade.initial_stop_loss, trade.terminus_target, trade.mae, trade.mfe,
            trade.how_closed, trade.trading_model.name if trade.trading_model else '',
            trade.tags, trade.trade_notes, trade.overall_analysis_notes, trade.trade_management_notes,
            trade.errors_notes, trade.improvements_notes, trade.screenshot_link
        ])
    output.seek(0)
    return Response(output, mimetype="text/csv",
                    headers={"Content-Disposition": "attachment;filename=trades_export.csv"})


# --- IMPORT TRADES ---
@trades_bp.route('/import', methods=['GET', 'POST'])
@login_required
def import_trades():
    form = ImportTradesForm()
    if form.validate_on_submit():
        csv_file = form.csv_file.data
        try:
            stream = io.StringIO(csv_file.stream.read().decode("UTF-8"), newline=None)
            csv_reader = csv.DictReader(stream)
            imported_count = 0
            error_count = 0
            error_details = []

            for row_num, row in enumerate(csv_reader, 1):
                try:
                    trade_date_str = row.get('Date')
                    if not trade_date_str:
                        error_details.append(f"Row {row_num + 1}: Missing Date.");
                        error_count += 1;
                        continue
                    trade_date = py_datetime.strptime(trade_date_str, '%Y-%m-%d').date()

                    instrument = row.get('Instrument')
                    direction = row.get('Direction')
                    if not instrument or not direction:
                        error_details.append(f"Row {row_num + 1}: Missing Instrument or Direction.");
                        error_count += 1;
                        continue

                    new_trade = Trade(user_id=current_user.id, trade_date=trade_date, instrument=instrument,
                                      direction=direction)
                    new_trade.point_value = INSTRUMENT_POINT_VALUES.get(instrument, 1.0)

                    # Optional fields from CSV
                    new_trade.initial_stop_loss = _parse_form_float(row.get('Initial SL'))
                    new_trade.terminus_target = _parse_form_float(row.get('Terminus Target'))
                    new_trade.mae = _parse_form_float(row.get('MAE'))
                    new_trade.mfe = _parse_form_float(row.get('MFE'))
                    new_trade.how_closed = row.get('How Closed')
                    new_trade.tags = row.get('Tags')
                    new_trade.trade_notes = row.get('Trade Notes')
                    new_trade.overall_analysis_notes = row.get('Overall Analysis')
                    new_trade.trade_management_notes = row.get('Management Notes')
                    new_trade.errors_notes = row.get('Errors')
                    new_trade.improvements_notes = row.get('Improvements')
                    new_trade.screenshot_link = row.get('External Screenshot Link')

                    # Gross P&L is usually calculated, but if provided, can be stored or used for verification
                    # For simplicity, not directly setting P&L if entries/exits are also imported

                    model_name = row.get('Trading Model')
                    if model_name:
                        model = TradingModel.query.filter_by(user_id=current_user.id, name=model_name).first()
                        if model:
                            new_trade.trading_model_id = model.id
                        else:
                            error_details.append(
                                f"Row {row_num + 1}: Trading Model '{model_name}' not found. Trade imported without model.")

                    # Placeholder for importing entries/exits - requires more complex CSV structure and parsing
                    # e.g., if CSV has Entry 1 Price, Entry 1 Contracts, Entry 1 Time, etc.
                    # Or if entries/exits for one trade are on multiple CSV lines.
                    # For now, this import creates a trade without detailed entry/exit points.

                    db.session.add(new_trade)
                    imported_count += 1
                except ValueError as ve:
                    error_details.append(f"Row {row_num + 1}: Data conversion error - {ve}. Row data: {row}");
                    error_count += 1
                except Exception as e_row:
                    error_details.append(f"Row {row_num + 1}: Unexpected error - {e_row}. Row data: {row}");
                    error_count += 1

            if imported_count > 0:
                db.session.commit()
            else:
                db.session.rollback()

            if imported_count > 0: flash(f'Successfully imported {imported_count} trades.', 'success')
            if error_count > 0: flash(f'Skipped or had errors with {error_count} rows during import.', 'danger')
            if error_details:
                for err_detail in error_details[:10]:  # Show first few errors
                    flash(err_detail, 'warning')
                if len(error_details) > 10:
                    flash(f"...and {len(error_details) - 10} more errors. Check server logs for all details.",
                          'warning')

            return redirect(url_for('trades.view_trades_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error importing trades file: {str(e)}', 'danger')
            current_app.logger.error(f"Fatal error during trade import process: {e}", exc_info=True)

    return render_template('trades/import_trades.html', title="Import Trades", form=form)