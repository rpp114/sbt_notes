from flask import Blueprint

bp = Blueprint('evaluation', __name__,
               template_folder='templates',
               static_folder='static')#,
            #    static_url_path='/static/evaluation')

from . import routes, models
