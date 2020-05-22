# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, redirect, HttpResponse
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet
from models import Department, User, ApprovalRecord, AttendenceRecord, Holiday, UnclockReport, CurrentAttendenceReport
from serializers import DepartmentSerializer, UserSerializer, ApprovalRecordSerializer, AttendanceRecordSerializer
from rest_framework.pagination import PageNumberPagination
from django.views.generic.base import TemplateView
from django.views.generic import ListView, View, DetailView
from attendence.common.holiday import Schedule
from attendence.common.statistics import LeaveInfoFromMysql
import datetime
from django.conf import settings
import json
from django.core.exceptions import ObjectDoesNotExist
from attendence.common.tools import RecordDict
from attendence.form import LoginForm, AttendenceStatsForm, QueryFrom, UnclockQueryForm, CurrentAttendenceForm, NewUserForm
from attendence.common.wraps import check_login
from django.db.models import Q

DEFAULT_ATTENDENCE_RULE = getattr(settings, 'DEFAULT_ATTENDENCE_RULE', None)
# PageNumberPagination


class AttendancePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    page_query_param = 'p'
    max_page_size = 20


class DepartmentViewSet(ModelViewSet):
    """部门信息"""
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer


class UserView(ReadOnlyModelViewSet):
    """员工信息"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    # pagination_class
    # permission_classes


class ApprovalRecordView(ReadOnlyModelViewSet):
    """补打卡申请记录"""
    queryset = ApprovalRecord.objects.all()
    serializer_class = ApprovalRecordSerializer


class AttendanceRecordView(ReadOnlyModelViewSet):
    """考勤记录"""
    queryset = AttendenceRecord.objects.all()
    serializer_class = AttendanceRecordSerializer
    pagination_class = AttendancePagination


class LoginRequireMixin(object):
    """登陆验证"""
    @classmethod
    def as_view(cls, **kwargs):
        view = super(LoginRequireMixin, cls).as_view(**kwargs)
        return check_login(view)


class HomePageView(LoginRequireMixin, TemplateView):
    """index.html"""
    template_name = "index.html"


class LoginView(View):
    """登陆认证页面"""
    def get(self, request):
        if request.session.get('is_login', None):
            return redirect('/')
        return render(request, 'login.html')

    def post(self, request):
        """处理认证"""
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            jobnumber = login_form.cleaned_data['jobnumber']
            password = login_form.cleaned_data['password']
            try:
                userobj = User.objects.get(jobnumber=jobnumber, is_delete=False)
                if userobj.password == password:
                    request.session['is_login'] = True
                    request.session['userid'] = userobj.userid
                    request.session['jobnumber'] = userobj.jobnumber
                    request.session['username'] = userobj.name
                    return redirect('/')
                else:
                    message = u'无效的工号或密码'
            except User.DoesNotExist as why:
                message = u'用户不存在'
        else:
            message = login_form.errors

        return render(request, 'login.html', locals())


class LogoutView(LoginRequireMixin, View):
    """登出"""
    def get(self, request):
        if not request.session.get('is_login', None):
            return redirect("/login")
        request.session.flush()
        return redirect("/login")


class QueryMixin(object):
    """考勤查询数据组装 ;此混合器没有使用"""

    def default_record_dates(self):
        """默认的查询日期范围"""
        s = Schedule()
        time_now = datetime.date.today().strftime('%Y-%m-%d')
        default_stime, default_etime = s.get_lastweek(time_now)
        return [day for day in Schedule.iter_diffdays(default_stime, default_etime)]

    def person_query(self, jobnumber, record_dates=None):
        """个人考勤数据查询组装"""
        records = []
        usrobj = User.objects.get(jobnumber=jobnumber)
        approval_records = ApprovalRecord.objects.record_query(userid=usrobj.userid, record_dates=record_dates)
        attendence_records = AttendenceRecord.objects.record_query(attendence_id=usrobj.attendence_id, record_dates=record_dates)
        departname = Department.objects.get(department_id=usrobj.department_id).name
        for attendence_record in attendence_records:
            record_date = attendence_record.record_date
            ret = RecordDict()
            ret.update(usrobj.__dict__)
            ret.update(attendence_record.__dict__)
            ret.update({'approval_info': approval_records.get(record_date)})
            ret.update({'department_name': departname})
            records.append(ret)
        return records

    def dept_query(self, deptId, record_dates=None):
        """部门考勤数据查询组装"""
        pass


class PersonQueryViewNew(LoginRequireMixin, QueryMixin, View):
    """重构的个人考勤查询, 尚未使用"""
    def get(self, request):
        records = None
        query_form = QueryFrom(request.GET)
        if query_form.is_valid():
            jobnumber = query_form.cleaned_data['jobnumber']
            stime = query_form.cleaned_data['stime']
            etime = query_form.cleaned_data['etime']
            record_dates = self.default_record_dates() if not stime and not etime else [day for day in Schedule.iter_diffdays(stime, etime)]
            records = self.person_query(jobnumber=jobnumber, record_dates=record_dates)
            holidayobjs = {obj.day: obj for obj in Holiday.objects.filter(day__in=record_dates)}
            execfilename = '-'.join([record_dates[0], record_dates[-1], jobnumber])
            return render(request, 'person_query_new.html', locals())
        else:
            errors = query_form.errors
            return render(request, 'person_query_new.html', locals())


class PersonQueryView(LoginRequireMixin, ListView):
    """个人考勤查询页面 """
    template_name = "person_query.html"
    # model = AttendenceRecord
    # paginate_by = DEFAULT_ATTENDENCE_RULE.get('PAGINATE_BY')
    context_object_name = 'records'
    # ordering = 'record_date'

    def default_params(self):
        s = Schedule()
        time_now = datetime.date.today().strftime('%Y-%m-%d')
        default_stime, default_etime = s.get_lastweek(time_now)
        stime = self.request.GET.get('stime', default_stime)
        etime = self.request.GET.get('etime', default_etime)
        stime = stime if stime != '' else default_stime
        etime = etime if etime != '' else default_etime
        jobnumber = self.request.GET.get('jobnumber', None)
        return stime, etime, jobnumber

    def get_queryset(self):
        """返回符合条件的查询集合"""
        stime, etime, jobnumber = self.default_params()
        ret = AttendenceRecord.objects.attendence_query(stime, etime, jobnumber)
        return ret

    def get_context_data(self, **kwargs):
        """附加额外的信息,完善数据；如 请休假信息"""
        context = super(PersonQueryView, self).get_context_data(**kwargs)
        context['stime'], context['etime'],  context['jobnumber'] = self.default_params()
        try:
            userobj = User.objects.get(jobnumber=context['jobnumber'])
            deptobj = Department.objects.query_mult_department(department_id=userobj.department_id)
            approval_info = ApprovalRecord.objects.approval_query(context['stime'], context['etime'], userobj.userid)
            holidayobjs = {obj.day: obj for obj in Holiday.objects.holiday_query(context['stime'], context['etime'])}
            context['deptobj'] = deptobj
            context['userobj'] = userobj
            context['approval_info'] = approval_info
            context['holidayobjs'] = holidayobjs
            context['execfilename'] = '-'.join([context['stime'], context['etime'],  context['jobnumber']])
        except Exception as why:
            print why
        return context


class ApprovalQueryView(LoginRequireMixin, ListView):
    """个人请休假审批查询"""
    template_name = "approval_query.html"
    paginate_by = DEFAULT_ATTENDENCE_RULE.get('PAGINATE_BY')
    context_object_name = 'records'
    # ordering = ''

    def get_queryset(self):
        ret = []
        stime = self.request.GET.get('stime', None)
        etime = self.request.GET.get('etime', None)
        jobnumber = self.request.GET.dict().get('jobnumber', None)
        try:
            days = [day for day in Schedule.iter_diffdays(stime, etime)]
            userid = User.objects.get(jobnumber=jobnumber).userid
            leave = LeaveInfoFromMysql()
            for day in days:
                ret += leave.query_leave_info(userid, day)
        except Exception:
            pass
        return ret

    def get_context_data(self, **kwargs):
        context = super(ApprovalQueryView, self).get_context_data(**kwargs)
        jobnumber = self.request.GET.get('jobnumber', None)
        stime = self.request.GET.get('stime', None)
        etime = self.request.GET.get('etime', None)
        context['jobnumber'] = jobnumber or u'员工工号'
        context['stime'] = stime or u'开始日期'
        context['etime'] = etime or u'结束日期'
        try:
            userobj = User.objects.get(jobnumber=jobnumber)
            deptobj = Department.objects.query_mult_department(department_id=userobj.department_id)
            context['deptobj'] = deptobj
            context['userobj'] = userobj
        except Exception:
            pass

        return context


class UserQuery(LoginRequireMixin, DetailView):
    """用户查询"""
    template_name = 'user_info.html'
    context_object_name = 'userobj'
    slug_field = 'jobnumber'
    slug_url_kwarg = 'jobnumber'
    model = User


class DeptQueryView(LoginRequireMixin, ListView):
    """部门考勤查询,待优化view 和mixin 实现"""
    template_name = 'dept_attendence_query.html'
    # paginate_by = DEFAULT_ATTENDENCE_RULE.get('PAGINATE_BY')
    context_object_name = 'records'

    def default_params(self):
        s = Schedule()
        time_now = datetime.date.today().strftime('%Y-%m-%d')
        default_stime, default_etime = s.get_lastweek(time_now)
        stime = self.request.GET.get('stime', default_stime)
        etime = self.request.GET.get('etime', default_etime)
        stime = stime if stime != '' else default_stime
        etime = etime if etime != '' else default_etime
        deptId = self.request.GET.get('deptId', None)
        return stime, etime, deptId

    def get_queryset(self):
        """返回部门下所有员工指定日期的考勤"""
        records = []
        stime, etime, deptId = self.default_params()
        if not deptId:
            return records
        try:
            deptIds = Department.objects.query_subdeptId(deptId)
            userobjs = User.objects.query_deptids_user(deptIds)
            for userobj in userobjs:
                approval_record = ApprovalRecord.objects.approval_query(stime, etime, userobj.userid)
                departname = Department.objects.query_mult_department(department_id=userobj.department_id).name
                for recordobj in AttendenceRecord.objects.attendence_query(stime, etime, userobj.jobnumber):
                    record_date = recordobj.record_date
                    ret = RecordDict()
                    ret.update(userobj.__dict__)
                    ret.update(recordobj.__dict__)
                    ret.update({'approval_info': approval_record.get(record_date)})
                    ret.update({'department_name': departname})
                    records.append(ret)
        except ObjectDoesNotExist:
            pass
        return records

    def get_context_data(self, **kwargs):
        """附加信息"""
        context = super(DeptQueryView, self).get_context_data(**kwargs)
        context['stime'], context['etime'], context['deptId'] = self.default_params()
        _ret = [
            {
                'id': dept.department_id,
                'name': dept.name,
                'pId': dept.parentid,
                'open': 0,
            } for dept in Department.objects.all()
        ]
        context['org_data'] = json.dumps(_ret)
        holidayobjs = {obj.day: obj for obj in Holiday.objects.holiday_query(context['stime'], context['etime'])}
        context['holidayobjs'] = holidayobjs
        try:
            deptobj = Department.objects.query_mult_department(department_id=context['deptId'])
            dept_name = deptobj.name
            context['deptobj'] = deptobj
        except Department.DoesNotExist:
            dept_name = u'未知的部门'

        context['execfilename'] = '-'.join([context['stime'], context['etime'],  dept_name])
        return context

@check_login
def Org(request):
    """用于组织架构的生成"""
    _ret = [
        {
            'id': dept.department_id,
            'name': dept.name,
            'pId': dept.parentid,
            'open': 0,
        } for dept in Department.objects.all()
    ]
    return render(request, 'dept_tree.html', {'data': json.dumps(_ret)})


class DeptDetailView(LoginRequireMixin, ListView):
    """部门详情"""
    template_name = 'dept_detail.html'
    context_object_name = 'deptobj'

    def get_queryset(self):
        deptId = self.request.GET.get('deptId')
        try:
            ret = Department.objects.query_mult_department(department_id=deptId)
        except Department.DoesNotExist:
            ret = []
        return ret

    def get_context_data(self, **kwargs):
        context = super(DeptDetailView, self).get_context_data(**kwargs)
        deptId = self.request.GET.get('deptId')
        if deptId == '1':
            userobjs = User.objects.all()
        else:
            userobjs = User.objects.query_deptids_user(deptIds=[deptId])
        context['userobjs'] = userobjs
        return context


class StatsMixin(object):
    """考勤统计查询混合类 方便其他view引用"""
    def person_stats(self, jobnumber, month):
        """个人考勤统计"""
        ret = {}
        s = Schedule()
        now_year = datetime.date.today().strftime("%Y")
        record_dates = [d for d in s.iter_mothdays(int(now_year), int(month))]
        # 准备前置数据
        userobj = User.objects.get(jobnumber=jobnumber)
        attendence_records = AttendenceRecord.objects.record_query(attendence_id=userobj.attendence_id, record_dates=record_dates)
        approval_records = ApprovalRecord.objects.record_query(userid=userobj.userid, record_dates=record_dates)
        holiday_info = Holiday.objects.holiday_info(record_dates=record_dates)
        # 初始化
        unclockin_num = unclockout_num = worktime_lt_num = late_num = early_num = 0
        # 计算
        for attendence_record in attendence_records:
            record_date = attendence_record.record_date
            # 不统计节假日/请休假情况
            if not holiday_info.get(record_date, None) and len(approval_records.get(record_date, [])) == 0:
                if not attendence_record.clockin_time:
                    unclockin_num += 1
                if not attendence_record.clockout_time:
                    unclockout_num += 1
                if attendence_record.clockin_time_warning:
                    late_num += 1
                if attendence_record.clockout_time_warning:
                    early_num += 1
                if attendence_record.worktime_warning:
                    worktime_lt_num += 1
        # 组装
        ret.update(
            {  'name': userobj.name,
               'jobnumber': userobj.jobnumber,
               'deptname': Department.objects.query_mult_department(department_id=userobj.department_id).name,
               'month': '-'.join([now_year, month]),
               'unclockin_num': unclockin_num,
               'unclockout_num': unclockout_num,
               'worktime_lt_num': worktime_lt_num,
               'late_num': late_num,
               'early_num': early_num
             }
         )
        return ret

    def dept_stats(self, deptId, month, func):
        """部门考勤统计"""
        ret = []
        deptIds = Department.objects.query_subdeptId(deptId)
        userobjs = User.objects.query_deptids_user(deptIds)
        for userobj in userobjs:
            ret.append(func(userobj.jobnumber, month))
        return ret

    def get_org_data(self):
        """获取组装结构"""
        ret = [
            {
                'id': dept.department_id,
                'name': dept.name,
                'pId': dept.parentid,
                'open': 0,
            } for dept in Department.objects.all()
        ]
        return json.dumps(ret)

    def person_approval_stats(self, jobnumber, month):
        """个人请休假信息统计"""
        ret = {}
        s = Schedule()
        now_year = datetime.date.today().strftime("%Y")
        record_dates = [d for d in s.iter_mothdays(int(now_year), int(month))]
        # 准备前置数据
        userobj = User.objects.get(jobnumber=jobnumber)
        attendence_records = AttendenceRecord.objects.record_query(attendence_id=userobj.attendence_id,
                                                                   record_dates=record_dates)
        approval_records = ApprovalRecord.objects.record_query(userid=userobj.userid, record_dates=record_dates)
        holiday_info = Holiday.objects.holiday_info(record_dates=record_dates)
        # 初始化
        unclock_day = winter_leave = sick_leave = person_leave = fullpay_sick_leave = halfpay_sick_leave = marriage_leave = maternity_leave \
            = siling_leave = dead_leave = baby_leave = 0
        # stats
        for attendence_record in attendence_records:
            record_date = attendence_record.record_date
            # 不统计节假日/请休假情况
            if not holiday_info.get(record_date, None) and len(approval_records.get(record_date, [])) == 0:
                if not attendence_record.clockin_time or not attendence_record.clockout_time:
                    unclock_day += 1
        # 计算需要去重
        has_sum_list = []
        for day, approval_objs in approval_records.iteritems():
            if len(approval_objs) > 0:
                for approval_obj in approval_objs:
                    if approval_obj.instance_id not in has_sum_list:
                        if approval_obj.approval_type == u'请假':
                            if approval_obj.aproval_desc in [u'年假']:
                                winter_leave += s.count_diff_day(approval_obj.start_time, approval_obj.end_time, int(month))
                            if approval_obj.aproval_desc in [u'司龄假']:
                                siling_leave += s.count_diff_day(approval_obj.start_time, approval_obj.end_time, int(month))
                            if approval_obj.aproval_desc in [u'病假']:
                                sick_leave += s.count_diff_day(approval_obj.start_time, approval_obj.end_time, int(month))
                            if approval_obj.aproval_desc in [u'事假']:
                                person_leave += s.count_diff_day(approval_obj.start_time, approval_obj.end_time, int(month))
                            if approval_obj.aproval_desc in [u'全薪病假']:
                                fullpay_sick_leave += s.count_diff_day(approval_obj.start_time, approval_obj.end_time, int(month))
                            if approval_obj.aproval_desc in [u'半薪病假/事假']:
                                halfpay_sick_leave += s.count_diff_day(approval_obj.start_time, approval_obj.end_time, int(month))
                            if approval_obj.aproval_desc in [u'婚假']:
                                marriage_leave += s.count_diff_day(approval_obj.start_time, approval_obj.end_time, int(month))
                            if approval_obj.aproval_desc in [u'丧假']:
                                dead_leave += s.count_diff_day(approval_obj.start_time, approval_obj.end_time, int(month))
                            if approval_obj.aproval_desc in [u'产检假或陪产假']:
                                maternity_leave += s.count_diff_day(approval_obj.start_time, approval_obj.end_time, int(month))
                            if approval_obj.aproval_desc in [u'产假']:
                                baby_leave += s.count_diff_day(approval_obj.start_time, approval_obj.end_time, int(month))
                            has_sum_list.append(approval_obj.instance_id)
        # 组装
        ret.update(
            {
                'name': userobj.name,
                'jobnumber': userobj.jobnumber,
                'deptname': Department.objects.query_mult_department(department_id=userobj.department_id).name,
                'month': '-'.join([now_year, month]),
                'unclock_day': unclock_day,
                'winter_leave': winter_leave,
                'sick_leave': sick_leave,
                'person_leave': person_leave,
                'fullpay_sick_leave': fullpay_sick_leave,
                'halfpay_sick_leave': halfpay_sick_leave,
                'marriage_leave': marriage_leave,
                'maternity_leave': maternity_leave,
                'siling_leave': siling_leave,
                'dead_leave': dead_leave,
                'baby_leave': baby_leave
            }
        )
        return ret


class PersonAttendanceStats(LoginRequireMixin, StatsMixin, View):
    """个人考勤统计"""
    def get(self, request):
        """获取分析统计数据"""
        records = None
        org_data = self.get_org_data()
        statsform = AttendenceStatsForm(request.GET)
        if statsform.is_valid():
            jobnumber = statsform.cleaned_data['jobnumber']
            deptId = statsform.cleaned_data['deptId']
            month = statsform.cleaned_data['month']
            if deptId:
                records = self.dept_stats(deptId, month, self.person_stats)
                deptName = Department.objects.query_mult_department(department_id=deptId).name
                execfilename = '-'.join([deptName, month])
            if jobnumber:
                records = [self.person_stats(jobnumber, month)]
                username = User.objects.get(jobnumber=jobnumber).name
                execfilename = '-'.join([username, month])

        return render(request, 'attendance_stats.html', locals(), )


class UclockReportView(LoginRequireMixin, ListView):
    """昨天未打卡通知报告"""
    template_name = 'unclock_report.html'
    model = UnclockReport
    context_object_name = 'records'
    ordering = 'jobnumber'

    def get_queryset(self):
        ret = []
        unclockform = UnclockQueryForm(self.request.GET)
        if unclockform.is_valid():
            day = unclockform.cleaned_data['day']
            for recordobj in UnclockReport.objects.filter(day=day):
                tmp = {}
                userobj = User.objects.get(jobnumber=recordobj.jobnumber)
                try:
                    deptname = Department.objects.query_mult_department(department_id=userobj.department_id).name
                except Department.DoesNotExist:
                    deptname = userobj.department_id
                tmp.update(recordobj.__dict__)
                tmp.update({
                    'name': userobj.name,
                    'departname': deptname
                })
                ret.append(tmp)
            return ret


class ApprovalStatsView(LoginRequireMixin, StatsMixin, View):
    """个人请休假情况统计"""
    def get(self, request):
        org_data = self.get_org_data()
        records = []
        statsform = AttendenceStatsForm(request.GET)
        if statsform.is_valid():
            jobnumber = statsform.cleaned_data['jobnumber']
            deptId = statsform.cleaned_data['deptId']
            month = statsform.cleaned_data['month']
            if deptId:
                records = self.dept_stats(deptId, month, self.person_approval_stats)
                deptName = Department.objects.query_mult_department(department_id=deptId).name
                execfilename = '-'.join([deptName, month])
            if jobnumber:
                records = [self.person_approval_stats(jobnumber, month)]
                username = User.objects.get(jobnumber=jobnumber).name
                execfilename = '-'.join([username, month])
        return render(request, 'approval_stats.html', locals(), )


class CurrentAttendenceView(LoginRequireMixin, ListView):
    """当天上午签到未打卡通知报告"""
    template_name = 'current_unclock.html'
    model = CurrentAttendenceReport
    context_object_name = 'records'
    ordering = 'jobnumber'

    def get_queryset(self):
        ret = []
        unclockform = CurrentAttendenceForm(self.request.GET)
        if unclockform.is_valid():
            day = unclockform.cleaned_data['day']
            for recordobj in CurrentAttendenceReport.objects.filter(day=day):
                tmp = {}
                userobj = User.objects.get(jobnumber=recordobj.jobnumber)
                try:
                    deptname = Department.objects.query_mult_department(department_id=userobj.department_id).name
                except Department.DoesNotExist:
                    deptname = userobj.department_id
                tmp.update(recordobj.__dict__)
                tmp.update({
                    'name': userobj.name,
                    'departname': deptname
                })
                ret.append(tmp)
            return ret


class NewUserlistView(LoginRequireMixin, ListView):
    """员工管理，用于hr给新员工补充attendence_id信息"""
    template_name = 'new_user_list.html'
    context_object_name = 'newuser_objs'
    ordering = 'jobnumber'


    def get_queryset(self):
        # return User.objects.filter(is_delete=False).filter(Q(attendence_id__isnull=True)| \
                                                                                #Q(attendence_id__exact='')| \
                                                                                #Q(attendence_id__exact=None))
        return User.objects.filter(is_delete=False)


class NewUserView(LoginRequireMixin, View):
    """新员工编辑,只限更新添加attendence_id"""
    def get(self, request, *args, **kwargs):
        if request.GET.get('id', None):
            try:
                userobj = User.objects.get(id=request.GET.get('id'))
                return render(request, 'newuser_edit.html', locals())
            except Exception as why:
                return HttpResponse(why)

    def post(self, request, *args, **kwargs):
        id = request.POST.get('id', None)
        attendence_id = request.POST.get('attendence_id', None)
        if id:
            try:
                userobj = User.objects.get(id=id)
                ser = UserSerializer(instance=userobj, data={'attendence_id': attendence_id}, partial=True)
                if ser.is_valid():
                    ser.save()
                    return redirect('/newuser/manager')
                else:
                    return HttpResponse(ser.errors)
            except Exception as why:
                return HttpResponse(why)
        else:
            return HttpResponse('invaild params')

