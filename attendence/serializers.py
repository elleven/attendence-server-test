# -*- coding: utf-8 -*-
from rest_framework import serializers
from models import Department, User, ApprovalRecord, AttendenceRecord, Holiday
from django.utils import timezone


class DepartmentSerializer(serializers.ModelSerializer):
    """ 示例 校验字段合法性"""

    def validate_name(self, validated_value):
        # 校验命名规则
        return validated_value

    def validate(self, attrs):
        attrs['update_time'] = timezone.now()
        return attrs

    class Meta:
        model = Department
        fields = ('id', 'name', 'department_id', 'parentid', 'update_time', 'create_time')


class UserSerializer(serializers.ModelSerializer):

    def validate(self, attrs):
        attrs['update_time'] = timezone.now()
        return attrs

    class Meta:
        model = User
        exclude = ('password',)


class ApprovalRecordSerializer(serializers.ModelSerializer):

    def validate(self, attrs):
        attrs['update_time'] = timezone.now()
        return attrs

    class Meta:
        model = ApprovalRecord
        fields = '__all__'


class AttendanceRecordSerializer(serializers.ModelSerializer):

    def validate(self, attrs):
        attrs['update_time'] = timezone.now()
        return attrs

    class Meta:
        model = AttendenceRecord
        fields = '__all__'


class HolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Holiday
        fields = '__all__'
