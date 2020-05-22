# coding=utf-8
# import os,django
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "attendence_server.settings")
# django.setup()
from django.conf import settings
from attendence.models import Department, User, ApprovalRecord, AttendenceRecord, Holiday
from holiday import Schedule
import time
import logging

logger = logging.getLogger('default')

STATISTICS_DEPTS = getattr(settings, 'DEFAULT_ORG', None)
STATISTICS_DEVELOP_DEPTS = getattr(settings, 'DEFAULT_DEVELOP_ORG', None)
STATISTICS_DEPTS_HRBP = getattr(settings, 'DEFAULT_ORG_HRBP_MAP', None)


class OrgFromMysql(object):
    """从数据库获取公司组织结构"""
    def __init__(self):
        # dept name to id map
        self.dept_name_id_map = None
        self.dept_id_name_map = None
        # default deptIds of org
        self.default_deptIds = None
        # default deptIds of develop org
        self.default_develop_deptIds = None
        # default dept to userIds map
        self.deptId_user_map = {}
        # default parentId to subId map
        self.parentId_subId_map = {}
        # attendenceId to jobnumber map
        self.attendenceId_jobnum = {}

    def get_level_one_departs(self):
        """从settings获取配置的一级部门"""
        all_level_one_departs = []
        for item in STATISTICS_DEPTS_HRBP:
            all_level_one_departs += item.get('departments')
        return all_level_one_departs

    def init_data(self):
        """从数据库加载组织结构数据,用于统计报表;
            此处是根据setting.py 定义的二级部门归纳统计的"""
        self.dept_name_id_map = {dept.name: dept.department_id for dept in Department.objects.all()}
        self.dept_id_name_map = {deptId: name for name, deptId in self.dept_name_id_map.iteritems()}
        self.default_deptIds = [self.dept_name_id_map[dept] for dept in STATISTICS_DEPTS.keys()]
        self.default_develop_deptIds = [self.dept_name_id_map[dept] for dept in STATISTICS_DEVELOP_DEPTS]

        for deptId in self.default_deptIds:
            self.parentId_subId_map[deptId] = self.query_subdeptId([deptId])

        for deptId, sub_deptIds in self.parentId_subId_map.iteritems():
            sub_deptIds.append(deptId)
            self.deptId_user_map[deptId] = User.objects.query_deptids_user(deptIds=sub_deptIds)
        managers = []
        for userobj in User.objects.filter(is_delete=False):
            self.attendenceId_jobnum[userobj.attendence_id] = userobj.jobnumber
            # 单独处理管理层
            if '1' in userobj.department_id.split(','):
                managers.append(userobj)
        self.deptId_user_map['1'] = managers
        logger.info('init org data from mysql done')

    def init_data_2(self):
        """从数据库加载组织结构数据，用于统计报表；
           此处是根据setting.py 定义的一级部门归纳统计
           没时间重构，只能凑合了。。。"""
        self.dept_name_id_map = {dept.name: dept.department_id for dept in Department.objects.all()}
        self.dept_id_name_map = {deptId: name for name, deptId in self.dept_name_id_map.iteritems()}
        self.default_deptIds = [self.dept_name_id_map[dept] for dept in self.get_level_one_departs()]
        self.default_develop_deptIds = [self.dept_name_id_map[dept] for dept in STATISTICS_DEVELOP_DEPTS]

        for deptId in self.default_deptIds:
            self.parentId_subId_map[deptId] = self.query_subdeptId([deptId])

        for deptId, sub_deptIds in self.parentId_subId_map.iteritems():
            sub_deptIds.append(deptId)
            self.deptId_user_map[deptId] = User.objects.query_deptids_user(deptIds=sub_deptIds)
        managers = []
        for userobj in User.objects.filter(is_delete=False):
            self.attendenceId_jobnum[userobj.attendence_id] = userobj.jobnumber
            # 单独处理管理层
            if '1' in userobj.department_id.split(','):
                managers.append(userobj)
        self.deptId_user_map['1'] = managers
        logger.info('init org data2 from mysql done')
        # for dptid, userids in self.deptId_user_map.iteritems():
        #   logger.info('%s, %s ', dptid, len(userids))

    def query_subdeptId(self, parentId=[]):
        """根据父ID递归查询子ID，返回所有子id 列表"""
        result = []

        def query(parentId, result):
            queryObj = Department.objects.filter(parentid__in=parentId)
            if len(queryObj) == 0:
                return
            subdepts = [deptobj.department_id for deptobj in queryObj]
            result += subdepts[:]
            return query(subdepts, result)
        query(parentId, result)
        return result

    def get_user(self):
        """过滤获取北京员工"""
        return User.objects.filter(workplace='北京', is_delete=False)


