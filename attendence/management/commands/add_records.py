# -*- coding=utf-8 -*-
from django.core.management.base import BaseCommand
from attendence.common.execlclient import ExcelParse
from attendence.serializers import AttendanceRecordSerializer
import logging
import time

""" 用于初期手动从考勤文件数据 导入考勤数据至数据库；目前已不使用"""
logger = logging.getLogger('default')


def formatwt(wtime):
    """
        出勤时间单位统一换小时，例如10.5h"""
    wtime = str(wtime)
    if wtime is None or wtime is '':
        return ''
    hour, miniute = wtime.split(':')
    hour = int(hour)
    miniute = int(miniute)
    formattime = hour + round(miniute / 60.0, 1)
    return str(formattime)


class Command(BaseCommand):
    """手动导入考勤记录"""
    def handle(self, *args, **options):
        default_file = '考勤.xls'
        attendence_file = args[1] if len(args) > 0 else default_file
        attendence_info = ExcelParse(attendence_file, encoding='gbk')
        for item in attendence_info.data:
            attendence_id = item[u'登记号码']
            time_struct = time.strptime(item[u'日期'], "%Y/%m/%d")
            record_date = time.strftime("%Y-%m-%d", time_struct)
            clockin_time = ' '.join([record_date, item[u'签到时间']]) if item[u'签到时间'] and item[u'签到时间'] != '' else None
            clockout_time = ' '.join([record_date, item[u'签退时间']])  if item[u'签退时间'] and item[u'签退时间'] != '' else None
            worktime = formatwt(item[u'出勤时间']) or None
            try:
                ser = AttendanceRecordSerializer(data={'attendence_id': attendence_id,
                                                        'record_date': record_date,
                                                        'clockin_time': clockin_time,
                                                        'clockout_time': clockout_time,
                                                        'worktime': worktime})
                if ser.is_valid():
                    ser.save()
                    # print attendence_id, record_date, clockin_time, clockout_time, worktime
                else:
                    logger.warn('%s', ser.errors)
            except Exception as why:
                logger.error(why)
