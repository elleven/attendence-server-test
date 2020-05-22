#!/usr/bin/python
# -*- coding=utf-8 -*-
from django.core.management.base import BaseCommand
from attendence.common.reporter import Reporter
from attendence.common.holiday import Schedule
import logging
import datetime
import sys

logger = logging.getLogger('default')


class Command(BaseCommand):
    """根据一级部门归纳，将考勤周报发送给hrbp"""

    def add_arguments(self, parser):
        parser.add_argument('deptname', type=str, help='部门名称')
        # parser.add_argument('stime', type=str, help='开始时间:%Y-%m-%d')
        # parser.add_argument('etime', type=str, help='结束时间:%Y-%m-%d')

    def handle(self, *args, **options):
        s = Schedule()
        time_now = datetime.date.today().strftime('%Y-%m-%d')
        default_stime, default_etime = s.get_lastweek(time_now)
        stime = options.get('stime', default_stime)
        etime = options.get('etime', default_etime)
        logger.info('ready go')
        reporter = Reporter()
        reporter.get_data_2(stime, etime)
        # args 或者 kargs 指定部门，则发送指定部门的考勤
        arg = options.get('deptname', None)
        if arg != 'pro':
            deptname = arg
            logger.info('start send weekly_reprot_to_hrbpto %s', deptname)
            reporter.base_report_to(deptname)
            sys.exit(0)
        logger.info('start  send weekly_reprot_to_hrbp')
        # 发送各部门考勤周报execl给hrbps
        reporter.weekly_reprot_to_hrbp()
        # 发送个人周平均出勤小于10的周报execl给hr
        reporter.base_reprot_to_boss_2_execl()