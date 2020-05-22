# coding=utf-8
from django.conf import settings
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import jinja2
import logging
from statistics import Statistics
from execlclient import ExcelParse

"""
考勤周报，设定渲染邮件格式或者execl附件；
设定相应周报的发送人员
"""
logger = logging.getLogger('default')

DEFAULT_SMTP_HOST = getattr(settings, 'DEFAULT_SMTP_HOST', None)
DEFAULT_SMTP_PORT = getattr(settings, 'DEFAULT_SMTP_PORT', None)
DEFAULT_SMTP_USER = getattr(settings, 'DEFAULT_SMTP_USER', None)
DEFAULT_SMTP_PWSSD = getattr(settings, 'DEFAULT_SMTP_PWSSD', None)
DEFAULT_TMPL = getattr(settings, 'DEFAULT_TMPL', None)
DEFAULT_ORG_TMPL = getattr(settings, 'DEFAULT_ORG_TMPL', None)
HISTORY_REPORTER_DIR = getattr(settings, 'HISTORY_REPORTER_DIR', None)
DEFAULT_ORG = getattr(settings, 'DEFAULT_ORG', None)
DEFAULT_NOTIFY_TMPL = getattr(settings, 'DEFAULT_NOTIFY_TMPL', None)
DEFAULT_NOTIFY_RESULT_TMPL = getattr(settings, 'DEFAULT_NOTIFY_RESULT_TMPL', None)
DEFAULT_PERSON_TMPL = getattr(settings, 'DEFAULT_PERSON_TMPL', None)
DEFAULT_ORG_HRBP_MAP = getattr(settings, 'DEFAULT_ORG_HRBP_MAP', None)

class TigerSmtp(object):
    """smtp 邮件发送，自定义各种邮件发送格式"""
    def __init__(self):
        self.host = DEFAULT_SMTP_HOST
        self.port = DEFAULT_SMTP_PORT
        self.user = DEFAULT_SMTP_USER
        self.passwd = DEFAULT_SMTP_PWSSD
        self.smtp = smtplib.SMTP(self.host, self.port)
        self.smtp.starttls()
        self.smtp.ehlo()
        try:
            self.smtp.login(self.user, self.passwd)
        except smtplib.SMTPAuthenticationError as why:
            logger.error(why)

    def create_base_msg(self, rec, cc, subject, attachment_file, text):
        """
        发送带有文件/文本附言的邮件
        :param rec:
        :param cc:
        :param subject:
        :param attachment_file:
        :param text:
        :return:
        """
        msg = MIMEMultipart()
        msg['From'] = self.user
        msg['Subject'] = subject
        msg['To'] = ';'.join(rec)
        msg['CC'] = ';'.join(cc)
        msg.attach(MIMEText(text, 'plain', 'utf-8'))
        attachfile = MIMEApplication(open(attachment_file, 'rb').read())
        attachfile.add_header('Content-Disposition', 'attachment', filename=('utf-8', '', subject))
        msg.attach(attachfile)
        return msg

    def create_base_report_msg(self, rec, cc, subject, records, title, average_time):
        """
        默认的统计报告发送邮件模版
        :param rec:
        :param cc:
        :param subject:
        :param records: 考勤记录
        :param title: 邮件题目
        average_time 平均出勤时间
        days_num 总共统计的天数
        :return:
        """
        tmpl = jinja2.Template(DEFAULT_TMPL)
        cont = tmpl.render(records=records, title=title, average_time=average_time)
        msg = MIMEText(cont, _subtype='html', _charset='utf8')
        msg['From'] = self.user
        msg['Subject'] = subject
        msg['CC'] = ';'.join(cc)
        msg['To'] = ';'.join(rec)
        return msg

    def create_boss_report_msg(self, rec, cc, subject, title, records):
        """
        发送部门平均出勤时间邮件模版
        :param rec:
        :param cc:
        :param subject:
        :param records:
        :return:
        """
        tmpl = jinja2.Template(DEFAULT_ORG_TMPL)
        cont = tmpl.render(records=records, title=title)
        msg = MIMEText(cont, _subtype='html', _charset='utf8')
        msg['From'] = self.user
        msg['Subject'] = subject
        msg['CC'] = ';'.join(cc)
        msg['To'] = ';'.join(rec)
        return msg

    def create_boss_report_msg_2(self, rec, cc, subject, title, records):
        """
        发送个人平均出勤时间邮件模版
        :param rec:
        :param cc:
        :param subject:
        :param records:
        :return:
        """
        tmpl = jinja2.Template(DEFAULT_PERSON_TMPL)
        cont = tmpl.render(records=records, title=title)
        msg = MIMEText(cont, _subtype='html', _charset='utf8')
        msg['From'] = self.user
        msg['Subject'] = subject
        msg['CC'] = ';'.join(cc)
        msg['To'] = ';'.join(rec)
        return msg

    def create_notify_msg(self, rec, cc, subject, info):
        """未打卡通知邮件模版"""
        tmpl = jinja2.Template(DEFAULT_NOTIFY_TMPL)
        cont = tmpl.render(info=info, title=subject)
        msg = MIMEText(cont, _subtype='html', _charset='utf8')
        msg['From'] = self.user
        msg['Subject'] = subject
        msg['CC'] = ';'.join(cc)
        msg['To'] = ';'.join(rec)
        return msg

    def create_notify_result_msg(self, rec, cc, subject, infos):
        """未打卡通知邮件汇总模版"""
        tmpl = jinja2.Template(DEFAULT_NOTIFY_RESULT_TMPL)
        cont = tmpl.render(infos=infos, title=subject)
        msg = MIMEText(cont, _subtype='html', _charset='utf8')
        msg['From'] = self.user
        msg['Subject'] = subject
        msg['CC'] = ';'.join(cc)
        msg['To'] = ';'.join(rec)
        return msg

    def commit(self, msg, rec):
        """happy send """
        self.smtp.sendmail(self.user, rec, msg.as_string())

    def quit(self):
        self.smtp.quit()


