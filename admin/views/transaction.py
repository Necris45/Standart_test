from flask import flash, redirect, request
from flask_admin.contrib.sqla import ModelView
from wtforms import validators
from flask_admin import expose
from flask_admin.model import template
from flask_admin.babel import gettext
from flask_admin.helpers import get_redirect_target
from flask_admin.model.helpers import get_mdict_item_or_list

class TransactionView(ModelView):
    column_display_pk = True
    can_edit = True
    can_create = False
    can_delete = False
    can_view_details = True
    edit_modal = False

    # form_args = {
    #     'username': dict(label='ЮЗЕР', validators=[validators.DataRequired()]),
    #     'password': dict(label='ПАРОЛЬ', validators=[validators.DataRequired()]),
    # }

    column_list = ['id', 'sum', 'comision', 'status', 'created_at', 'user_id']
    column_labels = {
        'id': 'ID',
        'sum': 'Сумма',
        'comision': 'Размер комисcии',
        'status': 'Статус транзакции',
        'created_at': 'Дата и время создания',
        'user_id': 'ID пользователя'
    }
    # column_editable_list = ['status']
    form_columns = ['status']
    # form_columns = ['sum', 'comision', 'status', 'created_at', 'user_id']

    AVAILABLE_STATUS_TYPES = [
        (1, u'Подтверждена'),
        (2, u'Отменена')
    ]

    form_choices = {
        'status': AVAILABLE_STATUS_TYPES
    }

    column_filters = ['user_id', 'status']

    @expose('/edit/', methods=('GET', 'POST'))
    def edit_view(self):
        """This code was copied from the
           flask_admin.model.base.BaseModelView.edit_view method"""
        return_url = get_redirect_target() or self.get_url('.index_view')

        id = get_mdict_item_or_list(request.args, 'id')
        if id is None:
            return redirect(return_url)
        model = self.get_one(id)

        if model is None:
            flash(gettext('Record does not exist. '), 'error')
            return redirect(return_url)
        if model.status != 0:
            flash(gettext('You can not change this status. '), 'error')
            return redirect(return_url)

        return super(TransactionView, self).edit_view()
