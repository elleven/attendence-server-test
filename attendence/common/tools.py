# -*- coding=utf-8 -*-
from django.conf import settings
from attendence.common.holiday import to_timestamp

DEFAULT_ATTENDENCE_RULE = getattr(settings, 'DEFAULT_ATTENDENCE_RULE', None)


class RecordDict(dict):
    """扩展字典"""

    @property
    def worktime_warning(self):
        """检测出勤时间是否小于10小时"""
        worktime_warn = DEFAULT_ATTENDENCE_RULE.get('WORKTIME_WARN')
        if self['worktime'] and float(self['worktime']) < worktime_warn:
            return True
        return False

    @property
    def clockin_time_warning(self):
        """检测签到时间是否大于10:30, 此处不考虑请休假/节日情况/未打卡情况"""
        clockin_time_warn = DEFAULT_ATTENDENCE_RULE.get('CLOCKIN_TIME_WARN')
        if self['clockin_time']:
            clockin_time_timestamp = to_timestamp(self['clockin_time'])
            clockin_time_warn = ' '.join([self['clockin_time'].split()[0], clockin_time_warn])
            clockin_time_warn_timestamp = to_timestamp(clockin_time_warn)
            if clockin_time_timestamp > clockin_time_warn_timestamp:
                return True
        return False

    @property
    def clockout_time_warning(self):
        """检测签退时间是否早于19:00,此处不考虑请休假/节假日/未打卡情况"""
        clockout_time_warn = DEFAULT_ATTENDENCE_RULE.get('CLOCKOUT_TIME_WARN')
        if self['clockout_time']:
            clockout_time_timestamp = to_timestamp(self['clockout_time'])
            clockout_time_warn = ' '.join([self['clockout_time'].split()[0], clockout_time_warn])
            clockout_time_warn_timestamp = to_timestamp(clockout_time_warn)
            if clockout_time_timestamp < clockout_time_warn_timestamp:
                return True
        return False