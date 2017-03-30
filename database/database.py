# -*- coding: utf-8 -*-
import MySQLdb
from utils.utils import get_logger
import ConfigParser


class Database:
    def __init__(self, hostname, username, password, db_name):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.db_name = db_name
        self.fields_mapping = {'last_update': {'index': 0, 'name': 'updating_date'},
                               'email': {'index': 2, 'name': 'EMAIL'},
                               'city': {'index': 4, 'name': 'CITY'},
                               'address': {'index': 5, 'name': 'ADDRESS'},
                               'phone': {'index': 6, 'name': 'PHONE'},
                               'degree': {'index': 10, 'name': 'DEGREE'},
                               'graduation_year': {'index': 12, 'name': 'GRADYR'},
                               'major': {'index': 14, 'name': 'MAINFAC'},
                               'first_name': {'index': 20, 'name': 'PRVNAME'},
                               'last_name': {'index': 21, 'name': 'FAMNAME'},
                               'work_place': {'index': 26, 'name': 'work'},
                               'job_title': {'index': 28, 'name': 'role'},
                               'cid': {'index': 23, 'name': 'C_id'}}
        self.db = MySQLdb.connect(self.hostname, self.username, self.password, self.db_name, charset='utf8',
                                  use_unicode=True)
        self.logger = get_logger(self.__class__.__name__)

    def fetch_latest(self, table_name, n=50):
        data = []
        cursor = self.db.cursor()
        sql_cmd = 'SELECT * FROM {0} ORDER BY LAST_UPD desc LIMIT {1};'.format(table_name, n+1)
        results = self.execute(sql_cmd, True)
        skip_first = True
        for r in results:
            if skip_first:
                skip_first = False
                continue
            d = {}
            for k in self.fields_mapping:
                d[k] = r[self.fields_mapping[k]['index']]
            data.append(d)
        cursor.close()
        return data

    def update_records(self, records):
        for record in records:
            sql_cmd = 'UPDATE {0} SET'.format(self.table_name)
            first = True
            for f in self.fields_mapping:
                if f in record and f != 'cid':
                    if first:
                        sql_cmd += " {0}={1}".format(self.fields_mapping[f]['name'], record[f])
                        first = False
                    else:
                        sql_cmd += ", {0}={1}".format(self.fields_mapping[f]['name'], record[f])

            sql_cmd += ' WHERE C_id={0};'.format(record['cid'])
            # self.execute(sql_cmd)
            print(sql_cmd)

    def execute(self, sql_cmd, fetchall=False):
        cursor = self.db.cursor()
        self.logger.info('Executing: {0}'.format(sql_cmd))
        cursor.execute(sql_cmd)
        if fetchall:
            results = cursor.fetchall()
            return results
        cursor.close()

    def __del__(self):
        self.db.close()
