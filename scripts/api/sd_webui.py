import json
import concurrent.futures
from scripts import bucket
from pathlib import Path
from scripts.utils import Utils
from scripts.loggin import get_logger
from scripts.handle_exception import HandleException


class SdWebui:

    def __init__(
        self,
        models_json_path: str = "./json/",
        data_image_url_path: str = "./image/inputs/url/image_url.json",
        hyperparameter_data_path:
        str = "./json/t2i_test/hyperparameter_data.json",
        output_image_folder: str = "./image/outputs/",
    ):
        self.models_json_path = models_json_path
        self.data_image_url_path = data_image_url_path
        self.hyperparameter_data_path = hyperparameter_data_path
        self.output_image_folder = output_image_folder
        self.logger = get_logger("SdWebui")
        self.utils = Utils(self.logger)
        self.handle_exception = HandleException(self.logger)

    def handle_json(self, main_json: dict, task_name):
        payload = next(
            (task["params"] for task in main_json.get("payload", [])
             if task["task"] == task_name),
            None,
        )
        return payload

    # 获取hyperparameter_data
    def get_hyperparameter_data(self):
        if self.hyperparameter_data_path is None:
            return {}

        hyperparameter_data = self.handle_exception.txt_error_handler(
            self.hyperparameter_data_path, "r", "json_read")

        return hyperparameter_data

    # 图片url转为列表
    def data_image_url(self):
        data_image_url_dict = self.handle_exception.txt_error_handler(
            self.data_image_url_path, "r", "json_read")
        if data_image_url_dict is None:
            return []

        return list(data_image_url_dict.values())

    # 模板转为列表
    def data_models_json(self):
        data_json = []
        files = self.utils.filter_files(self.models_json_path, [".txt"])
        for file_path in files:
            data_json.append(file_path)
        data_json.sort()
        return data_json

    def base64_json_new(self, url: str, image_url_id: int, models_id: int,
                        hyperparameter_id: int):
        image_url = self.data_image_url()
        if not image_url:
            self.logger.error("图片url列表为空")
            return None

        if not (0 <= image_url_id < len(image_url)):
            self.logger.error("图片URL ID超出范围")
            return None

        image_url = image_url[image_url_id]

        image_Image = self.utils.image_url_to_image(image_url)
        image_base64 = self.utils.image_url_to_base64(image_url)

        if image_base64 is None or image_Image is None:
            self.logger.error(f"图片{image_url}无法下载")
            return None

        width, height = self.utils.image_size(image_Image)

        models_json_data = self.data_models_json()
        if not models_json_data:
            self.logger.error("模型json列表为空")
            return None

        if not (0 <= models_id < len(models_json_data)):
            self.logger.error("模型 ID超出范围")
            return None

        # 获取模型json
        models_json_name = models_json_data[models_id]

        data_dict = self.handle_exception.txt_error_handler(
            models_json_name, "r", "read")
        if data_dict is None:
            return None

        hyperparameter_data = self.get_hyperparameter_data()[hyperparameter_id]

        if "ratio" in hyperparameter_data:
            # 获得分辨率
            enable_sdxl = True
            if "sdxl_vae.safetensors" in data_dict:
                enable_sdxl = False

            # 获得输入比例
            input_width, input_height = hyperparameter_data["ratio"].split(":")
            input_ratio = round(int(input_width) / int(input_height), 2)

            key = self.utils.find_closest_key(
                input_ratio, bucket.get_resolution_dict(enable_sdxl))
            width, height = bucket.get_resolution_dict(enable_sdxl)[key].split(
                "_")
            data_dict = data_dict.replace("$width_hr$", "$width$").replace(
                "$height_hr$", "$height$")

        # 替换占位符
        replacements = bucket.get_replacements_sd_webui_base64_json_new(
            int(width), int(height), image_base64, hyperparameter_data)
        new_data = self.utils.replace_placeholders(data_dict, replacements)
        # 转换为json
        data_dict = json.loads(new_data)

        # 查找模型路径
        models_path = self.get_models_path_json(url)
        if models_path is None:
            return None

        new_main_json = bucket.base64_json_dict(data_dict, models_path,
                                                image_url)

        self.logger.info(f"使用的图片: {image_url}")
        self.logger.info(f"使用的json: {models_json_name}")

        return new_main_json

    def get_models_path_json(self, url: str):
        reponse = self.handle_exception.request_get_handler(
            f"{url}/sdapi/v1/sd-models")

        if reponse is None or reponse.status_code != 200:
            self.logger.error("获得模型路径失败")
            return None

        models_list = reponse.json()
        models_data = {
            Path(data.get("title")).stem: Path(data.get("title"), "")
            for data in models_list
        }
        return models_data

    def tagger(self, url: str, main_json: dict):
        response_dict = self.get_response_dict()

        response_dict["time"] = main_json.get("time", 0)
        main_json = main_json.get("main_json", main_json)

        # 解析json
        wd_14_json = self.handle_json(main_json, "tagger")

        response = self.handle_exception.request_post_handler(
            url=f"{url}/tagger/v1/interrogate", json=wd_14_json)

        if response is None or response.status_code != 200:
            self.logger.error("wd1.4失效")
            response_dict["main_json"] = main_json
            return response_dict

        wd_v1_4_time = response.elapsed.total_seconds()
        image_tag = response.json().get("caption", {}).get("tag", {})
        data = ", ".join(map(str, list(image_tag.keys())))
        main_json_data = json.dumps(main_json).replace("$tagger_placeholder$",
                                                       data)
        new_main_json = json.loads(main_json_data)

        response_dict["main_json"] = new_main_json
        response_dict["time"] = wd_v1_4_time + response_dict["time"]
        self.logger.info(f"{url}_wd1.4耗时: {wd_v1_4_time} seconds")
        return response_dict

    def count_faces(self, url: str, main_json: dict):
        response_dict = self.get_response_dict()
        response_dict["time"] = main_json.get("time", 0)

        main_json = main_json.get("main_json", main_json)

        count_faces_json = self.handle_json(main_json, "count_faces")

        response = self.handle_exception.request_post_handler(
            url=f"{url}/count_faces", json=count_faces_json)

        if response is None or response.status_code != 200:
            self.logger.error("count_faces_失效")
            return response_dict

        if response.json().get("code", -1) == -1:
            self.logger.warning("没有检测到脸部")
            return response_dict

        count_faces = response.json().get("faces_count", 0)
        sequence = ",".join(str(i) for i in range(count_faces))
        main_json = json.loads(
            json.dumps(main_json).replace("$facecount_placeholder$", sequence))

        time = response.elapsed.total_seconds()
        response_dict["main_json"] = main_json
        response_dict["time"] = time + response_dict["time"]
        self.logger.info(f"{url}_count_faces耗时: {time} seconds")

        return response_dict

    def switching_model(self, url: str, main_json: dict):

        # 解析json
        switching_json = {
            "sd_model_checkpoint":
            main_json["models"]["Stable-diffusion"][0]["model_name"]
        }

        response = self.handle_exception.request_post_handler(
            url=f"{url}/sdapi/v1/options", json=switching_json)

        if response is None or response.status_code != 200:
            self.logger.error(f"{url}_切换模型失败")
            return None

        time = response.elapsed.total_seconds()
        self.logger.info(f"{url}_切换模型时间: {time} seconds")
        return time

    def txt2img(self, url: str, main_json: dict):
        response_dict = self.get_response_dict()
        main_json = main_json.get("main_json", main_json)
        response_dict["time"] = main_json.get("time", 0)

        t2i_data_json = self.handle_json(main_json, "txt2img")

        response = self.handle_exception.request_post_handler(
            url=f"{url}/sdapi/v1/txt2img", json=t2i_data_json)

        if response is None or response.status_code != 200:
            self.logger.error(f"{url}_文生图失败")
            return response_dict

        t2i_time = response.elapsed.total_seconds()
        self.logger.info(f"{url}_文生图时间: {t2i_time} seconds")
        response_dict["time"] = t2i_time + response_dict["time"]
        response_dict["image_base64"] = response.json()["images"][0]
        response_dict["main_json"] = main_json
        return response_dict

    def img2img(self, url: str, main_json: dict):
        response_dict = self.get_response_dict()
        response_dict["time"] = main_json.get("time", 0)
        init_base64 = main_json.get("image_base64", "")
        main_json = main_json.get("main_json", main_json)

        i2i_data_json = self.handle_json(main_json, "img2img")

        if init_base64:
            i2i_data_json = json.loads(
                json.dumps(i2i_data_json).replace("$txt2img_placeholder$",
                                                  init_base64))

        response = self.handle_exception.request_post_handler(
            url=f"{url}/sdapi/v1/img2img", json=i2i_data_json)

        if response is None or response.status_code != 200:
            self.logger.error(f"{url}_图生图失败")
            return response_dict

        i2i_time = response.elapsed.total_seconds()
        self.logger.info(f"{url}_图生图时间: {i2i_time} seconds")
        response_dict["time"] = i2i_time + response_dict["time"]
        response_dict["image_base64"] = response.json()["images"][0]
        response_dict["main_json"] = main_json

        return response_dict

    def extra_single_image(self, url: str, main_json: dict):
        response_dict = self.get_response_dict()
        response_dict["time"] = main_json.get("time", 0)
        image_base64 = main_json.get("image_base64", "")
        main_json = main_json.get("main_json", main_json)

        extra_data_json = self.handle_json(main_json, "extra-single-image")

        _extra_data_json = json.loads(
            json.dumps(extra_data_json).replace("$extra_placeholder$",
                                                image_base64))

        response = self.handle_exception.request_post_handler(
            url=f"{url}/sdapi/v1/extra-single-image", json=_extra_data_json)

        if response is None or response.status_code != 200:
            self.logger.error(f"{url}_extra-single-image失败")
            return response_dict

        extra_single_time = response.elapsed.total_seconds()
        self.logger.info(
            f"{url}_extra-single-image时间: {extra_single_time} seconds")
        response_dict["time"] = extra_single_time + response_dict["time"]
        response_dict["image_base64"] = response.json()["image"]
        response_dict["main_json"] = main_json

        return response_dict

    def reactor(self, url: str, main_json: dict):
        response_dict = self.get_response_dict()
        response_dict["time"] = main_json.get("time", 0)
        image_base64 = main_json.get("image_base64", "")
        main_json = main_json.get("main_json", main_json)

        reactor_data_json = self.handle_json(main_json, "reactor")

        _reactor_data_json = json.loads(
            json.dumps(reactor_data_json).replace("$reactor_placeholder$",
                                                  image_base64))

        response = self.handle_exception.request_post_handler(
            url=f"{url}/reactor/image", json=_reactor_data_json)

        if response is None or response.status_code != 200:
            self.logger.error(f"{url}_reactor失败")
            return response_dict

        reactor_time = response.elapsed.total_seconds()
        self.logger.info(f"{url}_reactor时间: {reactor_time} seconds")
        response_dict["time"] = reactor_time + response_dict["time"]
        response_dict["image_base64"] = response.json()["image"]
        response_dict["main_json"] = main_json

        return response_dict

    def invocations_process(self, url: str, models_id: int, image_url_id: int):
        main_json = self.base64_json_new(url, image_url_id, models_id)

        if main_json is None:
            return

        response = self.handle_exception.request_post_handler(
            url=f"{url}/invocations", json=main_json)

        if response.status_code != 200:
            self.logger.error(f"{url}_invocations失败")
            return

        image_base64 = response.json()["image"]

        file_name = self.utils.save_image(image_base64,
                                          self.output_image_folder)

        if not file_name:
            self.logger.warning(f"{url}_图片保存失败")
            return

        invocations_time = round(response.json()["timeCost"] / 1000, 2)
        self.logger.info(f"{url}_图片保存成功: {file_name}")
        self.logger.info(f"{url}_invocations时间: {invocations_time} seconds")
        return

    def call_method_by_name(self, name, *args, **kwargs):
        # 使用 getattr 获取实例方法
        method = getattr(self, name, None)
        if method:
            return method(*args, **kwargs)
        else:
            self.logger.warning(f"Method {name} not found")

    def get_response_dict(self):
        return {
            "status": 0,
            "main_json": {},
            "time": 0,
            "image_base64": "",
        }

    def handle_request(self, url: str, main_json: dict):
        payload = main_json.get("payload", [])
        response_dict = main_json
        for index, task in enumerate(payload):
            if task["task"] == "extra-single-image":
                response_dict = self.extra_single_image(url, response_dict)
            else:
                response_dict = self.call_method_by_name(
                    task["task"], url, response_dict)
            if index == len(payload) - 1:
                return response_dict

    def main_process(self, url: str, models_id: int, image_url_id: int,
                     hyperparameter_id: int):
        # 解析超参数
        main_json = self.base64_json_new(url, image_url_id, models_id,
                                         hyperparameter_id)
        if main_json is None:
            return

        time = 0
        switching_model_time = self.switching_model(url, main_json)
        if switching_model_time is not None:
            time += switching_model_time

        response_dict = self.handle_request(url, main_json)
        image_base64 = response_dict.get("image_base64", "")
        time += response_dict.get("time", 0)
        self.logger.info(f"{url}_总时间: {time} seconds")

        file_name = self.utils.save_image(image_base64,
                                          self.output_image_folder)
        if not file_name:
            self.logger.warning("保存图片失败")
            return
        self.logger.info(f"{url}_保存图片成功: {file_name}")

    def thread_entry(self, urls: list, models_id: int, image_url_id: int,
                     hyperparameter_data: dict):
        # 创建一个线程池，用于所有任务
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            [
                executor.submit(self.main_process, url, models_id,
                                image_url_id, hyperparameter_data)
                for url in urls
            ]
