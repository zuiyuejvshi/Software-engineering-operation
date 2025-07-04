__doc__ = """数据库提取服务模块

该模块提供了从数据库对象中提取结构化数据的函数集合。
所有函数都接收数据库模型对象作为输入，并返回包含提取数据的字典。
这些函数主要用于将数据库对象转换为前端可用的数据格式。
"""


def extractUser(user, withPassword=False):
    """
    从用户对象中提取用户信息并转换为字典格式

    Args:
        user: 用户数据库模型对象
        withPassword: 布尔值，是否在返回数据中包含密码字段
            - True: 返回包含密码的完整用户信息
            - False: 返回不包含密码的用户信息（默认）

    Returns:
        dict: 包含用户信息的字典，字段包括：
            - id: 用户ID
            - account: 用户账号
            - password: 用户密码（仅当withPassword=True时返回）
            - signature: 用户签名
            - email: 用户邮箱
            - telephone: 用户电话
            - role: 用户角色
    """
    if withPassword:
        return {"id": user.id,
                "account": user.account,
                "password": user.password,
                "signature": user.signature,
                "email": user.email,
                "telephone": user.telephone,
                "role": user.role}
    else:
        return {"id": user.id,
                "account": user.account,
                "signature": user.signature,
                "email": user.email,
                "telephone": user.telephone,
                "role": user.role}


def extractJournal(journal, likeNum: int, commentNum: int):
    """
    从日志对象中提取日志信息并转换为字典格式

    Args:
        journal: 日志数据库模型对象
        likeNum: 整数，该日志获得的点赞数
        commentNum: 整数，该日志获得的评论数

    Returns:
        dict: 包含日志信息的字典，字段包括：
            - id: 日志ID
            - title: 日志标题
            - firstParagraph: 日志第一段内容
            - content: 日志内容（按行分割的列表）
            - publishTime: 发布时间
            - authorID: 作者ID
            - bookID: 相关书籍ID
            - likeNum: 点赞数
            - commentNum: 评论数
    """
    return {"id": journal.id,
            "title": journal.title,
            "firstParagraph": journal.firstParagraph,
            "content": journal.content.split("\n"),
            "publishTime": journal.publishTime,
            "authorID": journal.authorID,
            "bookID": journal.bookID,
            "likeNum": likeNum,
            "commentNum": commentNum}


def extractJournalComment(comment):
    """
    从日志评论对象中提取评论信息并转换为字典格式

    Args:
        comment: 日志评论数据库模型对象

    Returns:
        dict: 包含评论信息的字典，字段包括：
            - id: 评论ID
            - journalID: 所属日志ID
            - authorID: 评论作者ID
            - content: 评论内容
            - publishTime: 发布时间
            - isRead: 是否已读
    """
    return {"id": comment.id,
            "journalID": comment.journalID,
            "authorID": comment.authorID,
            "content": comment.content,
            "publishTime": comment.publishTime,
            "isRead": comment.isRead}


def extractBook(book) -> dict:
    """
    从书籍对象中提取书籍信息并转换为字典格式

    Args:
        book: 书籍数据库模型对象

    Returns:
        dict: 包含书籍信息的字典，字段包括：
            - id: 书籍ID
            - isbn: ISBN号
            - title: 书籍标题
            - originTitle: 原始标题
            - subtitle: 副标题
            - author: 作者
            - page: 页数
            - publishDate: 出版日期
            - publisher: 出版社
            - description: 描述
            - doubanScore: 豆瓣评分
            - doubanID: 豆瓣ID
            - type: 书籍类型
    """
    return {"id": book.id,
            "isbn": book.isbn,
            "title": book.title,
            "originTitle": book.originTitle,
            "subtitle": book.subtitle,
            "author": book.author,
            "page": book.page,
            "publishDate": book.publishDate,
            "publisher": book.publisher,
            "description": book.description,
            "doubanScore": book.doubanScore,
            "doubanID": book.doubanID,
            "type": book.type}


def extractGroup(group) -> dict:
    """
    从圈子对象中提取圈子信息并转换为字典格式

    Args:
        group: 圈子数据库模型对象

    Returns:
        dict: 包含圈子信息的字典，字段包括：
            - id: 圈子ID
            - name: 圈子名称
            - description: 圈子描述
            - establishTime: 建立时间
            - founderID: 创建者ID
    """
    return {"id": group.id,
            "name": group.name,
            "description": group.description,
            "establishTime": group.establishTime,
            "founderID": group.founderID}


def extractGroupUser(groupUser) -> dict:
    """
    从圈子用户关系对象中提取信息并转换为字典格式

    Args:
        groupUser: 圈子用户关系数据库模型对象

    Returns:
        dict: 包含圈子用户关系信息的字典，字段包括：
            - userID: 用户ID
            - groupID: 圈子ID
            - joinTime: 加入时间
    """
    return {"userID": groupUser.userID,
            "groupID": groupUser.groupID,
            "joinTime": groupUser.joinTime}


def extractGroupDiscussion(groupDiscussion) -> dict:
    """
    从圈子讨论对象中提取讨论信息并转换为字典格式

    Args:
        groupDiscussion: 圈子讨论数据库模型对象

    Returns:
        dict: 包含讨论信息的字典，字段包括：
            - id: 讨论ID
            - groupID: 所属圈子ID
            - posterID: 发布者ID
            - postTime: 发布时间
            - title: 讨论标题
            - content: 讨论内容
            - isRead: 是否已读
    """
    return {"id": groupDiscussion.id,
            "groupID": groupDiscussion.groupID,
            "posterID": groupDiscussion.posterID,
            "postTime": groupDiscussion.postTime,
            "title": groupDiscussion.title,
            "content": groupDiscussion.content,
            "isRead": groupDiscussion.isRead}


def extractGroupDiscussionReply(reply) -> dict:
    """
    从圈子讨论回复对象中提取回复信息并转换为字典格式

    Args:
        reply: 圈子讨论回复数据库模型对象

    Returns:
        dict: 包含回复信息的字典，字段包括：
            - authorID: 回复作者ID
            - discussionID: 所属讨论ID
            - replyTime: 回复时间
            - content: 回复内容
            - isRead: 是否已读
    """
    return {"authorID": reply.authorID,
            "discussionID": reply.discussionID,
            "replyTime": reply.replyTime,
            "content": reply.content,
            "isRead": reply.isRead}


def extractError(error) -> dict:
    """
    从错误对象中提取错误信息并转换为字典格式

    Args:
        error: 错误数据库模型对象

    Returns:
        dict: 包含错误信息的字典，字段包括：
            - errorCode: 错误代码
            - title: 错误标题
            - title_en: 英文错误标题
            - content: 错误内容
            - publishTime: 发布时间
            - authorID: 作者ID
            - referenceLink: 参考链接
    """
    return {"errorCode": error.errorCode,
            "title": error.title,
            "title_en": error.title_en,
            "content": error.content,
            "publishTime": error.publishTime,
            "authorID": error.authorID,
            "referenceLink": error.referenceLink}


def extractChat(char) -> dict:
    """
    从聊天对象中提取聊天信息并转换为字典格式

    Args:
        char: 聊天数据库模型对象

    Returns:
        dict: 包含聊天信息的字典，字段包括：
            - id: 聊天ID
            - senderID: 发送者ID
            - receiverID: 接收者ID
            - content: 聊天内容
            - sendTime: 发送时间
            - isRead: 是否已读
    """
    return {"id": char.id,
            "senderID": char.senderID,
            "receiverID": char.receiverID,
            "content": char.content,
            "sendTime": char.sendTime,
            "isRead": char.isRead}
