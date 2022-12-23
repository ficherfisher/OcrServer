import os
import sys
sys.path.append(os.path.abspath(os.path.dirname(os.getcwd())))


import pymysql
from server import middleware
import read_mysql_to_redis
"""
创建数据库，添加用户信息
"""


class operate_mysql:
    def __init__(self):
        self.__conn__ = pymysql.connect(host='localhost', user='root', passwd='Mdf3-bY3H-67gE-7fbo')
        self.__cursor__ = self.__conn__.cursor()
        self.__middleware = middleware
        self.__cursor__.execute("""create database if not exists ocr_database_server""")

    def __del__(self):
        self.__cursor__.close()
        self.__conn__.close()

    def create_user_table(self):
        sql_string = """
            create table user_table(
                username varchar (50) PRIMARY KEY,
                password varchar (50),
                registration_time date ,
                user_email varchar (30),
                company text,
                remaining_times varchar (10)
            );
            """
        try:
            self.__conn__.select_db('ocr_database_server')
            self.__cursor__.execute(sql_string)
            self.__conn__.commit()
        except Exception as e:
            print("class operate_mysql function create_user_table:{}".format(e))

    def create_usage_table(self, username):
        temp = self.__middleware.handle_username(username)
        sql_string = """
            create table {}(
                nonce varchar(50),
                access_time text,
                picture_url text,
                status integer,
                ocr_result text
            );
            """.format(str(temp))
        try:
            self.__conn__.select_db('ocr_database_server')
            self.__cursor__.execute(sql_string)
            self.__conn__.commit()
        except Exception as e:
            print("class operate_mysql function create_usage_table:{}".format(e))

    def insert_user_table(self, username, password, user_email, company, remaining_times=500000):
        temp = self.__middleware.handle_username(username)
        current_time = self.__middleware.get_current_time()
        sql_string = """
            insert into user_table (username, password, registration_time, user_email, company, remaining_times) 
            values ('{}','{}', '{}', '{}', '{}', '{}');
        """.format(temp, password, current_time, user_email, company, remaining_times)
        try:
            self.__conn__.select_db('ocr_database_server')
            self.__cursor__.execute(sql_string)
            self.__conn__.commit()
        except Exception as e:
            print("class operate_mysql function insert_user_table:{}".format(e))
        finally:
            self.create_usage_table(username)


if __name__ == "__main__":
    operate_mysql = operate_mysql()
    user_name = "firestorm-sea"
    pass_word = "d4154fQd5453vSFQWd124faFlxzA"
    email = "none 后续添加"
    company_name = "武汉踏浪公司"
    remaining_number = 10000
    operate_mysql.create_user_table()
    operate_mysql.insert_user_table(user_name, pass_word, email, company_name)  # 1todo 增加参数 remaining_number
    read_mysql_to_redis.mysql_to_redis()

