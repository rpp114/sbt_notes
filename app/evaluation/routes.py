
from flask import request, render_template
from flask_login import login_required

from app.evaluation import bp
from app import db, models


@bp.route('/', methods = ['GET'])
@login_required
def index():
    print('in the blueprint index')
    user = models.User.query.get(1)
    print(user)
    return render_template('evaluation/index.html')