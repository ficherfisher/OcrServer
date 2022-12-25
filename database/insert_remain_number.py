import pymysql
from server import middleware
import read_mysql_to_redis


class insert_mysql:
    def __init__(self):
        self.__conn__ = pymysql.connect(host='localhost',
                                        user='root',
                                        passwd='********',
                                        database='*********')
        self.__cursor__ = self.__conn__.cursor()
        self.__middleware = middleware

    def __del__(self):
        self.__cursor__.close()
        self.__conn__.close()

    def insert_remaining_number_mysql(self, username, remaining_number=100000):
        md5_username = middleware.handle_username(username)
        sql_string = """UPDATE user_table SET remaining_times = '{}' WHERE username = '{}'""" \
            .format(remaining_number, md5_username)
        try:
            self.__cursor__.execute(sql_string)
            self.__conn__.commit()
        except Exception as e:
            print(e)


if __name__ == "__main__":
    insert_class = insert_mysql()
    user = "test1"
    insert_number = 1000
    insert_class.insert_remaining_number_mysql(user)   # 1todo 修改增加次数
    read_mysql_to_redis.mysql_to_redis()


