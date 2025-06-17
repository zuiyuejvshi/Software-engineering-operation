import re
from email.mime.text import MIMEText
from smtplib import SMTP_SSL, SMTPException
from typing import Union

from bs4 import BeautifulSoup
from requests import get as rget

from Service.utils import getConfig

__doc__ = """
网络服务模块

该模块提供了网络相关的服务功能，主要包括：
1. 邮件服务（Mail类）
   - 发送验证码邮件
   - 支持HTML格式邮件内容
   - 使用SSL加密的SMTP服务

2. API服务（API类）
   - 调用第三方API（如豆瓣图书API）
   - 网页内容解析
   - 数据提取和格式化

所有网络请求都包含适当的错误处理和异常捕获。
"""


class Mail:
    """
    邮件服务类

    该类提供了邮件发送功能，主要用于发送验证码等系统邮件。
    使用smtplib和email库实现，支持SSL加密的SMTP服务。
    相比Flask自带的邮件功能，提供了更灵活的配置和更好的控制。

    Attributes:
        _host: SMTP服务器地址
        _port: SMTP服务器端口
        _username: 邮箱账号
        _password: 邮箱密码
        _sender: 发件人地址
        captchaPattern: 验证码邮件HTML模板
    """

    def __init__(self):
        """
        初始化邮件服务

        从配置文件读取邮件服务器配置信息，包括：
        - 服务器地址和端口
        - 账号和密码
        - 发件人信息
        """
        info = getConfig('E-Mail')
        self._host = info['Host']  # 邮件服务器
        self._port = info['Port']  # 服务器端口
        self._username = info['Username']  # 邮箱账号
        self._password = info['Password']  # 邮箱密码
        self._sender = info['Sender']  # 发件人
        self.captchaPattern = """
        <h1>尊敬的用户：</h1>
        <p>您正在请求重设密码，为保证您的账号安全，需要根据邮箱验证码确定是您本人操作。</p>
        <p>您的验证码为：</p>
        <br><h2>{}</h2>
        <p>验证码10分钟内有效，请及时操作。</p>
        <p>如果这不是您本人的操作，请忽略此邮件。</p>
        <p></p>
        <p align="right">此致</p>
        <p align="right">墨韵平台 Steven</p>"""

    def sendCaptcha(self, receiver: str, captcha: Union[str, int]) -> bool:
        """
        发送验证码邮件

        将验证码以HTML格式发送到指定邮箱，包含完整的邮件模板。

        Args:
            receiver: 收件人邮箱地址
            captcha: 验证码，可以是字符串或整数

        Returns:
            bool: 发送结果
                - True: 发送成功
                - False: 发送失败

        Note:
            - 验证码会被转换为字符串格式
            - 邮件使用HTML格式，包含完整的样式和布局
        """
        if isinstance(captcha, int):
            captcha = str(captcha)
        content = self.captchaPattern.format(captcha)
        message = MIMEText(content, 'html', 'utf-8')
        message['Subject'] = "墨韵 - 验证码"
        message['From'] = self._sender
        message['To'] = receiver
        return self._send(receiver, message)

    def _send(self, receivers: Union[str, list], message: MIMEText) -> bool:
        """
        发送邮件的内部方法

        使用SMTP_SSL连接邮件服务器并发送邮件。

        Args:
            receivers: 收件人邮箱地址，可以是单个地址或地址列表
            message: 邮件内容对象（MIMEText）

        Returns:
            bool: 发送结果
                - True: 发送成功
                - False: 发送失败

        Note:
            - 使用SSL加密的SMTP连接
            - 包含调试信息输出
            - 自动处理连接关闭
        """
        try:
            smtpObj = SMTP_SSL(self._host, self._port)
            smtpObj.set_debuglevel(1)
            # 登录到服务器
            smtpObj.login(self._username, self._password)
            # 发送
            smtpObj.sendmail(self._sender, [receivers], message.as_string())
            # 退出
            smtpObj.quit()
            return True
        except SMTPException as e:
            print(e)
            return False


class API:
    """
    API服务类

    该类提供了调用第三方API的功能，主要用于获取外部数据。
    目前支持豆瓣图书API，可以获取图书的详细信息。

    Attributes:
        UA: 用户代理字符串，用于模拟浏览器请求
    """

    def __init__(self):
        """
        初始化API服务

        设置默认的用户代理字符串，用于模拟浏览器请求。
        """
        self.UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 ' \
                  'Safari/537.36 Edg/113.0.1774.57'

    def getBookInfo_Douban(self, doubanID) -> dict:
        """
        从豆瓣获取图书信息

        通过豆瓣图书页面获取图书的详细信息，包括：
        - 基本信息（标题、作者、出版社等）
        - 评分信息
        - 图书简介
        - 元数据（ISBN、页数等）

        Args:
            doubanID: 豆瓣图书ID，可以是字符串或数字

        Returns:
            dict: 包含图书信息的字典，字段包括：
                - isbn: ISBN号
                - title: 图书标题
                - originTitle: 原作名
                - author: 作者
                - page: 页数
                - publishDate: 出版日期
                - publisher: 出版社
                - description: 图书简介
                - doubanScore: 豆瓣评分
                - doubanID: 豆瓣ID

        Note:
            - 使用BeautifulSoup解析HTML内容
            - 自动处理ID的类型转换
            - 包含完整的错误处理
        """
        if not isinstance(doubanID, str):
            doubanID = str(doubanID)
        r = rget(f"https://book.douban.com/subject/{doubanID}", headers={"User-Agent": self.UA})
        HTML = r.text
        r.close()
        soup = BeautifulSoup(HTML, 'html.parser')

        title = soup.find('span', attrs={'property': 'v:itemreviewed'}).text  # 标题
        score = soup.find('strong', attrs={'class': 'll rating_num'}).text.strip()  # 豆瓣评分
        # 图书元信息
        metaInfo = {}
        htmlInfo = soup.find('div', id='info').text.split('\n')
        htmlInfo = [i.strip() for i in htmlInfo if not re.fullmatch(' *', i)]

        i, j = 0, 0
        while i < len(htmlInfo):
            if re.fullmatch('.+:', htmlInfo[i]):  # 一个单独的key
                k = htmlInfo[i][:-1]
                v = ""
                j = i + 1  # value从下一个段开始
                while j < len(htmlInfo) and not re.fullmatch('.+:.*', htmlInfo[j]):  # 找到下一个key
                    v += htmlInfo[j]
                    j += 1
                metaInfo[k] = v
                i = j
            elif re.fullmatch('.+:.+', htmlInfo[i]):  # key:value形式的内容
                k, v = htmlInfo[i].split(':')
                metaInfo[k] = v.strip()
                i += 1
            else:
                i += 1

        # 图书简介
        intro = soup.find('span', attrs={'class': 'all hidden'})
        introduction = [i.text.strip() for i in intro.find_all('p')]
        introduction = '\n'.join(introduction)

        return {'isbn': metaInfo.get('ISBN'),
                'title': title,
                'originTitle': metaInfo.get('原作名'),
                'author': metaInfo.get('作者'),
                'page': metaInfo.get('页数'),
                'publishDate': metaInfo.get('出版年'),
                'publisher': metaInfo.get('出版社'),
                'description': introduction,
                'doubanScore': score,
                'doubanID': doubanID}
