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
