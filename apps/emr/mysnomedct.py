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
