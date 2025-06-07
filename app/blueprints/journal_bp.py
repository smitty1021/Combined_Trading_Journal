from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, current_app, abort)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import date as py_date, datetime as py_datetime, timedelta

from app import db
from app.models import DailyJournal, DailyJournalImage, Trade
from app.forms import DailyJournalForm  # Assuming DailyJournalForm is in app.forms
from app.utils import record_activity  # Assuming record_activity is in app.utils

journal_bp = Blueprint('journal', __name__,
                       template_folder='../templates/journal',
                       url_prefix='/journal')


def _is_allowed_image(filename):
    """Checks if the filename has an allowed image extension."""
    # Duplicated from trades_bp for now, consider moving to utils.py if widely used
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in current_app.config.get('ALLOWED_IMAGE_EXTENSIONS',
                                                                     {'png', 'jpg', 'jpeg', 'gif'})


def _handle_daily_journal_image_uploads(form, daily_journal_instance, image_field_name, image_type_tag):
    """Helper to handle image uploads for a daily journal field."""
    if form[image_field_name].data:
        for image_file in form[image_field_name].data:
            if image_file and _is_allowed_image(image_file.filename):
                original_filename = secure_filename(image_file.filename)
                file_ext = os.path.splitext(original_filename)[1].lower()
                unique_filename = f"{uuid.uuid4().hex}{file_ext}"
                upload_folder = current_app.config['UPLOAD_FOLDER']
                # Consider a subfolder for journal images:
                # journal_image_upload_folder = os.path.join(upload_folder, 'daily_journal_images')
                # if not os.path.exists(journal_image_upload_folder): os.makedirs(journal_image_upload_folder)
                # file_path = os.path.join(journal_image_upload_folder, unique_filename)
                file_path = os.path.join(upload_folder, unique_filename)  # Using main UPLOAD_FOLDER for now

                try:
                    image_file.save(file_path)
                    dj_image = DailyJournalImage(
                        daily_journal_id=daily_journal_instance.id,
                        user_id=current_user.id,
                        filename=original_filename,
                        filepath=unique_filename,
                        filesize=os.path.getsize(file_path),
                        mime_type=image_file.mimetype,
                        image_type=image_type_tag
                    )
                    db.session.add(dj_image)
                except Exception as e_save:
                    current_app.logger.error(
                        f"Failed to save journal image {original_filename} for journal {daily_journal_instance.id}: {e_save}",
                        exc_info=True)
                    flash(f"Could not save image: {original_filename}", "warning")
            elif image_file:
                flash(f"Image type not allowed for journal image: {image_file.filename}", "warning")