class LeaveInfoFromMysql(object):
    """从数据库获取请休假信息，提供查询"""

    def __init__(self):
        self.leave_info = {}

    def get_object(self):
        """获取审批状态通过的请休假记录"""
        _object = ApprovalRecord.objects.filter(status="COMPLETED", result="agree")
        logger.info('load ApprovalRecord from mysql done')
        return _object

    def init_data(self):
        """格式化请休假信息，方便统计报表查询"""

        for record in self.get_object():
            if record.originator_userid in self.leave_info:
                self.leave_info[record.originator_userid].append(record)
            else:
                self.leave_info[record.originator_userid] = [record]
        logger.info('format ApprovalRecord done')

    def get_leave_info(self, userid, date):
        """给定日期和userid 查询请假信息,考虑到请假有半天情况，一天可能有多种请假组合，返回列表"""
        ret = []
        records = self.leave_info.get(userid, [])
        if len(records) == 0:
            return records
        for record in records:
            stime = record.start_time.split()[0]
            etime = record.end_time.split()[0]
            if self.check_time_in_range(date, stime, etime):
                ret.append(record)
        return ret

    def check_time_in_range(self, date, stime, etime):
        """给定指定日期，判断日期是否在范围之内
            date='2019-10-01
            stime=2019-10-01
            etime=2019-10-02'
            """
        datetimestamp = int(time.mktime(time.strptime(date, "%Y-%m-%d")))
        stimestamp = int(time.mktime(time.strptime(stime, "%Y-%m-%d")))
        etimestamp = int(time.mktime(time.strptime(etime, "%Y-%m-%d")))
        if etimestamp >= datetimestamp >= stimestamp:
            return True
        return False

    def query_leave_info(self, userid, date):
        """根据指定用户，指定日期从数据库查询符合记录的请假申请记录"""
        ret = []
        _object = ApprovalRecord.objects.filter(originator_userid=userid,)
        for record in _object:
            stime = record.start_time.split()[0]
            etime = record.end_time.split()[0]
            if self.check_time_in_range(date, stime, etime):
                ret.append(record)
        return ret


class AttendenceFromMysql(object):
    """从数据库获取考勤数据
    此处 attendence_id 不等于jobnumber，属于考勤设备中人员编号
    { attendence_id : [record,...]}"""
    def __init__(self, stime, etime):
        self.attendence_info = {}
        # 几天的考勤数据
        self.days_num = None
        self.stime = stime
        self.etime = etime

    def init_data(self):
        """初始化指定时间范围内的考勤记录"""
        timerange = [date for date in Schedule.iter_diffdays(self.stime, self.etime)]
        self.days_num = len(timerange)
        _object = AttendenceRecord.objects.filter(record_date__in=timerange)
        for record in _object:
            attendence_id = record.attendence_id
            if attendence_id in self.attendence_info:
                self.attendence_info[attendence_id].append(record)
            else:
                self.attendence_info[attendence_id] = [record]
        logger.info('laod AttendenceRecord from %s to %s done', self.stime, self.etime)

    def get_average_worktime(self):
        """ 计算考勤范围内的平均出勤时间"""
        ret = {}
        for attendence_id, records in self.attendence_info.iteritems():
            worktime_list = [float(record.worktime) for record in records if record.worktime]
            if len(worktime_list) > 0:
                ret[attendence_id] = round(sum(worktime_list)/len(worktime_list), 1)
        return ret


def sort_key(item):
    timeArray = time.strptime(item.get('record_date'), "%Y-%m-%d")
    return int(time.mktime(timeArray))


