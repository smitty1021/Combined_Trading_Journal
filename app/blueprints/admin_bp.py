from flask import (Blueprint, render_template, current_app, request,
                   redirect, url_for, flash, abort, jsonify)  # Added abort
from flask_login import login_required, current_user

from app import db
from app.models import User, UserRole, Activity  # Ensure Activity is imported for deletion
from app.forms import AdminCreateUserForm, AdminEditUserForm
from app.utils import admin_required, record_activity, generate_token, send_email  # Added generate_token, send_email

admin_bp = Blueprint('admin', __name__,
                     template_folder='../templates/admin',
                     url_prefix='/admin')


@admin_bp.route('/dashboard')
@login_required
@admin_required
def show_admin_dashboard():
    total_users = "N/A"
    try:
        total_users = User.query.count()
        current_app.logger.info(f"Admin {current_user.username} accessed admin dashboard.")
    except Exception as e:
        current_app.logger.error(f"Error fetching admin dashboard stats: {e}", exc_info=True)
        flash("Could not load all dashboard statistics.", "warning")
    return render_template('dashboard.html', title='Admin Dashboard', total_users=total_users)


@admin_bp.route('/users')
@login_required
@admin_required
def admin_users_list():
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('ITEMS_PER_PAGE', 10)
    users_on_page, users_pagination, total_users_count, active_users_count, admin_users_count = [], None, 0, 0, 0
    try:
        users_pagination = User.query.order_by(User.username.asc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        users_on_page = users_pagination.items
        total_users_count = users_pagination.total
        active_users_count = User.query.filter_by(is_active=True).count()
        admin_users_count = User.query.filter_by(role=UserRole.ADMIN).count()
        current_app.logger.info(f"Admin {current_user.username} accessed user list page {page}.")
    except Exception as e:
        current_app.logger.error(f"Error fetching user list for admin: {e}", exc_info=True)
        flash("Could not load user list.", "danger")
        total_users_count = active_users_count = admin_users_count = "Error"
    return render_template('users.html', title='User Management',
                           users=users_on_page, pagination=users_pagination,
                           total_users_count=total_users_count,
                           active_users_count=active_users_count,
                           admin_users_count=admin_users_count,
                           UserRole=UserRole)


@admin_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_create_user():
    form = AdminCreateUserForm()
    if form.validate_on_submit():
        if User.find_by_username(form.username.data):
            flash('Username already exists.', 'danger')
        elif User.find_by_email(form.email.data):
            flash('Email address is already registered.', 'danger')
        else:
            try:
                new_user = User(
                    username=form.username.data,
                    email=form.email.data.lower(),
                    name=form.name.data if form.name.data else None,
                    role=UserRole(form.role.data),
                    is_active=form.is_active.data,
                    is_email_verified=form.is_email_verified.data
                )
                new_user.set_password(form.password.data)
                db.session.add(new_user)
                db.session.commit()
                flash_message = f'User "{new_user.username}" created successfully'
                flash_category = 'success'
                if not new_user.is_email_verified:
                    token = generate_token(new_user.email, salt='email-verification-salt')
                    verification_url = url_for('auth.verify_email', token=token, _external=True)
                    email_sent = send_email(
                        to=new_user.email,
                        subject="Your Account Was Created - Verify Your Email",
                        template_name="verify_email.html",
                        username=new_user.username,
                        verification_url=verification_url
                    )
                    if email_sent:
                        flash_message += ". A verification email has been sent."
                    else:
                        flash_message += ". Verification email could not be sent."
                        flash_category = 'warning'
                record_activity('admin_user_create', f"Admin {current_user.username} created user: {new_user.username}",
                                user_id_for_activity=current_user.id)
                flash(flash_message, flash_category)
                return redirect(url_for('admin.admin_users_list'))
            except ValueError:
                flash('Invalid role selected.', 'danger')
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error creating user by admin {current_user.username}: {e}", exc_info=True)
                flash(f'An error occurred: {str(e)}', 'danger')
    elif request.method == 'POST':
        flash('Please correct form errors.', 'warning')
    return render_template('create_user.html', title='Create New User', form=form)


@admin_bp.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_user(user_id):
    user_to_edit = User.query.get_or_404(user_id)
    form = AdminEditUserForm(obj=user_to_edit)
    if request.method == 'GET':  # Pre-populate role correctly for GET
        form.role.data = user_to_edit.role.value if user_to_edit.role else None

    if form.validate_on_submit():
        if form.username.data != user_to_edit.username and User.query.filter(User.username == form.username.data,
                                                                             User.id != user_id).first():
            flash('That username is already taken.', 'danger')
        elif form.email.data.lower() != user_to_edit.email and User.query.filter(User.email == form.email.data.lower(),
                                                                                 User.id != user_id).first():
            flash('That email address is already registered.', 'danger')
        else:
            try:
                user_to_edit.username = form.username.data
                if user_to_edit.email != form.email.data.lower():  # If email changed
                    user_to_edit.email = form.email.data.lower()
                    user_to_edit.is_email_verified = False  # Require re-verification if admin doesn't check the box
                    # Or send new verification email
                user_to_edit.name = form.name.data if form.name.data else None
                user_to_edit.role = UserRole(form.role.data)
                user_to_edit.is_active = form.is_active.data
                user_to_edit.is_email_verified = form.is_email_verified.data  # Allow admin to set this

                if form.new_password.data:
                    user_to_edit.set_password(form.new_password.data)
                    flash('User password has been updated.', 'info')

                db.session.commit()
                record_activity('admin_user_edit',
                                f"Admin {current_user.username} edited user: {user_to_edit.username}",
                                user_id_for_activity=current_user.id)
                flash(f'User "{user_to_edit.username}" updated.', 'success')
                return redirect(url_for('admin.admin_users_list'))
            except ValueError:
                flash('Invalid role selected.', 'danger')
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error editing user {user_id} by admin {current_user.username}: {e}",
                                         exc_info=True)
                flash(f'An error occurred: {str(e)}', 'danger')
    elif request.method == 'POST':
        flash('Please correct form errors.', 'warning')
    return render_template('edit_user.html', title='Edit User', form=form, user_id=user_id,
                           username=user_to_edit.username)


