import base64
import io
import logging
import os
import shutil
import sys
import uuid
from PIL import Image
import urllib.request
from scripts.handle_exception import HandleException
from pathlib import Path


class Utils:

    def __init__(self, logging: logging.Logger):
        self.logging = logging
        self.handle_exception = HandleException(logging)

    def get_file_name(self, file_path):
        return os.path.basename(file_path)

    # 图片转为base64
    def image_to_base64(self, image_path):
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")
        except Exception as e:
            self.logging.error(f"图片解析失败: {e}")
            return None

    # url图片转为base64
    def image_url_to_base64(self, image_url):
        try:
            with urllib.request.urlopen(image_url) as url:
                image = url.read()
                return base64.b64encode(image).decode()
        except Exception:
            return None

    # url图片转为PIL.Image
    def image_url_to_image(self, image_url):
        try:
            # 从URL获取图像数据
            with urllib.request.urlopen(image_url) as url:
                image = url.read()
                # 读取图像数据并转换为Image格式
                img = Image.open(io.BytesIO(image))
                return img
        except Exception as e:
            self.logging.error(f"图片解析失败: {e}")
            return None

    # 获取合适的图片大小
    def image_size(self, input_image):
        # image = Image.open(input_image)

        width, height = input_image.size
        resize_ratio = width / height

        resize_width = 0
        resize_height = 0
        if resize_ratio < 1:
            resize_width = 512
            resize_height = int(512 * height / width)
        elif resize_ratio == 1:
            resize_width = 512
            resize_height = 512
        else:
            resize_height = 512
            resize_width = int(512 * width / height)

        return resize_width, resize_height

    # base64保存图片
    def save_image(self, base64_str, folder):
        try:
            if base64_str == "":
                return None
            image_data = base64.b64decode(base64_str)
            file_name = f"{uuid.uuid4().hex[:20]}.jpg"
            save_image_path = os.path.join(folder, file_name)
            with open(save_image_path, "wb") as img_file:
                img_file.write(image_data)
            return file_name
        except Exception as e:
            self.logging.error(f"Failed to save image: {e}")
            return None

    # 批量调整图片大小
    def batch_adjust_image_size(self, image_folder_path, target_size):
        try:
            files = self.filter_files(image_folder_path,
                                      [".png", ".jpg", ".jpeg", ".tif"])
            for file in files:
                img = self.handle_exception.image_error_handler(file)

                img = self.adjust_image_size(img, target_size)
                img.save(file)
            return True
        except Exception as e:
            self.logging.error(f"批量调整图片大小出错: {e}")
            return False

    # 批量复制图片
    def batch_copy_image(self, image_folder_path, save_folder_path):
        try:
            files = self.filter_files(image_folder_path,
                                      [".png", ".jpg", ".jpeg", ".tif"])
            for file in files:
                shutil.copy(file, save_folder_path)
            return True
        except Exception as e:
            self.logging.error(f"批量复制图片出错：{e}")
            return False

    # 批量删除图片
    def batch_delete_image(self, image_folder_path):
        try:
            files = self.filter_files(image_folder_path,
                                      [".png", ".jpg", ".jpeg", ".tif"])
            for file in files:
                os.remove(file)
            return True
        except Exception as e:
            self.logging.error(f"批量删除图片出错：{e}")
            return False

    # 更新进度条
    def update_progress(self, progress, name):
        bar_length = 50
        block = int(round(bar_length * progress))
        bar = "=" * block + "-" * (bar_length - block)
        sys.stdout.write(f"\r{name} [{bar}] {progress * 100:.2f}%")
        sys.stdout.flush()

    # 定义一个函数来计算宽高比例
    def aspect_ratio(self, image: Image):
        height, width = image.size
        return height / width

    # 定义一个函数来调整图片大小
    def adjust_image_size(self, img: Image, target_size):
        # 获取调整比例
        original_width, original_height = img.size
        small_size = (original_width if original_width <= original_height else
                      original_height)
        resize_ratio = target_size / small_size

        # 调整图片大小
        new_width = int(original_width * resize_ratio)
        new_height = int(original_height * resize_ratio)
        img = img.resize((new_width, new_height), Image.LANCZOS)
        return img

    # 过滤器
    def filter_files(self, folder_path: str, filter_list: list):
        return [
            f for f in Path(folder_path).glob("*")
            if f.suffix.lower() in filter_list
        ]