class Statistics(object):
    """根据指定的时间范围 收集考勤数据，组织架构数据，请休假数据；
       并根据需求处理返回周报需要的数据。
    { deptid: {
               jobnumber: [{record...}, ...]
             }
    }"""
    def __init__(self, stime, etime):
        self.stime = stime
        self.etime = etime
        self.lables = ['deaprtname', 'jobnumber', 'username', 'record_date', 'clockin_time', 'clockout_time', 'worktime',  'leave_info']
        self.lables_CN = [u'部门', u'工号', u'姓名', u'日期', u'签到时间', u'签退时间', u'出勤时间', u'请假详情', u'平均出勤时间']
        self.statistic_data = {}
        # org
        self.org = OrgFromMysql()
        # leave info
        self.leave = LeaveInfoFromMysql()
        # init attendance
        self.att = None
        self.average_worktime = {}
        # 请休假信息
        self.holiday = None
        # 平均出勤小于10
        self.person_worktime_len_ten = []

    def _init_attendence(self):
        """初始化指定时间范围内的考勤记录、节假日信息"""
        self.att = AttendenceFromMysql(self.stime, self.etime)
        self.att.init_data()
        self.holiday = {holidayobj.day: holidayobj.is_holiday for holidayobj in Holiday.objects.holiday_query(self.stime, self.etime)}

    def assembly_record(self):
        """根据二级部门归纳考勤报表信息"""
        # 加载考勤数据
        self._init_attendence()
        # 加载组织架构数据
        self.org.init_data()
        # 加载请休假信息
        self.leave.init_data()
        # 归纳考勤数据
        for deptId, users_obj in self.org.deptId_user_map.iteritems():
            self.statistic_data[deptId] = {userobj.jobnumber:  self._format_data(userobj) for userobj in users_obj}
        logger.info('assembly_record ok ')

    def assembly_record_2(self):
        """根据一级部门归纳考勤报表信息"""
        # 加载考勤数据
        self._init_attendence()
        # 加载组织架构数据
        self.org.init_data_2()
        # 加载请休假信息
        self.leave.init_data()
        # 归纳考勤数据
        for deptId, users_obj in self.org.deptId_user_map.iteritems():
            self.statistic_data[deptId] = {userobj.jobnumber: self._format_data(userobj) for userobj in users_obj}
        logger.info('assembly_record_2 ok ')

    def _format_data(self, userobj):
        """根据请休假信息，节假日信息，考勤信息，用户信息，组织生产用的的考勤报表数据"""
        ret = []
        worktime_list = []
        timerange = {date for date in Schedule.iter_diffdays(self.stime, self.etime)}
        results = self.att.attendence_info.get(userobj.attendence_id, [])
        if len(results) != self.att.days_num:
            result_range = {record.record_date for record in results}
            for diff in timerange - result_range:
                diffobj = AttendenceRecord(record_date=diff)
                results.append(diffobj)
        for attendence_record in results:
            # 组装数据
            record_date = attendence_record.record_date
            _record = {k: None for k in self.lables}
            # 组装请休假信息
            leave_records = self.leave.get_leave_info(userid=userobj.userid, date=record_date)
            approval_types = []
            for record in leave_records:
                # 如果aproval_desc 没有则取aproval_type 作为请假类型
                type_s = record.aproval_desc if record.aproval_desc != 'null' and record.aproval_desc else record.approval_type
                approval_types.append(type_s)
            approval_type_s = approval_types[0] if len(approval_types) > 0 else ''
            approval_type_e = approval_types[1] if len(approval_types) > 1 else approval_type_s
            _record['leave_info'] = '|'.join(['-'.join([record.approval_type, record.start_time, record.end_time]) for record in leave_records])
            # 组装用户信息
            _record['deaprtname'] = self.org.dept_id_name_map.get(userobj.mult_department_id, u'老虎集团')
            _record['jobnumber'] = userobj.jobnumber
            _record['username'] = userobj.name
            # 组装考勤记录
            _record['record_date'] = record_date
            _record['clockin_time'] = attendence_record.clockin_time.split()[1] if attendence_record.clockin_time else approval_type_s
            _record['clockout_time'] = attendence_record.clockout_time.split()[1] if attendence_record.clockout_time else approval_type_e
            _record['worktime'] = attendence_record.worktime if attendence_record.worktime else ''
            # 组装出勤时间列表
            if not _record['leave_info'] and _record['worktime'] != '' and _record['worktime']:
                if not self.holiday.get(record_date):
                    worktime_list.append(float(_record['worktime']))
            ret.append(_record)
        # 计算平均出勤
        average_time = round(sum(worktime_list) / len(worktime_list), 1) if len(worktime_list) != 0 else 0
        self.average_worktime.update({userobj.jobnumber: average_time})
        # 根据打卡日期排序
        ret.sort(key=sort_key)
        # 过滤平均出勤时间小于10的
        if float(average_time) and float(average_time) < 10.0:
            self.person_worktime_len_ten.append(
                {
                    'name': userobj.name,
                    'jobnumber': userobj.jobnumber,
                    'deaprtname': self.org.dept_id_name_map.get(userobj.mult_department_id, u'老虎集团'),
                    'average_time': average_time
                }
            )
        return ret

    def base_report_data(self):
        """将所有用户的考勤信息，写入列表，用于生成全员的execl周报文件
           """
        all_records = []
        for dept, value in self.statistic_data.iteritems():
            for jobbumber, records in value.iteritems():
                for record in records:
                    all_records.append([record.get(k) for k in self.lables])
        all_records.insert(0, self.lables_CN)
        return all_records

    def base_depts_data(self, deptnames):
        """获取指定部门列表的考勤数据，并合并返回考勤数据
        用于生成execl 数据"""
        all_records = []
        for departname in deptnames:
            deptId = self.org.dept_name_id_map.get(departname)
            for jobnumber, records in self.statistic_data.get(deptId).iteritems():
                for record in records:
                    all_records.append([record.get(k) for k in self.lables])
        all_records.insert(0, self.lables_CN)
        return all_records

    def base_dept_data(self, deptname):
        """获取指定部门的考勤报表信息，用于html"""
        all_records = []
        deptId = self.org.dept_name_id_map.get(deptname)
        dept_record = self.statistic_data.get(deptId)
        for jobnumber, records in dept_record.iteritems():
            all_records += records
        logger.info('get %s weekly report data done', deptname)
        return all_records

    def base_dev_report_data(self):
        """汇总研发部门考勤记录数据，用于html， 已废弃"""
        all_records = []
        for deptId in self.org.default_develop_deptIds:
            dept_record = self.statistic_data.get(deptId)
            for jobnumber, records in dept_record.iteritems():
                all_records += records
        logger.info('get development weekly report data done')
        return all_records

    def dept_average_report_data(self):
        """各部门平均出勤时间数据"""
        all_records = []
        for deptId, value in self.statistic_data.iteritems():
            deptname = self.org.dept_id_name_map.get(deptId)
            dept_worktime = [self.average_worktime.get(jobnumber) for jobnumber in value if self.average_worktime.get(jobnumber, None)]
            dept_average_time = round(sum(dept_worktime)/len(dept_worktime), 1) if len(dept_worktime) > 0 else 0
            all_records.append({'deaprtname': deptname,
                                'average_time': dept_average_time})
        all_records.sort(key=lambda x: x['average_time'], reverse=True)
        logger.info('get dept average_time report data done')
        return all_records

    def person_report_data(self):
        """个人平均出勤时间统计排名；
        返回周平均出勤时间《 10 的人员考勤信息"""
        self.person_worktime_len_ten.sort(key=lambda x: x['average_time'])
        return self.person_worktime_len_ten

    def person_report_data_execl(self):
        """个人平均出勤时间统计排名；
        返回周平均出勤时间《 10 的人员考勤信息,用于写入execl"""
        lables = ['name', 'jobnumber', 'deaprtname', 'average_time']
        lables_CN = [u'姓名', u'工号', u'部门', u'周平均出勤']
        all_records = []
        uniq = []
        # 排序
        self.person_worktime_len_ten.sort(key=lambda x: x['average_time'])
        for record in self.person_worktime_len_ten:
            if record.get('jobnumber') not in uniq:
                all_records.append([record.get(k) for k in lables])
                uniq.append(record.get('jobnumber'))
        all_records.insert(0, lables_CN)
        return all_records

    def query_dept_report(self, deptname):
        """查询某个部门考勤"""
        all_records = []
        deptId = self.org.dept_name_id_map.get(deptname)
        dept_record = self.statistic_data.get(deptId)
        for jobnumber, records in dept_record.iteritems():
            for record in records:
                all_records.append([record.get(k) for k in self.lables])
        all_records.insert(0, self.lables_CN)
        return all_records


