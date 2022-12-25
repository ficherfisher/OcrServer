import pymysql
import redis
import json


class redis_to_mysql:
    def __init__(self):
        self.__conn__ = pymysql.connect(host='localhost',
                                        user='root',
                                        passwd='********',
                                        database='********')
        self.__cursor__ = self.__conn__.cursor()
        self.__pool_0 = redis.ConnectionPool(host='127.0.0.1', port=6379, db=0)
        self.__r_0 = redis.StrictRedis(connection_pool=self.__pool_0)
        self.__pool_1 = redis.ConnectionPool(host='127.0.0.1', port=6379, db=1)
        self.__r_1 = redis.StrictRedis(connection_pool=self.__pool_1)
        self.__save_information_to_mysql()
        self.__save_usage_to_mysql()

    def __del__(self):
        self.__cursor__.close()
        self.__conn__.close()

    def __read_user_information(self):
        keys = self.__r_0.keys()
        for key in keys:
            rest_count = self.__r_0.hget(key, "remaining_times")
            yield {"username": key.decode(), "rest_count": rest_count.decode()}

    def __read_user_usage(self):
        keys = self.__r_1.keys()
        for key in keys:
            access_time = self.__r_1.hget(key, "access_time")
            picture_url = self.__r_1.hget(key, "picture_url")
            status = self.__r_1.hget(key, "status")
            username = self.__r_1.hget(key, "username")
            ocr_result = self.__r_1.hget(key, "ocr_result")
            nonce = self.__r_1.hget(key, "nonce")
            yield {"username": username.decode(), "nonce": nonce.decode(), "status": status.decode(),
                   "access_time": access_time.decode(), "picture_url": picture_url.decode(), 
                   "ocr_result": ocr_result.decode(), "redis_nonce": key.decode()}

    def __save_information_to_mysql(self):

        for dicts in self.__read_user_information():
            sql_string = """UPDATE user_table SET remaining_times = '{}' WHERE username = '{}'""" \
                .format(dicts["rest_count"], dicts["username"])
            try:
                self.__cursor__.execute(sql_string)
                self.__conn__.commit()
            except Exception as e:
                print(e)

    def __save_usage_to_mysql(self):
        for dicts in self.__read_user_usage():
            sql_string = """
                        insert into {} (nonce, access_time, picture_url, status, ocr_result) values ('{}', '{}', '{}', '{}', {});
                    """.format(dicts["username"], dicts["nonce"], dicts["access_time"],
                               dicts["picture_url"], dicts["status"], json.dumps(dicts["ocr_result"]))
            try:
                self.__cursor__.execute(sql_string)
                self.__conn__.commit()
                self.__r_1.delete(dicts["redis_nonce"])
            except Exception as e:
                print(e)


if __name__ == "__main__":
    redis_to_mysql()

