# -*- coding: utf-8 -*-
from django import template
from django.utils.safestring import mark_safe
from django.utils.html import format_html

register = template.Library()


@register.filter
def multi(x, y):
    """自定义过滤器，for test"""
    return x*y


@register.simple_tag(takes_context=True)
def check_clock_time(context, record):
    """自定义标签过滤器,检测打卡时间
    1、无打卡、无请假记录的 （在无打卡的位置） 标色
    2、工时不足10小时 （在工时上） 标色
    3、晚于10:30，早于19:00 （在时间上） 标色"""
    red_font_code = '#FF0000'
    black_font_code = '#000000'
    html_template = "<td class='text-l'><font color='%s'>%s</font></td>"
    approval_info = context['approval_info']
    holidayobj = context['holidayobjs'].get(record.record_date)
    # 优化显示
    clockin_time = record.clockin_time if record.clockin_time and record.clockin_time != 'None' else ''
    clockout_time = record.clockout_time if record.clockout_time and record.clockout_time != 'None' else ''
    worktime = record.worktime if record.worktime and record.worktime != 'None' else ''
    # 默认页面
    record_date_html = html_template % (black_font_code, ' '.join([record.record_date, holidayobj.weekday]))
    clockin_time_html = html_template % (black_font_code, clockin_time)
    clockout_time_html = html_template % (black_font_code, clockout_time)
    worktime_html = html_template % (black_font_code, worktime)
    # 检测是否有请休假记录
    if len(approval_info.get(record.record_date)) > 0:
        ret_html = '\n'.join([record_date_html, clockin_time_html, clockout_time_html, worktime_html])
        return format_html(ret_html)
    # 检测是否为休息日/节假日
    if holidayobj.is_holiday:
        if not clockin_time:
            clockin_time_html = html_template % (black_font_code, u'休息日哦～')
        if not clockout_time:
            clockout_time_html = html_template % (black_font_code, u'休息日哦～')
        ret_html = '\n'.join([record_date_html, clockin_time_html, clockout_time_html, worktime_html])
        return format_html(ret_html)
    # 检测签到记录
    if not clockin_time:
        clockin_time_html = html_template % (red_font_code, u'签到未打卡')
    if record.clockin_time_warning:
        clockin_time_html = html_template % (red_font_code, clockin_time)
    # 检测签退记录
    if not clockout_time:
        clockout_time_html = html_template % (red_font_code, u'签退未打卡')
    if record.clockout_time_warning:
        clockout_time_html = html_template % (red_font_code, clockout_time)
    # 检测出勤记录
    if not worktime :
        worktime_html = html_template % (red_font_code, u'')
    if record.worktime_warning:
        worktime_html = html_template % (red_font_code, worktime)
    ret_html = '\n'.join([record_date_html, clockin_time_html, clockout_time_html, worktime_html])
    return format_html(ret_html)


@register.simple_tag()
def check_approval_info(record, approval_info):
    """检查请休假记录"""
    html_template = "<td class='text-l'>%s</td>"
    record_date = record.record_date
    approval_type = []
    approval_desc = []
    approval_objs = approval_info.get(record_date)
    if len(approval_objs) > 0:
        for approval_obj in approval_objs:
            aproval_desc = approval_obj.aproval_desc if approval_obj.aproval_desc not in ['null', 'None', ''] else approval_obj.approval_type
            t = '/'.join([approval_obj.approval_type, aproval_desc])
            d = '--'.join([approval_obj.start_time, approval_obj.end_time])
            approval_type.append(t)
            approval_desc.append(d)
    approval_type_str = '|'.join(approval_type)
    approval_desc_str = '|'.join(approval_desc)
    approval_type_html = html_template % approval_type_str
    approval_desc_html = html_template % approval_desc_str
    ret_html = '\n'.join([approval_type_html, approval_desc_html])
    return format_html(ret_html)


@register.simple_tag(takes_context=True)
def check_clock_time_for_dept(context, record):
    """部门考勤规则"""
    red_font_code = '#FF0000'
    black_font_code = '#000000'
    html_template = "<td class='text-l'><font color='%s'>%s</font></td>"
    approval_info = record['approval_info']
    holidayobj = context['holidayobjs'].get(record['record_date'])
    # 优化显示
    clockin_time = record['clockin_time'] if record['clockin_time'] and record['clockin_time'] != 'None' else ''
    clockout_time = record['clockout_time'] if record['clockout_time'] and record['clockout_time'] != 'None' else ''
    worktime = record['worktime'] if record['worktime'] and record['worktime'] != 'None' else ''
    # 默认页面
    record_date_html = html_template % (black_font_code, ' '.join([record['record_date'], holidayobj.weekday]))
    clockin_time_html = html_template % (black_font_code, clockin_time)
    clockout_time_html = html_template % (black_font_code, clockout_time)
    worktime_html = html_template % (black_font_code, worktime)
    # 检测是否有请休假记录
    if len(approval_info) > 0:
        ret_html = '\n'.join([record_date_html, clockin_time_html, clockout_time_html, worktime_html])
        return format_html(ret_html)
    # 检测是否为休息日/节假日
    if holidayobj.is_holiday:
        if not clockin_time:
            clockin_time_html = html_template % (black_font_code, u'休息日哦～')
        if not clockout_time:
            clockout_time_html = html_template % (black_font_code, u'休息日哦～')
        ret_html = '\n'.join([record_date_html, clockin_time_html, clockout_time_html, worktime_html])
        return format_html(ret_html)
    # 检测签到记录
    if not clockin_time:
        clockin_time_html = html_template % (red_font_code, u'签到未打卡')
    if record.clockin_time_warning:
        clockin_time_html = html_template % (red_font_code, clockin_time)
    # 检测签退记录
    if not clockout_time:
        clockout_time_html = html_template % (red_font_code, u'签退未打卡')
    if record.clockout_time_warning:
        clockout_time_html = html_template % (red_font_code, clockout_time)
    # 检测出勤记录
    if not worktime:
        worktime_html = html_template % (red_font_code, u'')
    if record.worktime_warning:
        worktime_html = html_template % (red_font_code, worktime)
    ret_html = '\n'.join([record_date_html, clockin_time_html, clockout_time_html, worktime_html])
    return format_html(ret_html)


@register.simple_tag()
def check_approval_info_for_dept(record):
    """检查请休假记录"""
    html_template = "<td class='text-l'>%s</td>"
    approval_type = []
    approval_desc = []
    approval_objs = record['approval_info']
    if len(approval_objs) > 0:
        for approval_obj in approval_objs:
            aproval_desc = approval_obj.aproval_desc if approval_obj.aproval_desc not in ['null', 'None', ''] else approval_obj.approval_type
            t = '/'.join([approval_obj.approval_type, aproval_desc])
            d = '--'.join([approval_obj.start_time, approval_obj.end_time])
            approval_type.append(t)
            approval_desc.append(d)
    approval_type_str = '|'.join(approval_type)
    approval_desc_str = '|'.join(approval_desc)
    approval_type_html = html_template % approval_type_str
    approval_desc_html = html_template % approval_desc_str
    ret_html = '\n'.join([approval_type_html, approval_desc_html])
    return format_html(ret_html)
