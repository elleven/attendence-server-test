#!/usr/bin/python
# -*- coding=utf-8 -*-
import django
import os
import schedule
import logging
import time
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "attendence_server.settings")
django.setup()
from attendence.crons import cron_initAttendance
from attendence.crons import cron_current_attendence


def task():
    """win7环境下执行的task，用于从设备同步考勤数据到数据库，以及检测当天上午签到未打卡的情况"""
    logger = logging.getLogger('default')
    logger.info(u'init attendance task will exec at 05:00')
    schedule.every().day.at('05:00').do(cron_initAttendance)
    logger.info(u'init current attendance task will exec at 15:00')
    schedule.every().day.at('14:00').do(cron_current_attendence)
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    task()