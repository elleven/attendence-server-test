#!/usr/bin/python
# -*- coding=utf-8 -*-
#import django
#import os
#os.environ.setdefault("DJANGO_SETTINGS_MODULE", "attendence_server.settings")
#django.setup()
import requests
import time
from django.conf import settings
import sys
import logging
# from attendence.models import ApprovalRecord
import json
from wraps import retry_decorator

logger = logging.getLogger('default')

DD_APP_KEY = getattr(settings, 'DD_APP_KEY', None)
DD_APP_SECRET = getattr(settings, 'DD_APP_SECRET', None)
DD_TOKEN_EXPIRE = getattr(settings, 'DD_TOKEN_EXPIRE', 3600)


class DDTalkClient(object):

    """封装钉钉开放平台基本接口"""
    def __init__(self):
        self.access_token = {}
        self.get_accesstoken()

    def get_accesstoken(self):
        """获取access_token，加上时间戳，判断是否过期，用于防止token过期"""
        uri = 'https://oapi.dingtalk.com/gettoken'
        params = {'appkey': DD_APP_KEY,
                  'appsecret': DD_APP_SECRET}
        r = requests.get(url=uri, params=params)
        if r.status_code == requests.codes.ok:
            ret = {'token': r.json()['access_token'],
                   'timestamps': int(time.time())}
            self.access_token.update(ret)
            logger.info('sync token')

    @retry_decorator(retry=3)
    def request(self, uri, params, method):
        """请求默认会重试三次，避免因超时导致数据获取失败"""
        ret = None
        logger.info('trying request: %s method: %s params: %s', uri, method, params)
        if 'timestamps' not in self.access_token or int(time.time()) - self.access_token.get('timestamps') > DD_TOKEN_EXPIRE:
            logger.warn('token is expired')
            self.get_accesstoken()
        if method == 'GET':
            params.setdefault('access_token', self.access_token['token'])
            r = requests.get(url=uri, params=params)
            if r.status_code == requests.codes.ok:
                logger.info('errmsg: %s', r.json().get('errmsg'))
                ret = r.json()
        elif method == 'POST':
            r = requests.post(url=uri, data=params, params={'access_token': self.access_token['token']})
            if r.status_code == requests.codes.ok:
                logger.info('errmsg: %s', r.json().get('errmsg'))
                ret = r.json()
        if ret is None:
            raise AttributeError
        return ret

    def get_child_dept(self, parentId=1):
        """
        根据父级部门id 获取子部门ID列表
        :param parentId:
        :return:
        """
        uri = 'https://oapi.dingtalk.com/department/list_ids'
        params = {'id': parentId}
        method = "GET"
        ret = self.request(uri, params, method).get('sub_dept_id_list')
        return ret

    def get_dept_lists(self, parentId=1, fetch_child=True):
        """
        根据父部门id获取 所有部门信息
        :param parentId:
        :param fetch_child:
        :return:
        """
        uri = "https://oapi.dingtalk.com/department/list"
        params = {'id': parentId,
                  'fetch_child': fetch_child}
        method = "GET"
        ret = self.request(uri, params, method).get('department')
        return ret

    def get_dept_info(self, deptId):
        """
        根据部门id获取部门详情
        :param deptId:
        :return:
        """
        uri = "https://oapi.dingtalk.com/department/get"
        params = {'id': deptId}
        method = "GET"
        ret = self.request(uri, params, method)
        return ret

    def get_parentid(self, deptId):
        """根据部门id 查找父部门id"""
        return self.get_dept_info(deptId=deptId)['parentid']

    def iscontain_subdept(self, deptId):
        """
        判断是否包含子部门
        :param deptId:
        :return: true or false
        """
        return self.get_dept_info(deptId)['groupContainSubDept']

    def get_dept_userids(self, deptId):
        """
        根据部门ID 获取部门内的userid列表
        :param deptId:
        :return:
        """
        uri = "https://oapi.dingtalk.com/user/getDeptMember"
        params = {'deptId': deptId}
        method = "GET"
        ret = self.request(uri, params, method).get('userIds')
        return ret

    def get_dept_userinfo(self, deptId):
        """
        根据部门id获取部门用户详情
        :param deptId:
        :return:
        """
        uri = "https://oapi.dingtalk.com/user/listbypage"
        method = "GET"
        ret = []
        offset = 0
        while True:
            params = {'department_id': deptId,
                      'size': 100,
                      'offset': offset}
            r = self.request(uri, params, method)
            ret += r.get('userlist', None)
            offset += 1
            if not r.get('hasMore', False):
                break
        return ret

    def get_userinfo(self, userId):
        """
        根据userid获取用户详情
        :param userId:
        :return:
        """
        uri = "https://oapi.dingtalk.com/user/get"
        params = {'userid': userId}
        method = "GET"
        ret = self.request(uri, params, method)
        return ret

    def get_process_ids(self, process_code, start_time, end_time=None, size=20):
        """
        根据条件查询审批实例列表
        :param process_code:
        :param start_time:   millis_timestamp  13 位
        :param end_time:
        :param size:
        :return: [
                "85bf4b7c-fc71-4489-aaab-65428d6e2176",
                "4dbc813f-c90b-4938-88ae-2786ee9a9cda"
               ]
        """
        uri = "https://oapi.dingtalk.com/topapi/processinstance/listids"
        method = "POST"
        ret = []
        next_cursor = 0
        while True:
            params = {'process_code': process_code,
                      'start_time': start_time,
                      'end_time': end_time,
                      'size': size,
                      'cursor': next_cursor}
            r = self.request(uri, params, method).get('result')
            ret += r.get('list')
            next_cursor = r.get('next_cursor', None)
            if not next_cursor:
                break

        return ret

    def get_processinfo(self, process_instance_id):
        """根据审批实例ID获取审批实例的详情"""
        uri = "https://oapi.dingtalk.com/topapi/processinstance/get"
        method = "POST"
        params = {'process_instance_id': process_instance_id}
        ret = self.request(uri, params, method).get('process_instance')
        return ret

    def get_attendance(self, datefrom, dateto, userid_list):
        """ 根据提供的日期范围以及用户ID 查询下载考勤数据
        起始与结束工作日最多相隔7天
        userid_list不能超过50个"""
        uri = "https://oapi.dingtalk.com/attendance/list"
        method = "POST"
        headers = {'content-type': 'application/json'}
        offset = 0
        ret = []
        while True:
            params = json.dumps({
                'workDateFrom': datefrom,
                'workDateTo': dateto,
                'userIdList': userid_list,
                'offset': offset,
                'limit': 50,
            })
            r = self.request(uri, params, method,)
            ret += r.get('recordresult', None)
            offset += 1
            if not r.get('hasMore', False):
                break
        return ret