@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_user(user_id):
    user_to_delete = User.query.get_or_404(user_id)
    if user_to_delete.id == current_user.id:
        flash("You cannot delete your own account.", 'danger')
        return redirect(url_for('admin.admin_users_list'))
    if user_to_delete.is_admin() and User.query.filter_by(role=UserRole.ADMIN).count() <= 1:
        flash("Cannot delete the last admin account.", 'warning')
        return redirect(url_for('admin.admin_users_list'))

    try:
        username_for_log = user_to_delete.username
        # Handle related data (e.g., reassign or delete user's files, models, trades, journals)
        # This example only deletes activities. Ensure cascade settings or manual deletion for other models.
        Activity.query.filter_by(user_id=user_id).delete()
        # If File model has user_id and cascade is not set to delete orphans, you might need:
        # File.query.filter_by(user_id=user_id).delete() (after deleting actual files from disk)
        # Similar logic for TradingModel, Trade, DailyJournal etc. if not cascaded from User model.

        db.session.delete(user_to_delete)
        db.session.commit()
        record_activity('admin_user_delete', f"Admin {current_user.username} deleted user: {username_for_log}",
                        user_id_for_activity=current_user.id)
        flash(f'User "{username_for_log}" has been deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting user {user_id} by admin {current_user.username}: {e}", exc_info=True)
        flash(f'Error deleting user: {str(e)}', 'danger')
    return redirect(url_for('admin.admin_users_list'))

# ... (after admin_delete_user route) ...

@admin_bp.route('/users/bulk_delete', methods=['POST'])
@login_required
@admin_required
def admin_bulk_delete_users():
    """Handles bulk deletion of users by an admin."""
    data = request.get_json()
    if not data or 'user_ids' not in data:
        return jsonify({'status': 'error', 'message': 'Missing user_ids parameter.'}), 400

    user_ids_to_delete_str = data['user_ids']
    if not isinstance(user_ids_to_delete_str, list):
        return jsonify({'status': 'error', 'message': 'user_ids must be a list.'}), 400

    deleted_count = 0
    skipped_count = 0
    skipped_users_info = [] # To store reasons for skipping

    # Convert string IDs to integers and filter out invalid ones
    user_ids_to_delete = []
    for user_id_str_item in user_ids_to_delete_str:
        try:
            user_ids_to_delete.append(int(user_id_str_item))
        except ValueError:
            skipped_count += 1
            skipped_users_info.append(f"Invalid User ID format: {user_id_str_item}")
            current_app.logger.warning(f"Admin bulk delete: Invalid user ID format {user_id_str_item}.")

    if not user_ids_to_delete: # If all provided IDs were invalid or list was empty
         if skipped_count > 0: # Only invalid IDs were provided
             return jsonify({'status': 'error', 'message': 'No valid user IDs provided for deletion.', 'skipped_info': skipped_users_info}), 400
         else: # Empty list of IDs was provided
             return jsonify({'status': 'info', 'message': 'No users selected for deletion.'}), 200


    # It's safer to commit changes for each user individually or collect all operations
    # and do one commit, but individual commits with try/except give more granular feedback.
    # However, for bulk operations, a single transaction might be preferred.
    # The v3 app did a final commit. Let's try to delete valid users.

    admin_users_total_in_db = User.query.filter_by(role=UserRole.ADMIN).count()

    for user_id in user_ids_to_delete:
        if user_id == current_user.id:
            skipped_count += 1
            skipped_users_info.append(f"User ID {user_id} (cannot delete self)")
            current_app.logger.warning(f"Admin bulk delete: Skipped deleting current user (ID: {user_id}).")
            continue

        user_to_delete = User.query.get(user_id)
        if not user_to_delete:
            skipped_count += 1
            skipped_users_info.append(f"User ID {user_id} (not found)")
            current_app.logger.warning(f"Admin bulk delete: User ID {user_id} not found.")
            continue

        # Prevent deleting the last admin if this user is an admin and is part of the current deletion batch
        is_last_admin_check = False
        if user_to_delete.is_admin():
            # This check needs to be careful if multiple admins are in the deletion list
            # A simpler check: if this user is admin AND after this deletion admin_users_total_in_db would be 0
            # This needs refinement if deleting multiple admins at once.
            # For simplicity, if only one admin exists, don't delete them.
            if admin_users_total_in_db <= 1:
                skipped_count += 1
                skipped_users_info.append(f"{user_to_delete.username} (cannot delete last admin)")
                current_app.logger.warning(f"Admin bulk delete: Skipped deleting last admin {user_to_delete.username}.")
                continue

        username_for_log = user_to_delete.username
        try:
            # Handle related data (cascade settings in models.py are preferred)
            # Explicitly delete activities if not cascaded properly or for logging
            Activity.query.filter_by(user_id=user_id).delete()
            # Add deletion for Files on disk if File model doesn't handle it via events/cascade
            # user_files = File.query.filter_by(user_id=user_id).all()
            # for file_record in user_files:
            #     file_disk_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file_record.filepath)
            #     if os.path.exists(file_disk_path): os.remove(file_disk_path)
            #     db.session.delete(file_record) # If cascade delete not set on User.files

            db.session.delete(user_to_delete)
            # If an admin was successfully marked for deletion, decrement count for subsequent checks in this batch
            if user_to_delete.is_admin():
                admin_users_total_in_db -=1

            record_activity('admin_bulk_user_delete',
                            f"Admin {current_user.username} bulk deleted user: {username_for_log} (ID: {user_id})",
                            user_id_for_activity=current_user.id) # Log against the admin performing action
            deleted_count += 1
            current_app.logger.info(f"Admin bulk delete: Marked user {username_for_log} (ID: {user_id}) for deletion.")
        except Exception as e:
            # db.session.rollback() # Rollback for this specific user might be complex if batching
            skipped_count += 1
            skipped_users_info.append(f"{username_for_log} (error: {str(e)})")
            current_app.logger.error(f"Admin bulk delete: Error marking user ID {user_id} for deletion: {e}", exc_info=True)

    try:
        db.session.commit() # Commit all successful deletions (and activity logs if not auto-committed)
        message = f"Bulk delete completed. Successfully deleted: {deleted_count} user(s)."
        status = 'success'
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Admin bulk delete: Error during final commit: {e}", exc_info=True)
        message = f'An error occurred during the final commit of deletions: {str(e)}'
        status = 'error'
        # Reset counts if commit failed
        deleted_count = 0
        # skipped_count might need re-evaluation if we don't know which ones failed to commit

    if skipped_count > 0:
        message += f" Skipped: {skipped_count} user(s)."
        if skipped_users_info:
             message += f" Details: {'; '.join(skipped_users_info)}."

    flash(message, status if status == 'success' and deleted_count > 0 else ('warning' if skipped_count > 0 else 'danger'))
    return jsonify({'status': status, 'message': message, 'deleted_count': deleted_count, 'skipped_count': skipped_count, 'skipped_info': skipped_users_info})