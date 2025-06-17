import os

import cv2

__doc__ = """
图像处理工具模块

该模块提供了一系列用于图像处理的工具函数，主要包括：
1. 获取图像尺寸
2. 图像裁剪（多种方式）
   - 指定尺寸裁剪
   - 按比例裁剪
   - 正方形裁剪

所有函数都使用OpenCV (cv2) 进行图像处理，支持常见的图像格式。
注意：大多数裁剪操作会直接修改原图像文件。
"""


from typing import Tuple

def getImageSize(filePath: str) -> Tuple[int, int]:
    """
    获取图像的尺寸（高度和宽度）

    Args:
        filePath: 图像文件的路径

    Returns:
        Tuple[int, int]: 包含图像尺寸的元组 (高度, 宽度)

    Raises:
        FileNotFoundError: 当指定的文件不存在时抛出
    """
    if not os.path.exists(filePath):
        raise FileNotFoundError(f"File not found: {filePath}")
    img = cv2.imread(filePath)
    return img.shape[0], img.shape[1]


def cropImage(filePath: str, width: int, height: int, hAlign: str = "center", vAlign: str = "center") -> bool:
    """
    按照指定尺寸裁剪图像

    该函数会根据指定的宽度、高度和对齐方式裁剪图像。
    裁剪后的图像会直接覆盖原图像文件。

    Args:
        filePath: 要裁剪的图像文件路径
        width: 裁剪后的目标宽度（像素）
        height: 裁剪后的目标高度（像素）
        hAlign: 水平对齐方式
            - "left": 左对齐
            - "center": 居中对齐（默认）
            - "right": 右对齐
        vAlign: 垂直对齐方式
            - "top": 顶部对齐
            - "center": 居中对齐（默认）
            - "bottom": 底部对齐

    Returns:
        bool: 裁剪操作的结果
            - True: 裁剪成功
            - False: 裁剪失败（当指定的宽度或高度大于原图时）

    Raises:
        ValueError: 当hAlign或vAlign参数值无效时抛出
        FileNotFoundError: 当指定的文件不存在时抛出
    """
    if not os.path.exists(filePath):
        raise FileNotFoundError(f"File not found: {filePath}")
    img = cv2.imread(filePath)
    originHeight, originWidth = img.shape[0], img.shape[1]
    if width > originWidth or height > originHeight:
        return False
    if hAlign == "left":
        widthRange = (0, width)
    elif hAlign == "center":
        widthRange = ((originWidth - width) // 2, (originWidth + width) // 2)
    elif hAlign == "right":
        widthRange = (originWidth - width, originWidth)
    else:
        raise ValueError("hAlign must be one of 'left', 'center', 'right'")
    if vAlign == "top":
        height_range = (0, height)
    elif vAlign == "center":
        height_range = ((originHeight - height) // 2, (originHeight + height) // 2)
    elif vAlign == "bottom":
        height_range = (originHeight - height, originHeight)
    else:
        raise ValueError("vAlign must be one of 'top', 'center', 'bottom'")
    img = img[height_range[0]:height_range[1], widthRange[0]:widthRange[1]]
    cv2.imwrite(filePath, img)
    return True


def cropImageByScale(filePath: str, width: int, height: int) -> bool:
    """
    按照指定宽高比例裁剪图像

    该函数会根据指定的宽高比例，在保持比例的同时进行最大尺寸的裁剪。
    裁剪后的图像会直接覆盖原图像文件。

    Args:
        filePath: 要裁剪的图像文件路径
        width: 目标宽高比中的宽度值
        height: 目标宽高比中的高度值

    Returns:
        bool: 裁剪操作的结果
            - True: 裁剪成功
            - False: 裁剪失败（当文件不存在时）

    Raises:
        FileNotFoundError: 当指定的文件不存在时抛出

    Note:
        该函数会保持原始图像的宽高比，并尽可能保留最大的图像区域。
        裁剪后的图像会居中显示。
    """
    if not os.path.exists(filePath):
        raise FileNotFoundError(f"File not found: {filePath}")
    img = cv2.imread(filePath)
    originHeight, originWidth = img.shape[0], img.shape[1]
    if originWidth / originHeight > width / height:
        newWidth = originHeight * width // height
        newHeight = originHeight
    else:
        newWidth = originWidth
        newHeight = originWidth * height // width
    img = img[(originHeight - newHeight) // 2:(originHeight + newHeight) // 2,
          (originWidth - newWidth) // 2:(originWidth + newWidth) // 2]
    cv2.imwrite(filePath, img)
    return True


def cropImageSquare(filePath: str) -> bool:
    """
    将图像裁剪为正方形

    该函数会将图像裁剪为正方形，取原图中心区域。
    裁剪后的图像会直接覆盖原图像文件。

    Args:
        filePath: 要裁剪的图像文件路径

    Returns:
        bool: 裁剪操作的结果
            - True: 裁剪成功
            - False: 裁剪失败（当文件不存在时）

    Raises:
        FileNotFoundError: 当指定的文件不存在时抛出

    Note:
        如果原图已经是正方形，则不会进行任何修改。
        裁剪时会取原图中心区域，确保重要内容不会被裁掉。
    """
    if not os.path.exists(filePath):
        raise FileNotFoundError(f"File not found: {filePath}")
    img = cv2.imread(filePath)
    originHeight, originWidth = img.shape[0], img.shape[1]
    if originWidth == originHeight:
        return True
    edgeLength = min(originWidth, originHeight)
    if originWidth > originHeight:
        newImg = img[:, (originWidth - edgeLength) // 2:(originWidth + edgeLength) // 2]
    else:
        newImg = img[(originHeight - edgeLength) // 2:(originHeight + edgeLength) // 2, :]
    cv2.imwrite(filePath, newImg)
    return True
