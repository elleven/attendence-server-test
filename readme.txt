# 考勤平台概述
## 背景
    目前公司OA系统借助于叮叮应用实现，公司组织架构信息、相关审批流程等都通过叮叮进行，而考勤系统是独立的系统（系统设备属于中控智慧旗下产品www.zkteco.com）；由此对Hr进行考勤统计，相关指标
评定造成了不便，起初是借助考勤系统报表功能进行人工导出统计，工作量大/效率低；而周期需求很频繁；由此催生了考勤平台的需求，旨在整合分散的考勤数据和组织架构/审批数据进行统一查询/统计。

## 考勤平台组成

 1、考勤平台服务分为 attendance-server 和 定时task;
 2、定时task 分为： 同步考勤数据task/同步组织结构task/同步审批数据task 旨在定时同步数据到统一的数据库；提供对外查询/统计
 3、同步考勤数据task 由于限于考勤设备sdk ，只限部署到windows 平台；

## 考勤平台现有部署情况
 1、数据库地址: 172.25.50.168:3306
 2、服务和部分task部署: 172.25.50.158
 3、考勤同步task 部署: 172.25.50.188 win7
 4、访问域名: kq.test.net
 5、仅限HR内部访问

## 部署依赖
1、项目地址 git@git.test.net:test/attendence_server.git
2、项目采用 uwsgi + django 基于python 2.7 ;依赖详见 requirement.txt
3、特殊依赖 win7 下 需要安装考勤设备sdk, www.zkteco.com；参加 脱机通讯开发手册-副本
4、依赖 mysql 数据库，需要提前部署mysql；

## 部署步骤
1、同步考勤task
  win7 下参考www.zkteco.com 下载sdk，并注册sdk;
  配置安装 python2.7 并安装requirement.txt；
  运行task python attendence-task.py；
2、server和其他task部署
  linux下 配置python2.7环境，并安装requirement.txt；
  django 初始化数据库，生成表结构；
  部署uwsgi 并启动 uwsgi --ini uwsgi.ini
  部署task  python manager.py crontab add
  配置admin 创建admin 用户
  授权Hr账户
