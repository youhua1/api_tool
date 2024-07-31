import json
import logging
import requests
from requests import exceptions
from PIL import Image
from scripts.loggin import get_logger


class HandleException:

    def __init__(self, logger: logging.Logger = None):
        self.logger = logger
        if logger is None:
            self.logger = get_logger("HandleException")

    def image_error_handler(self, image_path: str):
        try:
            img = Image.open(image_path)
            return img
        except IOError:
            self.logger.error("无法打开图像文件")
            return None
        except Exception as e:
            self.logger.error(f"处理图像时发生错误: {e}")
            return None

    def txt_error_handler(self,
                          txt_path: str,
                          mode: str,
                          handle_mode: str,
                          write_content=None):
        try:
            if handle_mode == "read":
                with open(txt_path, mode, encoding='utf-8') as file:
                    text = file.read()
                    return text

            elif handle_mode == "write":
                with open(txt_path, mode, encoding='utf-8') as file:
                    file.write(write_content)
                    return True
            elif handle_mode == "json_write":
                with open(txt_path, mode) as file:
                    json.dump(write_content, file, indent=4)
                    return True

            elif handle_mode == "json_read":
                with open(txt_path, mode, encoding='utf-8') as file:
                    data = json.load(file)
                    return data
            else:
                self.logger.error("无法处理文本文件")
                return None

        except FileNotFoundError:
            self.logger.error("无法打开文本文件")
            return None

        except Exception as e:
            self.logger.error(f"处理文本时发生错误: {e}")
            return None

    def request_post_handler(self, url, json):
        try:
            return requests.post(url, json=json)

        except requests.exceptions.HTTPError as e:
            self.logger.error(f"{url}--HTTP请求错误: {e}")
            return None

        except Exception as e:
            self.logger.error(f"{url}--处理请求时发生错误: {e}")
            return None

    def request_get_handler(self, url):
        try:
            return requests.get(url)

        except exceptions.ConnectionError:
            self.logger.error("连接错误： 无法连接到服务器。")
        except exceptions.HTTPError as http_err:
            self.logger.error(f"HTTP错误: {http_err}")
        except exceptions.Timeout:
            self.logger.error("请求超时: 服务器响应超时。")
        except exceptions.RequestException as req_err:
            self.logger.error(f"请求异常: {req_err}")
