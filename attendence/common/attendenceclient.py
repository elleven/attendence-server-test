# coding=utf-8
# attendace-client

'''
考勤数据读取并处理；
包含 考勤设备数据读取处理；
     钉钉考勤数据读取处理；
'''

import sys
import logging
import time
import datetime
from django.conf import settings
from holiday import Schedule
from ddtalkclient import DDTalkClient

logger = logging.getLogger('default')
try:
    import win32com.client
except ImportError as why:
    logger.warn('%s  only on win7 ', why)


A_MACHINES = getattr(settings, 'A_MACHINES', None)


def user_name_to_gbk(username):
    return str(username.split(u'\x00')[0].encode('utf-8'))


def to_timestamp(timestr):
    """时间转时间戳"""
    if timestr:
        timeArray = time.strptime(timestr, "%Y-%m-%d %H:%M:%S")
        return int(time.mktime(timeArray))


def to_timestr(timestamp):
    """时间戳转时间"""
    if timestamp:
        timeArray = time.localtime(timestamp)
        return time.strftime("%Y-%m-%d %H:%M:%S", timeArray)


class AttendanceClient(object):
    """
    封装考勤设备SDK接口，用于下载考勤数据；
    通过pywin32 调用SDK接口；仅限win下生效；
    考勤设备：位于北京办公室
    AttendenceInfo:
    { userid1: ["2019-04-02 09:10:59",...],
      userid2: [".."] }

    UserInfo:
    {
    userId1:username1,
    userId2:username2,
    ...
    }

    """
    RegisterName = 'zkemkeeper.ZKEM.1'

    def __init__(self, machineIp, machineId=1, port=4370, stime=None, etime=None):
        self.Client = win32com.client.Dispatch(AttendanceClient.RegisterName)
        self.MachineId = machineId
        self.Port = port
        self.MachineIp = machineIp
        self.stime = stime
        self.etime = etime
        self._AttendenceInfo = {}
        self._UserInfo = {}
        if self.Client.Connect_net(self.MachineIp, self.Port):
            logger.info('connect to %s successed', self.MachineIp)
            self.InitData()
        else:
            logger.info('connect to %s failed', self.MachineIp)

    def InitData(self):
        """
        如果给定了时间范围，将会下载时间范围内考勤数据；否则下载全部
        :return:
        """
        if self.stime and self.etime:
            self.LoadTimeAttendance(self.stime, self.etime)
        else:
            # load ALL
            self.LoadAllAttendance()
        # load user info
        # self.LoadUserInfo()

    def LoadAllAttendance(self):
        """
        下载全部考勤记录，保存至self._AttendenceInfo
        :return:
        """
        if self.Client.ReadAllGLogData(1):
            while True:
                result, UserId, VerifyMode, InOutMode, Year, Month, Day, Hour, Minute, Second, WorkCode  \
                                           = self.Client.SSR_GetGeneralLogData(self.MachineId)
                if not result:
                    break
                attendenceTime = '%s-%s-%s %s:%s:%s' % (Year, Month, Day, Hour, Minute, Second)
                UserId = int(UserId)
                if self._AttendenceInfo.has_key(UserId):
                    self._AttendenceInfo[UserId].append(attendenceTime)
                else:
                    self._AttendenceInfo[UserId] = [attendenceTime]
            logger.info('load %s attendance data to local cache sucessfully', self.MachineIp)
        else:
            logger.error('load %s attendance failed', self.MachineIp)

    def LoadUserInfo(self):
        """
        读取用户信息,userid:username
        :return:
        """
        if self.Client.ReadAllUserId(self.MachineId):
            while True:
                result, userId, userName, pwd, privilege, state = self.Client.SSR_GetAllUserInfo(self.MachineId)
                if not result:
                    break
                elif state:
                    userId = int(userId)
                    self._UserInfo[userId] = user_name_to_gbk(userName)
            logger.info('load %s userinfo successfully', self.MachineIp)
        else:
            logger.error('load %s userinfo failed', self.MachineIp)

    def LoadTimeAttendance(self, stime, etime):
        """
        下载指定时间范围内考勤记录，保存到self._AttendenceInfo
        :param stime: 2019-04-02 00:00:00
        :param etime: 2019-04-02 23:59:59
        :return:
        """
        if self.Client.ReadTimeGLogData(self.MachineId,stime,etime):
            while True:
                result, UserId, VerifyMode, InOutMode, Year, Month, Day, Hour, Minute, Second, WorkCode  \
                                            = self.Client.SSR_GetGeneralLogData(self.MachineId)
                if not result:
                    break
                attendenceTime = '%s-%s-%s %s:%s:%s' % (Year, Month, Day, Hour, Minute, Second)
                UserId = int(UserId)
                if self._AttendenceInfo.has_key(UserId):
                    self._AttendenceInfo[UserId].append(attendenceTime)
                else:
                    self._AttendenceInfo[UserId] = [attendenceTime]
            logger.info('load %s %s - %s attendenceinfo successfully', self.MachineIp, stime, etime)
        else:
            logger.error('load %s %s -%s attendenceinfo failed', self.MachineIp, stime, etime)

    @property
    def AttendenceInfo(self):
        return self._AttendenceInfo


