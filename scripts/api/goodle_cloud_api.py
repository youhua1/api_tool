import os
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from scripts.handle_exception import HandleException
from scripts.utils import Utils
from scripts.loggin import get_logger
from google.oauth2 import service_account
from googleapiclient.discovery import build


class GoogleDriveAPI:

    def __init__(self, service_account_file: str):
        self.service_account_file = service_account_file
        self.credentials = None
        self.service = None
        self.scopes = ["https://www.googleapis.com/auth/drive"]
        self.image_head = "https://drive.google.com/uc?export=download&id="
        self.logger = get_logger("GoogleDriveAPI")
        self.utils = Utils(self.logger)
        self.handle_exception = HandleException(self.logger)

    def load_google_app(self):
        try:
            # 从服务账号文件中加载凭据
            coeds = service_account.Credentials.from_service_account_file(
                self.service_account_file, scopes=self.scopes)
            # 创建Google Drive API服务
            service = build("drive", "v3", credentials=coeds)
            return service
        except Exception as error:
            self.logger.error(f"加载google时候: {error}")
            return None

    def create_folder(self, folder_name, parent_folder_id=None):
        file_metadata = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        if parent_folder_id:
            file_metadata["parents"] = [parent_folder_id]

        # 创建文件夹
        service = self.load_google_app()

        if service is None:
            return

        folder = service.files().create(body=file_metadata,
                                        fields="id").execute()
        return folder.get("id")

    def find_folderID_by_name(self, folder_name):
        # 创建Google Drive API客户端
        service = self.load_google_app()

        if service is None:
            return

        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
        results = service.files().list(q=query,
                                       spaces='drive',
                                       fields='files(id, name)').execute()
        items = results.get("files", [])
        if len(items) > 0:
            return items[0].get("id")
        return None

    def upload_file_to_drive(self, file_path, file_name, folder_name):
        # 创建Google Drive API客户端
        service = self.load_google_app()

        if service is None:
            return

        folder_id = self.find_folderID_by_name(folder_name)
        if folder_id is None:
            folder_id = self.create_folder(folder_name)

        # 上传图片文件
        file_metadata = {"name": file_name, "parents": [folder_id]}
        media = MediaFileUpload(file_path, mimetype="image/jpeg")
        file = (service.files().create(body=file_metadata,
                                       media_body=media,
                                       fields="id").execute())
        self.logger.info("File ID: %s" % file.get("id"))

        # 设置文件权限为公开
        file_id = file.get("id")
        permission = {
            "type": "anyone",
            "role": "reader",
        }
        service.permissions().create(fileId=file_id, body=permission).execute()

    def find_file_in_drive(self, folder_name):
        # 创建Google Drive API客户端
        service = self.load_google_app()

        if service is None:
            return None

        folder_id = self.find_folderID_by_name(folder_name)
        if folder_id is None:
            self.logger.warning(f"Folder {folder_name} not found.")
            return None

        # 查询文件夹中的文件
        query = f"'{folder_id}' in parents"
        results = (service.files().list(
            q=query,
            fields="nextPageToken, files(id, name, mimeType)").execute())
        items = results.get("files", [])

        if not items:
            self.logger.warning("No files found.")
        else:
            image_url_id_list = []
            for item in items:
                # 如果文件是图片，获取其公开可分享链接
                if item["mimeType"].startswith("image/"):
                    file_id = item["id"]
                    image_url_id_list.append(file_id)

            return image_url_id_list

    def batch_upload_file_to_drive(self, image_folder_path: str,
                                   folder_name: str):
        files = self.utils.filter_files(image_folder_path, [".jpg"])
        if not files:
            self.logger.warning("JPG format image not found.")

        for file in files:
            # 上传图片文件
            self.upload_file_to_drive(file, file.stem, folder_name)

    def delete_file_in_drive(
        self,
        file_id: str,
    ):
        # 创建Google Drive API客户端
        service = self.load_google_app()
        if not service:
            return

        # 删除文件
        try:
            service.files().delete(fileId=file_id).execute()
            self.logger.info("File deleted: %s" % file_id)

        except HttpError as error:
            self.logger.error("或许是图片id错误,请检查图片id是否正确")
            self.logger.error(error)
        except Exception as e:
            self.logger.error("An error occurred: %s" % e)

    def batch_delete_file_in_drive(self, image_json_path: str):
        image_dict = self.handle_exception.txt_error_handler(
            image_json_path, "r", "json_read")
        if image_dict is None:
            return None

        for image_id in list(image_dict.keys()):
            self.delete_file_in_drive(image_id)

    def batch_download_image(self, image_json_path: str, save_path: str):
        image_dict = self.handle_exception.txt_error_handler(
            image_json_path, "r", "json_read")
        if image_dict is None:
            return None
        image_list = list(image_dict.values())
        for index, image_url in enumerate(image_list):
            file_name = os.path.join(save_path, f"{index}.jpg")
            self.utils.download_image(image_url, file_name)
            self.utils.update_progress((index + 1) / len(image_list),
                                       "download image:")

    def get_image_info_json(self,
                            folder_name: str,
                            image_folder_path: str = ""):
        if image_folder_path:
            # 批量上传图片文件到Google Drive
            self.batch_upload_file_to_drive(image_folder_path, folder_name)

        # 获得Google Drive中所有的文件
        image_url_id_list = self.find_file_in_drive(folder_name)

        if image_url_id_list is None:
            return None

        # 保存数据到json
        self.save_image_url_to_json(image_url_id_list, folder_name)

    # 保存图片链接到json
    def save_image_url_to_json(self, image_url_id_list, name):
        image_json_path = os.path.join("./image/inputs/url", f"{name}.json")
        data_url_dict = {}
        for image_url_id in image_url_id_list:
            data_url_dict[image_url_id] = self.image_head + image_url_id

        # 写入图片
        self.handle_exception.txt_error_handler(image_json_path, "w",
                                                "json_write", data_url_dict)
