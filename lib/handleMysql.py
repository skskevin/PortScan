# -*- coding:utf-8 -*- # 
import MySQLdb


class handleMysql(object):
    def __init__(self, host, user, password, db, port,charset):
        self.conn=MySQLdb.connect(host=host,user=user,passwd=password,port=port,db=db,charset=charset)
        
    def DMLSQL(self,sql):
        try:
            cursor=self.conn.cursor()
            cursor.execute(sql)
            self.conn.commit()
        except Exception,e:
            self.conn.rollback()
            print e
        cursor.close()
    def Truncate(self,table):
        try:
            cursor=self.conn.cursor()
            sql='truncate table '+table
            cursor.execute(sql)
            self.conn.commit()
        except Exception,e:
            self.conn.rollback()
            print e
        cursor.close()

    def Select(self,sql):
        try:
            cursor=self.conn.cursor()
            cursor.execute(sql)
            rs=cursor.fetchall()
        except Exception,e:
            print e
        cursor.close()
        
        return rs

    def Disconnect(self):
        self.conn.close()