class Organization(object):
    """从钉钉获取组织结构信息，用于同步组织结构信息至数据库;
    同时也可直接提供组织架构相关查询入口
      """
    def __init__(self):
        self.d = DDTalkClient()
        self._deptinfo = {}
        self._userinfo = {}

    def init_departinfo(self):
        """初始化部门信息，返回所有部门名称及对应的部门ID，包括所有层级部门"""
        logger.info('load depart info from ddtalk')
        deptdict = {}
        deptlist = self.d.get_dept_lists(parentId=1, fetch_child=True)
        for dept in deptlist:
            deptdict.setdefault(dept['id'], dept)

        # 递归处理部门名称
        def process(item):
            if item['parentid'] == 1:
                return item['name']
            else:
                parentid = item['parentid']
                parentitem = deptdict[parentid]
                name = "%s-%s" % (process(parentitem), item['name'])
                return name

        for deptid, value in deptdict.iteritems():
            deprtname = process(value)
            self._deptinfo.setdefault(deprtname, deptid)

    def init_userinfo(self):
        """初始化公司员工信息"""
        logger.info('load user info from ddtalk')
        for deptid in self._deptinfo.itervalues():
            users = self.d.get_dept_userinfo(deptId=deptid)
            if len(users) > 0:
                for user in users:
                    if 'jobnumber' in user:
                        jobnumber = user['jobnumber']
                        if jobnumber not in self.userinfo:
                            self._userinfo.setdefault(jobnumber, user)

    def userinfo_acl(self, userinfo, workplace):
        """
        过滤处理符合策略的的userinfo
        :param userinfo:
        :return: True or Fasle
        """
        # rules1 workPlace 北京
        if userinfo.get('workPlace', None) != workplace:
            return False
        # is not boss
        if userinfo.get('isBoss', None):
            return False
        # is active
        if not userinfo.get('active', None):
            return False
        # is hide
        if userinfo.get('isHide', None):
            return False
        # department belont to 1
        if 1 in userinfo.get('department', []):
            return False
        return True

    def get_bj_userinfo(self):
        """获取北京办公室员工"""
        workspace = u'北京'
        return {jobnumber: user for jobnumber, user in self._userinfo.iteritems() if self.userinfo_acl(user, workspace)}\

    @property
    def deptinfo(self):
        return self._deptinfo

    @property
    def userinfo(self):
        return self._userinfo


