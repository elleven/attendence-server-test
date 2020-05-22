# -*- coding=utf-8 -*-
import logging
from django.db import connections
from django.http import HttpResponseRedirect

"""装饰器汇总"""
logger = logging.getLogger('default')


def retry_decorator(retry=3):
    def my_decorator(func):
        def wrapped(*args, **kwargs):
            num = 0
            while num < retry:
                try:
                    return func(*args, **kwargs)
                except Exception as why:
                    num += 1
                    logger.warn(u'%s retry %s', why, str(num))
        return wrapped
    return my_decorator


def close_old_connections():
    for conn in connections.all():
        conn.close_if_unusable_or_obsolete()


def handle_db_connections(func):
    def func_wrapper(*args, **kwargs):
        close_old_connections()
        return func(*args, **kwargs)
    return func_wrapper


def check_login(func):
    def wrapper(request, *args, **kwargs):
        if request.session.get('is_login', False):
            return func(request, *args, **kwargs)
        else:
            next = request.get_full_path()
            red = HttpResponseRedirect('/login/?next=' + next)
            return red
    return wrapper