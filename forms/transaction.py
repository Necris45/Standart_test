from wtforms.fields import StringField

class ReadOnlyStringField(StringField):
    @staticmethod
    def readonly_condition():
        # Dummy readonly condition
        return False

    def __call__(self, *args, **kwargs):
        # Adding `readonly` property to `input` field
        if self.readonly_condition():
            kwargs.setdefault('readonly', True)
        return super(ReadOnlyStringField, self).__call__(*args, **kwargs)

    def populate_obj(self, obj, name):
        # Preventing application from updating field value
        # (user can modify web page and update the field)
        if not self.readonly_condition():
            super(ReadOnlyStringField, self).populate_obj(obj, name)
