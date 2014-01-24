from redis.client import list_or_args


class Redis(object):
    _all_data = {}

    def __init__(self, host='localhost', port=6379, db=0, socket_timeout=None):
        self._db_data = self._all_data.setdefault((host, port, db), {})

    def _check_strings(self, *values):
        for value in values:
            assert isinstance(value, basestring), repr(value)

    def delete(self, *names):
        self._check_strings(*names)
        for name in names:
            self._db_data.pop(name, None)

    def exists(self, name):
        return name in self._db_data

    def flushall(self):
        for db_data in self._all_data.itervalues():
            db_data.clear()

    def flushdb(self):
        self._db_data.clear()

    def get(self, name):
        self._check_strings(name)
        value = self._db_data.get(name)
        assert isinstance(value, (basestring, type(None))), repr(value)
        return value

    def keys(self):
        return list(self._db_data)

    def mget(self, keys, *args):
        args = list_or_args(keys, args)
        return [self.get(name) for name in args]

    def pipeline(self):
        return _Pipeline(self)

    def sadd(self, name, *values):
        py_set = self.smembers(name)
        py_set.update(str(value) for value in values)
        self._store_pyvalue(name, py_set or None)

    def scard(self, name):
        return len(self.smembers(name))

    def set(self, name, value):
        self._store_pyvalue(name, str(value))

    def sinterstore(self, dest, keys, *args):
        args = list_or_args(keys, args)
        value = set()
        if args:
            value |= self.smembers(args[0])
            for arg in args[1:]:
                value &= self.smembers(arg)
        self._store_pyvalue(dest, value or None)

    def smembers(self, name):
        self._check_strings(name)
        value = self._db_data.get(name)
        assert isinstance(value, (set, type(None))), repr(value)
        return value or set()

    def srem(self, name, *values):
        py_set = self.smembers(name)
        py_set -= set(str(value) for value in values)
        self._store_pyvalue(name, py_set or None)

    def sunionstore(self, dest, keys, *args):
        args = list_or_args(keys, args)
        value = set()
        for arg in args:
            value |= self.smembers(arg)
        self._store_pyvalue(dest, value or None)

    def _store_pyvalue(self, name, value):
        self._check_strings(name)
        if value is not None:
            self._db_data[name] = value
        else:
            self.delete(name)


class _Pipeline(object):
    def __init__(self, conn):
        self._conn = conn
        self._pending = []

    def delete(self, *names):
        self._pending.append(('delete', names))

    def execute(self):
        while self._pending:
            func_name, args = self._pending.pop(0)
            getattr(self._conn, func_name)(*args)

    def sadd(self, name, *values):
        self._pending.append(('sadd', (name, ) + values))

    def set(self, name, value):
        self._pending.append(('set', (name, value)))

    def srem(self, name, *values):
        self._pending.append(('srem', (name, ) + values))

    def __enter__(self):
        return self

    def __exit__(self, etype, evalue, tb):
        pass
