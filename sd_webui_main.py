from scripts.api.sd_webui import SdWebui

if __name__ == "__main__":
    url0 = "http://192.168.1.165:7860"
    url1 = "http://192.168.1.165:7861"
    sd = SdWebui(
        # 模板配置路径
        models_json_path=R"json\sd\olympic",
        # 图片路径
        data_image_url_path="./image/inputs/url/user_image.json")

    for i in range(0, 30):
        sd.main_process(
            # 请求地址
            url=url0,
            # 模板配置id
            models_id=0,
            # 图片id
            image_url_id=i)

    # sd.thread_entry(
    #     urls=[url1, url0],
    #     # 模板配置id
    #     models_id=0,
    #     # 图片id
    #     image_url_id=0,
    # )