class ParseProcess(object):
    """
    合并处理多个考勤设备的数据，统一考勤数据格式
    attendenceinfo :
    {
     attendance_id:{
          2019-04-02:["2019-04-02 09:10:58",...],
          2019-04-03: [ ...],
       ...
      }
   """

    def __init__(self, stime=None, etime=None):
        self.stime = stime
        self.etime = etime
        self._process_record = None
        self.srcData = [AttendanceClient(machine, stime=stime, etime=etime) for machine in A_MACHINES]

    def process_rule(self):
        """ 格式化考勤数据，不做考勤规则处理"""
        if self._process_record is not None:
            return self._process_record
        ret = {}
        # 合并多个数据源
        for attence_obj in self.srcData:
            for key, value in attence_obj.AttendenceInfo.iteritems():
                if key in ret:
                    ret[key] += value
                else:
                    ret[key] = value
        # 格式化数据源
        for key, value in ret.iteritems():
            ret[key] = self._parseRecord(value)
        logger.info('collect data done')
        self._process_record = ret
        return ret

    def _parseRecord(self, record):
        """按照日期归纳考勤记录
           新增隔天签退打卡支持，需要把符合签退范围的隔天打卡记录也归纳
           PM = ("14:00:00", "04:39:59")
           :param: record
          ['2019-04-02 09:10:58',...]

          return {
                  2019-04-02:["2019-04-02 09:10:58",...],
                  2019-04-03:[ ...],
                  ...
                  }

        """
        def clockout_check(clocktime):
            """新增隔天签退打卡支持，需要把符合签退范围的隔天打卡记录也归纳
               检查签退时间是否符合设定的签退范围，如果符合return yester_d or None；"""
            day, hour = clocktime.split()
            day_struct = datetime.datetime.strptime(day, "%Y-%m-%d")
            now_d = day_struct.strftime('%Y-%m-%d')
            yester_d = (day_struct + datetime.timedelta(days=-1)).strftime('%Y-%m-%d')

            clockout_rule_start = "%s 04:40:00" % yester_d
            clockout_rule_end = "%s 04:39:59" % now_d

            if to_timestamp(clockout_rule_start) < to_timestamp(clocktime) <= to_timestamp(clockout_rule_end):
                return yester_d
            else:
                return now_d

        ret = {}
        for clocktime in record:
            # key, value = clocktime.split()
            # day_struct = datetime.datetime.strptime(key, "%Y-%m-%d")
            # day = day_struct.strftime('%Y-%m-%d')
            day = clockout_check(clocktime)

            if day in ret:
                ret[day].append(clocktime)
            else:
                ret[day] = [clocktime]

        return ret


class ParseProcessFromDD(object):
    """用于钉钉考勤数据源的考勤数据处理
     attendenceinfo :
    {
     userid:{
          2019-04-02:["2019-04-02 09:10:58",...],
          2019-04-03: [ ...],
       ...
      }"""

    def __init__(self, stime, etime, userid_list):
        """format time :2018-05-01 00:00:00
            """
        self.d = DDTalkClient()
        self.stime = stime
        self.etime = etime
        self.userid_list = userid_list
        if len(self.userid_list) > 50:
            logger.warn('userid_list不能超过50个')
        self.srcData = self.loaddata()
        self._process_record = None

    def loaddata(self):
        return self.d.get_attendance(self.stime, self.etime, self.userid_list)

    def process_rule(self):
        """格式化考勤数据"""
        if self._process_record is not None:
            return self._process_record
        ret = {}
        # 此处以userid 归纳
        for record in self.srcData:
            userid = record['userId']
            if userid in ret:
                # 此处判定打卡是否符合考勤规定，在范围外或其他无效打卡，不计入有效考勤
                if record['locationResult'] == 'Normal':
                    # 时间戳ms 转换成时间str
                    clocktime = to_timestr(record['userCheckTime']/1000)
                    ret[userid].append(clocktime)
            else:
                if record['locationResult'] == 'Normal':
                    clocktime = to_timestr(record['userCheckTime'] / 1000)
                    ret[userid] = [clocktime]
        # 格式化数据
        for key, value in ret.iteritems():
            ret[key] = self._parse_record(value)
        logger.info('collect data done')
        self._process_record = ret
        return ret

    def _parse_record(self, record):
        """按照日期归纳考勤记录
          return {
                  2019-04-02:["2019-04-02 09:10:58",...],
                  2019-04-03:[ ...],
                  ...
                  }"""
        ret = {}
        for item in record:
            key, value = item.split()
            time_struct = time.strptime(key, "%Y-%m-%d")
            key = time.strftime("%Y-%m-%d", time_struct)
            # key = ''.join(key.split('-'))
            if key in ret:
                ret[key].append(item)
            else:
                ret[key] = [item]
        return ret


