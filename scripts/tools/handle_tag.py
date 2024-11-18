import os
import shutil
from scripts.utils import Utils
from scripts.loggin import get_logger
from scripts.handle_exception import HandleException


class HandleTag:

    def __init__(self, input_folder: str):
        self.logger = get_logger("HandleTag")
        self.handle_exception = HandleException(self.logger)
        self.utils = Utils(self.logger)
        self.input_folder = input_folder

    def merge_tags(self):
        # 获取input_folder下所有的子文件夹
        subfile_list = [
            f for f in os.listdir(self.input_folder)
            if os.path.isdir(os.path.join(self.input_folder, f))
        ]

        if len(subfile_list) != 2:
            print("输入的文件夹中必须有且两个子文件夹。")
            return

        folder1 = os.path.join(self.input_folder, subfile_list[0])
        folder2 = os.path.join(self.input_folder, subfile_list[1])

        txt_files = self.utils.filter_files(folder1, [".txt"])
        # 遍历第一个文件夹中的文件
        for index, file in enumerate(txt_files):

            file1_path = os.path.join(folder1, file.name)
            file2_path = os.path.join(folder2, file.name)

            # 如果两个文件夹中都有这个文件
            if os.path.exists(file2_path):
                # 读取文件内容
                with open(file1_path, 'r', encoding='utf-8') as file1:
                    content1 = file1.read()
                with open(file2_path, 'r', encoding='utf-8') as file2:
                    content2 = file2.read()

                # 合并内容
                merged_content = content1 + "," + content2

                # 保存合并后的文件
                output_path = os.path.join(self.input_folder, file.name)
                with open(output_path, 'w', encoding='utf-8') as output_file:
                    output_file.write(merged_content)
        # 更新进度
            self.utils.update_progress((index + 1) / len(txt_files),
                                       "Processing merge_tags:")
        # 删除两个文件夹
        shutil.rmtree(folder1)
        shutil.rmtree(folder2)

    def contains_both_keywords(self, line, delete_file_field):
        """检查是否包含 'delete_file_field' 和 ''"""
        return delete_file_field in line

    def process_line(self, line):
        """将 '1boy' 或 '1girl' 提前到行首"""
        keywords = ['1boy', '1girl', '2boy', '2girl']

        # 分割逗号并去除多余空格
        tags = [tag.strip() for tag in line.split(',') if tag.strip()]

        # 查找 '1boy' 或 '1girl'
        found_keyword = None
        for keyword in keywords:
            if keyword in tags:
                found_keyword = keyword
                tags.remove(keyword)
                break

        # 如果找到了 '1boy' 或 '1girl'，将其提前到首位
        if found_keyword:
            tags.insert(0, found_keyword)

        # 返回重新排序后的行
        return ', '.join(tags)

    def check_and_delete_file(self, file_path, delete_file_field):
        """检查文件中是否包含 '1boy' 和 '1girl'，如果包含则删除该文件及对应的图片"""
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # 检查文件中是否存在同时包含 '1boy' 和 '1girl' 的行
        for line in lines:
            if self.contains_both_keywords(line, delete_file_field):
                # 删除 .txt 文件
                os.remove(file_path)

                # 检查是否有对应的 .jpg 文件
                jpg_file_path = str(file_path).replace('.txt', '.jpg')
                if os.path.exists(jpg_file_path):
                    os.remove(jpg_file_path)  # 删除同名的 .jpg 文件
                return True  # 文件已被删除

        return False  # 文件未删除

    def process_file(self, file_path):
        """处理文件，调整关键词位置"""
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # 如果文件没有被删除，继续处理行内容
        processed_lines = [self.process_line(line) for line in lines]

        # 将处理后的内容写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines("\n".join(processed_lines))

    def adjustment_tag_process_folder(self, delete_file_field: str = "******"):
        """处理文件夹中的所有 .txt 文件"""

        txt_files = self.utils.filter_files(self.input_folder, [".txt"])
        # 遍历第一个文件夹中的文件
        for index, file in enumerate(txt_files):

            # 先检查是否删除文件
            if not self.check_and_delete_file(file, delete_file_field):
                # 如果文件没有被删除，则调整关键词位置
                self.process_file(file)

            # 更新进度
            self.utils.update_progress(
                (index + 1) / len(txt_files),
                "Processing adjustment_tag_process_folder:")