def test():
    for dept in Department.objects.all():
        if dept.department_id == '75411395':
            print dept.name, dept.department_id, dept.parentid
    print len(Department.objects.filter(department_id='12312312'))


def testOrg():
    org = OrgFromMysql()
    org.init_data_2()
    # print org.query_subdeptId([u'75411398'])
    #for k, v in org.parentId_subId_map.iteritems():
    #   print k, v
    for k, v in org.deptId_user_map.iteritems():
        print org.dept_id_name_map[k], k, len(v)
        #if k == u'75411398':
        #    for i in v:
        #        print i.name
    # print org.query_subdeptId(parentId=['75411395'])
    #for k, v in org.deptId_user_map.iteritems():
     #   print k, v


def testS():
    s = Statistics('2019-10-13', '2019-10-17')
    s.assembly_record()
    for item in s.query_dept_report(u'研发-运维'):
        print item[0], item[1], item[2]


def testS1():
    s = Statistics('2019-10-13', '2019-10-17')
    s.assembly_record()
    for dept, jobnumber in s.statistic_data.iteritems():
        for number, values in jobnumber.iteritems():
            print dept, number, values


def Atest():
    A = AttendenceFromMysql('2019-10-13', '2019-10-17')
    A.init_data()
    for jobnumber, record in A.attendence_info.iteritems():
        print jobnumber, len(record)


if __name__ == '__main__':
    testOrg()
    #test()
    #testS()
    #Atest()