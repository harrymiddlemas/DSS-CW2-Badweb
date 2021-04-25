import random
import sqlite3

DATABASE = 'database.sqlite'


def generate_random_user_path_id():
    user_path_id = ''
    for i in range(16):
        user_path_id += str(random.randint(1, 9))
    return user_path_id


db = sqlite3.connect(DATABASE)
c = db.cursor()
number_of_users = c.execute('SELECT COUNT(*) FROM USERS').fetchall()[0][0]
users = c.execute('SELECT USERID FROM USERS').fetchall()
c.execute('ALTER TABLE USERS ADD USER_PATH_ID INTEGER(16)')
for i in range(number_of_users):
    userid = users[i][0]
    c.execute(
        'UPDATE USERS SET USER_PATH_ID = ' + str(generate_random_user_path_id()) + ' WHERE USERID = ' + str(
            userid))

db.commit()
