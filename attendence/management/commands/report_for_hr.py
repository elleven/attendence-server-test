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
    """发送指定时间范围内的全员考勤信息邮件给hr"""

    def add_arguments(self, parser):
        parser.add_argument('stime', type=str, help='开始时间:%Y-%m-%d')
        parser.add_argument('etime', type=str, help='结束时间:%Y-%m-%d')

    def handle(self, *args, **options):
        s = Schedule()
        time_now = datetime.date.today().strftime('%Y-%m-%d')
        default_stime, default_etime = s.get_lastweek(time_now)
        stime = options.get('stime', default_stime)
        etime = options.get('etime', default_etime)
        logger.info('ready go')
        reporter = Reporter()
        reporter.get_data(stime, etime)
        logger.info('start  send base_weekly_report')
        # 发送考勤周报给HR
        reporter.base_weekly_report_to_hr()