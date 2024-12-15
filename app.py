import hashlib

import click
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
    transaction_owner = db.relationship("Transaction")

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
    comision = db.Column(db.Float, default=0.1)
    status = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


# class MyUserAdmin(ModelView):
#   excluded_list_columns = ('password',)

def count_user():
    count = db.session.query(User).count()
    return count


def count_transaction():
    count = db.session.query(Transaction).count()
    return count

#
# @app.route('/users_count')
# def users():
#     x = count_user()
#     y = count_transaction()
#     return f'users = {x}, transaction = {y}'


class MyView(BaseView):
    @expose('/')
    def index(self):
        # data = [{'title': 'count_user', 'count': count_user()},
        #         {'title': 'count_transaction', 'count': count_transaction()}]
        # print(data)
        data = ['username', 'password', 'balance', 'comision_rate', 'webhook', 'role']
        return self.render('index.html', jsondata=data)

    # def is_accessible(self):
    #     return current_user.is_authenticated()


admin = Admin(app)
admin.add_view(MyView(name='Dashboard'))
admin.add_view(UserView(User, db.session))
admin.add_view(TransactionView(Transaction, db.session))


@app.cli.command("create-admin")
@click.argument("name")
def create_user(name):
    try:
        hashed_password = hashlib.sha256(name.encode('utf-8')).hexdigest()
        new_user = User(name, hashed_password, role=0)
        print(new_user)
        db.session.add(new_user)
        db.session.commit()
        return 'Done'
    except Exception as e:
        db.session.rollback()
        return f'Error: {e}'


if __name__ == "__main__":
    app.run(debug=True)
