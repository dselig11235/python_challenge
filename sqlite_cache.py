from cache import Cache
import sqlite3

class SQLiteCache(Cache):
    def __init__(self, filename, *args, keytype='text', valtype='json', **kwargs):
        '''filename should be the filename of the sqlite3 database or ":memory:"
        create an in-memory database. The keytype and valtype fields specify
        the type of the key and value stored in the cache respectively'''
        super().__init__(*args, **kwargs)
        self.filename = filename
        self.keytype = keytype
        self.valtype = valtype
        self.conn = sqlite3.connect(filename, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
        #No parameter substitution for identifiers (column names)
        #asserting that types are alpha should eliminate any injection attacks
        assert(keytype.isalpha())
        assert(valtype.isalpha())
        self.conn.execute(f"create table if not exists SQLiteCache " +
                f"(key {keytype} primary key, val {valtype}, expires timestamp);")
    def lookup(self, key):
        c = self.conn.cursor()
        c.execute('select val, expires from SQLiteCache where key = ?;', [key])
        res = c.fetchone()
        if res is None:
            return res
        else:
            val, expires = res
            if expires < datetime.now():
                self.remove(key)
                return None
            else:
                return val
    def add(self, key, val):
        c = self.conn.cursor()
        expires = datetime.now() + self.ttl
        c.execute("insert into SQLiteCache (key, val, expires) values (?, ?, ?);", [key, val, expires])
    def remove(self, key):
        self.conn.execute("delete from SQLiteCache where key = ?", [key])
    def list(self):
        c = self.conn.execute("select key from SQLiteCache")
        yield from c

