# -*- coding: utf-8 -*-
import ldap
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication
from django.conf import settings

'''
未完成的认证类， 可忽略
'''
AD_DOMAIN = getattr(settings, 'AD_DOMAIN', '')


class TigerLdap(object):
    def __init__(self):
        self.ad = ldap.initialize(AD_DOMAIN)
        self.ad.protocol_version = 3
        self.ad.set_option(ldap.O, 0)


class LdapAuthentication(BaseAuthentication):
    """AD 认证登陆/查询"""

    def authenticate(self, request):
        username = request.data.get('username') or request.query_params.get('username')
        password = request.data.get('password') or request.query_params.get('password')
        if not username or not password:
            raise exceptions.AuthenticationFailed('invaild username or password')

    def authenticate_header(self, request):
        pass