class Approval(object):
    """从钉钉初始化四类请假类型的审批信息，用于同步至数据库，
      也可直接对外提供相关查询；
    self._approval_info
    { userid : [
    { leaveinfo } ,
      ] ,
      ..} """

    def __init__(self, start_time, end_time=None):
        self.d = DDTalkClient()
        self.process_codes = {u'补打卡': '',
                              u'公出': '',
                              u'出差': '',
                              u'请假': ''
                              }
        self.start_time = start_time
        self.end_time = end_time
        self.approval_instances = []
        # 被修改的实例标记为modify
        self.instance_modify = []
        # 被撤销的实例标记为revoke
        self.instance_revoke = []
        self._approval_info = []
        # approval = ApprovalRecord._meta.fields
        # self._format_fields = [approval[i].name for i in range(len(approval))][0:-2]
        self._format_fields = ['instance_id', 'approval_type', 'status', 'result', 'originator_userid', 'originator_dept_id',
                               'approval_reason', 'aproval_desc', 'start_time', 'end_time']

    def init_approval(self):
        """初始化审批数据"""
        logger.info('start process data')
        for approval_record in self.approval_instances:
            self.process(approval_record)
        logger.info('process data done')

    def process(self, data):
        """处理数据"""
        try:
            if data['approval_type'] == u'补打卡':
                self.process_budaka(data)
            if data['approval_type'] == u'公出':
                self.process_gongchu(data)
            if data['approval_type'] == u'出差':
                self.process_chuchai(data)
            if data['approval_type'] == u'请假':
                self.process_qingjia(data)
        except Exception as why:
            logger.error(why)
            logger.warn(data)

    def process_budaka(self, data):
        """处理未打卡数据，返回统一格式，未打卡审批模版改动需要同步改动此处"""
        ret = {fields: data.get(fields, None) for fields in self._format_fields}
        for form_component_value in data.get('form_component_values'):
            if 'name' in form_component_value:
                if form_component_value[u'name'] == u'缺卡原因':
                    ret['approval_reason'] = form_component_value[u'value']
                if form_component_value[u'name'] == u'说明':
                    ret['aproval_desc'] = form_component_value[u'value']
                if form_component_value[u'name'] == u'日期':
                    ret['end_time'] = ret['start_time'] = form_component_value[u'value']
        self._approval_info.append(ret)

    def process_gongchu(self, data):
        """处理公出申请数据，返回统一格式，公出申请模版改动需要同步改动此处"""
        ret = {fields: data.get(fields, None) for fields in self._format_fields}
        for form_component_value in data.get('form_component_values'):
            if 'name' in form_component_value:
                if form_component_value[u'name'] == u'公出事由':
                    ret['approval_reason'] = form_component_value[u'value']
                if form_component_value[u'name'] == u'公出地点':
                    ret['aproval_desc'] = form_component_value[u'value']
                if form_component_value[u'name'] == u'["开始时间","结束时间"]':
                    ret['start_time'] = json.loads(form_component_value[u'value'])[0]
                    ret['end_time'] = json.loads(form_component_value[u'value'])[1]
        self._approval_info.append(ret)

    def process_qingjia(self, data):
        """处理请假数据，返回统一格式，请假申请模版改动，需要同步改动此处"""
        ret = {fields: data.get(fields, None) for fields in self._format_fields}
        for form_component_value in data.get('form_component_values'):
            if 'name' in form_component_value:
                if form_component_value[u'name'] == u'请假事由':
                    ret['approval_reason'] = form_component_value[u'value']
                if form_component_value[u'name'] == u'["开始时间","结束时间"]':
                    tmp = json.loads(form_component_value[u'value'])
                    ret['aproval_desc'] = tmp[-2]
                    ret['start_time'], ret['end_time'] = tmp[0:2]
        self._approval_info.append(ret)

    def process_chuchai(self, data):
        """处理出差数据，返回统一格式，出差申请模版改动，需要同步改动此处"""
        ret = {fields: data.get(fields, None) for fields in self._format_fields}
        for form_component_value in data.get('form_component_values'):
            if 'name' in form_component_value:
                if form_component_value[u'name'] == u'出差说明':
                    ret['approval_reason'] = form_component_value[u'value']
                if form_component_value[u'name'] == u'行程明细':
                    for row in json.loads(form_component_value[u'value'])[0].get('rowValue'):
                        if row['key'] == u'出差地点':
                            ret['aproval_desc'] = row['value']
                        if row['key'] == u'开始时间-结束时间':
                            ret['start_time'] = row['value'][0]
                            ret['end_time'] = row['value'][1]
        self._approval_info.append(ret)

    def get_approval_data(self):
        """获取审批实例详情数据；很慢，考虑改进为多线程"""
        logger.info('load approval data from ddtalk')
        for process_type, process_code in self.process_codes.iteritems():
            ret = self.d.get_process_ids(process_code=process_code, start_time=self.start_time, end_time=self.end_time)
            for instance_id in ret:
                try:
                    data = self.d.get_processinfo(process_instance_id=instance_id)
                    data.setdefault('instance_id', instance_id)
                    data.setdefault('approval_type', process_type)
                    if data.get('biz_action', None) == 'REVOKE':
                        data['status'] = 'REVOKE'
                        self.instance_revoke.append(data['main_process_instance_id'])
                    if data.get('biz_action', None) == 'MODIFY':
                        self.instance_modify.append(data['main_process_instance_id'])
                    self.approval_instances.append(data)
                except Exception as why:
                    logger.error(why)

    def get_approval_info(self):
        """进一步处理 提供给上层调用"""
        pass

    @property
    def approval_info(self):
        return self._approval_info


