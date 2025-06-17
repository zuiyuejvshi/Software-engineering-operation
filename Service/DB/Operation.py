from datetime import datetime

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

from typing import Optional
from Service.DB.ExtractInfo import *
from Service.utils import getConfig


class Database:
    """
    数据库操作类，提供对数据库的增删改查等基本操作

    该类封装了所有与数据库交互的操作，包括：
    - 用户管理（添加、修改、查询用户信息）
    - 日志管理（发布、评论、点赞）
    - 书籍管理（添加、查询书籍信息）
    - 圈子管理（创建、加入圈子，发布讨论）
    - 消息管理（私信、通知）
    - 错误处理

    基本函数命名规范：
    - get__(): 获取单个记录
    - getAll__(): 获取多个记录
    - add__(): 添加记录
    - modify__(): 修改记录
    - delete__(): 删除记录

    对于需要时间戳的操作，可以传入datetime对象，否则会自动使用当前时间。
    """

    def __init__(self, app: Flask):
        """
        初始化数据库连接

        Args:
            app: Flask应用实例，用于配置数据库连接

        初始化过程：
        1. 从配置文件读取数据库连接信息
        2. 构建数据库连接URI
        3. 初始化SQLAlchemy实例
        4. 附加数据模型
        """
        info = getConfig("Database")
        client = f"{info['Type'].lower()}+{info['Driver']}"
        host = info["Host"]
        port = info["Port"]
        account = info["Account"]
        password = info["Password"]
        database = info["Database"]
        URI = f"{client}://{account}:{password}@{host}:{port}/{database}"
        app.config["SQLALCHEMY_DATABASE_URI"] = URI
        self.db = SQLAlchemy(app)
        self._attachModel()

    """用户相关操作"""

    def addUser(self, account, password, email, telephone, role="student") -> int:
        """
        添加新用户到数据库

        Args:
            account: 用户名，用于登录
            password: 用户密码（明文），将在函数内部进行加密
            email: 用户邮箱，可以为空
            telephone: 用户电话，可以为空
            role: 用户角色，默认为"student"，可选值包括：
                - "student": 学生
                - "teacher": 教师
                - "admin": 管理员

        Returns:
            int: 新创建用户的ID

        Note:
            - 邮箱和电话如果为空字符串，将被设置为None
            - 密码会使用werkzeug.security进行加密存储
            - 会自动记录用户的最后登录时间
        """
        email = None if email == "" else email
        telephone = None if telephone == "" else telephone
        user = User(account=account, password=generate_password_hash(password), signature="",
                    email=email, telephone=telephone, role=role,
                    lastLoginTime=datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S'))
        self.db.session.add(user)
        self.db.session.commit()

        return user.id

    def modifyUser(self, userID: int, **kwargs):
        """
        修改指定用户的信息

        Args:
            userID: 要修改的用户ID
            **kwargs: 要修改的字段和值的键值对，可以包含：
                - account: 用户名
                - password: 密码（会自动加密）
                - signature: 签名
                - email: 邮箱
                - telephone: 电话
                - role: 角色

        Returns:
            bool: 修改是否成功
                - True: 修改成功
                - False: 用户不存在
        """
        user = User.query.filter_by(id=userID).first()
        if not user:
            return False
        for key in kwargs:
            if hasattr(user, key):
                setattr(user, key, kwargs[key])
        self.db.session.commit()
        return True

    def modifyUserByAccount(self, account: str, password):
        """
        根据用户名重置用户密码

        Args:
            account: 用户名
            password: 新密码（明文），将在函数内部进行加密

        Note:
            - 密码会使用werkzeug.security进行加密存储
            - 如果用户不存在，将抛出异常
        """
        user = User.query.filter_by(account=account).first()
        user.password = generate_password_hash(password)
        self.db.session.commit()

    @staticmethod
    def getUser(userID: object, withPasswd: object = False) -> Optional[dict]:
        """
        根据用户ID获取用户信息

        Args:
            userID: 用户ID
            withPasswd: 是否在返回数据中包含密码
                - True: 返回包含密码的完整用户信息
                - False: 返回不包含密码的用户信息（默认）

        Returns:
            Optional[dict]: 用户信息字典，如果用户不存在则返回None
        """
        info = User.query.filter_by(id=userID).first()
        if not info:
            return None
        else:
            return extractUser(info, withPasswd)

    @staticmethod
    def searchUser(keyword, withPasswd=False) -> list[dict]:
        """
        根据关键字搜索用户

        Args:
            keyword: 搜索关键字，将匹配用户名
            withPasswd: 是否在返回数据中包含密码
                - True: 返回包含密码的完整用户信息
                - False: 返回不包含密码的用户信息（默认）

        Returns:
            list[dict]: 匹配的用户信息列表，如果没有匹配则返回空列表
        """
        users = User.query.filter(User.account.like(f"%{keyword}%")).all()
        if not users:
            return []
        else:
            return [extractUser(info, withPasswd) for info in users]

    @staticmethod
    def getAllUser(withPasswd=False) -> list[dict]:
        """
        获取所有用户的信息

        Args:
            withPasswd: 是否在返回数据中包含密码
                - True: 返回包含密码的完整用户信息
                - False: 返回不包含密码的用户信息（默认）

        Returns:
            list[dict]: 所有用户的信息列表，如果没有用户则返回空列表
        """
        infoList = User.query.all()
        if not infoList:
            return []
        else:
            return [extractUser(info, withPasswd) for info in infoList]

    @staticmethod
    def getUserByAccount(account: str, withPasswd=False) -> Optional[dict]:
        """
        根据用户名获取用户信息

        Args:
            account: 用户名
            withPasswd: 是否在返回数据中包含密码
                - True: 返回包含密码的完整用户信息
                - False: 返回不包含密码的用户信息（默认）

        Returns:
            Optional[dict]: 用户信息字典，如果用户不存在则返回None
        """
        info = User.query.filter_by(account=account).first()
        if not info:
            return None
        else:
            return extractUser(info, withPasswd)

    @staticmethod
    def getAllUserByAccount(account: str, withPasswd=False) -> list[dict]:
        """
        根据用户名获取所有匹配的用户信息

        Args:
            account: 用户名
            withPasswd: 是否在返回数据中包含密码
                - True: 返回包含密码的完整用户信息
                - False: 返回不包含密码的用户信息（默认）

        Returns:
            list[dict]: 匹配的用户信息列表，如果没有匹配则返回空列表
        """
        infoList = User.query.filter_by(account=account).all()
        if not infoList:
            return []
        else:
            return [extractUser(info, withPasswd) for info in infoList]

    def checkLogin(self, account, password):
        """
        验证用户登录

        Args:
            account: 用户名
            password: 密码（明文）

        Returns:
            Union[int, bool]: 
                - 如果验证成功，返回用户ID
                - 如果验证失败，返回False
        """
        usersInfo = self.getAllUserByAccount(account, withPasswd=True)
        if len(usersInfo) == 0:
            return False
        else:
            for info in usersInfo:
                if check_password_hash(info["password"], password):
                    return info["id"]
            else:
                return False

    """日志相关操作"""

    @staticmethod
    def getJournal(journalID: int):
        """
        获取指定日志的详细信息

        Args:
            journalID: 日志ID

        Returns:
            dict: 日志信息字典，包含：
                - 日志基本信息
                - 点赞数
                - 评论数
        """
        journal = Journal.query.filter_by(id=journalID).first()
        likeNum = JournalLike.query.filter_by(journalID=journal.id).count()
        commentNum = JournalComment.query.filter_by(journalID=journal.id).count()
        return extractJournal(journal, likeNum, commentNum)

    @staticmethod
    def getAllJournalByID(journalID: list) -> dict[dict]:
        """
        批量获取多个日志的详细信息

        Args:
            journalID: 日志ID列表

        Returns:
            dict[dict]: 以日志ID为键的日志信息字典
        """
        journals = Journal.query.filter(Journal.id.in_(journalID)).all()
        res = {}
        for journal in journals:
            likeNum = JournalLike.query.filter_by(journalID=journal.id).count()
            commentNum = JournalComment.query.filter_by(journalID=journal.id).count()
            res[journal.id] = extractJournal(journal, likeNum, commentNum)
        return res

    @staticmethod
    def getAllJournalByAuthorID(authorID: int = None, limit=None) -> list[dict]:
        """
        获取指定作者的所有日志

        Args:
            authorID: 作者ID，如果为None则获取所有日志
            limit: 返回结果的数量限制，None表示不限制

        Returns:
            list[dict]: 日志信息列表，按发布时间降序排列
        """
        if authorID is None and limit is None:  # 按时间降序排列
            journals = Journal.query.order_by(Journal.publishTime.desc()).all()
        elif authorID is None and limit is not None:
            journals = Journal.query.order_by(Journal.publishTime.desc()).limit(limit).all()
        elif authorID is not None and limit is None:
            journals = Journal.query.filter_by(authorID=authorID).order_by(Journal.publishTime.desc()).all()
        else:
            journals = Journal.query.filter_by(authorID=authorID).order_by(Journal.publishTime.desc()).limit(
                limit).all()
        res = []
        for journal in journals:
            likeNum = JournalLike.query.filter_by(journalID=journal.id).count()
            commentNum = JournalComment.query.filter_by(journalID=journal.id).count()
            res.append(extractJournal(journal, likeNum, commentNum))
        return res

    @staticmethod
    def getAllJournal():
        """
        获取所有日志信息

        Returns:
            list[dict]: 所有日志的信息列表，按发布时间降序排列
        """
        res = []
        journals = Journal.query.order_by(Journal.publishTime.desc()).all()
        for journal in journals:
            likeNum = JournalLike.query.filter_by(journalID=journal.id).count()
            commentNum = JournalComment.query.filter_by(journalID=journal.id).count()
            res.append(extractJournal(journal, likeNum, commentNum))
        return res

    @staticmethod
    def searchJournal(keyword: str) -> list[dict]:
        """
        搜索日志

        Args:
            keyword: 搜索关键字，将匹配日志标题和内容

        Returns:
            list[dict]: 匹配的日志信息列表
        """
        journalsInfo = Journal.query.filter(
            Journal.title.like("%" + keyword + "%") | Journal.content.like("%" + keyword + "%")).all()
        res = []
        for journal in journalsInfo:
            likeNum = JournalLike.query.filter_by(journalID=journal.id).count()
            commentNum = JournalComment.query.filter_by(journalID=journal.id).count()
            res.append({"id": journal.id,
                        "title": journal.title,
                        "firstParagraph": journal.firstParagraph,
                        "content": journal.content,
                        "publishTime": journal.publishTime,
                        "authorID": journal.authorID,
                        "bookID": journal.bookID,
                        "likeNum": likeNum,
                        "commentNum": commentNum})
        return res

    def addJournal(self, title: str, content: list, publishTime: str, authorID: int, bookID: int) -> int:
        """
        添加新日志

        Args:
            title: 日志标题
            content: 日志内容列表，第一段将作为firstParagraph
            publishTime: 发布时间
            authorID: 作者ID
            bookID: 相关书籍ID

        Returns:
            int: 新创建的日志ID
        """
        journal = Journal(title=title,
                          firstParagraph=content[0],
                          content="\n".join(content),
                          publishTime=publishTime,
                          authorID=authorID,
                          bookID=bookID)
        self.db.session.add(journal)
        self.db.session.commit()
        return Journal.query.filter_by(title=title, authorID=authorID).first().id

    def markAllJournalCommentAsRead(self, journalID: int):
        """
        将指定日志的所有评论标记为已读

        Args:
            journalID: 日志ID
        """
        JournalComment.query.filter_by(journalID=journalID).update({"isRead": True})
        self.db.session.commit()

    @staticmethod
    def getJournalComments(journalID) -> list[dict]:
        """
        获取指定日志的所有评论

        Args:
            journalID: 日志ID

        Returns:
            list[dict]: 评论信息列表，按发布时间降序排列
        """
        comments = JournalComment.query.filter_by(journalID=journalID).order_by(JournalComment.publishTime.desc()).all()
        if not comments:
            return []
        else:
            return [extractJournalComment(comment) for comment in comments]

    def addJournalComment(self, journalID, content, authorID, publishTime: str = None):
        """
        添加日志评论

        Args:
            journalID: 日志ID
            content: 评论内容
            authorID: 评论作者ID
            publishTime: 发布时间，如果为None则使用当前时间

        Returns:
            bool: 添加是否成功
        """
        if not publishTime:
            publishTime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        comment = JournalComment(content=content, publishTime=publishTime, authorID=authorID, journalID=journalID)
        self.db.session.add(comment)
        self.db.session.commit()
        return True

    @staticmethod
    def getJournalLikeNum(journalID) -> int:
        """
        获取指定日志的点赞数

        Args:
            journalID: 日志ID

        Returns:
            int: 点赞数
        """
        return JournalLike.query.filter_by(journalID=journalID).count()

    def addJournalLike(self, journalID, authorID) -> bool:
        """
        添加日志点赞

        Args:
            journalID: 日志ID
            authorID: 点赞用户ID

        Returns:
            bool: 添加是否成功
                - True: 添加成功
                - False: 已经点赞过
        """
        publishTime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if JournalLike.query.filter_by(journalID=journalID, authorID=authorID).first():
            return False
        else:
            like = JournalLike(journalID=journalID, authorID=authorID, publishTime=publishTime)
            self.db.session.add(like)
            self.db.session.commit()
            return True

    """书籍相关操作"""

    @staticmethod
    def searchBook(keyword: str) -> list[dict]:
        """
        搜索书籍

        Args:
            keyword: 搜索关键字，将匹配书籍标题和作者

        Returns:
            list[dict]: 匹配的书籍信息列表，按豆瓣评分降序排列
        """
        booksInfo = Book.query.filter(
            Book.title.like(f"%{keyword}%") | Book.author.like(f"%{keyword}%")).order_by(
            Book.doubanScore.desc()).all()

        return [extractBook(book) for book in booksInfo]

    @staticmethod
    def getBook(bookID: int):
        """
        获取指定书籍的详细信息

        Args:
            bookID: 书籍ID

        Returns:
            dict: 书籍信息字典
        """
        book = Book.query.filter_by(id=bookID).first()
        return extractBook(book)

    def modifyBook(self, bookID: int, **kwargs):
        """
        修改书籍信息

        Args:
            bookID: 书籍ID
            **kwargs: 要修改的字段和值的键值对

        Returns:
            bool: 修改是否成功
                - True: 修改成功
                - False: 书籍不存在
        """
        book = Book.query.filter_by(id=bookID).first()
        if not book:
            return False
        for key, value in kwargs.items():
            if hasattr(book, key):
                setattr(book, key, value)
        self.db.session.commit()
        return True

    @staticmethod
    def getAllBook(limit=0) -> list[dict]:
        """
        获取所有书籍信息

        Args:
            limit: 返回结果的数量限制，0表示不限制

        Returns:
            list[dict]: 书籍信息列表，按出版日期降序排列
        """
        if not limit:
            books = Book.query.filter_by().order_by(Book.publishDate.desc()).all()
        else:
            books = Book.query.filter_by().order_by(Book.publishDate.desc()).limit(limit).all()
        return [extractBook(book) for book in books]

    """圈子相关操作"""

    def addGroup(self, name: str, description: str, founderID: int, establishTime: str = None) -> int:
        """
        创建新圈子

        Args:
            name: 圈子名称
            description: 圈子描述
            founderID: 创建者ID
            establishTime: 创建时间，如果为None则使用当前时间

        Returns:
            int: 新创建的圈子ID
        """
        if not establishTime:
            establishTime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        group = Group(name=name, description=description, founderID=founderID, establishTime=establishTime)
        self.db.session.add(group)
        self.db.session.commit()
        return Group.query.filter_by(name=name, founderID=founderID, establishTime=establishTime).first().id

    @staticmethod
    def getGroup(groupID: int) -> dict:
        """
        获取指定圈子的详细信息

        Args:
            groupID: 圈子ID

        Returns:
            dict: 圈子信息字典
        """
        group = Group.query.filter_by(id=groupID).first()
        return extractGroup(group)

    def modifyGroup(self, groupID: int, **kwargs):
        """
        修改圈子信息

        Args:
            groupID: 圈子ID
            **kwargs: 要修改的字段和值的键值对

        Returns:
            bool: 修改是否成功
                - True: 修改成功
                - False: 圈子不存在
        """
        group = Group.query.filter_by(id=groupID).first()
        if not group:
            return False
        for key, value in kwargs.items():
            if hasattr(group, key):
                setattr(group, key, value)
        self.db.session.commit()
        return True

    @staticmethod
    def getAllGroup() -> list[dict]:
        """
        获取所有圈子信息

        Returns:
            list[dict]: 圈子信息列表
        """
        groups = Group.query.filter_by().all()
        return [extractGroup(group) for group in groups]

    @staticmethod
    def searchGroup(keyword: str) -> list[dict]:
        """
        搜索圈子

        Args:
            keyword: 搜索关键字，将匹配圈子名称和描述

        Returns:
            list[dict]: 匹配的圈子信息列表
        """
        groups = Group.query.filter(
            Group.name.like(f"%{keyword}%") | Group.description.like(f"%{keyword}%")).all()
        return [extractGroup(group) for group in groups]

    """圈子内的帖子相关操作"""

    @staticmethod
    def getGroupAllDiscussion(groupID: int) -> list[dict]:
        """
        获取指定圈子的所有帖子

        Args:
            groupID: 圈子ID

        Returns:
            list[dict]: 帖子信息列表，按发布时间降序排列
        """
        discussions = GroupDiscussion.query.filter_by(groupID=groupID).order_by(GroupDiscussion.postTime.desc()).all()
        return [extractGroupDiscussion(discussion) for discussion in discussions]

    def markAllDiscussionAsRead(self, groupID: int):
        """
        将指定圈子的所有帖子标记为已读

        Args:
            groupID: 圈子ID
        """
        GroupDiscussion.query.filter_by(groupID=groupID).update({"isRead": True})
        self.db.session.commit()

    def addGroupDiscussion(self, posterID: int, groupID: int, postTime: str, title: str, content: str)->int:
        """
        添加新帖子

        Args:
            posterID: 发布者ID
            groupID: 圈子ID
            postTime: 发布时间
            title: 帖子标题
            content: 帖子内容

        Returns:
            int: 新创建的帖子ID
        """
        discussion = GroupDiscussion(posterID=posterID, groupID=groupID, postTime=postTime, title=title,
                                     content=content)
        self.db.session.add(discussion)
        self.db.session.commit()
        return GroupDiscussion.query.filter_by(posterID=posterID, groupID=groupID, postTime=postTime).first().id

    @staticmethod
    def getGroupDiscussion(discussID: int) -> dict:
        """
        获取指定帖子的详细信息

        Args:
            discussID: 帖子ID

        Returns:
            dict: 帖子信息字典
        """
        discussion = GroupDiscussion.query.filter_by(id=discussID).first()
        return extractGroupDiscussion(discussion)

    def deleteGroupDiscussion(self, discussID: int) -> bool:
        """
        删除指定帖子

        Args:
            discussID: 帖子ID

        Returns:
            bool: 删除是否成功
                - True: 删除成功
                - False: 帖子不存在
        """
        discussion = GroupDiscussion.query.filter_by(id=discussID).first()
        if not discussion:
            return False
        self.db.session.delete(discussion)
        self.db.session.commit()
        return True

    """帖子的回复相关操作"""

    def addGroupDiscussionReply(self, discussionID: int, authorID: int, content: str, replyTime: str = None) -> bool:
        """
        添加帖子回复

        Args:
            discussionID: 帖子ID
            authorID: 回复作者ID
            content: 回复内容
            replyTime: 回复时间，如果为None则使用当前时间

        Returns:
            bool: 添加是否成功
        """
        if not replyTime:
            replyTime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        reply = GroupDiscussionReply(authorID=authorID, discussionID=discussionID, replyTime=replyTime, content=content)
        self.db.session.add(reply)
        self.db.session.commit()
        return True

    @staticmethod
    def getGroupDiscussionReplies(discussionID: int) -> list[dict]:
        """
        获取指定帖子的所有回复

        Args:
            discussionID: 帖子ID

        Returns:
            list[dict]: 回复信息列表，按回复时间升序排列
        """
        reply = GroupDiscussionReply.query.filter_by(discussionID=discussionID).order_by(
            GroupDiscussionReply.replyTime.asc()).all()
        return [extractGroupDiscussionReply(reply) for reply in reply]

    @staticmethod
    def getGroupDiscussionRepliesNum(discussionID: int) -> int:
        """
        获取指定帖子的回复数量

        Args:
            discussionID: 帖子ID

        Returns:
            int: 回复数量
        """
        return GroupDiscussionReply.query.filter_by(discussionID=discussionID).count()

    def markAllDiscussionReplyAsRead(self, discussionID: int):
        """
        将指定帖子的所有回复标记为已读

        Args:
            discussionID: 帖子ID
        """
        GroupDiscussionReply.query.filter_by(discussionID=discussionID).update({"isRead": True})
        self.db.session.commit()

    @staticmethod
    def getGroupReplies(groupID: int, limit=5) -> list[dict]:
        """
        获取指定圈子的最新回复

        Args:
            groupID: 圈子ID
            limit: 返回结果的数量限制，默认为5

        Returns:
            list[dict]: 回复信息列表，按回复时间降序排列
        """
        discussionID = [discussion.id for discussion in GroupDiscussion.query.filter_by(groupID=groupID).all()]
        replies = GroupDiscussionReply.query.filter(GroupDiscussionReply.discussionID.in_(discussionID)).order_by(
            GroupDiscussionReply.replyTime.desc()).limit(limit).all()
        return [extractGroupDiscussionReply(reply) for reply in replies]

    """圈子成员相关操作"""

    @staticmethod
    def getAllGroupUser(groupID: int) -> list[dict]:
        """
        获取指定圈子的所有成员

        Args:
            groupID: 圈子ID

        Returns:
            list[dict]: 成员信息列表，按加入时间降序排列
        """
        user = GroupUser.query.filter_by(groupID=groupID).order_by(GroupUser.joinTime.desc()).all()
        return [extractGroupUser(user) for user in user]

    @staticmethod
    def getGroupUserNum(groupID: int) -> int:
        """
        获取指定圈子的成员数量

        Args:
            groupID: 圈子ID

        Returns:
            int: 成员数量
        """
        return GroupUser.query.filter_by(groupID=groupID).count()

    @staticmethod
    def getGroupDiscussionNum(groupID: int) -> int:
        """
        获取指定圈子的帖子数量

        Args:
            groupID: 圈子ID

        Returns:
            int: 帖子数量
        """
        return GroupDiscussion.query.filter_by(groupID=groupID).count()

    """错误响应相关操作"""

    @staticmethod
    def getError(errorCode: int) -> dict:
        """
        获取指定错误码的错误信息

        Args:
            errorCode: 错误码

        Returns:
            dict: 错误信息字典，包含：
                - errorCode: 错误码
                - title: 错误标题
                - title_en: 英文错误标题
                - content: 错误内容
                - publishTime: 发布时间
                - authorID: 作者ID
                - referenceLink: 参考链接
        """
        error = Error.query.filter_by(errorCode=errorCode).first()
        return {"errorCode": error.errorCode,
                "title": error.title,
                "title_en": error.title_en,
                "content": error.content,
                "publishTime": error.publishTime,
                "authorID": error.authorID,
                "referenceLink": error.referenceLink}

    """消息相关操作"""

    def getAllUnreadMessage(self, userID: int) -> dict[str, list[dict]]:
        """
        获取用户的所有未读消息

        包括以下类型的消息：
        - 书评回复
        - 圈子新帖
        - 帖子回复
        - 私信

        Args:
            userID: 用户ID

        Returns:
            dict[str, list[dict]]: 按类型分类的未读消息字典，包含：
                - journalComment: 书评回复列表
                - groupDiscussion: 圈子新帖列表
                - discussionReply: 帖子回复列表
                - chat: 私信列表
        """
        # 书评回复
        journalComments = JournalComment.query.filter_by(authorID=userID, isRead=False).all()
        journalComments = [extractJournalComment(comment) for comment in journalComments]
        for comment in journalComments:
            comment["account"] = self.getUser(comment["authorID"])['account']
        # 圈子新帖
        groupID = [item.id for item in Group.query.filter_by(founderID=userID).all()]
        groupDiscussions = GroupDiscussion.query.filter(GroupDiscussion.groupID.in_(groupID),
                                                        GroupDiscussion.isRead == False).all()
        groupDiscussions = [extractGroupDiscussion(discussion) for discussion in groupDiscussions]
        for discussion in groupDiscussions:
            discussion["account"] = self.getUser(discussion["posterID"])['account']
        # 帖子回复
        discussionID = [item.id for item in GroupDiscussion.query.filter_by(posterID=userID).all()]
        discussionReplies = GroupDiscussionReply.query.filter(
            GroupDiscussionReply.discussionID.in_(discussionID), GroupDiscussionReply.isRead == False).all()
        discussionReplies = [extractGroupDiscussionReply(reply) for reply in discussionReplies]
        for reply in discussionReplies:
            reply["account"] = self.getUser(reply["authorID"])['account']
        # 私信
        chats = Chat.query.filter_by(receiverID=userID, isRead=False).all()
        chats = [extractChat(chat) for chat in chats]
        for chat in chats:
            chat["account"] = self.getUser(chat["senderID"])['account']
        return {"journalComment": journalComments,
                "groupDiscussion": groupDiscussions,
                "discussionReply": discussionReplies,
                "chat": chats}

    @staticmethod
    def getAllUnreadMessageNum(userID: int) -> dict[str, int]:
        """
        获取用户的所有未读消息数量

        包括以下类型的消息：
        - 书评回复
        - 圈子新帖
        - 帖子回复
        - 私信

        Args:
            userID: 用户ID

        Returns:
            dict[str, int]: 按类型分类的未读消息数量字典，包含：
                - journalComment: 书评回复数量
                - groupDiscussion: 圈子新帖数量
                - discussionReply: 帖子回复数量
                - chat: 私信数量
        """
        # 书评回复
        journalCommentsNum = JournalComment.query.filter_by(authorID=userID, isRead=False).count()
        # 圈子新帖
        groupID = [item.id for item in Group.query.filter_by(founderID=userID).all()]
        groupDiscussionsNum = GroupDiscussion.query.filter(
            GroupDiscussion.groupID.in_(groupID), GroupDiscussion.isRead == False).count()
        # 帖子回复
        discussionID = [item.id for item in GroupDiscussion.query.filter_by(posterID=userID).all()]
        discussionRepliesNum = GroupDiscussionReply.query.filter(
            GroupDiscussionReply.discussionID.in_(discussionID), GroupDiscussionReply.isRead == False).count()
        # 私信
        chatsNum = Chat.query.filter_by(receiverID=userID, isRead=False).count()
        return {"journalComment": journalCommentsNum,
                "groupDiscussion": groupDiscussionsNum,
                "discussionReply": discussionRepliesNum,
                "chat": chatsNum}

    """数据模型定义"""

    def _attachModel(self):
        """
        定义数据库模型类

        包括以下模型：
        - User: 用户模型
        - Book: 书籍模型
        - Journal: 日志模型
        - JournalComment: 日志评论模型
        - JournalLike: 日志点赞模型
        - Group: 圈子模型
        - GroupDiscussion: 圈子讨论模型
        - GroupUser: 圈子用户关系模型
        - GroupDiscussionReply: 圈子讨论回复模型
        - Error: 错误信息模型
        - Chat: 聊天消息模型
        """
        global User, Book, Journal, JournalComment, JournalLike, Group, GroupDiscussion, GroupUser, GroupDiscussionReply
        global Error, Chat

        class User(self.db.Model):
            """用户模型"""
            id = self.db.Column(self.db.Integer, primary_key=True, autoincrement=True)
            account = self.db.Column(self.db.String(24), unique=True)
            password = self.db.Column(self.db.String(128), unique=False)
            signature = self.db.Column(self.db.String(128), unique=False)
            email = self.db.Column(self.db.String(120), unique=False)
            telephone = self.db.Column(self.db.String(11), unique=False)
            lastLoginTime = self.db.Column(self.db.DateTime, unique=False)
            role = self.db.Column(self.db.Enum("student", "teacher", "admin"), unique=False)

            def __init__(self, account, password, signature, email, telephone, lastLoginTime, role):
                self.account = account
                self.password = password
                self.signature = signature
                self.email = email
                self.telephone = telephone
                self.lastLoginTime = lastLoginTime
                self.role = role

        class Book(self.db.Model):
            """书籍模型"""
            id = self.db.Column(self.db.Integer, primary_key=True, autoincrement=True)
            isbn = self.db.Column(self.db.String(32), unique=True)
            title = self.db.Column(self.db.String(128), unique=False)
            originTitle = self.db.Column(self.db.String(128), unique=False)
            subtitle = self.db.Column(self.db.String(128), unique=False)
            author = self.db.Column(self.db.String(128), unique=False)
            page = self.db.Column(self.db.Integer, unique=False)
            publishDate = self.db.Column(self.db.String(24), unique=False)
            publisher = self.db.Column(self.db.String(32), unique=False)
            description = self.db.Column(self.db.Text, unique=False)
            doubanScore = self.db.Column(self.db.Float, unique=False)
            doubanID = self.db.Column(self.db.String(24), unique=False)
            type = self.db.Column(
                self.db.Enum("马列主义、毛泽东思想、邓小平理论", "哲学、宗教", "社会科学总论", "政治、法律", "军事", "经济",
                             "文化、科学、教育、体育", "语言、文字", "文学", "艺术", "历史、地理", "自然科学总论",
                             "数理科学和化学", "天文学、地球科学", "生物科学", "医药、卫生", "农业科学", "工业技术",
                             "交通运输", "航空、航天", "环境科学、安全科学", "综合性图书"), unique=False)

            def __init__(self, isbn, title, originTitle, subtitle, author, page, publishDate, publisher, description,
                         doubanScore, doubanID, type):
                self.isbn = isbn
                self.title = title
                self.originTitle = originTitle
                self.subtitle = subtitle
                self.author = author
                self.page = page
                self.publishDate = publishDate
                self.publisher = publisher
                self.description = description
                self.doubanScore = doubanScore
                self.doubanID = doubanID
                self.type = type

        class Journal(self.db.Model):
            """日志模型"""
            id = self.db.Column(self.db.Integer, primary_key=True, autoincrement=True)
            title = self.db.Column(self.db.String(128), unique=False)
            firstParagraph = self.db.Column(self.db.Text, unique=False)
            content = self.db.Column(self.db.Text, unique=False)
            publishTime = self.db.Column(self.db.DateTime, unique=False)
            authorID = self.db.Column(self.db.Integer, unique=False)
            bookID = self.db.Column(self.db.Integer, unique=False)

            def __init__(self, title, firstParagraph, content, publishTime, authorID, bookID):
                self.title = title
                self.firstParagraph = firstParagraph
                self.content = content
                self.publishTime = publishTime
                self.authorID = authorID
                self.bookID = bookID

        class JournalComment(self.db.Model):
            """日志评论模型"""
            id = self.db.Column(self.db.Integer, primary_key=True, autoincrement=True)
            publishTime = self.db.Column(self.db.DateTime, unique=False)
            authorID = self.db.Column(self.db.Integer, unique=False)
            journalID = self.db.Column(self.db.Integer, unique=False)
            content = self.db.Column(self.db.Text, unique=False)
            isRead = self.db.Column(self.db.Boolean, nullable=False, default=False)

            def __init__(self, publishTime, authorID, journalID, content):
                self.publishTime = publishTime
                self.authorID = authorID
                self.journalID = journalID
                self.content = content

        class JournalLike(self.db.Model):
            """日志点赞模型"""
            authorID = self.db.Column(self.db.Integer, unique=False)
            journalID = self.db.Column(self.db.Integer, unique=False)
            __table_args__ = (self.db.PrimaryKeyConstraint('authorID', 'journalID'),)  # 让authorID和journalID作为联合主键
            publishTime = self.db.Column(self.db.DateTime, unique=False)

            def __init__(self, authorID, journalID, publishTime):
                self.authorID = authorID
                self.journalID = journalID
                self.publishTime = publishTime

        class Group(self.db.Model):
            """圈子模型"""
            id = self.db.Column(self.db.Integer, primary_key=True, autoincrement=True)
            name = self.db.Column(self.db.String(32), unique=True)
            founderID = self.db.Column(self.db.Integer, unique=False)
            description = self.db.Column(self.db.Text, unique=False)
            establishTime = self.db.Column(self.db.DateTime, unique=False)

            def __init__(self, name, founderID, description, establishTime):
                self.name = name
                self.founderID = founderID
                self.description = description
                self.establishTime = establishTime

        class GroupDiscussion(self.db.Model):
            """圈子讨论模型"""
            id = self.db.Column(self.db.Integer, primary_key=True, autoincrement=True)
            posterID = self.db.Column(self.db.Integer, unique=False)
            groupID = self.db.Column(self.db.Integer, unique=False)
            postTime = self.db.Column(self.db.DateTime, unique=False)
            title = self.db.Column(self.db.String(256), unique=False)
            content = self.db.Column(self.db.Text, unique=False)
            isRead = self.db.Column(self.db.Boolean, nullable=False, default=False)

            def __init__(self, posterID, groupID, postTime, title, content):
                self.posterID = posterID
                self.groupID = groupID
                self.postTime = postTime
                self.title = title
                self.content = content

        class GroupUser(self.db.Model):
            """圈子用户关系模型"""
            userID = self.db.Column(self.db.Integer, unique=False)
            groupID = self.db.Column(self.db.Integer, unique=False)
            __table_args__ = (self.db.PrimaryKeyConstraint('userID', 'groupID'),)  # 联合主键
            joinTime = self.db.Column(self.db.DateTime, unique=False)

            def __init__(self, userID, groupID, joinTime):
                self.userID = userID
                self.groupID = groupID
                self.joinTime = joinTime

        class GroupDiscussionReply(self.db.Model):
            """圈子讨论回复模型"""
            authorID = self.db.Column(self.db.Integer, unique=False)
            discussionID = self.db.Column(self.db.Integer, unique=False)
            replyTime = self.db.Column(self.db.DateTime, unique=False)
            __table_args__ = (self.db.PrimaryKeyConstraint('authorID', 'discussionID', 'replyTime'),)  # 联合主键
            content = self.db.Column(self.db.Text, unique=False)
            isRead = self.db.Column(self.db.Boolean, nullable=False, default=False)

            def __init__(self, authorID, discussionID, replyTime, content):
                self.authorID = authorID
                self.discussionID = discussionID
                self.replyTime = replyTime
                self.content = content

        class Error(self.db.Model):
            """错误信息模型"""
            errorCode = self.db.Column(self.db.Integer, primary_key=True, autoincrement=True)
            title = self.db.Column(self.db.String(128), unique=False)
            title_en = self.db.Column(self.db.String(128), unique=False)
            content = self.db.Column(self.db.Text, unique=False)
            publishTime = self.db.Column(self.db.DateTime, unique=False)
            authorID = self.db.Column(self.db.Integer, unique=False)
            referenceLink = self.db.Column(self.db.String(128), unique=False)

            def __init__(self, title, title_en, content, publishTime, authorID, referenceLink):
                self.title = title
                self.title_en = title_en
                self.content = content
                self.publishTime = publishTime
                self.authorID = authorID
                self.referenceLink = referenceLink

        class Chat(self.db.Model):
            """聊天消息模型"""
            id = self.db.Column(self.db.Integer, primary_key=True, autoincrement=True)
            senderID = self.db.Column(self.db.Integer, nullable=False)
            receiverID = self.db.Column(self.db.Integer, nullable=False)
            content = self.db.Column(self.db.Text, nullable=False)
            sendTime = self.db.Column(self.db.DateTime, nullable=False)
            isRead = self.db.Column(self.db.Boolean, nullable=False, default=False)

            def __init__(self, senderID, receiverID, content, sendTime):
                self.senderID = senderID
                self.receiverID = receiverID
                self.content = content
                self.sendTime = sendTime
