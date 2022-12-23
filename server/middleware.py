import hashlib
import time
"""
整个项目的中间所需函数
"""


def handle_username(username_string):
    m = hashlib.md5()
    m.update(username_string.encode("utf8"))
    return m.hexdigest()


def get_current_time():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


if __name__ == "__main__":
    print(get_current_time())


