from flask_admin.contrib.sqla import ModelView

class UserView(ModelView):
    can_edit = True
    can_create = True
    can_delete = True
    can_view_details = True

    form_columns = ['username', 'password', 'balance', 'comision_rate', 'webhook', 'role']

    column_exclude_list = ('password',)
