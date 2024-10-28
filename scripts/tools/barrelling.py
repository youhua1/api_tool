import os
from PIL import Image
from scripts.utils import Utils
from scripts import bucket
from scripts.loggin import get_logger
from scripts.handle_exception import HandleException
from pathlib import Path


class Barrelling:

    def __init__(self):
        self.logger = get_logger("Barrelling")
        self.utils = Utils(self.logger)
        self.handle_exception = HandleException(self.logger)

    def get_nearest_ratio_sdxl(self, ordinary_ratio):
        # SDXL模式下的近似比例选择
        if ordinary_ratio < 0.25 or ordinary_ratio > 4:
            return -1

        key = self.utils.find_closest_key(ordinary_ratio,
                                          bucket.get_resolution_dict())
        return key

    # 获得sd最近值
    def get_nearest_ratio_sd(self, ordinary_ratio):
        if ordinary_ratio > 1.25:
            return 1.5
        elif ordinary_ratio < 0.85:
            return 0.67
        else:
            return 1

    # 获得最近值
    def get_nearest_ratio(self, ordinary_ratio, enable_sd):
        if enable_sd:
            return self.get_nearest_ratio_sd(ordinary_ratio)
        else:
            return self.get_nearest_ratio_sdxl(ordinary_ratio)

    # 分配桶
    def barrelling(self, image_data: dict, output_image_path: str,
                   file_name: str):
        # 创建桶文件夹
        bucket_name = image_data["img_size"]
        bucket_output = os.path.join(output_image_path, bucket_name)
        os.makedirs(bucket_output, exist_ok=True)

        # 保存到分配桶的目录
        new_output_path = os.path.join(bucket_output, file_name)
        img = image_data["img"]
        img.save(new_output_path)

    # 获取图片信息
    def get_image_info(self, image_path: str, enable_sd: bool):
        img = self.handle_exception.image_error_handler(image_path)
        if img is None:
            return {"img": None}

        aspect_ratio_value = self.utils.aspect_ratio(img)

        # 获取比例
        ratio = round(float(aspect_ratio_value), 2)

        # 获取附件比例
        resolution_dict = bucket.get_resolution_dict(enable_sd)
        target_ratio = (ratio if ratio in resolution_dict else
                        self.get_nearest_ratio(ratio, enable_sd))
        if target_ratio < 0:
            return {"img": None}

        # 获取调整目标
        image_size = resolution_dict[target_ratio]
        img_data = {
            "img": img,
            "img_ratio": target_ratio,
            "img_size": image_size
        }
        return img_data

    # 调整图片大小
    def resize_image(self, image_data: dict):

        # 获取调整目标
        new_image_size = image_data["img_size"].split("_")
        new_image_size_array = [int(num) for num in new_image_size]
        target_size = min(new_image_size_array)

        # 调整图片
        img = self.utils.adjust_image_size(image_data["img"], target_size)
        image_data["img"] = img
        return image_data

    # 删除元数据
    def remove_metadata(self, image_path: Path, save_image_path):
        # 尝试打开图像文件
        img = self.handle_exception.image_error_handler(image_path)

        if img is None:
            return

        # 转换图像格式到RGB
        if img.mode != "RGB":
            img = img.convert("RGB")

        # 保存新的JPEG图像
        img.save(save_image_path, format="JPEG")
        img.close()  # 关闭图像文件以释放资源

        # 删除原始图像文件
        try:
            if image_path.suffix == ".jpg":
                return
            os.remove(image_path)
        except FileNotFoundError:
            self.logger.error(f"文件 {image_path} 已被移除或不存在。")
        except Exception as e:
            self.logger.error(f"删除文件 {image_path} 时发生错误：{e}")

    def main_barrelling(self, image_path: str, enable_bucket: bool,
                        enable_resize_image: bool, enable_sd: bool):
        # 获取图片列表
        image_files = self.utils.filter_files(
            image_path, [".png", ".jpg", ".jpeg", ".bmp", ".tif", ".webp"])
        for index, file in enumerate(image_files):
            # 更改为jpg格式
            image_name = file.with_suffix(".jpg")

            # 删除元数据
            self.remove_metadata(file, image_name)

            # 获取图片信息
            img_data = self.get_image_info(image_name, enable_sd)

            # 调整图片
            if enable_resize_image:
                img_data = self.resize_image(img_data)
                if not isinstance(img_data["img"], Image.Image):
                    continue

            # 启用分桶
            if enable_bucket:
                self.barrelling(img_data, image_path, image_name.name)

                try:
                    os.remove(image_name)
                except PermissionError as e:
                    self.logger.error(
                        f"Error: {e}. Make sure the file is not open or that you have permission to delete it."
                    )
                except Exception as e:
                    self.logger.error(f"An unexpected error occurred: {e}")

            else:
                img_data["img"].save(image_name)

            # 更新进度
            self.utils.update_progress((index + 1) / len(image_files),
                                       "Processing barrelling:")
