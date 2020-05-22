#!/usr/bin/python
# -*- coding=utf-8 -*-
from django.core.management.base import BaseCommand
from attendence.common.holiday import Schedule
from attendence.serializers import HolidaySerializer
from attendence.models import Holiday
import logging

logger = logging.getLogger('default')

DEFAULT_WEEKDAY = {
    0: u'星期一',
    1: u'星期二',
    2: u'星期三',
    3: u'星期四',
    4: u'星期五',
    5: u'星期六',
    6: u'星期日',
}


class Command(BaseCommand):
    """从开源节假日接口，获取指定年份的节假日信息到数据库,用于同步节假日信息至本地"""

    def add_arguments(self, parser):
        parser.add_argument('year', type=int, help='年份:%Y')

    def handle(self, *args, **options):
        s = Schedule()
        year = options.get('year')
        for day in s.iter_yeardays(year):
            weekday = s.get_weekday(day)
            weekday_hunman = DEFAULT_WEEKDAY.get(weekday)
            ret = s.get_holiday(day)
            is_holiday = ret['holiday'] if ret else False
            holiday_info = ret['name'] if ret else None
            try:
                instance = Holiday.objects.get(day=day)
            except Holiday.DoesNotExist:
                instance = None
            ser = HolidaySerializer(data={'day': day,
                                          'weekday': weekday_hunman,
                                          'is_holiday': is_holiday,
                                          'holiday_info': holiday_info
                                          }, instance=instance)
            if ser.is_valid():
                ser.save()
            else:
                logger.warn('%s', ser.errors)


