# -*- coding=utf-8 -*-
from django.core.management.base import BaseCommand
from attendence.common.execlclient import ExcelParse
from attendence.models import User
from django.core.exceptions import ObjectDoesNotExist
from attendence.serializers import UserSerializer
import logging

logger = logging.getLogger('default')


class Command(BaseCommand):
    """手动从文件中更新用户数据 增加attendence_id 和 jobnumber信息，目前已不使用"""
    def handle(self, *args, **options):
        default_file = '人员.xls'
        user_file = args[1] if len(args) > 0 else default_file
        user_info = ExcelParse(user_file)
        for item in user_info.data:
            jobnumber = item[u'姓氏']
            attendence_id = item[u'人员编号']
            try:
                instance = User.objects.get(jobnumber=jobnumber)
                ser = UserSerializer(instance=instance, data={'attendence_id': attendence_id}, partial=True)
                if ser.is_valid():
                    ser.save()
                else:
                    logger.warn('%s', ser.errors)
            except ObjectDoesNotExist:
                logger.warn('%s not found ', jobnumber)