@journal_bp.route('/daily', methods=['GET'])
@journal_bp.route('/daily/<string:date_str>', methods=['GET', 'POST'])
@login_required
def manage_daily_journal(date_str=None):
    if date_str is None:
        # Default to today's date if no date is provided
        target_date = py_date.today()
        # Redirect to the date-specific URL to make it bookmarkable and consistent
        return redirect(url_for('journal.manage_daily_journal', date_str=target_date.strftime('%Y-%m-%d')))
    else:
        try:
            target_date = py_datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            flash("Invalid date format. Please use YYYY-MM-DD.", "danger")
            return redirect(url_for('journal.manage_daily_journal', date_str=py_date.today().strftime('%Y-%m-%d')))

    # Try to find existing journal for this date and user
    daily_journal = DailyJournal.query.filter_by(user_id=current_user.id, journal_date=target_date).first()

    form_obj = daily_journal if daily_journal else None  # Pass existing journal to form for pre-population
    form = DailyJournalForm(obj=form_obj)

    if request.method == 'POST' and form.validate_on_submit():
        if daily_journal is None:  # Create new journal entry
            daily_journal = DailyJournal(user_id=current_user.id, journal_date=target_date)
            db.session.add(daily_journal)
            action_desc = "created"
        else:  # Update existing
            action_desc = "updated"

        # Populate DailyJournal object from form
        # Basic fields can be populated like this:
        form.populate_obj(daily_journal)
        # Ensure journal_date is set correctly (it should be from form or target_date)
        daily_journal.journal_date = target_date

        try:
            db.session.flush()  # To get daily_journal.id if it's new

            # Handle image uploads
            _handle_daily_journal_image_uploads(form, daily_journal, 'pre_market_screenshots', 'pre_market')
            _handle_daily_journal_image_uploads(form, daily_journal, 'eod_chart_screenshots', 'eod_chart')

            # Handle deletion of existing images (if checkboxes are added to the form)
            if daily_journal.id:  # Only if journal entry exists
                for image in daily_journal.images:
                    if request.form.get(f'delete_dj_image_{image.id}'):
                        if image.filepath:
                            try:
                                image_path_to_delete = os.path.join(current_app.config['UPLOAD_FOLDER'], image.filepath)
                                if os.path.exists(image_path_to_delete):
                                    os.remove(image_path_to_delete)
                            except OSError:
                                current_app.logger.warning(
                                    f"Could not delete daily journal image file on disk: {image.filepath}")
                        db.session.delete(image)

            db.session.commit()
            record_activity('daily_journal_save',
                            f"Daily journal for {target_date.strftime('%Y-%m-%d')} {action_desc}.")
            flash(f'Daily journal for {target_date.strftime("%d-%b-%Y")} has been {action_desc}!', 'success')
            return redirect(url_for('journal.manage_daily_journal', date_str=target_date.strftime('%Y-%m-%d')))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error saving daily journal for {target_date}: {e}", exc_info=True)
            flash(f'An error occurred while saving the daily journal: {str(e)}', 'danger')

    elif request.method == 'POST':  # Form validation failed
        flash('Please correct the errors in the form and try again.', 'warning')

    # Fetch trades for this specific day to display in the "Daily Trading Log"
    trades_for_day = Trade.query.filter_by(user_id=current_user.id, trade_date=target_date) \
        .order_by(Trade.id.asc()).all()

    # Calculate cumulative PNL for the day
    cumulative_daily_pnl = sum(trade.gross_pnl for trade in trades_for_day if trade.gross_pnl is not None)

    # Prepare data for psych scorecard radar chart
    # The DailyJournal model has review_psych_..._rating fields for the day, and an average_review_psych_rating property.
    psych_labels = ["Discipline", "Motivation", "Focus", "Mastery", "Composure", "Resilience", "Mind", "Energy"]
    psych_values = [
        daily_journal.review_psych_discipline_rating if daily_journal else None,
        daily_journal.review_psych_motivation_rating if daily_journal else None,
        daily_journal.review_psych_focus_rating if daily_journal else None,
        daily_journal.review_psych_mastery_rating if daily_journal else None,
        daily_journal.review_psych_composure_rating if daily_journal else None,
        daily_journal.review_psych_resilience_rating if daily_journal else None,
        daily_journal.review_psych_mind_rating if daily_journal else None,
        daily_journal.review_psych_energy_rating if daily_journal else None,
    ]
    # Filter out None values if chart library requires it, or handle in JS
    valid_psych_values = [v if v is not None else 0 for v in psych_values]  # Default to 0 for chart if None

    # Previous and next day for navigation
    prev_day = target_date - timedelta(days=1)
    next_day = target_date + timedelta(days=1)

    return render_template('journal/manage_daily_journal.html',
                           title=f"Daily Journal - {target_date.strftime('%A, %d %b %Y')}",
                           form=form,
                           daily_journal_entry=daily_journal,  # Pass the existing entry if any
                           journal_date=target_date,
                           trades_for_day=trades_for_day,
                           cumulative_daily_pnl=cumulative_daily_pnl,
                           psych_labels=psych_labels,
                           psych_values=valid_psych_values,  # Pass processed values for chart
                           prev_day_str=prev_day.strftime('%Y-%m-%d'),
                           next_day_str=next_day.strftime('%Y-%m-%d'),
                           today_str=py_date.today().strftime('%Y-%m-%d'))