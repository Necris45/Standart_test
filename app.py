import hashlib
import datetime
import click
from flasgger import Swagger, swag_from
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_admin import Admin, expose, AdminIndexView
from tasks import flask_app, long_running_task
from celery.result import AsyncResult
from flask import request, jsonify

from admin.views.userviews import UserView
from admin.views.transaction import TransactionView

flask_app.secret_key = 'your_secret_key'
flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(flask_app)
migrate = Migrate(flask_app, db)

swagger = Swagger(flask_app, template={
    "info": {
        "title": "My Flask API",
        "description": "An example API using Flask and Swagger",
        "version": "1.0.0"
    }
})


class User(db.Model):
    __table_name__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    balance = db.Column(db.Float, default=0)
    comision_rate = db.Column(db.Float, default=0.1)
    webhook = db.Column(db.String, default='')
    role = db.Column(db.Integer, default=1)


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


admin = Admin(flask_app, name='Стандарт', index_view=DashBoardView(), endpoint='admin')
admin.add_view(UserView(User, db.session, name='Пользователь'))
admin.add_view(TransactionView(Transaction, db.session, name='Транзакции'))


def check_user_id(id):
    return User.query.filter_by(id=id).first()

def check_transaction_id(id):
    return Transaction.query.filter_by(id=id).first()


def status_to_text(status_id):
    statuses = {0: "Ожидание",
                1: "Подтверждена",
                2: "Отменена",
                3: "Истекла"}
    return statuses[status_id]


@flask_app.post("/trigger_task")
def start_task() -> dict[str, object]:
    iterations = request.args.get('iterations')
    print(iterations)
    result = long_running_task.delay(int(iterations))
    return {"result_id": result.id}


@flask_app.get("/get_result")
def task_result() -> dict[str, object]:
    result_id = request.args.get('result_id')
    result = AsyncResult(result_id)  # -Line 4
    if result.ready():  # -Line 5
        # Task has completed
        if result.successful():  # -Line 6

            return {
                "ready": result.ready(),
                "successful": result.successful(),
                "value": result.result,  # -Line 7
            }
        else:
            # Task completed with an error
            return jsonify({'status': 'ERROR', 'error_message': str(result.result)})
    else:
        # Task is still pending
        return jsonify({'status': 'Running'})


@swagger.validate('CreateTransaction')
@flask_app.route('/create_transaction', methods=['POST'])
def create_transaction():
    """
    post endpoint
    ---
    tags:
      - create_transaction
    parameters:
      - name: body
        in: body
        required: true
        schema:
          id: Transaction

          properties:
            user_id:
              type: integer
              required: true
              description: Owner .
            sum:
              type: float
              required: true
              description: sum of transaction
            transaction_id:
              type: integer
              description: arbitrary id
    responses:
      200:
        description: The product inserted in the database
        schema:
          $ref: '#/definitions/Transaction'
    """
    if not request.json or not 'sum' in request.json:
        return 'not found sum', 400
    data = request.get_json(force=True)
    if 'transaction_id' in request.json and 'user_id' in request.json:
        if check_transaction_id(data.get('transaction_id')):
            return 'transaction with this transaction_id already exist', 400
        user = check_user_id(data.get('user_id'))
        if not user:
            return 'not found user', 400
        try:
            new_transaction = Transaction()
            new_transaction.sum = data.get('sum')
            new_transaction.comision = data.get('sum') * user.comision_rate
            new_transaction.user_id = user.id
            db.session.add(new_transaction)
            db.session.commit()
            answer = {"status": "transaction create",
                      "new_transaction_id": new_transaction.id}
            return jsonify(answer), 201
        except Exception as e:
            db.session.rollback()
            return f'error: {e}', 400
    return 'not found user_id', 400


@flask_app.route('/cancel_transaction', methods=['POST'])
def cancel_transaction():
    if not request.json or not 'transaction_id' in request.json:
        return 'not found transaction_id', 400
    data = request.get_json(force=True)
    if 'transaction_id' in request.json and 'user_id' in request.json:
        canceled_transaction = check_transaction_id(data.get('transaction_id'))
        if canceled_transaction is None:
            return 'not found transaction with this id', 400
        if canceled_transaction.status != 0:
            return 'this transaction can not be canceled'
        user = check_user_id(data.get('user_id'))
        if not user:
            return 'not found user', 400
        if canceled_transaction.user_id != user.id:
            return 'wrong id', 400
        try:
            canceled_transaction.status = 2
            db.session.commit()
            answer = {"status": "transaction canceled",
                      "canceled_transaction_id": canceled_transaction.id}
            return jsonify(answer), 201
        except Exception as e:
            db.session.rollback()
            return f'error: {e}', 400
    return 'not found transaction_id', 400


@flask_app.route('/check_transaction', methods=['GET'])
def check_transaction():
    user_id = request.args.get('user_id')
    transaction_id = request.args.get('transaction_id')
    if transaction_id and user_id:
        user = check_user_id(user_id)
        if user:
            finded_transaction = check_transaction_id(transaction_id)
            if finded_transaction:
                if finded_transaction.user_id == user.id:
                    status = status_to_text(finded_transaction.status)
                    answer = {'id': finded_transaction.id,
                              'sum': finded_transaction.sum,
                              'comision': finded_transaction.comision,
                              'status': status}
                    return jsonify(answer)
                return 'wrong user_id', 400
            return 'not found transaction with this id', 400
        return 'not found user', 400
    return 'not found transaction_id or user_id', 400


transaction_create_schema = swagger.get_schema('transaction')

@flask_app.cli.command("create-admin")
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
    flask_app.run(debug=True)
