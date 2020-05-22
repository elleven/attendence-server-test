# -*- coding=utf-8 -*-
from django.core.management.base import BaseCommand
from attendence.common.statistics import OrgFromMysql, LeaveInfoFromMysql
from attendence.common.attendenceclient import Attendance
import logging
from django.conf import settings
from attendence.models import CurrentAttendenceReport, Holiday
import datetime
from attendence.common.wraps import handle_db_connections

logger = logging.getLogger('default')

DEFAULT_WHITE_LIST = getattr(settings, 'DEFAULT_WHITE_LIST', None)

@handle_db_connections
class Command(BaseCommand):
    """从考勤设备读取当前上午考勤信息，初始化签到未打卡人员到数据库；限win环境运行"""
    def handle(self, *args, **options):
        timeNow = datetime.date.today().strftime('%Y-%m-%d')
        # 判定今天是否为工作日
        if Holiday.objects.get(day=timeNow).is_holiday:
            logger.info('%s is holiday', timeNow)
            return
        org = OrgFromMysql()
        org.init_data()
        leave = LeaveInfoFromMysql()
        leave.init_data()
        stime = '{} {}'.format(timeNow, '04:40:59')
        etime = '{} {}'.format(timeNow, '14:59:59')
        att = Attendance(stime=stime, etime=etime)
        att_record = att.attendanceinfo()
        for userobj in org.get_user():
            # 忽略白名单的考勤通知
            if userobj.jobnumber in DEFAULT_WHITE_LIST:
                continue
            # 有请休假记录的忽略；
            if len(leave.get_leave_info(userid=userobj.userid, date=timeNow)) != 0:
                continue
            # 如果未有打卡记录则写入数据库
            if userobj.attendence_id and userobj.attendence_id not in [str(key) for key in att_record.keys()]:
                obj = CurrentAttendenceReport.objects.create(day=timeNow, jobnumber=userobj.jobnumber)
                obj.save()




































