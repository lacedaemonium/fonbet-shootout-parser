import sqlite3

connection = sqlite3.connect('fonbet.db')
cursor = connection.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS fonbet (
id INTEGER PRIMARY KEY NULL,
match_no TEXT NULL,
date_time TIMESTAMP NULL,
result_match TEXT NULL,
death_match TEXT NULL
)
''')

connection.commit()
connection.close()
exit(0)