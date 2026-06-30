from muscles import ValueObject


class EmailAddress(ValueObject):
    def normalize(self, value):
        # RU: ValueObject нормализует значение до проверки и сохранения.
        # EN: ValueObject normalizes the value before validation and storage.
        return str(value).strip().lower()

    def validate(self, value):
        # RU: Для примера нужна простая проверка; production-валидация может быть строже.
        # EN: The example needs a simple check; production validation may be stricter.
        if "@" not in value:
            raise ValueError("email must contain @")
        return True
