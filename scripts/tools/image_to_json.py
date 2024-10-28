import json
import re
from scripts.loggin import get_logger
from PIL import Image
from scripts import bucket
from scripts.handle_exception import HandleException
from scripts.utils import Utils


class ImageToJson:

    def __init__(self):
        self.logger = get_logger("ImageToJson")
        self.handle_exception = HandleException(self.logger)
        self.utils = Utils(self.logger)

    def imageInfo_to_dickInfo(self, image_path):
        try:
            img = Image.open(image_path)
        except Exception as e:
            self.logger.error(f"image error: {e}")
        metadata = img.info

        if "parameters" not in metadata:
            self.logger.warning(f"{image_path}____该图片没有sd参数信息")
            return None

        parameter = {}
        embeddings_components = []
        image_info = metadata["parameters"]
        image_info = (image_info.replace("\n", "").replace('"', "").replace(
            "Negative prompt: ",
            ",Negative prompt: ").replace("Steps:", ",Steps:"))

        if "TI hashes:" in image_info:
            # 提取 embeddings 部分并移除
            embeddings_start = image_info.find("TI hashes: ") + len(
                "TI hashes: ")
            embeddings_end = image_info.find(", Version:")
            embeddings = image_info[embeddings_start:embeddings_end]

            # 移除 embeddings 信息
            image_info = (image_info[:embeddings_start - len("TI hashes: ")] +
                          image_info[embeddings_end:])

            embeddings_components = re.split(
                r",\s*(?=[A-Za-z\s0-9])",
                embeddings,
            )

        # 使用正则表达式分割组件
        sd_components = re.split(
            r",\s*(?=[A-Za-z\s0-9]+: )",
            image_info,
        )

        no_prompt = 1
        parameter["prompt"] = sd_components[0]

        # 判断是否有 prompt
        if "Negative prompt" in sd_components[0]:
            parameter["prompt"] = ""
            no_prompt = 0

        controlnet_detect = False
        ADetailer_detect = False
        controlnet_list = []
        ADetailer_list = []
        controlnet_dict = {}
        ADetailer_dict = {}

        for i in range(no_prompt, len(sd_components)):
            hyper_parameter = sd_components[i].split(": ")
            key, value = hyper_parameter[0], hyper_parameter[1]

            # 处理布尔值
            new_value = value
            if value == "True":
                new_value = True
            elif value == "False":
                new_value = False
            elif re.match(r"^\d+$", value):
                new_value = int(value)
            elif re.match(r"^\d+\.\d+$", value):
                new_value = float(value)

            if "ControlNet" in key:
                controlnet_detect = True
                controlnet_dict["input_image"] = "$origin_base64_placeholder$"
                controlnet_dict["module"] = hyper_parameter[2]
                continue

            if "ADetailer model" in key:
                ADetailer_detect = True
                ADetailer_dict[key] = new_value

            if controlnet_detect:
                new_key = key.lower().replace(" ", "_")

                controlnet_dict[new_key] = new_value
            elif ADetailer_detect and "Lora hashes" not in key:
                ADetailer_dict[key] = new_value
            else:
                parameter[key] = new_value

            if "Save Detected Map" in key:
                controlnet_dict["save_detected_map"] = False
                controlnet_dict["resize_mode"] = 1
                controlnet_list.append(controlnet_dict)
                controlnet_dict = {}
                controlnet_detect = False
            elif "ADetailer version" in key:
                ADetailer_list.append(ADetailer_dict)
                ADetailer_dict = {}
                ADetailer_detect = False

        if embeddings_components:
            parameter["embeddings"] = embeddings_components

        if controlnet_list:
            parameter["controlnet"] = controlnet_list

        if ADetailer_list:
            parameter["ADetailer"] = ADetailer_list

        return parameter

    def dickInfo_to_json_ai_fasic_art(
        self,
        dick_info: dict,
        template_name: str,
        enable_t2i: bool,
        enable_cont_face: bool,
        enable_reactor: bool,
    ):
        # 添加expire_timestamp参数
        data_json = {"expire_timestamp": "xxxxx"}

        # 添加sagemaker参数
        data_json["sagemaker_params"] = bucket.sagemaker_params_dict(
            dick_info, template_name, True)

        # 启用cont_face时，添加cont_face参数
        if enable_cont_face:
            data_json["cont_face_params"] = bucket.cont_face_params_dict()

        # 添加wd1_4参数
        sd_params_list = [bucket.wd1_4_params_dict()]

        if enable_t2i:
            # 添加t2i参数
            sd_params_list.append(
                bucket.t2i_params_dict_ai_fasic_art(dick_info))
        else:
            # 添加i2i参数
            sd_params_list.append(
                bucket.i2i_params_dict_ai_fasic_art(dick_info))

        # 添加extra_single_image参数
        sd_params_list.append(bucket.extra_single_image_params_dict())

        # 启用reactor时，添加reactor参数
        if enable_reactor:
            sd_params_list.append(bucket.reactor_params_dict(enable_cont_face))

        # 整合sd_params_list的参数
        data_json["sd_params"] = sd_params_list
        return data_json

    def dickInfo_to_json_explore(self, dick_info: dict, template_name: str,
                                 enable_t2i: bool):
        # 添加expire_timestamp参数
        data_json = {
            "expire_timestamp": "xxxxx",
            "inference_id": "$inference_id$"
        }

        # 添加sagemaker参数
        data_json["sagemaker_params"] = bucket.sagemaker_params_dict(
            dick_info, template_name)

        # 设置空列表
        sd_params_list = []

        if enable_t2i:
            # 添加t2i参数
            sd_params_list.append(bucket.t2i_params_dict_explore(dick_info))
            # 修改t2i sagemaker 参数
            data_json["sagemaker_params"].pop("origin_placeholder", None)
        else:
            # 添加i2i参数
            sd_params_list.append(bucket.i2i_params_dict_explore(dick_info))

        # # 添加extra_single_image参数
        # sd_params_list.append(bucket.extra_single_image_params_dict())

        # 整合sd_params_list的参数
        data_json["sd_params"] = sd_params_list
        return data_json

    def get_image_info_json_ai_fasic_art(
        self,
        image_path,
        enable_t2i: bool,
        enable_cont_face: bool,
        enable_reactor: bool,
    ):
        dick_info = self.imageInfo_to_dickInfo(image_path)
        if dick_info is None:
            return None

        data_json = self.dickInfo_to_json_ai_fasic_art(dick_info,
                                                       image_path.stem,
                                                       enable_t2i,
                                                       enable_cont_face,
                                                       enable_reactor)

        data_str = json.dumps(data_json, indent=4)
        data_str = (data_str.replace('"xxxxx"', "xxxxx").replace(
            "666", "$width$").replace("667", "$height$"))

        return data_str

    def get_image_info_json_explore(self, image_path, enable_t2i: bool):
        dick_info = self.imageInfo_to_dickInfo(image_path)
        if dick_info is None:
            return None

        data_json = self.dickInfo_to_json_explore(dick_info, image_path.stem,
                                                  enable_t2i)

        data_str = json.dumps(data_json, indent=4)
        data_str = self.utils.replace_placeholders(data_str, bucket.get_replacements_image_to_json_get_image_info_json_explore())
        return data_str

    def batch_image_info_json(
        self,
        image_folder_path: str,
        enable_ai_fasic_art: bool = True,
        enable_t2i: bool = True,
        enable_cont_face: bool = False,
        enable_reactor: bool = False,
    ):
        # 获取图片文件
        files = self.utils.filter_files(image_folder_path, [".png", ".jpg"])

        # 定义保存 JSON 文件的通用方法
        def save_json(file, prefix: str, data_str: str):
            if data_str is None:
                return
            save_path = file.with_stem(
                f"{file.stem}_{prefix}_json").with_suffix(".txt")
            self.handle_exception.txt_error_handler(save_path, "w", "write",
                                                    data_str)

        # 如果启用了 AI Fasic Art 处理
        if enable_ai_fasic_art:
            for index, file in enumerate(files):
                data_str = self.get_image_info_json_ai_fasic_art(
                    file, enable_t2i, enable_cont_face, enable_reactor)
                save_json(file, "ai_fasic_art", data_str)
                self.utils.update_progress((index + 1) / len(files),
                                           "Processing ImageToJsonAiFasicArt:")
        else:
            # 否则使用 Explore 处理方式
            for index, file in enumerate(files):
                # T2I处理
                data_str = self.get_image_info_json_explore(file, True)
                save_json(file, "t2i", data_str)

                # I2I处理
                data_str = self.get_image_info_json_explore(file, False)
                save_json(file, "i2i", data_str)

                self.utils.update_progress((index + 1) / len(files),
                                           "Processing ImageToJsonExplore:")
