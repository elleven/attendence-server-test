# -*- coding=utf-8 -*-
from django.core.management.base import BaseCommand
from attendence.common.statistics import OrgFromMysql, LeaveInfoFromMysql, AttendenceFromMysql
import logging
from attendence.common.holiday import Schedule
from attendence.common.reporter import TigerSmtp
from django.conf import settings
from attendence.models import UnclockReport
import smtplib
from attendence.models import Holiday
logger = logging.getLogger('default')

DEFAULT_WHITE_LIST = getattr(settings, 'DEFAULT_WHITE_LIST', None)


class Command(BaseCommand):
    """检测未打卡情况，并发送通知；从数据库读取考勤信息;默认检测昨天打卡情况
      需要检测打卡时间是否超过了 11:30,如超过了也标记为未打卡"""
    def handle(self, *args, **options):
        ret = []
        s = Schedule()
        yesterday = Schedule.get_yesterday().strftime('%Y-%m-%d')
        # 判定昨天是否为工作日
        if Holiday.objects.get(day=yesterday).is_holiday:
            logger.info('%s is holiday', yesterday)
            return
        org = OrgFromMysql()
        org.init_data()
        leave = LeaveInfoFromMysql()
        leave.init_data()
        att = AttendenceFromMysql(stime=yesterday, etime=yesterday)
        att.init_data()
        sender = TigerSmtp()
        # 组装邮件内容
        subject = u'%s 未打卡通知' % yesterday
        default_rec = ['']
        cc = ['']
        for userobj in org.get_user():
            info = {}
            # 忽略白名单的考勤通知
            if userobj.jobnumber in DEFAULT_WHITE_LIST:
                continue
            # 有请休假记录的忽略；
            if len(leave.get_leave_info(userid=userobj.userid, date=yesterday)) == 0:
                department_id = sorted(userobj.department_id.split(','))[0]
                departname = org.dept_id_name_map.get(department_id)
                info.setdefault('departname', departname)
                info.setdefault('jobnumber', userobj.jobnumber)
                info.setdefault('name', userobj.name)
                info.setdefault('date', yesterday)
                record = att.attendence_info.get(userobj.attendence_id, [])
                message = None
                if len(record) == 0:
                    message = u'当天未有打卡记录'
                else:
                    if record[0].clockin_time is None or s.check_clockin(record[0].clockin_time):
                        message = u'签到未打卡'
                    if record[0].clockout_time is None:
                        message = u'签退未打卡'
                # 检测到未打卡记录才发送
                if message is not None:
                    info.setdefault('message', message)
                    if userobj.email:
                        rec = [userobj.email]
                        try:
                            msg = sender.create_notify_msg(rec, cc, subject, info)
                            sender.commit(msg, rec)

                            logger.info('send notify to %s ok', rec)
                            info.setdefault('result', u'success')
                        except smtplib.SMTPException as why:
                            logger.info('send notify to %s fail', rec)
                            logger.error(why)
                            info.setdefault('result', why)
                    else:
                        logger.info('%s email addr is None ', userobj.name)
                        info.setdefault('result', u'email is Null')
                    # 发送情况写入数据库
                    obj = UnclockReport.objects.create(day=yesterday, jobnumber=userobj.jobnumber, unclock_info=message, result=info['result'])
                    obj.save()
                    ret.append(info)
        # 发送汇总邮件 并写入数据库
        result_subject = u'%s 未打卡汇总报告' % yesterday
        result_rec = ['']
        try:
            result_msg = sender.create_notify_result_msg(result_rec, cc, result_subject, ret)
            sender.commit(result_msg, result_rec+cc)
        except smtplib.SMTPException as why:
            logger.info('send notify result to %s fail', result_rec)
            logger.error(why)









