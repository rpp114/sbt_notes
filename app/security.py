
import app
from flask_security import Security, SQLAlchemyUserDatastore

user_datastore = SQLAlchemyUserDatastore(app.db, app.models.User, app.models.Role)
security = Security(app, user_datastore)
