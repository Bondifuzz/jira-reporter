class DatabaseError(Exception):
    """Base exception for all database errors"""


class DBAlreadyExistsError(DatabaseError):
    pass


class DBRecordNotFoundError(DatabaseError):
    pass


class DBFuzzerNotFoundError(DBRecordNotFoundError):
    pass
