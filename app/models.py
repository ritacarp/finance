from datetime import datetime
from time import time
from app import db, login
from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy_utils import force_instant_defaults



class Users(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    hash = db.Column(db.String, nullable=True)
    cash = db.Column(db.Float, nullable=True)
    mobile = db.Column(db.String, nullable=True)
    comments = db.Column(db.String, nullable=True)
    orders = db.relationship('Orders', backref='custoner', lazy=True)

    def __repr__(self):
        return '<Person: User Name: {}, Email: {}, hash: {}, comments: {}>'.format(self.username, self.email, self.hash, self.comments)    

    def set_password(self, password):
        self.hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hash, password)

@login.user_loader
def load_user(id):
    return Users.query.get(int(id))


class Orders(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'),  nullable=False)
    type = db.Column(db.String, nullable=True)
    symbol = db.Column(db.String, nullable=True)
    name = db.Column(db.String, nullable=True)
    shares = db.Column(db.Integer, nullable=True)
    price = db.Column(db.Float, nullable=True)
    extended_price = db.Column(db.Float, nullable=True)
    order_date = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)