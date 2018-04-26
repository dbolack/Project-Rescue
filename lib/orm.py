from .config import config
import pymysql as mysql
import psycopg2 as postgresql
import psycopg2.extras as postgresql_extras
import sys
from psycopg2 import ProgrammingError
from datetime import *

# redneck drivers because I have no time
TYPE = 0
CONN = 1

def connect(cfg):
    res = None
    if cfg['type'] == 'postgresql':
        port = cfg.get('port', 5432)
        res = ('postgresql', postgresql.connect((
            'dbname={0} host={1} user={2} password={3} port={4}'
                .format(cfg['name'], cfg['host'], cfg['user'], cfg['pass'], port)
        )))
    if cfg['type'] == 'mysql':
        port = cfg.get('port', 3306)
        charset = cfg.get('charset', '')
        res = ('mysql', mysql.connect(
            host=cfg['host'], user=cfg['user'],
            passwd=cfg['pass'], db=cfg['name'],
            port=port,
            charset=charset,
        ))
    if config['commit_at_each_entry']:
        res[CONN].autocommit = True
    return res

def init():
    return {'src': connect(config['src']),
            'dst': connect(config['dst'])}

def close(cn):
    cn['src'][CONN].close()
    cn['dst'][CONN].close()

def fetch(conn, query, params=[]):
    if conn[TYPE] == 'postgresql':
        cur = conn[CONN].cursor(cursor_factory=postgresql_extras.DictCursor)
    if conn[TYPE] == 'mysql':
        cur = conn[CONN].cursor(mysql.cursors.DictCursor)
    cur.execute(query, params)
    while True:
        line = cur.fetchone()
        if not line: break
        yield dict(line)
    cur.close()

def fetchone(conn, query, params=[]):
    if conn[TYPE] == 'postgresql':
        cur = conn[CONN].cursor(cursor_factory=postgresql_extras.DictCursor)
    if conn[TYPE] == 'mysql':
        cur = conn[CONN].cursor(mysql.cursors.DictCursor)
    try:
        cur.execute(query+" LIMIT 1", params)
    except ProgrammingError as e:
        print("incorrectly formulated model definition :\n{0}".format(e))
        sys.exit(1)
    line = cur.fetchone()
    line = dict(line) if line else None
    cur.close()
    return line

def execute(conn, query, params=[]):
    cur = conn[CONN].cursor()
    cur.execute(query, params)
    cur.close()

def fetch_tables(conn):
    if conn[TYPE] == 'mysql':
        query = 'SHOW TABLES'
    if conn[TYPE] == 'postgresql':
        query = """SELECT table_name
                  FROM information_schema.tables
                  WHERE table_schema='public' AND table_type='BASE TABLE';"""
    for table in fetch(conn, query):
        yield list(table.values())[0]

def get_sequence_value(conn, table):
    # works only under mysql for the moment
    try:
        s = fetchone(conn, 'SELECT MAX(id) FROM {0}'.format(table))['MAX(id)']
    except mysql.err.InternalError:
        s = None
    except mysql.err.ProgrammingError:
        s = None
    return s

def set_sequence_value(conn, table, value):
    # works only under postgres for the moment
    if conn[TYPE] == 'postgresql':
        q = 'ALTER SEQUENCE {0}_id_seq RESTART WITH {1}'.format(table, value)
    elif conn[TYPE] == 'mysql':
        q = 'ALTER TABLE {0} auto_increment={1}'.format(table,value)
    try:
        execute(conn, q)
    except postgresql.ProgrammingError:
        pass

##################################

def translate_where(filters):
    res = {'macro': '', 'params': []}
    for k, v in filters.items():
        if v is None:
            res['macro'] += k+' IS NULL'
        else:
            res['macro'] += k+' = %s'
            res['params'].append(v)
        res['macro'] += ' AND '
    res['macro'] = res['macro'][:-4]
    if res['macro']:
        res['macro'] = 'WHERE '+res['macro']
    return res

def translate_result(conn, table, result):
    if conn[TYPE] == 'postgresql':
        return result
    if result is None: return None
    if table not in translate_result.data:
        translate_result.data[table] = describe(conn, table)
    output = {}
    for column, value in result.items():
        if column not in translate_result.data[table]:
            continue
        if translate_result.data[table][column]['Type'] == 'tinyint(1)':
            result[column] = True if value == 1 else False
        output[column] = result[column]
    return output
translate_result.data = {}

def insert(conn, table, values={}):
    if 'id' in values:
        print("inserting in {0} record #{1}".format(table, values['id']))
    else:
        print("inserting in {0} metadata".format(table))
    macro = []
    columns = []
    params = []
    for k, v in values.items():
        macro.append('%s')
        columns.append(k)
        params.append(v)
    execute(conn, 'INSERT INTO {0} ({1}) VALUES({2})'.format(
        table, ','.join(columns), ','.join(macro)
    ), params)

def delete(conn, table, filters={}):
    print("delete metadata from {0}".format(table))
    context = translate_where(filters)
    execute(conn, 'DELETE FROM {0} {1}'.format(
            table, context['macro']), context['params'])

def findone(conn, table, filters={}):
    context = translate_where(filters)
    return translate_result(conn, table, 
        fetchone(conn, 'SELECT * FROM {0} {1}'.format(
        table, context['macro']
    ), context['params']))

def find(conn, table, filters={}):
    context = translate_where(filters)
    for r in fetch(conn, 'SELECT * FROM {0} {1}'.format(
            table, context['macro']), context['params']):
        yield translate_result(conn, table, r)

def describe(conn, table):
    # works only under mysql for the moment
    res = {}
    for r in fetch(conn, 'DESCRIBE {0}'.format(table)):
        res[r['Field']] = r
    return res
