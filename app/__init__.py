from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_admin import Admin

db = SQLAlchemy()
login_manager = LoginManager()
admin = Admin()
migrate = Migrate()

def create_app():
    app = Flask(__name__)

    # ✅ LOAD CONFIG CORRECTLY
    app.config.from_object("sbt_notes.config")

    # ✅ INIT EXTENSIONS AFTER CONFIG
    db.init_app(app)
    login_manager.init_app(app)
    admin.init_app(app)
    migrate.init_app(app, db)

    # ✅ REGISTER BLUEPRINTS
    from sbt_notes.app.evaluation import bp as eval_bp
    app.register_blueprint(eval_bp, url_prefix="/evaluation")
    
    from sbt_notes.app.views import bp as main_bp
    app.register_blueprint(main_bp)

    # ✅ Import views/models LAST (avoid circular imports)
    from sbt_notes.app import views, models, admin as admin_views  # noqa: F401

    return app

# uWSGI will import this
app = create_app()


