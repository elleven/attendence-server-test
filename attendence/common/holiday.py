# coding=utf-8
import calendar
import datetime
import requests
import time


def to_timestamp(timestr):
    """时间转时间戳"""
    if timestr:
        format_str = "%Y-%m-%d %H:%M:%S" if len(timestr.split(':')) == 3 else "%Y-%m-%d %H:%M"
        timeArray = time.strptime(timestr, format_str)
        return int(time.mktime(timeArray))


def to_timestr(timestamp):
    """时间戳转时间"""
    if timestamp:
        timeArray = time.localtime(timestamp)
        return time.strftime("%Y-%m-%d %H:%M:%S", timeArray)


class Schedule(object):
    """节假日信息及相关时间判定功能"""
    def __init__(self):
        self.c = calendar.Calendar()
        self._schedule = {}

    def get_holiday(self, day):
        """从开源接口获取节假日信息，
           判定是否节假日信息{u'wage': 3, u'date': u'2020-01-01', u'holiday': True, u'name': u'\u5143\u65e6'}
           """
        holiday_api = 'http://timor.tech/api/holiday/info/'
        r = requests.get(holiday_api+day)
        holiday = r.json().get('holiday')
        if not holiday:
            if r.json().get('type')['type'] == 1:
                holiday = {'holiday': True,
                           'name': u'休息日'}
            return holiday
        return holiday

    def iter_yeardays(self, year):
        """迭代某一年的所有日期"""
        for month in range(1, 13):
            for day in self.iter_mothdays(year, month):
                yield day

    def iter_mothdays(self, year, month):
        """迭代某一年某一月的所有日期"""
        for day in self.c.itermonthdates(year, month):
            if month == int(day.strftime('%m')):
                yield day.strftime('%Y-%m-%d')

    @staticmethod
    def iter_diffdays(start, end):
        """迭代给定起始日期的所有日期
        start = '2019-06-01'
        end = '2019-08-04'
        暂时返回所有，后续改为只返回工作日"""
        datestart = datetime.datetime.strptime(start, '%Y-%m-%d')
        dateend = datetime.datetime.strptime(end, '%Y-%m-%d')
        while datestart <= dateend:
            yield datestart.strftime('%Y-%m-%d')
            datestart += datetime.timedelta(days=1)

    def get_weekday(self, date):
        """根据提供日期判定星期几"""
        year, month, day = date.split('-')
        return calendar.weekday(int(year), int(month), int(day))

    def get_lastweek(self, date):
        """给定日期返回上周日期的起始时间"""
        weekday_now = self.get_weekday(date)
        lastweek_start = datetime.datetime.strptime(date, '%Y-%m-%d') + datetime.timedelta(-(7 + weekday_now))
        lastweek_end = datetime.datetime.strptime(date, '%Y-%m-%d') + datetime.timedelta(-(weekday_now + 1))
        return lastweek_start.strftime('%Y-%m-%d'), lastweek_end.strftime('%Y-%m-%d')

    @staticmethod
    def get_yesterday():
        yesterday = datetime.date.today() + datetime.timedelta(-1)
        return yesterday

    def check_time_in_range(self, day, stime, etime):
        """给定指定日期，判断日期是否在范围之内
            date='2019-10-01
            stime=2019-10-01
            etime=2019-10-02'
            """
        datetimestamp = int(time.mktime(time.strptime(day, "%Y-%m-%d")))
        stimestamp = int(time.mktime(time.strptime(stime, "%Y-%m-%d")))
        etimestamp = int(time.mktime(time.strptime(etime, "%Y-%m-%d")))
        if etimestamp >= datetimestamp >= stimestamp:
            return True
        return False

    def get_lastday(self, year, month):
        """返回给定年月的最后一天lastday"""
        firstDayWeekDay, monthRange = calendar.monthrange(year, month)
        lastDay = datetime.datetime(year=year, month=month, day=monthRange)
        return lastDay

    def get_firstday(self, year, month):
        """返回给定年月的第一天firstday"""
        firstDay = datetime.datetime(year=year, month=month, day=1)
        return firstDay

    def get_days(self, year, month):
        """给定年月份 返回天数"""
        firstDayWeekDay, monthRange = calendar.monthrange(year, month)
        return int(monthRange)

    def count_diff_day(self, stime, etime, month):
        """给出起止时间，月份，计算当前月份内相差天数
        stime : 2019-10-11 上午
        etime : 2019-10-12 下午
        return  2 (day)"""
        stime_interval = etime_interval = None
        if len(stime.split()) == 2:
            stime_day, stime_interval = stime.split()
            etime_day, etime_interval = etime.split()
        else:
            stime_day = stime.split()[0]
            etime_day = etime.split()[0]
        s_y, s_m, s_d = stime_day.split('-')
        e_y, e_m, e_d = etime_day.split('-')
        n_y = time.strftime("%Y")
        if int(s_m) == int(e_m) == int(month):
            # 起止时间都在给定月份
            diff_days = (datetime.datetime(int(e_y), int(e_m), int(e_d)) - datetime.datetime(int(s_y), int(s_m), int(s_d))).days + 1
            if stime_interval and stime_interval == u'下午':
                diff_days = diff_days - 0.5
            if etime_interval and etime_interval == u'上午':
                diff_days = diff_days - 0.5
            return diff_days
        if int(s_m) == int(month) and int(e_m) != int(month):
            # 开始时间在指定月份，结束时间不在指定月份
            diff_days = (self.get_lastday(int(s_y), int(month)) - datetime.datetime(int(s_y), int(s_m), int(s_d))).days + 1
            if stime_interval and stime_interval == u'下午':
                diff_days = diff_days - 0.5
            return diff_days
        if int(e_m) == int(month) and int(s_m) != int(month):
            # 结束时间在指定月份，开始时间不在指定月份
            diff_days = (datetime.datetime(int(e_y), int(e_m), int(e_d)) - self.get_firstday(int(e_y), int(month))).days + 1
            if etime_interval and etime_interval == u'上午':
                diff_days = diff_days - 0.5
            return diff_days
        # 其他情况统计月份包含在开始结束️时间内的
        diff_days = self.get_days(int(n_y), int(month))
        return diff_days

    def check_clockin(self, clockin_time):
        """检测签到打卡时间是否超过了 11:30; 超过则返回true；其他返回false"""
        day = clockin_time.split()[0]
        clockin_time_standline = "%s 11:30:00" % day
        clock_time_timestamp = to_timestamp(clockin_time)
        clockin_time_standline_timestamp = to_timestamp(clockin_time_standline)
        if clock_time_timestamp > clockin_time_standline_timestamp:
            return True
        return False


def test():
    s = Schedule()
    for date in s.iter_mothdays(2019, 2):
        print date


def test2():
    s = Schedule()
    for date in s.iter_yeardays(2019):
        print date


def test3():
    s = Schedule()
    for date in s.iter_diffdays('2019-08-04', '2019-08-04'):
        print date
    print Schedule.get_yesterday()


def test4():
    s = Schedule()
    weekday = s.get_weekday(datetime.date.today().strftime('%Y-%m-%d'))
    lastweek_start = datetime.date.today() + datetime.timedelta(-(7+weekday))
    lastweek_end = datetime.date.today() + datetime.timedelta(-(weekday+1))
    print lastweek_start, lastweek_end, s.get_lastweek(datetime.date.today().strftime('%Y-%m-%d'))


def test5():
    s = Schedule()
    print s.get_holiday('2020-01-14')
    #print s.count_diff_day('2019-11-05', '2020-01-23')
    # print s.get_weekday('2019-10-26')


def test6():
    print to_timestr(1463392235000/1000)


def test7():
    s = Schedule()
    weekday = s.get_weekday(datetime.date.today().strftime('%Y-%m-%d'))
    print weekday


if __name__ == "__main__":
    test7()