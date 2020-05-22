# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from attendence.common.holiday import to_timestamp, Schedule
from django.core.exceptions import ObjectDoesNotExist
import time
from django.conf import settings

DEFAULT_ATTENDENCE_RULE = getattr(settings, 'DEFAULT_ATTENDENCE_RULE', None)


class DepartmentManager(models.Manager):
    """扩展"""
    def query_subdeptId(self, parentId):
        """根据父ID递归查询子ID，返回所有子id 列表"""
        result = []
        parentId = [parentId]

        def query(parentId, result):
            queryObj = self.filter(parentid__in=parentId)
            if len(queryObj) == 0:
                result += parentId
                return
            subdepts = [deptobj.department_id for deptobj in queryObj]
            result += subdepts[:]
            return query(subdepts, result)
        query(parentId, result)
        return result

    def query_mult_department(self, department_id):
        """归属多部门的情况，返回其中最上级部门"""
        if department_id and len(department_id.split(',')) > 1:
            min_id = min(department_id.split(','))
            return self.get(department_id=min_id)
        return self.get(department_id=department_id)


class Department(models.Model):
    """
    部门
    """
    name = models.CharField(
        _('department name'), max_length=125,
        db_index=True)

    department_id = models.CharField(
        _('department id'), max_length=125, null=False, unique=True)

    parentid = models.CharField(
        _('parent id '), max_length=125, null=True, blank=True)

    create_time = models.DateTimeField(
        auto_now_add=True)

    update_time = models.DateTimeField(
        default=timezone.now)

    def __unicode__(self):
        return self.name

    def __str__(self):
        return '(Department: %s, %s)' % (self.name, self.department_id)

    objects = DepartmentManager()

    class Meta:
        db_table = 'department'


class UserManager(models.Manager):
    """扩展"""
    def query_deptids_user(self, deptIds):
        # 空queryset
        ret = self.none()
        for deptid in deptIds:
            if deptid == '1':
                continue
            ret = ret | self.filter(department_id__contains=deptid, is_delete=False)
        return ret.distinct().order_by('jobnumber')
        # return self.filter(department_id__in=deptIds, is_delete=False).order_by('jobnumber')


class User(models.Model):
    """
    用户信息
    """

    name = models.CharField(
        _('user name'), max_length=125,
        db_index=True
    )
    password = models.CharField(
        max_length=125, null=True, blank=True)

    userid = models.CharField(
        _('user id'), max_length=125, null=False
    )
    jobnumber = models.CharField(
        _('job id'), max_length=125, null=False, unique=True
    )
    attendence_id = models.CharField(
        _('attendence id'), max_length=64, null=True, blank=True
    )
    email = models.CharField(
        _('user email'), max_length=125,  null=True, blank=True
    )
    department_id = models.CharField(
        _('department id'), max_length=125, null=False)

    workplace = models.CharField(
        _('workplace'), max_length=125, blank=True, null=True)

    is_delete = models.BooleanField(
        _('is delete'), default=False
    )

    create_time = models.DateTimeField(
        auto_now_add=True)

    update_time = models.DateTimeField(
        default=timezone.now)

    @property
    def mult_department_id(self):
        """用于统计周报时后的多部门id处理"""
        if len(self.department_id.split(',')) > 1:
            return min(self.department_id.split(','))
        return self.department_id

    def __unicode__(self):
        return self.name

    def __str__(self):
        return '(User: %s, %s)' % (self.name, self.userid)

    objects = UserManager()

    class Meta:
        db_table = 'user'


def sort_key(item):
    timeArray = time.strptime(item.record_date, str('%Y-%m-%d'))
    return int(time.mktime(timeArray))


