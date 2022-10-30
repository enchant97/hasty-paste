class StorageException(Exception):
    pass


class StorageReadException(StorageException):
    pass


class StorageWriteException(StorageException):
    pass
