import re
import dashscope
import os
import json
from pathlib import Path
from openai import OpenAI
from http import HTTPStatus
from scripts import bucket
from datetime import datetime
from scripts.utils import Utils
from scripts.loggin import get_logger
from scripts.handle_exception import HandleException
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest


class AliyunAi:

    def __init__(self, api_key, access_key, access_key_secret):
        self.api_key = api_key
        self.access_key = access_key
        self.access_key_secret = access_key_secret
        self.logger = get_logger("AliyunAi")
        self.utils = Utils(self.logger)
        self.handle_except = HandleException(self.logger)

    def translate_text(self, text, source_language, target_language):
        client = AcsClient(self.access_key, self.access_key_secret,
                           "cn-hangzhou")

        request = CommonRequest()
        request.set_accept_format("json")
        request.set_domain("mt.cn-hangzhou.aliyuncs.com")
        request.set_method("POST")
        request.set_protocol_type("https")
        request.set_version("2018-10-12")
        request.set_action_name("TranslateGeneral")

        request.add_query_param("FormatType", "text")
        request.add_query_param("SourceLanguage", source_language)
        request.add_query_param("TargetLanguage", target_language)
        request.add_query_param("SourceText", text)

        try:
            response = client.do_action_with_exception(request)
            response_dict = json.loads(response)

            if "Data" in response_dict and "Translated" in response_dict[
                    "Data"]:
                return response_dict["Data"]["Translated"]
        except Exception as e:
            self.logger.error(f"阿里云翻译 error: {e}")

        return None

    def aliyun_llm(self,
                   prompt: str,
                   txt_path: str = None,
                   model: str = "qwen-long"):
        client = OpenAI(
            api_key=self.api_key,  # 替换成真实DashScope的API_KEY
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )

        text = "I want you to be more professional"
        if txt_path:
            text = txt_path

        # 首次对话会等待文档解析完成，首次rt可能较长
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant."
                    },
                    {
                        "role": "system",
                        "content": text
                    },
                    {
                        "role": "user",
                        "content": prompt
                    },
                ],
            )

            return completion
        except Exception as e:
            self.logger.error("阿里云llm error:", e)
            return None

    def aliyun_vl(self,
                  image_path: str,
                  prompt: str,
                  model: str = "qwen-vl-plus"):
        # 提取图片的关键详细,将信息转换为关键词，并将关键词被为英文用逗号隔开
        dashscope.api_key = self.api_key

        messages = [{
            "role":
            "user",
            "content": [{
                "image": f"file://{image_path}"
            }, {
                "text": prompt
            }],
        }]
        try:
            response = dashscope.MultiModalConversation.call(model=model,
                                                             messages=messages)

            if response.status_code == HTTPStatus.OK:
                return response
        except Exception as e:
            self.logger.error("阿里云vl error:", e)
            return None

    def handle_vl_response(self, image_folder_path, data_path, log_path,
                           vl_prompt, vl_model):
        image_flies = self.utils.filter_files(
            image_folder_path, [".png", ".jpg", ".jpeg", ".tif"])
        input_tokens, output_tokens = self.get_model_tokens(vl_model, log_path)

        for index, image_path in enumerate(image_flies):
            aliyun_vl_response_data = self.aliyun_vl(image_path, vl_prompt,
                                                     vl_model)

            if aliyun_vl_response_data:
                # 处理vl response
                try:
                    text_result = aliyun_vl_response_data["output"]["choices"][
                        0]["message"]["content"][0]["text"].replace("\n", "")
                    output_file = Path(data_path) / f"{image_path.stem}.txt"
                    self.handle_except.txt_error_handler(
                        output_file, "w", "write", f"cn_content:{text_result}")
                    input_tokens += aliyun_vl_response_data["usage"][
                        "input_tokens"]
                    input_tokens += aliyun_vl_response_data["usage"][
                        "image_tokens"]
                    output_tokens += aliyun_vl_response_data["usage"][
                        "output_tokens"]
                except (KeyError, TypeError) as e:
                    self.logger.error(
                        f"Error processing file {image_path.name}: {e}")

            else:
                self.error_log_file(vl_model, image_path, log_path)

            # 更新进度条
            self.utils.update_progress((index + 1) / len(image_flies),
                                       "Processing images:")

        print("\n")
        self.utils.batch_delete_image(image_folder_path)

        self.log_file(vl_model, input_tokens, output_tokens, log_path)

    def handle_llm_response(self, data_path, log_path, llm_prompt, llm_model,
                            input_label, output_label):
        llm_input_tokens, llm_output_tokens = self.get_model_tokens(
            llm_model, log_path)
        txt_files = self.utils.filter_files(data_path, [".txt"])

        for index, txt_path in enumerate(txt_files):
            text = self.handle_except.txt_error_handler(txt_path, "r", "read")
            if text is None:
                continue
            text = text.split(input_label)[1]

            completion = self.aliyun_llm(llm_prompt, text, llm_model)
            if completion:
                text_result = completion.choices[0].message.content
                text_result = re.sub(r'["\'\n\{content: |\}]', '', text_result)
                llm_input_tokens += completion.usage.prompt_tokens
                llm_output_tokens += completion.usage.completion_tokens

                self.handle_except.txt_error_handler(
                    txt_path, "a", "write", f"\n{output_label}{text_result}")
            else:
                self.error_log_file(llm_model, txt_path, log_path)

            # 更新进度条
            self.utils.update_progress((index + 1) / len(txt_files),
                                       "Processing text files:")

        print("\n")
        self.log_file(llm_model, llm_input_tokens, llm_output_tokens, log_path)

    def handle_translate_response(self, train_txt_path, data_path, log_path,
                                  input_label, output_label):
        translate_files = self.utils.filter_files(data_path, [".txt"])

        for index, file_name in enumerate(translate_files):
            txt_path = os.path.join(data_path, file_name.name)
            end_txt_path = os.path.join(train_txt_path, file_name.name)
            text = self.handle_except.txt_error_handler(txt_path, "r", "read")
            if text is None:
                continue
            text = text.split(input_label)[1]

            translate_text = self.translate_text(text, "zh", "en")

            if translate_text:
                # 写入翻译结果
                self.handle_except.txt_error_handler(
                    txt_path, "a", "write",
                    f"\n{output_label}{translate_text}")

                self.handle_except.txt_error_handler(end_txt_path, "w",
                                                     "write", translate_text)

            else:
                self.error_log_file("translate", txt_path, log_path)

            # 更新进度条
            self.utils.update_progress((index + 1) / len(translate_files),
                                       "Translating text files:")

    def aliyun_vl_llm_batch(
        self,
        image_folder_path: str,
        vl_prompt: str,
        llm_prompt: str,
        filter_llm_prompt: str,
        vl_model: str = "qwen-vl-plus",
        llm_model: str = "qwen-long",
    ):
        # 构建路径
        data_path = os.path.join(image_folder_path, "data")
        log_path = os.path.join(image_folder_path, "log")
        train_txt_path = os.path.join(image_folder_path, "train_txt")
        os.makedirs(data_path, exist_ok=True)
        os.makedirs(log_path, exist_ok=True)
        os.makedirs(train_txt_path, exist_ok=True)

        # 对图片做处理
        self.utils.batch_copy_image(image_folder_path, train_txt_path)
        batch_resize_image_state = self.utils.batch_adjust_image_size(
            image_folder_path, 255)
        if not batch_resize_image_state:
            return

        # # vl过程
        self.handle_vl_response(image_folder_path, data_path, log_path,
                                vl_prompt, vl_model)

        # # llm过程
        self.handle_llm_response(data_path, log_path, llm_prompt, llm_model,
                                 "cn_content:", "cn_keyword:")

        # llm过滤过程
        self.handle_llm_response(data_path, log_path, filter_llm_prompt,
                                 llm_model, "cn_keyword:", "filter_keyword:")

        # 翻译过程
        self.handle_translate_response(train_txt_path, data_path, log_path,
                                       "filter_keyword:", "en_content:")

    def log_file(self, model_name, input_tokens, output_tokens,
                 save_folder_path):
        now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        price = (input_tokens *
                 bucket.get_aliyun_model_dict()[model_name]["input_tokens"] /
                 1000)
        price += (output_tokens *
                  bucket.get_aliyun_model_dict()[model_name]["output_tokens"] /
                  1000)

        logs_dict = {
            "model_name": model_name,
            "total_tokens": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            },
            "price": price,
            "end_time": now_time,
        }

        log_file_path = os.path.join(save_folder_path,
                                     f"{model_name}_logs.json")
        self.handle_except.txt_error_handler(log_file_path, "w", "write",
                                             json.dumps(logs_dict, indent=4))

    def error_log_file(self, model_name, file_path, save_folder_path):
        log_file_path = os.path.join(save_folder_path,
                                     f"{model_name}_error_logs.txt")
        self.handle_except.txt_error_handler(
            log_file_path, "a", "write",
            f"使用{model_name}模型时，文件{file_path}出错\n")

    def get_model_tokens(self, model_name, folder_path):
        log_file_path = os.path.join(folder_path, f"{model_name}_logs.json")

        if os.path.exists(log_file_path):
            data_dict = self.handle_except.txt_error_handler(
                log_file_path, "r", "json_read")
            if data_dict is None:
                return 0, 0

            return data_dict["total_tokens"]["input_tokens"], data_dict[
                "total_tokens"]["output_tokens"]
        return 0, 0