class AttendenceRecordManager(models.Manager):
    """扩展的manager"""
    def attendence_query(self, stime, etime, jobnumber):
        """自定义考勤查询,由于原始记录不存在未打卡的考勤，在此处补上（蛋疼，需要优化"""
        max_query_day = DEFAULT_ATTENDENCE_RULE.get('MAX_QUERY_DAYS')
        ret = []
        if not stime or not etime or not jobnumber:
            return ret
        days = [day for day in Schedule.iter_diffdays(stime, etime)]
        if len(days) > max_query_day:
            return ret
        try:
            attendence_id = User.objects.get(jobnumber=jobnumber).attendence_id
            ret = [recordobj for recordobj in self.filter(record_date__in=days, attendence_id=attendence_id)]
            if len(ret) != len(days):
                result_range = {record.record_date for record in ret}
                for diff in set(days) - result_range:
                    diffobj = AttendenceRecord(attendence_id=attendence_id, record_date=diff, clockin_time='', clockout_time='', worktime='')
                    ret.append(diffobj)
            ret.sort(key=sort_key)
        except ObjectDoesNotExist:
            pass
        return ret

    def record_query(self, attendence_id, record_dates=None):
        """查询指定用户指定日期范围的考勤"""
        ret = []
        try:
            ret = [recordobj for recordobj in self.filter(record_date__in=record_dates, attendence_id=attendence_id)]
            if len(ret) != len(record_dates):
                result_range = {record.record_date for record in ret}
                for diff in set(record_dates) - result_range:
                    diffobj = AttendenceRecord(attendence_id=attendence_id, record_date=diff, clockin_time='', clockout_time='', worktime='')
                    ret.append(diffobj)
            ret.sort(key=sort_key)
        except ObjectDoesNotExist:
            pass
        return ret


class ApprovalRecordManager(models.Manager):
    """审批记录扩展的manager"""
    def approval_query(self, stime, etime, userid):
        """自定义审批记录查询，注意此处返回是字典，key为日期"""
        max_query_day = DEFAULT_ATTENDENCE_RULE.get('MAX_QUERY_DAYS')
        s = Schedule()
        ret = {}
        if not stime or not etime or not userid:
            return ret
        days = [day for day in Schedule.iter_diffdays(stime, etime)]
        if len(days) > max_query_day:
            return ret
        try:
            approval_objs = self.filter(originator_userid=userid, status="COMPLETED", result='agree')
            for day in days:
                tmp = []
                for approval_obj in approval_objs:
                    stime = approval_obj.start_time.split()[0]
                    etime = approval_obj.end_time.split()[0]
                    if s.check_time_in_range(day, stime, etime):
                        tmp.append(approval_obj)
                ret[day] = tmp
        except ObjectDoesNotExist:
            pass
        return ret

    def record_query(self, userid, record_dates=None):
        """查询指定用户 指定日期范围内的请休假记录，返回{day : info,}"""
        s = Schedule()
        ret = {}
        try:
            approval_objs = self.filter(originator_userid=userid, status="COMPLETED", result='agree')
            for day in record_dates:
                tmp = []
                for approval_obj in approval_objs:
                    stime = approval_obj.start_time.split()[0]
                    etime = approval_obj.end_time.split()[0]
                    if s.check_time_in_range(day, stime, etime):
                        tmp.append(approval_obj)
                ret[day] = tmp
        except ObjectDoesNotExist:
            pass
        return ret

# Create your models here.


class ApprovalRecord(models.Model):
    """审批记录"""

    instance_id = models.CharField(
        _('approval instance id'), max_length=125, unique=True,
        null=False, blank=False
    )
    approval_type = models.CharField(
        _('approval type'), max_length=64
    )
    status = models.CharField(
        _('approval status'), max_length=64
    )
    result = models.CharField(
        _('approval result'), max_length=64, null=True, blank=True
    )
    originator_userid = models.CharField(
        _('originator userid'), max_length=64
    )
    originator_dept_id = models.CharField(
        _('originator deptid'), max_length=64
    )
    approval_reason = models.CharField(
        _('approval reason'), max_length=125, null=True, blank=True
    )
    aproval_desc = models.CharField(
        _('approval desc'), max_length=125, null=True, blank=True
    )
    start_time = models.CharField(
        _('start time'), max_length=64
    )
    end_time = models.CharField(
        _('end time'), max_length=64
    )
    create_time = models.DateTimeField(
        auto_now_add=True)

    update_time = models.DateTimeField(
        default=timezone.now)

    objects = ApprovalRecordManager()

    def __unicode__(self):
        return self.instance_id

    class Meta:
        db_table = 'approval_record'


