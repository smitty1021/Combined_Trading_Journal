from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import Activity # Import the Activity model

main_bp = Blueprint('main', __name__,
                    template_folder='../templates/main')

@main_bp.route('/')
@main_bp.route('/index') # You can have multiple routes for the same function
@login_required
def index():
    # Pass the Activity model to the template context so it can be used for ordering
    return render_template('index.html', title="Dashboard", Activity=Activity)