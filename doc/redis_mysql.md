## redis

- 简介

Redis 是完全开源免费的，遵守 BSD 协议，是一个灵活的高性能 key-value 数据结构存储，可以用来作为数据库、缓存和消息队列。

Redis 比其他 key-value 缓存产品有以下三个特点：

1.Redis 支持数据的持久化，可以将内存中的数据保存在磁盘中，重启的时候可以再次加载到内存使用。

2.Redis 不仅支持简单的 key-value 类型的数据，同时还提供 list，set，zset，hash 等数据结构的存储。

3.Redis 支持主从复制，即 master-slave 模式的数据备份。

- redis 与server API接口

```python
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


```

- redis 与 mysql API接口

```python

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
```

## mysql



- 简介

MySQL是一个开放源码的小型关联式数据库管理系统，开发者为瑞典MySQL AB公司。目前MySQL被广泛地应用在Internet上的中小型网站中。由于其体积小、速度快、总体拥有成本低，尤其是开放源码这一特点，许多中小型网站为了降低网站总体拥有成本而选择了MySQL作为网站数据库。

- mysql 与 redis API接口

```python

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
```

## 定时持久化

​		server --> redis --> mysql

定时将redis 数据持久化到mysql中，代码如下：

```python
import time
import os
import sched


schedule = sched.scheduler(time.time, time.sleep)


def execute_command(cmd, inc):
    os.system(cmd)
    schedule.enter(inc, 0, execute_command, (cmd, inc))


def main(cmd, inc1=3600*12):
    schedule.enter(0, 0, execute_command, (cmd, inc1))
    schedule.run()


if __name__ == '__main__':
    main("python3 read_redis_to_mysql.py", 3600)
```

启用新进程定时检测redis变化。定时调用redis->mysql API

