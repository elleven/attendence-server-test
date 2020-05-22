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
    """初始化数据"""
    def handle(self, *args, **options):
        logger.info('init user info')
        org = Organization()
        org.init_departinfo()
        org.init_userinfo()
        for userobj in User.objects.all():
            if userobj.jobnumber not in org.userinfo:
                print userobj.name
                ser = UserSerializer(instance=userobj, data={'is_delete': True}, partial=True)
                if ser.is_valid():
                    ser.save()
                else:
                    logger.warn('%s', ser.errors)