class Reporter(object):
    """考勤统计报告，设定各种考勤周报的数据组织，及发送"""
    def __init__(self):
        super(Reporter, self).__init__()
        self.stat = None
        self.timerange = None
        self.execl = ExcelParse()
        self.sender = TigerSmtp()

    def get_data(self, stime, etime):
        """根据setting里面定义的二级部门获取数据"""
        logger.info('ready make Statistics from %s to %s', stime, etime)
        self.stat = Statistics(stime, etime)
        self.stat.assembly_record()
        self.timerange = self.stat.stime.replace('-', '') + '-' + self.stat.etime.replace('-', '')

    def get_data_2(self, stime, etime):
        """根据setting里面定义的一级部门获取数据"""
        logger.info('ready make Statistics from %s to %s', stime, etime)
        self.stat = Statistics(stime, etime)
        self.stat.assembly_record_2()
        self.timerange = self.stat.stime.replace('-', '') + '-' + self.stat.etime.replace('-', '')

    def base_weekly_report_to_hr(self):
        """考勤统计报告发送统计附件给hr,同时保存本地"""
        rec = ['']
        cc = ['', '', '']
        subject = self.timerange + '-考勤统计报告.xls'
        # 生成统计报表文件
        attachment_file = HISTORY_REPORTER_DIR + subject
        records = self.stat.base_report_data()
        average_time = self.stat.average_worktime
        days_num = self.stat.att.days_num
        self.execl.writeToMergeExecl(records, average_time, days_num)
        self.execl.save(attachment_file)
        # 发送邮件
        msg = self.sender.create_base_msg(rec, cc, subject, attachment_file, subject)
        self.sender.commit(msg, rec + cc)
        logger.info('send base_weekly_report_to_hr %s ok', ','.join(rec+cc))

    def base_dept_report_to_leaders(self):
        """ 各部门员工考勤周报数据，发给各部门负责人"""
        for deptname, recipients in DEFAULT_ORG.iteritems():
            rec = recipients['rec']
            cc = recipients['cc']
            subject = deptname + u'-考勤统计报告'
            title = self.timerange + u'-考勤统计'
            records = self.stat.base_dept_data(deptname)
            average_time = self.stat.average_worktime
            try:
                msg = self.sender.create_base_report_msg(rec, cc, subject, records, title, average_time)
                self.sender.commit(msg, rec+cc)
                logger.info('send %s weekly_report_to_leader %s ok', deptname, ','.join(rec + cc))
            except smtplib.SMTPException as why:
                logger.info('send %s weekly_report_to_leader %s fail', deptname, ','.join(rec + cc))
                logger.error(why)

    def base_dev_report_to_devleader(self):
        """研发部门考勤周报发送给研发部leader，已废弃"""
        rec = ['']
        cc = []
        title = subject = self.timerange + u'-研发部门考勤统计汇总'
        records = self.stat.base_dev_report_data()
        average_time = self.stat.average_worktime
        try:
            msg = self.sender.create_base_report_msg(rec, cc, subject, records, title, average_time)
            self.sender.commit(msg, rec + cc)
            logger.info('send development weekly_report_to_leader %s ok', ','.join(rec + cc))
        except smtplib.SMTPException as why:
            logger.info('send development weekly_report_to_leader %s fail', ','.join(rec + cc))
            logger.error(why)

    def weekly_reprot_to_hrbp(self):
        """将各一级部门的考勤数据 对应发送给hrbp,发送execl附件;
        仅限以一级部门初始化数据时候使用"""
        cc = []
        for iterms in DEFAULT_ORG_HRBP_MAP:
            allrecords = []
            departments = iterms.get('departments')
            hrbp = iterms.get('hrbp')
            rec = hrbp
            allrecords += self.stat.base_depts_data(departments)
            subject = self.timerange + '-' + '-'.join(departments) + u'-考勤周报汇总.xls'
            attachment_file = HISTORY_REPORTER_DIR + subject
            average_time = self.stat.average_worktime
            days_num = self.stat.att.days_num
            self.execl.writeToMergeExecl(allrecords, average_time, days_num)
            self.execl.save(attachment_file)
            try:
                msg = self.sender.create_base_msg(rec, cc, subject.encode('utf8'), attachment_file, subject)
                self.sender.commit(msg, rec + cc)
                logger.info('send %s weekly_report_to_hrbp %s ok', subject, ','.join(rec + cc))
            except smtplib.SMTPException as why:
                logger.info('send %s weekly_report_to_hrbp %s fail', subject, ','.join(rec + cc))
                logger.error(why)

    def base_reprot_to_boss(self):
        """各部门周平均工时数（排序）"""
        rec = ['m']
        cc = ['', '']
        title = subject = self.timerange + u'-部门平均出勤时间统计报告'
        records = self.stat.dept_average_report_data()
        try:
            msg = self.sender.create_boss_report_msg(rec, cc, subject, title, records)
            self.sender.commit(msg, rec + cc)
            logger.info('send weekly_report_to_boss %s ok', ','.join(rec + cc))
        except smtplib.SMTPException as why:
            logger.info('send weekly_report_to_boss %s fail', ','.join(rec + cc))
            logger.error(why)

    def base_reprot_to_boss_2(self):
        """周平均工时不满10小时的员工（排序）"""
        rec = ['']
        cc = ['']

        title = subject = self.timerange + u'-个人平均出勤时间统计报告(<10)'
        records = self.stat.person_report_data()
        try:
            msg = self.sender.create_boss_report_msg_2(rec, cc, subject, title, records)
            self.sender.commit(msg, rec + cc)
            logger.info('send weekly_report_to_boss_2 %s ok', ','.join(rec + cc))
        except smtplib.SMTPException as why:
            logger.info('send weekly_report_to_boss_2 %s fail', ','.join(rec + cc))
            logger.error(why)

    def base_reprot_to_boss_2_execl(self):
        """周平均工时不满10小时的员工（排"""
        rec = ['']
        cc = ['']

        title = subject = self.timerange + u'-个人平均出勤时间统计报告.xls'
        records = self.stat.person_report_data_execl()
        attachment_file = HISTORY_REPORTER_DIR + subject
        self.execl.write_execl(records)
        self.execl.save(attachment_file)
        try:
            msg = self.sender.create_base_msg(rec, cc, subject.encode('utf8'), attachment_file, title)
            self.sender.commit(msg, rec + cc)
            logger.info('send weekly_report_to_hr_2 %s ok', ','.join(rec + cc))
        except smtplib.SMTPException as why:
            logger.info('send weekly_report_to_hr_2 %s fail', ','.join(rec + cc))
            logger.error(why)

    def base_report_to(self, deptname):
        """指定发送单个部门考勤报告，一般用于测试"""
        rec = ['']
        cc = []
        deptname = unicode(deptname, 'utf-8')
        subject = u'%s-考勤统计报告' % deptname
        title = u'%s-考勤统计' % self.timerange
        records = self.stat.base_dept_data(deptname)
        average_time = self.stat.average_worktime
        try:
            msg = self.sender.create_base_report_msg(rec, cc, subject, records, title, average_time)
            self.sender.commit(msg, rec + cc)
            logger.info('send %s weekly_report_to_leader %s ok', deptname, ','.join(rec + cc))
        except smtplib.SMTPException as why:
            logger.info('send %s weekly_report_to_leader %s fail', deptname, ','.join(rec + cc))
            logger.error(why)

