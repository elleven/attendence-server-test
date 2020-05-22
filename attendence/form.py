# -*- coding: utf-8 -*-
from django import forms
import datetime
from models import User, Department
from django.conf import settings
from attendence.common.holiday import Schedule

DEFAULT_ATTENDENCE_RULE = getattr(settings, 'DEFAULT_ATTENDENCE_RULE', None)


class LoginForm(forms.Form):
    """登陆验证表单"""
    jobnumber = forms.CharField(label="工号", max_length=10)
    password = forms.CharField(label="密码", max_length=256, widget=forms.PasswordInput)

    def clean(self):
        """验证"""
        return self.cleaned_data


class NewUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['id', 'name', 'jobnumber', 'attendence_id', 'email']


class QueryFrom(forms.Form):
    """考勤查询验证表单"""
    stime = forms.CharField(label='开始日期', max_length=20)
    etime = forms.CharField(label='结束日期', max_length=20)
    jobnumber = forms.CharField(label="工号", max_length=10)

    def clean_jobnumber(self):
        jobnumber = self.cleaned_data.get('jobnumber')
        try:
            User.objects.get(jobnumber=jobnumber)
        except User.DoesNotExist:
            raise forms.ValidationError('无效工号')
        return jobnumber

    def clean(self):
        max_query_day = DEFAULT_ATTENDENCE_RULE.get('MAX_QUERY_DAYS')
        stime = self.cleaned_data['stime']
        etime = self.cleaned_data['etime']
        if stime and etime:
            days = [day for day in Schedule.iter_diffdays(stime, etime)]
            if len(days) > max_query_day:
                raise forms.ValidationError('最大查询记录需要小于%s天' % max_query_day)
            else:
                return self.cleaned_data
        if not stime and not etime:
            return self.cleaned_data
        raise forms.ValidationError('无效的起止日期')


class AttendenceStatsForm(forms.Form):
    """ 考勤统计验证表单"""
    month = forms.CharField(label='月份', max_length=10)
    deptId = forms.CharField(label='部门id', max_length=50, required=False)
    jobnumber = forms.CharField(label="工号", max_length=10, required=False)

    def clean_month(self):
        """校验月份是否合法,并返回当前年月"""
        now_month = datetime.date.today().strftime("%m")
        month = self.cleaned_data.get('month')
        if int(month) >= int(now_month):
            raise forms.ValidationError('无效的月份')
        return month

    def clean_deptId(self):
        deptId = self.cleaned_data.get('deptId')
        if deptId:
            try:
                Department.objects.get(department_id=deptId)
            except Department.DoesNotExist:
                raise forms.ValidationError('无效部门')
        return deptId

    def clean_jobnumber(self):
        jobnumber = self.cleaned_data.get('jobnumber')
        if jobnumber:
            try:
                User.objects.get(jobnumber=jobnumber)
            except User.DoesNotExist:
                raise forms.ValidationError('无效工号')
        return jobnumber

    def clean(self):
        deptId = self.cleaned_data.get('deptId', None)
        jobnumber = self.cleaned_data.get('jobnumber', None)
        if deptId and jobnumber:
            raise forms.ValidationError('部门和工号二选一')
        return self.cleaned_data


class UnclockQueryForm(forms.Form):
    day = forms.CharField(label='日期', max_length=20)


class CurrentAttendenceForm(forms.Form):
    day = forms.CharField(label='日期', max_length=20)