from flask_admin.contrib.sqla import ModelView

class TransactionView(ModelView):
    can_edit = True
    can_create = True
    can_delete = True
    can_view_details = True

    form_columns = ['id', 'sum', 'comision', 'status', 'user_id']