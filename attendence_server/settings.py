
# -*- coding=utf-8 -*-
"""
Django settings for attendence_server project.

Generated by 'django-admin startproject' using Django 1.11.24.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""



import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '3d=m@*+p)(@4@)^3kdii_3^w1#k93it1(=c0joip)4snw37!-+'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['kq.test.net']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'attendence.apps.AttendenceConfig',
    'rest_framework',
    'django_crontab'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'attendence_server.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')]
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'builtins': ['django.templatetags.static'],
            'libraries': {
                'query_tags': 'attendence.templatetags.query_tags',
            },
        },
    },
]

WSGI_APPLICATION = 'attendence_server.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

# DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.sqlite3',
#        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
#    }
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'attendence',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': '',
        'port': '3306',
    }
}

# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static/')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'filters': {
        'require_debug_true': {
           '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'filters': [],
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '%s/attendence.log' % BASE_DIR,
            'formatter': 'verbose'
                }
    },
    'loggers': {
        'django_crontab': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'default': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

REST_FRAMEWORK = {
    "DEFAULT_VERSIONS_CLASS": "rest_framework.versioning.URLPathVersioning",
    "DEFAULT_VERSION": 'v1',
    "ALLOWED_VERSIONS": ['v1'],
    "VERSION_PARAM": 'version',
    "DEFAULT_PARSER_CLASSES": ['rest_framework.parsers.JSONParser', 'rest_framework.parsers.FormParser'],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    # "DEFAULT_AUTHENTICATION_CLASSES": ['auto_deploy.utils.authentications.LdapAuth', ]
}

# dd talk setting
DD_TOKEN_EXPIRE = 7200
# app key
DD_APP_KEY = ''
DD_APP_SECRET = ''

# attendance machine
A_MACHINES = ['', '', '']

# django-crontab
CRONJOBS = [
    ('00 23 * * *', 'attendence.crons.cron_inituser', '>>/tmp/cron_inituser.log 2>&1'),
    ('00 22 * * *', 'attendence.crons.cron_initApproval', '>>/tmp/cron_init_approval.log 2>&1'),
    ('00 06 * * *', 'attendence.crons.cron_attendence_notice', '>>/tmp/cron_attendence_notice.log 2>&1'),
    ('30 22 * * 0', 'attendence.crons.cron_initDept', '>>/tmp/cron_initdept.log 2>&1'),
    ('40 04 * * *', 'attendence.crons.cron_initAttendance_fromDD', '>>/tmp/cron_initattdence_fromdd.log 2>&1'),
    ('00 10 * * 0', 'attendence.crons.cron_weekly_report', '>>/tmp/cron_weekly_report.log 2>&1'),
    ('30 10 * * 0', 'attendence.crons.cron_weekly_report_hrbp', '>>/tmp/cron_weekly_report_hrbp.log 2>&1'),

]

# AD
AD_DOMAIN = ''
# smtp

DEFAULT_SMTP_HOST = ''
DEFAULT_SMTP_PORT = 587
DEFAULT_SMTP_USER = ''
DEFAULT_SMTP_PWSSD = ''

# history statistics file save
HISTORY_REPORTER_DIR = os.path.join(BASE_DIR, 'history/')

# hr rules
DEFAULT_ATTENDENCE_RULE = {
    'MAX_QUERY_DAYS': 91,
    'WORKTIME_WARN': 10.0,
    'CLOCKIN_TIME_WARN': '10:31:00',
    'CLOCKOUT_TIME_WARN': '19:00:00',
    'PAGINATE_BY': 91
}

# session 设置
SESSION_COOKIE_AGE = 60 * 10  # 设置过期时间10分钟，默认为两周
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # 设置关闭浏览器时失效
# statistics
#  各部门员工考勤周报数据，发给各部门负责人
DEFAULT_ORG = {
                u"test-department": {
                    'rec': [""],
                    'cc': [""]},

}

# 部门员工详细打卡数据，发给HRBP；对应关系表;
# 注意此处是一级部门
DEFAULT_ORG_HRBP_MAP = [
    {
        'departments': [u'test'],
        'hrbp': ['']
    },
]
DEFAULT_DEVELOP_ORG = [u'研发']

# 考勤周报模版
DEFAULT_TMPL = u'''
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN">
<html lang="ch">
<head>
    <title> Statistic Report Email</title>
</head>
<body>
    <h1 align="left">{{title}}</h1>
    <ol>
    <li>周平均出勤=有效出勤时间之和/有效出勤次数，无签到或签退未打卡记录和请休假信息视为有效出勤</li>
    </ol>

    <table border="1" align="center">
        <tr>
            <th>部门</th>
            <th>工号</th>
            <th>姓名</th>
            <th>日期</th>
            <th>签到时间</th>
            <th>签退时间</th>
            <th>出勤时间</th>
            <th>请假信息</th>
            <th>平均出勤</th>
        </tr>
    {% for record in records %}
        {% if loop.index0 % 7 == 0  and  0 < average_time.get(record.jobnumber,'0')|float() < 10 %}
            <tr>
                <td>{{record.deaprtname}}</td>
                <td>{{record.jobnumber}}</td>
                <td>{{record.username}}</td>
                <td>{{record.record_date}}</td>
                <td>{{record.clockin_time}}</td>
                <td>{{record.clockout_time}}</td>
                <td>{{record.worktime}}</td>
                <td>{{record.leave_info}}</td>
                <td rowspan='7' bgcolor="red">{{average_time.get(record.jobnumber)}}</td>

            </tr>
        {% elif loop.index0 % 7 == 0  and average_time.get(record.jobnumber,'0') |float() >= 10 %}
            <tr>
                <td>{{record.deaprtname}}</td>
                <td>{{record.jobnumber}}</td>
                <td>{{record.username}}</td>
                <td>{{record.record_date}}</td>
                <td>{{record.clockin_time}}</td>
                <td>{{record.clockout_time}}</td>
                <td>{{record.worktime}}</td>
                <td>{{record.leave_info}}</td>
                <td rowspan='7' >{{average_time.get(record.jobnumber)}}</td>
            </tr>
        {% elif loop.index0 % 7 == 0  and average_time.get(record.jobnumber,'0') |int() == 0 %}
            <tr>
                <td>{{record.deaprtname}}</td>
                <td>{{record.jobnumber}}</td>
                <td>{{record.username}}</td>
                <td>{{record.record_date}}</td>
                <td>{{record.clockin_time}}</td>
                <td>{{record.clockout_time}}</td>
                <td>{{record.worktime}}</td>
                <td>{{record.leave_info}}</td>
                <td rowspan='7' >倒班不计或无有效考勤记录</td>
            </tr>
        {% else %}
            <tr>
                <td>{{record.deaprtname}}</td>
                <td>{{record.jobnumber}}</td>
                <td>{{record.username}}</td>
                <td>{{record.record_date}}</td>
                <td>{{record.clockin_time}}</td>
                <td>{{record.clockout_time}}</td>
                <td>{{record.worktime}}</td>
                <td>{{record.leave_info}}</td>    
            </tr>
        {% endif %} 
    {% endfor %}
    </table>
</body>
</html>
'''
# 部门周平均出勤时间排名周报模版
DEFAULT_ORG_TMPL = u'''
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN">
<html lang="ch">
<head>
    <title>Statistic Weekly Report Email</title>
</head>
<body>
    <h1 align="center">{{title}}</h1>
    <ol>
    <li>部门平均出勤=有效出勤时间之和/有效出勤次数，无签到或签退未打卡记录和请休假信息视为有效出勤</li>
    <li>部门单位以二级部门做为统计单元</li>
    </ol>
    <table border="1" align="left">
        <tr>
            <th>部门</th> 
            <th>平均出勤</th>
        </tr>
    {% for record in records %}    
            <tr>
                <td>{{record.deaprtname}}</td>
                <td>{{record.average_time}}</td>
            </tr>
    {% endfor %}
    </table>
</body>
</html>
'''
# 个人周平均出勤时间周报模版
DEFAULT_PERSON_TMPL = u'''
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN">
<html lang="ch">
<head>
    <title>Statistic Weekly Report Email</title>
</head>
<body>
    <h1 align="center">{{title}}</h1>
    <ol>
    <li>统计个人周平均出勤时间小于10</li>
    <li>周平均出勤=有效出勤时间之和/有效出勤次数，无签到或签退未打卡记录和请休假信息视为有效出勤</li>
    </ol>
    <table border="1" align="center">
        <tr>
            <th>姓名</th> 
            <th>工号</th>
            <th>部门</th> 
            <th>平均出勤</th>
        </tr>
    {% for record in records %}    
            <tr>
                <td>{{record.name}}</td>
                <td>{{record.jobnumber}}</td>
                <td>{{record.deaprtname}}</td>
                <td>{{record.average_time}}</td>
            </tr>
    {% endfor %}
    </table>
</body>
</html>
'''
# 未打卡通知邮件模版
DEFAULT_NOTIFY_TMPL = u'''
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN">
<html lang="ch">
<head>
    <title>{{title}}</title>
</head>
<body>
    <p align='left'>hi {{info.name}} </p>
       <table border="1" align="center">
        <tr>
            <th>部门</th>
            <th>工号</th>
            <th>姓名</th>
            <th>日期</th>
            <th>未打卡信息</th>
        </tr>
        <tr>
            <td>{{info.departname}}</td>
            <td>{{info.jobnumber}}</td>
            <td>{{info.name}}</td>
            <td>{{info.date}}</td>
            <td>{{info.message}}</td>
        </tr> 
     </table>              
</body>
</html>
'''
# 未打卡通知汇总报告模版
DEFAULT_NOTIFY_RESULT_TMPL = u'''
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN">
<html lang="ch">
<head>
    <title>{{title}}</title>
</head>
<body>
    <h1 align="center">{{title}}</h1>
       <table border="1" align="center">
        <tr>
            <th>部门</th>
            <th>工号</th>
            <th>姓名</th>
            <th>日期</th>
            <th>未打卡信息</th>
            <th>发送结果</th>
        </tr>
        {% for info in infos %}
        <tr>
            <td>{{info.departname}}</td>
            <td>{{info.jobnumber}}</td>
            <td>{{info.name}}</td>
            <td>{{info.date}}</td>
            <td>{{info.message}}</td>
            <td>{{info.result}}</td>
        </tr> 
        {% endfor %}
     </table>              
</body>
</html>
'''
# 不计入打卡通知白名单
DEFAULT_WHITE_LIST = ['00001']
