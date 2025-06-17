"""
数据库初始化脚本

该脚本用于初始化MySQL数据库环境，主要功能包括：
1. 数据库创建
   - 创建新的数据库
   - 设置字符集为utf8
   - 设置排序规则为utf8_general_ci

2. 用户管理
   - 创建数据库管理员账户
   - 设置用户权限
   - 处理密码安全策略

3. 数据导入
   - 导入数据库表结构（DDL）
   - 创建初始数据表
   - 设置表关系

4. 管理员账户
   - 创建平台管理员账户
   - 设置管理员权限
   - 配置管理员信息

注意事项：
- 需要MySQL root用户权限
- 需要正确的数据库配置信息
- 需要DDL.sql文件
- 需要管理员账户配置信息
"""

# -*- coding: utf-8 -*-
import os
import subprocess
import warnings

import pymysql
from werkzeug.security import generate_password_hash

from Service.utils import getConfig

# 获取相关配置信息
db_info = getConfig("Database")  # 数据库配置信息
admin_info = getConfig("Admin")  # 管理员配置信息
# ddl_path = os.path.join(os.getcwd(), "DDL.sql").replace("\\", "/")
ddl_path = r'D:\wps\专业课\软件工程\test\DDL.sql'  # DDL文件路径
# root_passwd = input("请输入MySQL root用户密码：")
root_passwd = '414789'  # root用户密码

# 连接数据库
print(">>---------------------------------------初始化数据库---------------------------------------<<")
# try:
#     conn = pymysql.connect(
#         host=db_info["Host"],
#         port=db_info["Port"],
#         user="root",
#         password=root_passwd
#     )
#     cursor = conn.cursor()
# except pymysql.err.OperationalError:
#     warnings.warn("数据库连接失败，请检查MySQL服务是否正常，或root用户的密码是否正确")
#     exit(-1)
# print("数据库连接成功，正在使用root账户初始化数据库")

# 建立数据库连接
conn = pymysql.connect(
    host=db_info["localhost"],  # 数据库主机地址
    port=db_info["3306"],      # 数据库端口
    user='root',               # 数据库用户名
    password='1234'            # 数据库密码
)
cursor = conn.cursor()  # 创建游标对象

# 创建数据库
try:
    # 创建数据库，设置字符集和排序规则
    cursor.execute(
        "CREATE DATABASE IF NOT EXISTS %s DEFAULT CHARSET utf8 COLLATE utf8_general_ci;" % db_info["Database"])
    print(f"数据库 {db_info['Database']} 创建成功")
except pymysql.err.OperationalError:
    warnings.warn("数据库创建失败，请检查数据库名称是否合法")
    exit(-1)

# 创建数据库管理员账户
try:
    # 创建数据库用户
    cursor.execute("CREATE USER IF NOT EXISTS '%s'@'%s' IDENTIFIED BY '%s';" % (
        db_info["Account"], db_info["Host"], db_info["Password"]))
    print(f"用户'%s'@'%s'创建成功，密码: %s" % (db_info["Account"], db_info["Host"], db_info["Password"]))
except pymysql.err.OperationalError:  # 密码太简单，尝试降低安全级别再创建用户
    # 降低密码安全策略级别
    cursor.execute("SET global validate_password.policy = 0;")
    conn.commit()
    cursor.execute("CREATE USER IF NOT EXISTS '%s'@'%s' IDENTIFIED BY '%s';" % (
        db_info["Account"], db_info["Host"], db_info["Password"]))
    warnings.warn(f"密码级别过低，已降低密码安全级别")
    print(f"用户'%s'@'%s'创建成功，密码: %s" % (db_info["Account"], db_info["Host"], db_info["Password"]))

# 为数据库管理员账户授权
# 授予所有权限
cursor.execute(
    "GRANT ALL PRIVILEGES ON %s.* TO '%s'@'%s';" % (db_info["Database"], db_info["Account"], db_info["Host"]))
print(f"用户'%s'@'%s'授权成功" % (db_info["Account"], db_info["Host"]))
conn.commit()

# 导入DDL（数据库表结构）
print("mysql -u%s -p%s -h%s -P%s %s < %s" % (
        'root', root_passwd, db_info["Host"], db_info["Port"], db_info["Database"], ddl_path
))

# 使用subprocess执行mysql命令导入DDL
mysqlpath = r'D:\mysql\bin\mysql.exe'  # MySQL可执行文件路径
result = subprocess.call(mysqlpath + " -u%s -p%s -h%s -P%s %s < %s" % (
        'root', root_passwd, db_info["Host"], db_info["Port"], db_info["Database"], ddl_path
), shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print(result)
if result == 0:
    print("数据库表结构导入成功")
else:
    warnings.warn("数据库表结构导入失败")
    exit(-1)

print(">>---------------------------------------创建平台管理员---------------------------------------<<")

# 创建平台管理员账户
try:
    # 选择数据库
    cursor.execute("USE %s;" % db_info["Database"])
    # 插入管理员账户信息
    cursor.execute(
        """INSERT INTO user(id,account,password,signature,email,telephone,role) VALUES (%s,%s,%s,%s,%s,%s,%s);""",
        (admin_info["ID"], admin_info["Account"], generate_password_hash(admin_info["Password"]),
         admin_info["Signature"],
         admin_info["E-Mail"], admin_info["Telephone"], "admin")
    )
    conn.commit()
    print(f"管理员账户 {admin_info['Account']} 创建成功，密码: {admin_info['Password']}")
except pymysql.err.IntegrityError:
    warnings.warn("管理员账户创建失败，请检查管理员账户ID是否重复")
    exit(-1)

print("数据库初始化完成")
