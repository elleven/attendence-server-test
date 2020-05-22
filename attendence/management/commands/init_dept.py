#!/usr/bin/python
# -*- coding=utf-8 -*-
from django.core.management.base import BaseCommand
from attendence.common.ddtalkclient import Organization
from attendence.serializers import DepartmentSerializer
from attendence.models import Department
from django.core.exceptions import ObjectDoesNotExist
import logging


logger = logging.getLogger('default')


class Command(BaseCommand):
    """从钉钉初始化部门信息到数据库"""
    def handle(self, *args, **options):
        logger.info('init department info')
        org = Organization()
        org.init_departinfo()
        for deptname, deptid in org.deptinfo.iteritems():
            parentid = org.d.get_parentid(deptid)
            try:
                instance = Department.objects.get(department_id=deptid)
            except ObjectDoesNotExist:
                instance = None

            ser = DepartmentSerializer(data={'name': deptname,
                                             'department_id': deptid,
                                             'parentid': parentid}, instance=instance)
            if ser.is_valid():
                ser.save()
            else:
                logger.warn('%s', ser.errors)
