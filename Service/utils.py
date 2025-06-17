from datetime import datetime, timedelta
import os
import yaml
from typing import Union

__doc__ = """
工具函数模块

该模块提供了系统通用工具函数，主要包括：
1. 配置管理
   - 读取配置文件（支持自定义配置和默认配置）
   - 支持分类和键值对配置项
   - 支持多种配置数据类型

2. 时间处理
   - 处理服务器和客户端时区差异
   - 支持多种时间格式输出
   - 支持不同地区的时区设置
"""

def getConfig(category: str = None, key: str = None) -> Union[dict, str, int]:
    """
    获取配置文件中的配置项

    优先读取myConfig.yaml文件，如果不存在则读取config.yaml文件。
    支持获取整个配置、特定类别的配置或特定键值的配置。

    Args:
        category: 配置项类别，如果为None则返回整个配置
        key: 配置项键名，如果为None则返回整个类别的配置

    Returns:
        Union[dict, str, int]: 配置值
            - 如果category和key都为None，返回整个配置字典
            - 如果只有key为None，返回指定类别的配置字典
            - 否则返回指定类别和键名的具体配置值

    Note:
        - 配置文件使用YAML格式
        - 支持UTF-8编码
        - 使用yaml.FullLoader加载器以支持所有YAML特性
    """
    if os.path.exists(os.path.join(os.getcwd(), "myConfig.yaml")):
        with open("myConfig.yaml", "r", encoding="utf-8") as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
    else:
        with open("config.yaml", "r", encoding="utf-8") as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
    if category is None or category not in config:
        return config
    else:
        if key is None or key not in config[category]:
            return config[category]
        else:
            return config[category][key]


class Time:
    """
    时间处理类

    该类用于处理服务器和客户端之间的时区差异，确保时间显示的一致性。
    支持不同地区的时区设置，并提供多种时间格式的输出选项。

    Attributes:
        _host_time_zone: 服务器时区（UTC+0）
        _client_time_zone: 客户端时区配置
            - zh-CN: 中国时区（UTC+8）
    """

    _host_time_zone = 0  # UTC+0
    _client_time_zone = {'zh-CN': 8}  # UTC+8，东8区

    @classmethod
    def getClientNow(cls, region: str = "zh-CN", time_format: str = "datetime") -> str:
        """
        获取客户端当前时间

        根据指定的地区和格式返回当前时间。时间会根据客户端时区进行转换。

        Args:
            region: 地区代码，默认为"zh-CN"
            time_format: 时间格式，可选值：
                - "datetime": 返回完整日期时间（YYYY-MM-DD HH:MM:SS）
                - "date": 仅返回日期（YYYY-MM-DD）
                - "time": 仅返回时间（HH:MM:SS）

        Returns:
            str: 格式化后的时间字符串

        Raises:
            Exception: 当time_format参数无效时抛出异常

        Note:
            - 时间基于服务器UTC时间进行转换
            - 自动处理时区差异
            - 默认使用中国时区（UTC+8）
        """
        host_now = datetime.utcnow()  # 服务器时间
        client_now = host_now + timedelta(hours=cls._client_time_zone[region])  # 客户端时间
        if time_format == "datetime":
            return client_now.now().strftime("%Y-%m-%d %H:%M:%S")
        elif time_format == "date":
            return client_now.now().strftime("%Y-%m-%d")
        elif time_format == "time":
            return client_now.now().strftime("%H:%M:%S")
        else:
            raise Exception("Invalid format")
