# -*- coding=utf-8 -*-
from django.core.management.base import BaseCommand
from attendence.common.attendenceclient import Attendance
from attendence.serializers import AttendanceRecordSerializer
from attendence.common.wraps import handle_db_connections
import logging
from attendence.common.holiday import Schedule
import datetime

logger = logging.getLogger('default')


class Command(BaseCommand):
    """默认从考勤设备初始化昨天的考勤信息到数据库，win环境下执行"""
    @handle_db_connections
    def handle(self, *args, **options):
        logger.info('init attendance info')
        default_etime = "%s 04:39:59" % datetime.date.today().strftime('%Y-%m-%d')
        default_stime = "%s 04:40:00" % Schedule.get_yesterday().strftime('%Y-%m-%d')
        stime = options.get('stime', default_stime)
        etime = options.get('etime', default_etime)
        Att = Attendance(stime=stime, etime=etime)
        for jobnumber, mult_records in Att.attendanceinfo().iteritems():
            for day, record_info in mult_records.iteritems():
                clockin, clockout, worktime = record_info
                ser = AttendanceRecordSerializer(data={'attendence_id': jobnumber,
                                                        'record_date': day,
                                                        'clockin_time': clockin,
                                                        'clockout_time': clockout,
                                                        'worktime': worktime})
                if ser.is_valid():
                    ser.save()
                else:
                    logger.warn('%s', ser.errors)
        logger.info('write to mysql ok ')