class AttendenceRecord(models.Model):
    """打卡记录"""

    attendence_id = models.CharField(
        _('attendence id'), max_length=125, null=False
    )
    record_date = models.CharField(
        _('record time'), max_length=64, null=False
    )
    clockin_time = models.CharField(
        _('clockin time'), max_length=64, blank=True, null=True
    )
    clockout_time = models.CharField(
        _('clockin time'), max_length=64, blank=True, null=True
    )
    worktime = models.CharField(
        _('work time'), max_length=64, blank=True, null=True
    )
    create_time = models.DateTimeField(
        auto_now_add=True)

    update_time = models.DateTimeField(
        default=timezone.now)

    @property
    def worktime_warning(self):
        """检测出勤时间是否小于10小时"""
        worktime_warn = DEFAULT_ATTENDENCE_RULE.get('WORKTIME_WARN')
        if self.worktime and float(self.worktime) < worktime_warn:
            return True
        return False

    @property
    def clockin_time_warning(self):
        """检测签到时间是否大于10:30, 此处不考虑请休假/节日情况/未打卡情况"""
        clockin_time_warn = DEFAULT_ATTENDENCE_RULE.get('CLOCKIN_TIME_WARN')
        if self.clockin_time:
            clockin_time_timestamp = to_timestamp(self.clockin_time)
            clockin_time_warn = ' '.join([self.clockin_time.split()[0], clockin_time_warn])
            clockin_time_warn_timestamp = to_timestamp(clockin_time_warn)
            if clockin_time_timestamp > clockin_time_warn_timestamp:
                return True
        return False

    @property
    def clockout_time_warning(self):
        """检测签退时间是否早于19:00,此处不考虑请休假/节假日/未打卡情况"""
        clockout_time_warn = DEFAULT_ATTENDENCE_RULE.get('CLOCKOUT_TIME_WARN')
        if self.clockout_time:
            clockout_time_timestamp = to_timestamp(self.clockout_time)
            clockout_time_warn = ' '.join([self.clockout_time.split()[0], clockout_time_warn])
            clockout_time_warn_timestamp = to_timestamp(clockout_time_warn)
            if clockout_time_timestamp < clockout_time_warn_timestamp:
                return True
        return False

    objects = AttendenceRecordManager()

    class Meta:
        db_table = 'attendence_record'
        unique_together = ('attendence_id', 'record_date')
        index_together = [['attendence_id', 'record_date'], ]


class HolidayManager(models.Manager):
    """expand"""
    def holiday_query(self, stime, etime):
        days = [day for day in Schedule.iter_diffdays(stime, etime)]
        return self.filter(day__in=days)

    def holiday_info(self, record_dates=None):
        return {obj.day: obj.is_holiday for obj in self.filter(day__in=record_dates)}


class Holiday(models.Model):
    """节假日信息"""
    day = models.CharField(
        _('date time'), max_length=64, null=False, unique=True)

    weekday = models.CharField(
        _('date time'), max_length=64, null=True, blank=True)

    is_holiday = models.BooleanField(
        _('is holiday'), default=False)

    holiday_info = models.CharField(
         _('holiday info'), max_length=64, null=True, blank=True)

    objects = HolidayManager()

    class Meta:
        db_table = 'holiday'


class UnclockReport(models.Model):
    """未打卡记录"""

    day = models.CharField(
        _('date time'), max_length=64, null=False)

    jobnumber = models.CharField(
        _('job id'), max_length=20, null=False)

    unclock_info = models.CharField(
        _('unclock info'), max_length=125, null=False)

    result = models.CharField(
        _('result'), max_length=64, null=False)

    class Meta:
        db_table = 'unclock_report'


class CurrentAttendenceReport(models.Model):
    """当天出勤报告，统计未打卡人员"""

    day = models.CharField(
        _('date time'), max_length=64, null=False)

    jobnumber = models.CharField(
        _('job id'), max_length=20, null=False)

    class Meta:
        db_table = 'current_attendenace_report'
        unique_together = ('day', 'jobnumber')
