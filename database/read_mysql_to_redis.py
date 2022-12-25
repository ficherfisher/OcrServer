import pymysql
import redis


class mysql_to_redis:

    def __init__(self):
        self.__conn__ = pymysql.connect(host='localhost',
                                        user='root',
                                        passwd='*******',
                                        database='********')
        self.__cursor__ = self.__conn__.cursor()
        self.__redis_0__ = redis.Redis(host='localhost', port=6379, db=0)
        self.__save_user_redis()

    def __del__(self):
        self.__cursor__.close()
        self.__conn__.close()

    def __read_user_mysql_for_ocr(self):
        sql_string = """
            select username, password, remaining_times from user_table;
        """
        try:
            self.__cursor__.execute(sql_string)
            rest = self.__cursor__.fetchall()
            result = [dict(zip([k[0] for k in self.__cursor__.description], row)) for row in rest]
            return result
        except Exception as e:
            print(e)

    def __save_user_redis(self):
        user_dicts = self.__read_user_mysql_for_ocr()
        for i in user_dicts:
            self.__redis_0__.hset(i["username"], "password", i["password"])
            self.__redis_0__.hset(i["username"], "remaining_times", i["remaining_times"])


if __name__ == "__main__":
    """
    从mysql中读取信息保存到redis,
    该程序只在整个项目最先运行,只运行一次
    """
    mysql_to_redis()