def ClientTest1():
    logger = logging.getLogger()
    formatter = logging.Formatter('%(asctime)s %(levelname)-8s: %(message)s')
    console_handle = logging.StreamHandler(sys.stdout)
    console_handle.formatter = formatter
    logger.addHandler(console_handle)
    logger.setLevel(logging.INFO)
    dd = DDTalkClient()
    # print dd.access_token
    # print dd.get_child_dept(parentId=1)
    # print dd.get_dept_lists(parentId=1, fetch_child=True)
    # print dd.get_dept_userids(deptId=75545028)
    # print dd.get_dept_userinfo(deptId=90472241)
    # print dd.get_userinfo(userId=202455141429491590)
    # start_time = time.strptime("2019-08-01", "%Y-%m-%d")
    # start_timestamp = int(time.mktime(start_time))
    # millis_timestamp = int(round(start_timestamp * 1000))
    # print dd.get_dept_info(deptId=75411400)


def OrganizationTest1():
    logger = logging.getLogger()
    formatter = logging.Formatter('%(asctime)s %(levelname)-8s: %(message)s')
    console_handle = logging.StreamHandler(sys.stdout)
    console_handle.formatter = formatter
    logger.addHandler(console_handle)
    logger.setLevel(logging.INFO)
    org = Organization()
    org.init_departinfo()
    # for k, v in org.deptinfo.iteritems():
    #     print k, v
    org.init_userinfo()
    for user in org.get_bj_userinfo().itervalues():
        print user.get('jobnumber', None), user.get('userid', None), user.get('name', None), user.get('email', None), user.get('department', None), user.get('workPlace')


def ApprovalTest1():
    logger = logging.getLogger()
    formatter = logging.Formatter('%(asctime)s %(levelname)-8s: %(message)s')
    console_handle = logging.StreamHandler(sys.stdout)
    console_handle.formatter = formatter
    logger.addHandler(console_handle)
    logger.setLevel(logging.INFO)
    start_time = time.strptime("2019-06-01", "%Y-%m-%d")
    start_timestamp = time.mktime(start_time)
    millis_timestamp = int(round(start_timestamp * 1000))
    app = Approval(start_time=millis_timestamp)
    app.get_approval_data()
    for k, v in app.approval_instances.iteritems():
        print k, v


if __name__ == '__main__':
    # OrganizationTest1()
    ClientTest1()
    # ApprovalTest1()
