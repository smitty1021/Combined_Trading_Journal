from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from flask_login import login_required, current_user

# Import db and Settings model locally within the function where needed to avoid potential circular imports
# from app import db
# from app.models import Settings
from app.utils import record_activity

settings_bp = Blueprint('settings', __name__,
                        template_folder='../templates/settings',
                        url_prefix='/settings')


@settings_bp.route('/', methods=['GET', 'POST'])
@login_required
def view_settings():
    if request.method == 'POST':
        form_name = request.form.get('form_name')

        if form_name == 'change_theme':
            new_theme = request.form.get('theme', 'dark')  # Default to 'dark' if not provided
            if new_theme in ['light', 'dark']:  # Validate theme value
                session['theme'] = new_theme  # Always update the session for immediate effect

                # --- Save theme preference to the database ---
                from app import db  # Local import
                from app.models import Settings  # Local import

                user_settings = Settings.query.filter_by(user_id=current_user.id).first()
                if not user_settings:  # If no settings record exists for the user, create one
                    user_settings = Settings(user_id=current_user.id)
                    db.session.add(user_settings)

                user_settings.theme = new_theme  # Update the theme attribute

                try:
                    db.session.commit()
                    record_activity('theme_change_db', f"Theme changed to {new_theme} and saved to DB.")
                    flash(f'Theme preference updated to {new_theme.title()} and saved.', 'success')
                except Exception as e:
                    db.session.rollback()
                    current_app.logger.error(f"Could not save theme to DB for user {current_user.username}: {e}",
                                             exc_info=True)
                    record_activity('theme_change_session_only',
                                    f"Theme changed to {new_theme} (session only, DB save failed).")
                    flash(f'Theme preference updated for this session, but could not save permanently: {str(e)}',
                          'warning')
                # --- End of database saving logic ---

            else:
                flash('Invalid theme selected.', 'warning')
            return redirect(url_for('settings.view_settings'))

        # Add handling for other forms if this page manages more settings later
        # elif form_name == 'other_settings_form':
        #     pass

    # For GET request, or if POST was not for a known form
    return render_template('settings.html', title='User Settings')