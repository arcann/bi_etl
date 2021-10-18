class BulkLoaderException(Exception):
    def __init__(self, base_exception, message=None, password=None):
        self.base_exception = base_exception
        self.message = str(base_exception)
        if message is not None:
            self.message += message
        if password is not None:
            self.remove_password(password)
        self.errors_set = set()

    def add_error(self, error):
        self.errors_set.add(str(error))

    def remove_password(self, password):
        if password in self.message:
            self.message = self.message.replace(password, '*' * 8)

    def __repr__(self):
        return f"BulkLoaderException({type(self.base_exception)},message=({str(self)})"

    def __str__(self):
        msg = f"{self.message})"
        if len(self.errors_set) > 0:
            msg += '\n'
            msg += 'BULK LOAD ERROR SUMMARY:\n'
            msg += '------------------------\n'
            msg += '\n'.join(self.errors_set)
        return msg
