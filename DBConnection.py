import mysql.connector


mydb =mysql.connector.connect(host="car-parking.clduwfwypz0p.us-west-2.rds.amazonaws.com", user="admin", passwd="car-parking")

class Db:
    def __init__(self):
        self.cnx = mysql.connector.connect(
            host="car-parking.clduwfwypz0p.us-west-2.rds.amazonaws.com",
            user="admin",
            password="car-parking",
            database="parking"
            )
        self.cur = self.cnx.cursor(dictionary=True,buffered=True)

    def select(self, q, params=None):
        self.cur.execute(q, params)
        self.cnx.close()
        return self.cur.fetchall()

    def selectOne(self, q, params=None):
        self.cur.execute(q, params)
        self.cnx.close()
        return self.cur.fetchone()

    def insert(self, q, params=None):
        self.cur.execute(q, params)
        self.cnx.commit()
        self.cnx.close()
        return self.cur.lastrowid

    def update(self, q, params=None):
        self.cur.execute(q, params)
        self.cnx.commit()
        self.cnx.close()
        return self.cur.rowcount

    def delete(self, q, params=None):
        self.cur.execute(q, params)
        self.cnx.commit()
        self.cnx.close()
        return self.cur.rowcount