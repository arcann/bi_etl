class BulkLoaderException(Exception):
    """Wraps the exception from a bulk load, hiding any password and collecting a summary of the load errors."""

    def __init__(self, base_exception, message=None, password=None):
        """
        Parameters
        ----------
        base_exception:
            The exception that caused the failure. Its text starts the message.
        message:
            Optional text appended to the message.
        password:
            Optional password to replace with asterisks in the message (see :meth:`remove_password`).
        """

        self.base_exception = base_exception
        self.message = str(base_exception)
        if message is not None:
            self.message += message
        if password is not None:
            self.remove_password(password)
        self.errors_set = set()
        super().__init__(self.message)

    def add_error(self, error):
        """
        Add an error to the summary shown by :meth:`__str__`. Duplicates are ignored.

        Parameters
        ----------
        error:
            The error, converted with ``str``.
        """
        self.errors_set.add(str(error))

    def remove_password(self, password):
        """
        Replace every occurrence of *password* in the message with asterisks.

        Parameters
        ----------
        password:
            The text to hide.
        """
        if password in self.message:
            self.message = self.message.replace(password, '*' * 8)

    def __repr__(self):
        """Return the type of the base exception and the message with the error summary."""
        return f"BulkLoaderException({type(self.base_exception)},message='{str(self)}')"

    def __str__(self):
        """Return the message, followed by a summary of the errors added with :meth:`add_error` if there are any."""
        msg = f"{self.message}"
        if len(self.errors_set) > 0:
            msg += '\n'
            msg += 'BULK LOAD ERROR SUMMARY:\n'
            msg += '------------------------\n'
            msg += '\n'.join(self.errors_set)
        return msg
