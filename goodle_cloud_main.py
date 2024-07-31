from scripts.api.goodle_cloud_api import GoogleDriveAPI

if __name__ == "__main__":
    # 凭证
    google = GoogleDriveAPI(
        R"json\google_cloud\getimage-426208-b80704364d69.json")

    # 批量删除json路径
    google.batch_delete_file_in_drive(
        image_json_path=R"image\inputs\url\test.json")
