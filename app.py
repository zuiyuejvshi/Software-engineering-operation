import os
import random
from datetime import datetime
from flask import Flask, abort, render_template, url_for, request, redirect, session, flash, jsonify
from Service import Img, utils
from Service.DB.Operation import Database
from Service.File.File import FileMgr
from Service.Network import API, Mail
from Service.httpResponse import customizeHttpResponse

__doc__ = """
墨韵平台后端主应用

该模块实现了墨韵平台的所有主要功能，包括：
1. 用户管理
   - 用户注册和登录
   - 密码重置
   - 个人信息管理

2. 书评系统
   - 书评的发布和管理
   - 评论和点赞功能
   - 书评列表和详情展示

3. 书籍管理
   - 书籍信息的展示
   - 书籍信息的编辑（管理员功能）
   - 豆瓣图书信息集成

4. 圈子系统
   - 圈子的创建和管理
   - 讨论帖的发布和回复
   - 圈子成员管理

5. 搜索功能
   - 多类型搜索（用户、书籍、书评、圈子）
   - 搜索结果展示

6. 消息系统
   - 未读消息管理
   - 消息分类展示
   - 消息状态更新

所有功能都包含完整的权限控制和错误处理。
"""

# 创建全局变量：应用、服务
app = Flask(__name__,
            template_folder=(os.getcwd() + "/templates").replace("\\", "/"),
            static_folder=(os.getcwd() + "/static").replace("\\", "/"))  # app作为全局变量，并指定部分资源的路径
app.config.update(utils.getConfig('Flask'))  # 从配置文件中读取Flask配置

# 配置服务
api = API()  # 豆瓣API服务
mail = Mail()  # 邮件服务
db = Database(app)  # 数据库服务
fileMgr = FileMgr(workPath=os.getcwd())  # 文件管理服务
# 附加自定义的错误页面
customizeHttpResponse(app, fileMgr, db)

"""1.账号管理"""


