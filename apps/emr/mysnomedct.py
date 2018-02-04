"""
Copyright (c) Small Brain Records 2014-2018 Kevin Perdue, James Ryan with contributors Timothy Clemens and Dinh Ngoc Anh

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>
"""
import MySQLdb

from django.conf import settings

class SnomedctConnector():
	def __init__(self):
		self.ssl = settings.SNOMEDCT['ssl']
		self.host = settings.SNOMEDCT['host']
		self.user = settings.SNOMEDCT['user']
		self.passwd = settings.SNOMEDCT['passwd']
		self.db = settings.SNOMEDCT['db']
		self.cursor = None
		self.limit = 100

	def connect(self):
		conn = MySQLdb.connect(host=self.host, user=self.user, passwd=self.passwd, db=self.db, ssl=self.ssl)
		cursor = conn.cursor()
		return cursor

	def get_medications(self, query=None):
		if query:
			sql = "select conceptid, term from vw_medications WHERE term LIKE '%" + query + "%'"
		else:
			sql = 'select conceptid, term from vw_medications'
		self.cursor.execute(sql)
		results = self.cursor.fetchall()
		medications = []
		for row in results:
			medications.append({'concept_id': row[0], 'name': row[1]})
		return medications[:self.limit]

	def get_problems(self, query=None):
		if query:
			sql = "select conceptid, term from vw_problems WHERE term LIKE '%" + query + "%'"
		else:
			sql = 'select conceptid, term from vw_problems'
		self.cursor.execute(sql)
		results = self.cursor.fetchall()
		problems = []
		for row in results:
			problems.append({'code': row[0], 'term': row[1]})
		return problems[:self.limit]
