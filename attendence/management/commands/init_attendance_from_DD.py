# -*- coding=utf-8 -*-
from django.core.management.base import BaseCommand
from attendence.common.attendenceclient import AttendanceFromDD
from attendence.serializers import AttendanceRecordSerializer
from attendence.common.wraps import handle_db_connections
import logging
from attendence.common.holiday import Schedule
from attendence.models import User

logger = logging.getLogger('default')


def l_yield(lists, num):
    y = len(lists)
    while y >= num:
        x, y = y, y - num
        yield lists[y:x]
    else:
        if lists[0:y%num]:
            yield lists[0:y%num]


class Command(BaseCommand):
    """默认从钉钉初始化考勤数据到数据库"""
    @handle_db_connections
    def handle(self, *args, **options):
        logger.info('init attendance info from dd')
        default_etime = "%s 23:59:59" % Schedule.get_yesterday().strftime('%Y-%m-%d')
        default_stime = "%s 00:00:01" % Schedule.get_yesterday().strftime('%Y-%m-%d')
        stime = options.get('stime', default_stime)
        etime = options.get('etime', default_etime)
        userid_attid_map = {userobj.userid: userobj.attendence_id for userobj in User.objects.filter(is_delete=False).exclude(workplace__in=['北京', '合肥'])}
        userid_list = userid_attid_map.keys()
        for userids in l_yield(userid_list, 50):
            Att = AttendanceFromDD(stime=stime, etime=etime, userid_list=userids)
            for userid, mult_records in Att.attendanceinfo().iteritems():
                for day, record_info in mult_records.iteritems():
                    clockin, clockout, worktime = record_info
                    ser = AttendanceRecordSerializer(data={'attendence_id': userid_attid_map[userid],
                                                        'record_date': day,
                                                        'clockin_time': clockin,
                                                        'clockout_time': clockout,
                                                        'worktime': worktime})
                    if ser.is_valid():
                        # print ser.data
                        ser.save()
                    else:
                        logger.warn('%s', ser.errors)
        logger.info('write to mysql ok ')