class CacheException(Exception):
    pass


class CacheReadException(CacheException):
    pass


class CacheWriteException(CacheException):
    pass
