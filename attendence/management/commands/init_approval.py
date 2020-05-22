#!/usr/bin/python
# -*- coding=utf-8 -*-
from django.core.management.base import BaseCommand
from attendence.common.ddtalkclient import Approval
from attendence.serializers import ApprovalRecordSerializer
from attendence.models import ApprovalRecord
from django.core.exceptions import ObjectDoesNotExist
import logging
import time

logger = logging.getLogger('default')


class Command(BaseCommand):
    """初始化审批数据到数据库，手动执行此命令需要注意 更改时间范围"""
    def handle(self, *args, **options):
        logger.info('init approval info')
        # 第一次初始化本年度所有审批记录/非第一次执行，需要更改start_time
        start_time = options.get('start_time', '2019-01-01 00:00:00')
        start_time = time.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        start_timestamp = time.mktime(start_time)
        millis_timestamp = int(round(start_timestamp * 1000))
        app = Approval(start_time=millis_timestamp)
        app.get_approval_data()
        app.init_approval()
        for approval_record in app.approval_info:
            instance_id = approval_record['instance_id']
            try:
                instance = ApprovalRecord.objects.get(instance_id=instance_id)
            except ObjectDoesNotExist:
                instance = None
            ser = ApprovalRecordSerializer(instance=instance, data=approval_record)
            if ser.is_valid():
                ser.save()
            else:
                logger.warn('%s', ser.errors)

        logger.info('sync instance modify status')
        for instance_modify_id in app.instance_modify:
            try:
                instance_modify = ApprovalRecord.objects.get(instance_id=instance_modify_id)
            except ObjectDoesNotExist:
                instance_modify = None
            ser = ApprovalRecordSerializer(instance=instance_modify, data={'status': 'MODIFY'}, partial=True)
            if ser.is_valid():
                ser.save()
            else:
                logger.warn('%s', ser.errors)
        logger.info('sync instance revoke status')
        for instance_revoke_id in app.instance_revoke:
            try:
                instance_revoke = ApprovalRecord.objects.get(instance_id=instance_revoke_id)
            except ObjectDoesNotExist:
                instance_revoke = None
            ser = ApprovalRecordSerializer(instance=instance_revoke, data={'status': 'REVOKE'}, partial=True)
            if ser.is_valid():
                ser.save()
            else:
                logger.warn('%s', ser.errors)
        logger.info('total %s item load done', len(app.approval_info))