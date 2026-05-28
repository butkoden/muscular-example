from muscles import ValueObject


class EmailAddress(ValueObject):
    def normalize(self, value):
        return str(value).strip().lower()

    def validate(self, value):
        if "@" not in value:
            raise ValueError("email must contain @")
        return True
