from scripts.tools.image_to_json import ImageToJson


if __name__ == "__main__":
    ImageToJson().batch_image_info_json(
        # 图片路径
        image_folder_path=R"D:\work\resource\AIGC\script\my_script\api_tool\json\sd\olympic",
        # 生图模式
        enable_t2i=True,
        # 启用人脸识别
        enable_cont_face=False,
        # 启用换脸
        enable_reactor=True,
    )
