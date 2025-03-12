from pathlib import Path
from scripts.utils import Utils
from scripts.loggin import get_logger
from scripts.handle_exception import HandleException


class JsonToTag:

    def __init__(self, input_folder: str):
        self.logger = get_logger("HandleTag")
        self.handle_exception = HandleException(self.logger)
        self.utils = Utils(self.logger)
        self.input_folder = input_folder

    def str_to_list(self, tag_string: str):
        return [tag.strip() for tag in tag_string.split(" ") if tag.strip()]

    def handle_tag_general(self, tag_string: str):
        keywords = ['1boy', '1girl', '2boy', '2girl', '3boy', '3girl']
        tags = self.str_to_list(tag_string)
        # 查找 '1boy' 或 '1girl'
        found_keyword = []
        for keyword in keywords:
            if keyword in tags:
                found_keyword.append(keyword)
                tags.remove(keyword)

        # 如果没有找到 '1boy' 或 '1girl'，则添加 '1other'
        if not found_keyword:
            found_keyword.append("1other")

        return found_keyword, tags

    def json_to_tag(self, json_file: Path):
        tag_data = self.handle_exception.txt_error_handler(
            json_file, "r", "json_read")

        # 解析json数据
        danbooru_tag = tag_data.get("danbooru", {})
        tag_list_sex, tag_list_general = self.handle_tag_general(
            danbooru_tag.get("tag_string_general"))
        tag_list_character = self.str_to_list(
            danbooru_tag.get("tag_string_character"))
        tag_list_copyright = self.str_to_list(
            danbooru_tag.get("tag_string_copyright"))
        tag_list_artist = self.str_to_list(
            danbooru_tag.get("tag_string_artist"))
        filename = tag_data.get("filename")

        # 合并标签列表
        merge_tags_list = [
            item for sublist in [
                tag_list_sex, tag_list_character, tag_list_copyright,
                tag_list_artist, tag_list_general
            ] for item in sublist
        ]

        merge_tags_string = ", ".join(merge_tags_list)
        merge_tags_string = merge_tags_string.replace("_", " ")
        txt_path = json_file.with_name(filename).with_suffix(".txt")
        self.handle_exception.txt_error_handler(txt_path, "w", "write",
                                                merge_tags_string)
        try:
            # 尝试删除文件
            json_file.unlink()
        except FileNotFoundError:
            # 文件不存在时抛出的异常
            self.logger.error(f"错误：文件 {json_file} 不存在。")
        except Exception as e:
            # 其他类型的异常
            self.logger.error(f"错误：删除文件 {json_file} 时发生未知错误 - {e}")

    def batch_json_to_tag(self):
        files = self.utils.filter_files(self.input_folder, [".json"])
        for index, file in enumerate(files):
            self.json_to_tag(file)

            # 更新进度条
            self.utils.update_progress((index + 1) / len(files),
                                       "Processing json:")
