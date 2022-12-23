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
