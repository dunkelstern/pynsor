from typing import Dict, Any, List, Union, Tuple
import psycopg2

class Connection:
    def __init__(self, config: Dict[str, Any]):
        dsn = 'postgres://'
        if 'username' in config:
            dsn += config['username']
        if 'password' in config:
            dsn += ':' + config['password']
        if 'username' in config:
            dsn += '@'
        if 'host' in config:
            dsn += config['host']
        else:
            dsn += 'localhost'
        if 'port' in config:
            dsn += ':' + str(config['port'])
        if 'database' in config:
            dsn += '/' + config['database']

        self.dsn = dsn

    def __enter__(self):
        self.connection = psycopg2.connect(self.dsn)
        self.cursor = self.connection.cursor()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.cursor.close()
        if exc_type is None:
            self.connection.commit()
        else:
            self.connection.rollback()
        self.connection.close()

    def insert(self, table: str, data: Dict[str, Any]) -> None:
        keys = ", ".join([f'"{k}"' for k in data.keys()])
        placeholders = ", ".join([f'%({key})s' for key in data.keys()])
        sql = f"INSERT INTO {table} ({keys}) VALUES ({placeholders})"
        self.cursor.execute(sql, data)

    def create_table(self, table: str, items: List[Dict[str, str]]) -> str:
        """
        Create a TimescaleDB hypertable if it not exists already

        :param table: Table name
        :param items: Fields to create, is a list {'name': 'measurement', 'type': "TEXT", 'null': 'NOT NULL'}
        :returns: 'already_exists', 'ok' or 'error'
        """
        sql = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE  table_schema = 'public'
                AND    table_name   = %(table)s
            );
        """
        self.cursor.execute(sql, {'table': table})
        result = self.cursor.fetchone()
        if result[0] == True:
            return 'already_exists'

        try:
            fields = [f'"{value["name"]}" {value["type"]} {value["null"]}' for value in items]
            fields = ",\n".join(fields)
            sql = f"""
                CREATE TABLE {table} (
                    time TIMESTAMPTZ NOT NULL DEFAULT now(),
                    {fields}
                );

                SELECT create_hypertable('{table}', 'time')
            """
            self.cursor.execute(sql)
        except Exception:
            return 'error'
        return 'ok'

    def create_index(self, table: str, field: Union[str, List[str], Tuple[str]], type: str='BTREE', unique: bool=False) -> str:
        """
        Create an index over the fields

        :param table: Table to create index on
        :param field: str or list of str, fields to create index over
        :param type: index type, defaults to btree
        :returns: 'already_exists', 'ok' or 'error'
        """

        if isinstance(field, list) or isinstance(field, tuple):
            index_name = table + "_" + ("_".join(field)) + "_idx"
        else:
            index_name = table + "_" + field + "_idx"

        # check for existence first
        sql = """
            SELECT EXISTS(
                SELECT
                    i.relname
                FROM
                    pg_class t,
                    pg_class i,
                    pg_index ix,
                    pg_attribute a
                WHERE
                    t.oid = ix.indrelid
                    AND i.oid = ix.indexrelid
                    AND a.attrelid = t.oid
                    AND a.attnum = ANY(ix.indkey)
                    AND t.relkind = 'r'
                    AND t.relname = %(table)s
                    AND i.relname = %(index_name)s
            )
        """
        self.cursor.execute(sql, {'table': table, 'index_name': index_name})
        result = self.cursor.fetchone()
        if result[0] == True:
            return 'already_exists'

        if unique:
            sql = "CREATE UNIQUE INDEX"
        else:
            sql = "CREATE INDEX"
        sql += f" ON {table} USING {type} "
        if isinstance(field, list) or isinstance(field, tuple):
            sql += "(" + (",".join([f'"{v}"' for v in field])) + ")"
        else:
            sql += f'("{field}")'
        print(sql)
        self.cursor.execute(sql)

class DB:
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def connect(self) -> Connection:
        return Connection(self.config)
