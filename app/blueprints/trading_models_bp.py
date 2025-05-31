from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app import db  # Import db from the app package (app/__init__.py)
from app.models import TradingModel  # Import your TradingModel from app/models.py
from app.forms import TradingModelForm  # Import your TradingModelForm from app/forms.py

# Utils might be needed later if you add more complex parsing not handled by WTForms directly
# from app.utils import _parse_form_float # Example if needed

# Define the blueprint:
# 'trading_models' is the name of the blueprint.
# __name__ is the import name of the package where the blueprint is defined.
# template_folder='../templates/models' tells Flask where to look for this blueprint's templates,
# relative to this blueprint file's location.
trading_models_bp = Blueprint('trading_models', __name__,
                              template_folder='../templates/models')


# You can also specify a static_folder if this blueprint has its own static files

@trading_models_bp.route('/')
@login_required
def view_trading_models_list():
    """Displays a list of all trading models for the currently logged-in user."""
    current_app.logger.info(f"User {current_user.username} viewing their trading models list.")
    # Filter models by the current_user's id
    models = TradingModel.query.filter_by(user_id=current_user.id).order_by(TradingModel.name).all()
    return render_template('view_trading_models_list.html', models=models, title="Your Trading Models")


@trading_models_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_trading_model():
    """Handles the creation of a new trading model."""
    form = TradingModelForm()
    if form.validate_on_submit():
        name = form.name.data.strip()
        # Check if a model with the same name already exists for THIS user
        existing_model = TradingModel.query.filter_by(name=name, user_id=current_user.id).first()
        if existing_model:
            flash(f'A trading model with the name "{name}" already exists for you. Please choose a different name.',
                  'warning')
        else:
            new_model = TradingModel(user_id=current_user.id)  # Associate with the logged-in user
            form.populate_obj(new_model)  # Populates the new_model object with form data

            db.session.add(new_model)
            try:
                db.session.commit()
                current_app.logger.info(f"User {current_user.username} added new trading model: {name}")
                flash(f'Trading model "{name}" has been added successfully!', 'success')
                return redirect(url_for('trading_models.view_trading_models_list'))
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error adding trading model for user {current_user.username}: {e}",
                                         exc_info=True)
                flash(f'An error occurred while adding the trading model: {str(e)}', 'danger')
    else:
        if request.method == 'POST':  # If form submitted but not valid
            flash('Please correct the errors in the form.', 'danger')

    return render_template('add_trading_model.html', title="Add New Trading Model", form=form)


@trading_models_bp.route('/edit/<int:model_id>', methods=['GET', 'POST'])
@login_required
def edit_trading_model(model_id):
    """Handles editing an existing trading model."""
    # Fetch the model ensuring it belongs to the current user
    model_to_edit = TradingModel.query.filter_by(id=model_id, user_id=current_user.id).first_or_404()
    form = TradingModelForm(obj=model_to_edit)  # Pre-populate the form with the model's current data

    if form.validate_on_submit():
        new_name = form.name.data.strip()
        # Check if another model (excluding the current one) by the same user has the new name
        conflicting_model = TradingModel.query.filter(
            TradingModel.name == new_name,
            TradingModel.id != model_id,  # Exclude the current model being edited
            TradingModel.user_id == current_user.id
        ).first()

        if conflicting_model:
            flash(f'Another trading model with the name "{new_name}" already exists for you.', 'warning')
        else:
            form.populate_obj(model_to_edit)  # Update the model_to_edit object with new form data
            try:
                db.session.commit()
                current_app.logger.info(
                    f"User {current_user.username} edited trading model ID: {model_id}, Name: {new_name}")
                flash(f'Trading model "{model_to_edit.name}" has been updated successfully!', 'success')
                return redirect(url_for('trading_models.view_trading_models_list'))
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(
                    f"Error updating trading model ID {model_id} for user {current_user.username}: {e}", exc_info=True)
                flash(f'An error occurred while updating the trading model: {str(e)}', 'danger')
    elif request.method == 'POST':  # If form submitted but not valid
        flash('Please correct the errors in the form before saving.', 'danger')

    return render_template('edit_trading_model.html', title="Edit Trading Model", form=form, model=model_to_edit)


@trading_models_bp.route('/delete/<int:model_id>', methods=['POST'])  # Use POST for delete actions
@login_required
def delete_trading_model(model_id):
    """Handles deleting a trading model."""
    # Fetch the model ensuring it belongs to the current user
    model_to_delete = TradingModel.query.filter_by(id=model_id, user_id=current_user.id).first_or_404()

    # Check if the model is associated with any trades before deleting
    if model_to_delete.trades.first():
        flash(
            f'Cannot delete model "{model_to_delete.name}" as it is currently associated with existing trades. Please mark it as inactive or reassign trades first.',
            'danger')
        return redirect(url_for('trading_models.view_trading_models_list'))

    try:
        model_name_for_log = model_to_delete.name  # Get name before deleting
        db.session.delete(model_to_delete)
        db.session.commit()
        current_app.logger.info(
            f"User {current_user.username} deleted trading model: {model_name_for_log} (ID: {model_id})")
        flash(f'Trading model "{model_name_for_log}" has been deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting trading model ID {model_id} for user {current_user.username}: {e}",
                                 exc_info=True)
        flash(f'An error occurred while deleting the trading model: {str(e)}', 'danger')

    return redirect(url_for('trading_models.view_trading_models_list'))