#!/usr/bin/python
# -*- coding=utf-8 -*-
import datetime
import logging
from attendence.common.holiday import Schedule
from attendence.management.commands.init_attendance import Command as AttendanceCron
from attendence.management.commands.init_user import Command as UserCron
from attendence.management.commands.init_dept import Command as DeptCron
from attendence.management.commands.init_approval import Command as ApprovalCron
from attendence.management.commands.attendence_notice import Command as Notice_cron
from attendence.management.commands.sync_current_attendence import Command as CurrentAttCron
from attendence.management.commands.init_attendance_from_DD import Command as AttendanceFromDDCron
from attendence.management.commands.weekly_report import Command as WeeklyReport
from attendence.management.commands.weekly_report_hrbp import Command as WeeklyReportHrbp



"""计划任务汇总"""

logger = logging.getLogger('django_crontab')


def cron_inituser():
    """每天晚上 23：00 执行从钉钉同步用户数据到数据库
    django-crontab"""
    user_cron = UserCron()
    user_cron.handle()


def cron_initDept():
    """每月执行一次，从钉钉获取部门信息到数据库
    django-crontab"""
    dept_cron = DeptCron()
    dept_cron.handle()


def cron_initApproval():
    """每天晚上22：00 执行同步审批记录;同步最近30天的记录到数据库
     django-crontab"""
    days_ago = datetime.date.today() + datetime.timedelta(-30)
    days_ago = "%s 00:00:00" % days_ago
    approval_cron = ApprovalCron()
    approval_cron.handle(start_time=days_ago)


def cron_initAttendance():
    """每天上午05：00 执行同步昨天的考勤记录到数据库
    依赖win32com 仅限win7 环境下执行
    schedule """
    attendance_cron = AttendanceCron()
    attendance_cron.handle()


def cron_initAttendance_fromDD():
    """每天上午04：40 从钉钉同步昨天的考勤记录到数据库"""
    attendance_cron = AttendanceFromDDCron()
    attendance_cron.handle()


def cron_attendence_notice():
    """每天上午6点检测昨天未打卡情况，并发送通知
    django-crontab"""
    notice = Notice_cron()
    notice.handle()


def cron_current_attendence():
    """每天下午14：00 同步当天上午未打卡人员信息到数据库
    仅限win7环境下执行"""
    current_att = CurrentAttCron()
    current_att.handle()


def cron_weekly_report():
    """每周的周一上午10：00发送上周的考勤周报给hr boss"""
    s = Schedule()
    weekday = s.get_weekday(datetime.date.today().strftime('%Y-%m-%d'))
    if int(weekday) == 0:
        weekly = WeeklyReport()
        weekly.handle(deptname='pro')


def cron_weekly_report_hrbp():
    """每周的周一上午10：30发送上周的考勤周报给hrbp"""
    s = Schedule()
    weekday = s.get_weekday(datetime.date.today().strftime('%Y-%m-%d'))
    if int(weekday) == 0:
        weekly = WeeklyReportHrbp()
        weekly.handle(deptname='pro')