@app.route("/", methods=["GET", "POST"])
def index():
    """
    欢迎页面和登录入口

    处理用户登录请求和页面访问：
    - GET: 显示登录页面
    - POST: 处理登录表单提交

    Returns:
        - 登录成功：重定向到首页
        - 登录失败：返回登录页面并显示错误信息
        - 已登录：直接重定向到首页
    """
    if request.method == "POST":  # 用户发起登录请求
        # 获取表单数据
        account = request.form.get("account")
        password = request.form.get("password")

        # 验证用户名和密码是否正确
        userID = db.checkLogin(account, password)
        if userID:
            # 如果验证成功，跳转到首页
            session["loginUser"] = db.getUser(userID)  # 记录登录用户信息
            session["loginUser"]["profilePhoto"] = fileMgr.getProfilePhotoPath(session["loginUser"]["id"],
                                                                               enableDefault=True)
            db.modifyUser(session["loginUser"]["id"],
                          lastLoginTime=datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S"))  # 更新登录时间
            flash("登录成功", "success")
            return redirect(url_for("home"))
        else:  # 如果验证失败，跳转回登录页面
            flash("用户名或密码错误", "error")
            return redirect(url_for("index"))
    else:  # 用户发起访问请求
        if session.get("loginUser"):  # 如果用户已经登录，跳转到首页
            return redirect(url_for("home"))
        return render_template("index.html")


@app.route("/register", methods=["POST"])
def register():
    """
    用户注册

    处理用户注册请求，验证必要信息并创建新用户。

    Returns:
        - 注册成功：重定向到登录页面
        - 注册失败：返回注册页面并显示错误信息

    Note:
        - 账号、密码、邮箱为必填项
        - 用户名不能重复
    """
    if request.method == "POST":
        # 获取表单数据
        account = request.form.get("account")
        password = request.form.get("password")
        email = request.form.get("email")
        telephone = request.form.get("telephone")
        selection = request.form.get("role")

        if not account or not password or not email:
            flash("账号、密码、邮箱是必须的", "warning")
            return redirect(url_for("index") + "#register")
        # 验证用户名和密码是否可用
        if db.getUserByAccount(account):
            flash("用户名已存在，请尝试登录或找回密码", "info")
            return redirect(url_for("index") + "#login")
        else:
            db.addUser(account=account, password=password, email=email, telephone=telephone,role=selection)
            flash("注册成功，请登录", "success")

            return redirect(url_for("index") + "#login")


@app.route("/sendCaptcha", methods=["POST"])
def sendCaptcha():
    """
    发送验证码

    向用户邮箱发送验证码，用于密码重置。

    Returns:
        - 发送成功：重定向到密码重置页面
        - 发送失败：返回错误信息

    Note:
        - 验证码有效期为10分钟
        - 需要用户已注册且邮箱正确
    """
    if request.method == "POST":
        account = request.form.get("account")
        user = db.getUserByAccount(account)
        if not user:
            flash("用户名不存在，请先注册", "info")
            return redirect(url_for("index") + "#register")
        email = user["email"]
        captcha = str(random.randint(100000, 999999))
        mail.sendCaptcha(email, captcha)
        session["captcha"] = captcha
        session["resetPasswdAccount"] = account
        flash("验证码已发送，请注意查收", "success")
        return redirect(url_for("index") + "#resetPasswd")


@app.route("/resetPasswd", methods=["POST", "GET"])
def resetPasswd():
    """
    重置密码

    验证用户输入的验证码并更新密码。

    Returns:
        - 重置成功：重定向到登录页面
        - 重置失败：返回错误信息

    Note:
        - 需要先发送验证码
        - 验证码必须正确
    """
    if request.method == "POST":
        account = session.get("resetPasswdAccount")
        captcha = request.form.get("captcha")
        password = request.form.get("password")
        if captcha != session.get("captcha"):
            flash("验证码错误", "warning")
            return redirect(url_for("index") + "#resetPasswd")
        else:
            db.modifyUserByAccount(account=account, password=password)
            flash("密码修改成功，请重新登录", "success")
            return redirect(url_for("index") + "#login")


@app.route("/logout", methods=["GET"])
def logout():
    """
    用户登出

    清除用户会话并重定向到登录页面。

    Returns:
        重定向到登录页面
    """
    if session.get("loginUser"):
        session.pop("loginUser")
        flash("您已成功退出账号", "success")
    return redirect(url_for("index"))


"""2.主页"""


@app.route("/home", methods=["GET"])
def home():
    """
    用户主页

    显示用户的个人信息、最近书评和未读消息。

    Returns:
        - 已登录：显示主页内容
        - 未登录：重定向到登录页面

    Note:
        - 显示最近5篇书评
        - 显示未读消息数量
    """
    if not session.get("loginUser"):
        flash("请先登录", "info")
        return redirect(url_for("index"))
    # 获取首页相关信息
    unreadMessageNum = db.getAllUnreadMessageNum(session.get("loginUser")['id'])
    journals = db.getAllJournalByAuthorID(session.get("loginUser")['id'], limit=5)
    unreadMessageNum = db.getAllUnreadMessageNum(session.get("loginUser")['id'])
    for journal in journals:
        journal["headerPath"] = fileMgr.getJournalHeaderPath(journal["id"])
    return render_template("home.html", loginUser=session.get("loginUser"), journals=journals,
                           unreadMessageNum=unreadMessageNum)


"""3.书评"""


@app.route("/journalMenu", methods=["GET"])
def journalMenu():
    """
    书评列表页面

    显示所有书评的列表。

    Returns:
        - 已登录：显示书评列表
        - 未登录：重定向到登录页面

    Note:
        - 显示书评作者信息
        - 按时间倒序排列
    """
    if not session.get("loginUser"):
        flash("请先登录", "info")
        return redirect(url_for("index"))
    # 获取书评列表
    journals = db.getAllJournal()
    for journal in journals:
        journal["account"] = db.getUser(journal["authorID"])["account"]
    return render_template("journalMenu.html", loginUser=session.get("loginUser"), journals=journals)


@app.route("/journal/<int:journalID>", methods=["GET", "POST"])
def journal(journalID: int):
    """
    书评详情页面

    显示单篇书评的详细内容，支持评论和点赞功能。

    Args:
        journalID: 书评ID

    Returns:
        - GET: 显示书评详情
        - POST: 处理评论或点赞请求

    Note:
        - 显示书评作者信息
        - 显示相关书籍信息
        - 支持评论和点赞功能
    """
    if request.method == "GET":  # 查看书评
        journal = db.getJournal(journalID)
        journalHeader = fileMgr.getJournalHeaderPath(journal["id"])
        author = db.getUser(journal["authorID"])
        book = db.getBook(journal["bookID"])
        bookCover = fileMgr.getBookCoverPath(book["id"])
        # 获取评论
        comments = db.getJournalComments(journalID)
        for comment in comments:
            authorInfo = db.getUser(comment["authorID"])
            comment["account"] = authorInfo["account"]
            comment["profilePhoto"] = fileMgr.getProfilePhotoPath(comment["authorID"])
        # 标记为已读
        if session.get("loginUser") and journal['authorID'] == session.get("loginUser")['id']:
            db.markAllJournalCommentAsRead(journalID)
        return render_template("journal.html", loginUser=session.get("loginUser"), author=author,
                               journal=journal, journalHeader=journalHeader,
                               book=book, bookCover=bookCover,
                               comments=comments)
    else:  # POST
        if not session.get("loginUser"):
            flash("请先登录", "info")
            return redirect(url_for("index"))

        data = dict(request.form)
        if "commentUserID" in data:  # 评论
            comment = data["comment"]
            authorID = int(data["commentUserID"])
            publishTime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            db.addJournalComment(journalID, comment, authorID, publishTime)
            authorProfilePhoto = fileMgr.getProfilePhotoPath(authorID, enableDefault=True)
            return jsonify({"account": session.get("loginUser")["account"],
                            "authorID": authorID, "authorProfilePhoto": authorProfilePhoto,
                            "publishTime": publishTime,
                            "comment": comment})
        elif "likeUserID" in data:  # 点赞
            authorID = data["likeUserID"]
            likeNum = db.getJournal(journalID)["likeNum"]
            if db.addJournalLike(journalID, authorID):
                return jsonify({"likeNum": likeNum + 1, "isLiked": False})
            else:
                return jsonify({"likeNum": likeNum, "isLiked": True})


@app.route("/writeJournal", methods=["GET", "POST"])
def createJournal():
    """
    创建书评

    处理书评的创建请求，支持上传书评封面图片。

    Returns:
        - GET: 显示创建书评页面
        - POST: 处理书评提交

    Note:
        - 需要选择相关书籍
        - 支持上传封面图片
        - 自动裁剪图片为5:2比例
    """
    if not session.get("loginUser"):
        flash("请先登录", "info")
        return redirect(url_for("index"))
    if request.method == "GET":  # 准备写书评
        books = db.getAllBook()
        return render_template("writeJournal.html", loginUser=session.get("loginUser"), books=books)
    else:  # 发表书评
        journalHeader = request.files.get("journalHeader")  # 书评封面
        title = request.form.get("title")
        content = request.form.get("content").split('\r\n')
        publishTime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        authorID = session.get("loginUser")["id"]
        bookID = int(request.form.get("bookID"))
        journalID = db.addJournal(title, content, publishTime, authorID, bookID)
        if journalHeader:  # 处理书评封面
            targetPath = fileMgr.generateJournalHeaderPath(journalID, abs=True)
            journalHeader.save(targetPath)
            Img.cropImageByScale(targetPath, 5, 2)  # 裁剪为'5：2'图片
        flash("发表成功", "success")
        return redirect(url_for("journal", journalID=journalID))  # 返回到新书评页


"""4. 用户"""


@app.route("/profile", endpoint="selfProfile", methods=["GET"])
def profile():
    """
    个人主页重定向

    将/profile请求重定向到当前登录用户的个人主页。

    Returns:
        重定向到用户个人主页
    """
    if not session.get("loginUser"):
        flash("请先登录", "info")
        return redirect(url_for("index"))
    return redirect(url_for("profile", userID=session.get("loginUser")['id']))


@app.route("/profile/<int:userID>", methods=["GET"])
def profile(userID):
    """
    用户个人主页

    显示指定用户的个人信息和书评列表。

    Args:
        userID: 用户ID

    Returns:
        - 用户存在：显示个人主页
        - 用户不存在：404错误页面

    Note:
        - 显示用户基本信息
        - 显示用户的所有书评
        - 显示用户头像
    """
    if not session.get("loginUser"):
        flash("请先登录", "info")
        return redirect(url_for("index"))
    user = db.getUser(userID)
    if not user:  # 转到404
        abort(404)
    journals = db.getAllJournalByAuthorID(userID)
    profilePhoto = fileMgr.getProfilePhotoPath(userID)
    return render_template("profile.html", loginUser=session.get("loginUser"), user=user,
                           journals=journals, profilePhoto=profilePhoto)


@app.route("/editProfile", methods=["GET", "POST"])
def editProfile():
    """
    编辑个人资料

    处理用户个人资料的修改请求，支持更新头像。

    Returns:
        - GET: 显示编辑页面
        - POST: 处理修改请求

    Note:
        - 可以修改基本信息
        - 支持上传新头像
        - 自动裁剪头像为正方形
    """
    if not session.get("loginUser"):
        flash("请先登录", "info")
        return redirect(url_for("index"))
    if request.method == "POST":
        userID = session.get("loginUser")['id']
        account = request.form.get("account")
        signature = request.form.get("signature")
        email = request.form.get("email")
        telephone = request.form.get("telephone")
        db.modifyUser(userID, account=account, signature=signature, email=email, telephone=telephone)
        profilePhoto = request.files.get("profilePhoto")
        if profilePhoto:
            photoPath = fileMgr.getProfilePhotoPath(userID, abs=True, enableDefault=False)
            if not photoPath:  # 之前没设置过头像，使用的应该是默认头像
                photoPath = fileMgr.generateProfilePhotoPath(userID, abs=True)
            fileMgr.deleteProfilePhoto(userID)  # 删除原有头像
            profilePhoto.save(photoPath)  # 保存新头像
            Img.cropImageSquare(photoPath)  # 裁剪成正方形
        flash("修改成功", "success")
        session["loginUser"] = db.getUser(userID)  # 更新session中的用户信息
        session["loginUser"]["profilePhoto"] = fileMgr.getProfilePhotoPath(userID, enableDefault=True)
        return redirect(f"/profile/{userID}")
    else:
        profilePhoto = fileMgr.getProfilePhotoPath(session.get("loginUser")["id"])
        return render_template("editProfile.html", loginUser=session.get("loginUser"), profilePhoto=profilePhoto)


"""5. 书籍相关"""


@app.route("/bookMenu", methods=["GET"])
def bookMenu():
    """
    书籍列表页面

    显示所有书籍的列表。

    Returns:
        - 已登录：显示书籍列表
        - 未登录：重定向到登录页面

    Note:
        - 显示书籍封面
        - 显示基本信息
    """
    if not session.get("loginUser"):
        flash("请先登录", "info")
        return redirect(url_for("index"))
    books = db.getAllBook()
    for book in books:
        book["bookCover"] = fileMgr.getBookCoverPath(book["id"], enableDefault=True)
    return render_template("bookMenu.html", loginUser=session.get("loginUser"), books=books)


@app.route("/book/<int:bookID>", methods=["GET"])
def book(bookID: int):
    """
    书籍详情页面

    显示单本书籍的详细信息。

    Args:
        bookID: 书籍ID

    Returns:
        - 已登录：显示书籍详情
        - 未登录：重定向到登录页面

    Note:
        - 显示书籍封面
        - 显示完整信息
        - 显示豆瓣评分
    """
    if not session.get("loginUser"):
        flash("请先登录", "info")
        return redirect(url_for("index"))
    book = db.getBook(bookID)
    bookCover = fileMgr.getBookCoverPath(bookID, enableDefault=True)
    return render_template("book.html", loginUser=session.get("loginUser"), book=book, bookCover=bookCover)


@app.route("/editBook/<int:bookID>", methods=["GET", "POST"])
def editBook(bookID: int):
    """
    编辑书籍信息

    处理书籍信息的修改请求（仅管理员可用）。

    Args:
        bookID: 书籍ID

    Returns:
        - GET: 显示编辑页面
        - POST: 处理修改请求

    Note:
        - 需要管理员权限
        - 自动更新豆瓣评分
        - 支持修改所有信息
    """
    if not session.get("loginUser"):
        flash("请先登录", "info")
        return redirect(url_for("index"))
    if session.get("loginUser").get("role") != "admin":
        flash("您没有权限", "info")
        return redirect(url_for("home"))
    # 加载修改书籍的界面    
    if request.method == "GET":
        book = db.getBook(bookID)
        bookCover = fileMgr.getBookCoverPath(bookID, enableDefault=True)
        return render_template("editBook.html", loginUser=session.get("loginUser"), book=book, bookCover=bookCover)
    elif request.method == "POST":
        title = request.form.get("title")
        originTitle = request.form.get("originTitle")
        subtitle = request.form.get("subtitle")
        author = request.form.get("author")
        page = request.form.get("page")
        publisher = request.form.get("publisher")
        publishDate = request.form.get("publishDate")
        doubanID = request.form.get("doubanID")
        type = request.form.get("type")
        isbn = request.form.get("isbn")
        description = request.form.get("description")
        doubanScore = api.getBookInfo_Douban(doubanID)['doubanScore']
        if db.modifyBook(bookID,
                         isbn=isbn,
                         title=title,
                         originTitle=originTitle,
                         subtitle=subtitle,
                         author=author,
                         page=page,
                         publishDate=publishDate,
                         publisher=publisher,
                         description=description,
                         doubanScore=doubanScore,
                         doubanID=doubanID,
                         type=type):
            flash("修改成功", "success")
        else:
            flash("修改失败，请联系开发者修改", "error")
        return redirect(url_for("book", bookID=bookID))


"""6. 圈子相关"""


@app.route("/group", methods=["GET"])
def selfGroup():
    """
    我的圈子重定向

    将/group请求重定向到圈子列表页面。

    Returns:
        重定向到圈子列表页面
    """
    return redirect(url_for("groupMenu"))


@app.route("/groupMenu", methods=["GET"])
def groupMenu():
    """
    圈子列表页面

    显示所有圈子的列表。

    Returns:
        - 已登录：显示圈子列表
        - 未登录：重定向到登录页面

    Note:
        - 显示圈子图标
        - 显示成员数量
        - 显示讨论数量
    """
    if not session.get("loginUser"):
        flash("请先登录", "info")
        return redirect(url_for("index"))
    groups = db.getAllGroup()
    for group in groups:
        group["groupIcon"] = fileMgr.getGroupIconPath(group["id"], enableDefault=True)
        group["userNum"] = db.getGroupUserNum(group["id"])
        group["discussionNum"] = db.getGroupDiscussionNum(group["id"])
    return render_template("groupMenu.html", loginUser=session.get("loginUser"), groups=groups)


@app.route("/group/<int:groupID>", methods=["GET"])
def group(groupID: int):
    """
    圈子详情页面

    显示单个圈子的详细信息和讨论列表。

    Args:
        groupID: 圈子ID

    Returns:
        - 已登录：显示圈子详情
        - 未登录：重定向到登录页面

    Note:
        - 显示圈子基本信息
        - 显示讨论列表
        - 显示最新回复
        - 自动标记已读
    """
    if not session.get("loginUser"):
        flash("请先登录", "info")
        return redirect(url_for("index"))
    group = db.getGroup(groupID)
    group['account'] = db.getUser(group['founderID'])['account']
    if session.get("loginUser")["id"] == group['founderID']:
        db.markAllDiscussionAsRead(groupID)
    discussionsInfo = db.getGroupAllDiscussion(groupID)
    for discussion in discussionsInfo:
        discussion["account"] = db.getUser(discussion["posterID"])["account"]
        discussion["repliesNum"] = db.getGroupDiscussionRepliesNum(discussion["id"])
    group["groupIcon"] = fileMgr.getGroupIconPath(groupID, enableDefault=True)
    replies = db.getGroupReplies(groupID, limit=5)
    for reply in replies:
        reply["account"] = db.getUser(reply["authorID"])["account"]
        reply["profilePhoto"] = fileMgr.getProfilePhotoPath(reply["authorID"], enableDefault=True)
    return render_template("group.html",
                           loginUser=session.get("loginUser"),
                           group=group,
                           discussions=discussionsInfo, replies=replies)


@app.route("/editGroup/<int:groupID>", methods=["GET", "POST"])
def editGroup(groupID: int):
    """
    编辑圈子信息

    处理圈子信息的修改请求（仅圈主可用）。

    Args:
        groupID: 圈子ID

    Returns:
        - GET: 显示编辑页面
        - POST: 处理修改请求

    Note:
        - 需要圈主权限
        - 支持修改基本信息
        - 支持更换圈子图标
        - 支持管理讨论和成员
    """
    if not session.get("loginUser"):
        flash("请先登录", "info")
        return redirect(url_for("index"))
    group = db.getGroup(groupID)  # group信息
    group['account'] = db.getUser(group['founderID'])['account']
    group["groupIcon"] = fileMgr.getGroupIconPath(groupID, enableDefault=True)

    if session.get("loginUser").get("id") != group['founderID']:
        flash("您没有权限", "info")
        return redirect(url_for("home"))
    if request.method == "GET":
        discussions = db.getGroupAllDiscussion(groupID)  # discussion信息
        for discussion in discussions:
            discussion["account"] = db.getUser(discussion["posterID"])["account"]
            discussion["repliesNum"] = db.getGroupDiscussionRepliesNum(discussion["id"])
        groupUsers = db.getAllGroupUser(groupID)  # groupUser列表
        for user in groupUsers:
            user["account"] = db.getUser(user["userID"])["account"]
            user['profilePhoto'] = fileMgr.getProfilePhotoPath(user['userID'], enableDefault=True)
        return render_template("editGroup.html", loginUser=session.get("loginUser"), discussions=discussions,
                               group=group, groupUsers=groupUsers)
    else:
        data = dict(request.form)
        if data['operation'] == 'deleteDiscussion':
            db.deleteGroupDiscussion(int(data['discussionID']))
            flash("删除成功", "success")
            return jsonify({'status': 'success'})
        elif data['operation'] == 'editGroupInfo':
            name, description = data['groupName'], data['groupDescription']
            icon = request.files.get("groupIcon")
            db.modifyGroup(groupID, name=name, description=description)
            if icon:
                targetPath = fileMgr.generateGroupIconPath(groupID, abs=True)
                fileMgr.deleteGroupIcon(targetPath)
                icon.save(targetPath)
                Img.cropImageSquare(targetPath)
            return redirect(url_for("group", groupID=groupID))


@app.route("/createGroup", methods=["GET", "POST"])
def createGroup():
    """
    创建圈子

    处理新圈子的创建请求。

    Returns:
        - GET: 显示创建页面
        - POST: 处理创建请求

    Note:
        - 需要设置圈子名称和描述
        - 支持上传圈子图标
        - 自动裁剪图标为正方形
    """
    if not session.get("loginUser"):
        flash("请先登录", "info")
        return redirect(url_for("index"))
    if request.method == "GET":
        return render_template("createGroup.html", loginUser=session.get("loginUser"))
    else:
        groupIcon = request.files.get("groupIcon")
        name = request.form.get("name")
        description = request.form.get("description")
        founderID = session.get("loginUser")["id"]
        establishTime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        groupID = db.addGroup(name, description, founderID, establishTime)
        if groupIcon:
            targetPath = fileMgr.generateGroupIconPath(groupID, abs=True)
            groupIcon.save(targetPath)
            Img.cropImageSquare(targetPath)  # 裁剪为正方形
            flash("创建成功", "success")
        return redirect(url_for("group", groupID=groupID))


"""7. 圈子-讨论相关"""


@app.route("/discussion/<int:discussionID>", methods=["GET", "POST"])
def discussion(discussionID: int):
    """
    讨论详情页面

    显示单个讨论的详细内容和回复列表。

    Args:
        discussionID: 讨论ID

    Returns:
        - GET: 显示讨论详情
        - POST: 处理回复请求

    Note:
        - 显示讨论内容
        - 显示回复列表
        - 支持发表回复
        - 自动标记已读
    """
    if not session.get("loginUser"):
        flash("请先登录", "info")
        return redirect(url_for("index"))
    if request.method == "GET":  # 查看帖子
        discussion = db.getGroupDiscussion(discussionID)
        author = db.getUser(discussion["posterID"])
        discussionReplies = db.getGroupDiscussionReplies(discussionID)
        if session.get("loginUser")["id"] == discussion["posterID"]:
            db.markAllDiscussionReplyAsRead(discussionID)
        for reply in discussionReplies:
            reply["account"] = db.getUser(reply["authorID"])["account"]
            reply["profilePhoto"] = fileMgr.getProfilePhotoPath(reply["authorID"], enableDefault=True)
        return render_template("discussion.html", loginUser=session.get("loginUser"),
                               discussion=discussion, author=author, discussionReplies=discussionReplies)
    elif request.method == "POST":  # 发表回帖
        data = dict(request.form)
        replyUserID = int(data['replyUserID'])
        replyContent = data['replyContent']
        replyTime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.addGroupDiscussionReply(discussionID, replyUserID, replyContent, replyTime)
        authorProfilePhoto = fileMgr.getProfilePhotoPath(replyUserID, enableDefault=True)
        return jsonify({'account': session.get("loginUser")['account'],
                        'authorID': replyUserID, 'authorProfilePhoto': authorProfilePhoto,
                        'replyTime': replyTime, 'replyContent': replyContent})


@app.route("/writeDiscussion/<int:groupID>", methods=["GET", "POST"])
def writeDiscussion(groupID: int):
    """
    创建讨论

    处理新讨论的创建请求。

    Args:
        groupID: 圈子ID

    Returns:
        - GET: 显示创建页面
        - POST: 处理创建请求

    Note:
        - 需要设置标题和内容
        - 自动记录发帖时间
        - 自动关联到指定圈子
    """
    if not session.get("loginUser"):
        flash("请先登录", "info")
        return redirect(url_for("index"))
    if request.method == "GET":
        group = db.getGroup(groupID)
        return render_template("writeDiscussion.html", loginUser=session.get("loginUser"), group=group)
    else:  # 发表帖子
        title = request.form.get("title")
        content = request.form.get("content")
        posterID = session.get("loginUser")["id"]
        postTime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        id = db.addGroupDiscussion(posterID, groupID, postTime, title, content)
        flash("发表成功", "success")
        return redirect(url_for("discussion", discussionID=id))


"""8. 搜索相关"""


@app.route("/search", methods=["GET"])
def search():
    """
    搜索功能

    支持多种类型的搜索，包括用户、书籍、书评和圈子。

    Returns:
        搜索结果页面

    Note:
        - 支持多种搜索类型
        - 显示搜索耗时
        - 支持综合搜索
        - 显示相关图片
    """
    if not session.get("loginUser"):
        flash("请先登录", "info")
        return redirect(url_for("index"))

    searchStartTime = datetime.now()
    searchType = request.args.get("type")
    keyword = request.args.get("keyword")

    if searchType == "journal":
        results = db.searchJournal(keyword)
        for i in range(len(results)):
            results[i]["header"] = fileMgr.getJournalHeaderPath(results[i]["id"], enableDefault=True)
            results[i]["searchType"] = "journal"
    elif searchType == "book":
        results = db.searchBook(keyword)
        for i in range(len(results)):
            results[i]["bookCover"] = fileMgr.getBookCoverPath(results[i]["id"], enableDefault=True)
            results[i]["searchType"] = "book"
    elif searchType == "group":
        results = db.searchGroup(keyword)
        for i in range(len(results)):
            results[i]["groupIcon"] = fileMgr.getGroupIconPath(results[i]["id"], enableDefault=True)
            results[i]["founder"] = db.getUser(results[i]["founderID"])["account"]
            results[i]["searchType"] = "group"
    elif searchType == "user":
        results = db.searchUser(keyword)
        for i in range(len(results)):
            results[i]["profilePhoto"] = fileMgr.getProfilePhotoPath(results[i]["id"], enableDefault=True)
            results[i]["searchType"] = "user"
    elif searchType == "all":
        users = db.searchUser(keyword)
        for i in range(len(users)):
            users[i]["profilePhoto"] = fileMgr.getProfilePhotoPath(users[i]["id"], enableDefault=True)
            users[i]["searchType"] = "user"
        groups = db.searchGroup(keyword)
        for i in range(len(groups)):
            groups[i]["groupIcon"] = fileMgr.getGroupIconPath(groups[i]["id"], enableDefault=True)
            groups[i]["founder"] = db.getUser(groups[i]["founderID"])["account"]
            groups[i]["searchType"] = "group"
        books = db.searchBook(keyword)
        for i in range(len(books)):
            books[i]["bookCover"] = fileMgr.getBookCoverPath(books[i]["id"], enableDefault=True)
            books[i]["searchType"] = "book"
        journals = db.searchJournal(keyword)
        for i in range(len(journals)):
            journals[i]["header"] = fileMgr.getJournalHeaderPath(journals[i]["id"], enableDefault=True)
            journals[i]["searchType"] = "journal"
        results = users + groups + books + journals

    else:
        abort(404)
        return
    costTime = (datetime.now() - searchStartTime).total_seconds()
    return render_template("search.html", loginUser=session.get("loginUser"), keyword=keyword, results=results,
                           costTime=costTime, searchType=searchType)


"""9.消息中心"""


@app.route("/message", methods=["GET"])
def message():
    """
    消息中心

    显示用户的所有未读消息，按类型分类。

    Returns:
        - 已登录：显示消息列表
        - 未登录：重定向到登录页面

    Note:
        - 按消息类型分类显示
        - 显示发送者信息
        - 显示相关图片
        - 支持标记已读
    """
    if not session.get("loginUser"):
        flash("请先登录", "info")
        return redirect(url_for("index"))
    # 将所有消息按照ID整理为字典
    messages = db.getAllUnreadMessage(userID=session.get("loginUser").get("id"))
    journalIDList = list(set(i['journalID'] for i in messages['journalComment']))
    groupIDList = list(set(i['groupID'] for i in messages['groupDiscussion']))
    discussionIDList = list(set(i['discussionID'] for i in messages['discussionReply']))
    chatIDList = list(set(i['senderID'] for i in messages['chat']))
    journalIDList.sort()
    groupIDList.sort()
    discussionIDList.sort()
    chatIDList.sort()
    journals, journalsInfo, groups, groupsInfo, discussions, discussionsInfo, chats = {}, {}, {}, {}, {}, {}, {}
    for journalID in journalIDList:
        journals[journalID] = [i for i in messages['journalComment'] if i['journalID'] == journalID]
        journalsInfo[journalID] = db.getJournal(journalID)
    for groupID in groupIDList:
        groups[groupID] = [i for i in messages['groupDiscussion'] if i['groupID'] == groupID]
        groupsInfo[groupID] = db.getGroup(groupID)
    for discussionID in discussionIDList:
        discussions[discussionID] = [i for i in messages['discussionReply'] if i['discussionID'] == discussionID]
        discussionsInfo[discussionID] = db.getGroupDiscussion(discussionID)
    for senderID in chatIDList:
        chats[senderID] = [i for i in messages['chat'] if i['senderID'] == senderID]
    return render_template("message.html", loginUser=session.get("loginUser"), chats=chats,
                           journals=journals, journalInfo=journalsInfo,
                           groups=groups, groupInfo=groupsInfo,
                           discussions=discussions, discussionInfo=discussionsInfo)


if __name__ == "__main__":
    app.run(port=utils.getConfig("Flask", "Port"),
            host="0.0.0.0")
