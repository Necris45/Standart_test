from flask_admin.contrib.sqla import ModelView

class UserView(ModelView):
    column_display_pk = True
    can_edit = True
    can_create = True
    can_delete = True
    can_view_details = False
    create_modal = True
    edit_modal = True
    column_labels = {
        'id': 'ID',
        'username': 'Имя пользователя',
        'balance': 'Баланс',
        'comision_rate': 'Размер комиссии',
        'webhook': 'Вебхук',
        'role': 'Роль'
    }
    form_columns = ['username', 'password', 'balance', 'comision_rate', 'webhook', 'role']

    column_exclude_list = ('password',)

    AVAILABLE_USER_TYPES = [
        (0, u'Админ'),
        (1, u'Пользователь')
    ]

    form_choices = {
        'role': AVAILABLE_USER_TYPES
    }