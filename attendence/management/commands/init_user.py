#!/usr/bin/python
# -*- coding=utf-8 -*-
from django.core.management.base import BaseCommand
from attendence.common.ddtalkclient import Organization
from attendence.serializers import UserSerializer
from attendence.models import User
from django.core.exceptions import ObjectDoesNotExist
import logging


logger = logging.getLogger('init_data')


class Command(BaseCommand):
    """从钉钉获取用户数据初始化到数据库"""
    def handle(self, *args, **options):
        logger.info('init user info')
        org = Organization()
        org.init_departinfo()
        org.init_userinfo()
        for jobnumber, userinfo in org.userinfo.iteritems():
            name = userinfo['name']
            userid = userinfo['userid']
            email = userinfo.get('email', None)
            department_id = ",".join([str(x) for x in userinfo['department']])
            workplace = userinfo.get('workPlace', None)
            data = {'name': name,
                    'userid': userid,
                    'jobnumber': jobnumber,
                    'email': email,
                    'department_id': department_id,
                    'workplace': workplace,
                    'is_delete': False}
            try:
                instance = User.objects.get(jobnumber=jobnumber)
                ser = UserSerializer(instance=instance, data=data, partial=True)
                if ser.is_valid():
                    ser.save()
                else:
                    logger.warn('%s', ser.errors)
            except ObjectDoesNotExist:
                ser = UserSerializer(data=data)
                if ser.is_valid():
                    ser.save()
                else:
                    logger.warn('%s', ser.errors)

        # 处理标记删除员工
        for userobj in User.objects.all():
            if userobj.jobnumber not in org.userinfo:
                ser = UserSerializer(instance=userobj, data={'is_delete': True}, partial=True)
                if ser.is_valid():
                    ser.save()
                else:
                    logger.warn('%s', ser.errors)

