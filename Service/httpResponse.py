from flask import Flask, abort, render_template

from Service.File.File import FileMgr

__doc__ = """
自定义HTTP响应模块

该模块提供了自定义HTTP错误响应的功能，主要用于：
1. 自定义错误页面的展示
2. 处理不同类型的HTTP错误（404、418、500、503等）
3. 提供错误示例路由用于测试

每个错误处理函数都会：
- 从数据库获取错误信息
- 获取错误作者信息
- 获取相关图片资源
- 渲染自定义错误页面

错误页面包含：
- 错误代码
- 错误描述
- 作者信息
- 相关图片
"""


def customizeHttpResponse(app: Flask, fileMgr: FileMgr, db):
    """
    自定义HTTP响应处理函数

    该函数为Flask应用注册自定义的错误处理路由和处理器。
    每个错误处理器都会返回一个自定义的错误页面，包含详细的错误信息和相关资源。

    Args:
        app: Flask应用实例，用于注册路由和错误处理器
        fileMgr: 文件管理器实例，用于获取用户头像和错误图片
        db: 数据库实例，用于获取错误信息和用户信息

    Note:
        所有错误处理器都使用相同的模板（error.html）来渲染错误页面，
        但会根据不同的错误类型显示不同的错误信息和状态码。
    """

    @app.route("/errorSample/<int:errorCode>", methods=["GET"])
    def errorSample(errorCode):
        """
        错误示例路由，用于测试自定义错误页面

        该路由会触发指定错误码的HTTP错误，从而展示对应的错误页面。
        主要用于开发和测试阶段，验证错误页面的显示效果。

        Args:
            errorCode: 要触发的HTTP错误码，例如：
                - 404: 页面未找到
                - 418: 我是一个茶壶
                - 500: 服务器内部错误
                - 503: 服务不可用

        Returns:
            通过abort()触发对应的HTTP错误，然后由相应的错误处理器处理
        """
        abort(errorCode)  # 抛出异常，对应的异常将会触发

    @app.errorhandler(404)
    def page_not_found(error):
        """
        处理404错误（页面未找到）

        当用户访问不存在的页面时触发，返回自定义的404错误页面。

        Args:
            error: Flask错误对象，包含错误信息

        Returns:
            tuple: (渲染后的错误页面, 404状态码)
        """
        content = db.getError(error.code)
        author = db.getUser(content['authorID'])
        profilePhoto = fileMgr.getProfilePhotoPath(author['id'])
        errorImage = fileMgr.getErrorImagePath(error.code)
        return render_template('error.html', content=content, author=author, profilePhoto=profilePhoto,
                               errorCode=error.code, errorImage=errorImage), 404

    @app.errorhandler(418)
    def im_a_teapot(error):
        """
        处理418错误（我是一个茶壶）

        这是一个特殊的HTTP状态码，用于演示自定义错误页面。
        当服务器拒绝煮咖啡时触发（这是一个玩笑状态码）。

        Args:
            error: Flask错误对象，包含错误信息

        Returns:
            tuple: (渲染后的错误页面, 418状态码)
        """
        content = db.getError(error.code)
        author = db.getUser(content['authorID'])
        profilePhoto = fileMgr.getProfilePhotoPath(author['id'])
        errorImage = fileMgr.getErrorImagePath(error.code)
        return render_template('error.html', content=content, author=author, profilePhoto=profilePhoto,
                               errorCode=error.code, errorImage=errorImage), 418

    @app.errorhandler(500)
    def internal_server_error(error):
        """
        处理500错误（服务器内部错误）

        当服务器发生内部错误时触发，返回自定义的500错误页面。
        这通常表示服务器端代码出现了未处理的异常。

        Args:
            error: Flask错误对象，包含错误信息

        Returns:
            tuple: (渲染后的错误页面, 500状态码)
        """
        content = db.getError(error.code)
        author = db.getUser(content['authorID'])
        profilePhoto = fileMgr.getProfilePhotoPath(author['id'])
        errorImage = fileMgr.getErrorImagePath(error.code)
        return render_template('error.html', content=content, author=author, profilePhoto=profilePhoto,
                               errorCode=error.code, errorImage=errorImage), 500

    @app.errorhandler(503)
    def service_unavailable(error):
        """
        处理503错误（服务不可用）

        当服务器暂时无法处理请求时触发，返回自定义的503错误页面。
        这通常表示服务器正在进行维护或过载。

        Args:
            error: Flask错误对象，包含错误信息

        Returns:
            tuple: (渲染后的错误页面, 503状态码)
        """
        content = db.getError(error.code)
        author = db.getUser(content['authorID'])
        profilePhoto = fileMgr.getProfilePhotoPath(author['id'])
        errorImage = fileMgr.getErrorImagePath(error.code)
        return render_template('error.html', content=content, author=author, profilePhoto=profilePhoto,
                               errorCode=error.code, errorImage=errorImage), 503
