import hashlib
import datetime
import click
import requests
from flask import Flask, render_template, redirect, url_for, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_admin import Admin, BaseView, expose, AdminIndexView, helpers
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from wtforms import form, fields, validators
from werkzeug.security import generate_password_hash, check_password_hash

import constants
from admin.views.userviews import UserView
from admin.views.transaction import TransactionView

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)


class User(db.Model):
    __table_name__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    balance = db.Column(db.Float, default=0)
    comision_rate = db.Column(db.Float, default=0.1)
    webhook = db.Column(db.String, default='')
    role = db.Column(db.Integer, default=1)
    # transaction_owner = db.relationship("Transaction")

    # Flask-Login integration
    # def is_authenticated(self):
    #     return True
    #
    # def is_active(self):
    #     return True
    #
    # def is_anonymous(self):
    #     return False
    #
    # def get_id(self):
    #     return self.id
    #
    # # Required for administrative interface
    # def __unicode__(self):
    #     return self.username


class Transaction(db.Model):
    __table_name__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    sum = db.Column(db.Float, default=0.0)
    comision = db.Column(db.Float, default=10)
    status = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class DashBoardView(AdminIndexView):
    @expose('/')
    def add_data_db(self):
        user_count = User.query.count()
        transaction_count = Transaction.query.count()
        transaction_sum_by_day = 0
        date = datetime.datetime.now() - datetime.timedelta(days=1)
        all_transaction = Transaction.query.filter(Transaction.created_at >= date).all()
        for transaction in all_transaction:
            transaction_sum_by_day += transaction.sum
        last_transaction = Transaction.query.order_by(Transaction.created_at.desc()).limit(10).all()

        return self.render('admin/dashboardindex.html', user_count=user_count,
                           transaction_count=transaction_count, transaction_sum_by_day=transaction_sum_by_day,
                           last_transaction=last_transaction)


admin = Admin(app, name='Стандарт', index_view=DashBoardView(), endpoint='admin')
admin.add_view(UserView(User, db.session, name='Пользователь'))
admin.add_view(TransactionView(Transaction, db.session, name='Транзакции'))



@app.cli.command("create-admin")
@click.argument("name")
@click.argument("password")
def create_user(name, password):
    hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
    new_user = User()
    new_user.username = name
    new_user.password = hashed_password
    new_user.role = 0
    db.session.add(new_user)
    db.session.commit()
    return 'Done'


if __name__ == "__main__":
    app.run(debug=True)