class BaseRuleMixin(object):
    """
    考勤数据基本规则处理, 根据规定的的签到、签退时间范围
    处理打卡数据，标记签到、签退时间并计算出勤时间;

    {
     userid1:{
          2019-04-02:("2019-04-02 09:10:58", "2019-04-02 20:30:58"， 12.2 ),
          2019-04-03:(),
       ...
      }

    """

    def process_rule(self):
        """ 根据规定的签到、签退时间范围判定签到、签退时间"""
        ret = {}
        _process_base_record = super(BaseRuleMixin, self).process_rule()
        for jobnumber, records in _process_base_record.iteritems():
            ret[jobnumber] = {day: self.rules(day, record_info) for day, record_info in records.iteritems()}
        logger.info('parse base rule done')
        return ret

    def rules(self, date, records):
        """考勤规则 设定签到、签退打卡范围, 计算出勤时间
           支持隔天签退打卡的统计
        parmas:
           records: timestamp
        AM = ("04:40:00", "13:59:59")
        PM = ("14:00:00", "04:39:59")
        return ( clockin, clockout, worktime)

        """
        clockout = clockin = worktime = None

        # 打卡规则设定
        day_struct = datetime.datetime.strptime(date, "%Y-%m-%d")
        tomorrow_d = (day_struct + datetime.timedelta(days=1)).strftime('%Y-%m-%d')

        clockin_rule_start = "%s 04:40:00" % date
        clockin_rule_end = "%s 14:59:59" % date
        clockout_rule_start = "%s 15:00:00" % date
        clockout_rule_end = "%s 04:39:59" % tomorrow_d
        # 打卡时间戳排序
        timestamp_records = map(to_timestamp, records)
        timestamp_records.sort()
        # 判定签退时间
        for item in timestamp_records:
            if to_timestamp(clockout_rule_end) >= item >= to_timestamp(clockout_rule_start):
                clockout = item
        # 判定签到时间
        timestamp_records.reverse()
        for item in timestamp_records:
            if to_timestamp(clockin_rule_end) >= item >= to_timestamp(clockin_rule_start):
                clockin = item

        # 计算出勤时间
        if clockout and clockin:
            clock_start = datetime.datetime.utcfromtimestamp(clockin)
            clock_end = datetime.datetime.utcfromtimestamp(clockout)

            worktime = round((clock_end - clock_start).total_seconds()/3600, 1)

        return to_timestr(clockin), to_timestr(clockout), worktime


class ScheduleRuleMixin(object):
    """排班规则，给定的工作日期内 关联打卡记录;
    此混合类无效，不使用，废弃"""

    def process_rule(self):
        ret = {}
        if self.stime is None or self.etime is None:
            return super(ScheduleRuleMixin, self).process_rule()
        _process_schedule_record = super(ScheduleRuleMixin, self).process_rule()
        sdate = self.stime.split()[0]
        edate = self.etime.split()[0]
        s = Schedule()
        for jobnumber, records in _process_schedule_record.iteritems():
            ret[jobnumber] = {workday: records.get(workday, (None, None, None)) for workday in s.iter_diffdays(sdate, edate)}
        logger.info('parse schedule rule done')
        return ret


class Attendance(BaseRuleMixin, ParseProcess):
    """
    考勤设备数据格式化处理，考勤基本规则处理类；
    """
    def attendanceinfo(self):
        return self.process_rule()


class AttendanceFromDD(BaseRuleMixin, ParseProcessFromDD):
    """钉钉考勤数据处理，考勤基本规则处理；"""
    def attendanceinfo(self):
        return self.process_rule()


def maintest():
    logger = logging.getLogger()
    formatter = logging.Formatter('%(asctime)s %(levelname)-8s: %(message)s')
    console_handle = logging.StreamHandler(sys.stdout)
    console_handle.formatter = formatter
    logger.addHandler(console_handle)
    logger.setLevel(logging.INFO)
    src1 = AttendanceClient('172.25.0.26', stime='2019-04-02 00:00:00', etime='2019-04-02 23:59:59')
    src2 = AttendanceClient('172.25.0.27', stime='2019-04-02 00:00:00', etime='2019-04-02 23:59:59')
    # srcData = [src1, src2]
    # parse1 = ParseProcess(srcData)
    # A = Attendance(srcData=srcData)
    # print A.attendanceinfo()


if __name__ == '__main__':
    # maintest()
    pass
