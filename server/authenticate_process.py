import sys
import os
import middleware
sys.path.append(os.path.abspath(os.path.dirname(os.getcwd())))

import json
import hashlib
import time
from ocr_tools import ocr_system
import uuid
import redis


class authentication:

    def __init__(self):
        self.__ocr_system = ocr_system.run_ocr()
        self.__redis_db_0 = redis.Redis(host='localhost', port=6379, db=0)
        self.__redis_db_1 = redis.Redis(host='localhost', port=6379, db=1)

    def __get_password(self, username):
        try:
            md5_username = middleware.handle_username(username)
            password = self.__redis_db_0.hget(name=md5_username, key="password")
            return password.decode()
        except Exception as e:
            print("there is something wrong check_password :{}".format(e))
            return str(1)

    def __insert_database(self, user_name, insert_dicts, nonce_redis):
        try:
            md5_username = middleware.handle_username(user_name)
            self.__redis_db_1.hset(nonce_redis, "nonce", insert_dicts["nonce"])
            self.__redis_db_1.hset(nonce_redis, "username", md5_username)
            self.__redis_db_1.hset(nonce_redis, "access_time", insert_dicts["access_time"])
            self.__redis_db_1.hset(nonce_redis, "picture_url", insert_dicts["picture_url"])
            self.__redis_db_1.hset(nonce_redis, "status", insert_dicts["status"])
            self.__redis_db_1.hset(nonce_redis, "ocr_result", str(insert_dicts["ocr_result"]))
            self.__redis_db_0.hincrby(md5_username, "remaining_times", -1)
        except Exception as e:
            print("there is something wrong insert_sql :{}".format(e))

    def __get_sign(self, username, nonce):
        temp = "username=" + username + "&password=" + self.__get_password(username) + "&nonce=" + nonce
        m = hashlib.md5()
        m.update(temp.encode("utf8"))
        return m.hexdigest()

    def check_label(self, data_dict):
        temp = self.__redis_db_0
        labels = ["username", "nonce", "sign", "picture_url"]
        for index, label in enumerate(labels):
            if label not in data_dict:
                return index
        return "True"

    def check_sign(self, data_dict):
        sign = self.__get_sign(data_dict["username"], data_dict["nonce"])
        if sign != data_dict["sign"]:
            return 4
        return "True"

    def check_information(self, data_dict):
        check_label_tag = self.check_label(data_dict)
        if check_label_tag != "True":
            return "None", check_label_tag
        check_sign_tag = self.check_sign(data_dict)
        if check_sign_tag != "True":
            return "None", check_sign_tag
        ocr_result_dicts = self.__ocr_system.usage_text_sys(data_dict["picture_url"])
        import uuid
        nonce_redis = str(uuid.uuid4())
        insert_dicts = {
            "nonce": data_dict["nonce"], "access_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "picture_url": data_dict["picture_url"], "status": ocr_result_dicts['status'], 
            "ocr_result": ocr_result_dicts["text"]
            }
        self.__insert_database(user_name=data_dict["username"], insert_dicts=insert_dicts, nonce_redis=nonce_redis)
        return ocr_result_dicts["text"], ocr_result_dicts["status"]
