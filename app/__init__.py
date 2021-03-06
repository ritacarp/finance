from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_moment import Moment

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'
login.login_message = "Please log in"
moment = Moment(app)


from app import routes, models

from app.helpers import usd, stringSlice

# Custom filter
app.jinja_env.filters["usd"] = usd
app.jinja_env.filters['stringSlice'] = stringSlice
