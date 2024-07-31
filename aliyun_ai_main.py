from scripts.api.aliyun_ai import AliyunAi

if __name__ == "__main__":
    aliyun_ai = AliyunAi(api_key="sk-cebbd2ad8eb147da8125cc5c21edba5a",
                         access_key="LTAI5tGpqbz74kXwQYCmbPqU",
                         access_key_secret="HN1LXmK8WMHA5JpPEpO2OPUESSQvsn")

    aliyun_ai.aliyun_vl_llm_batch(
        image_folder_path=R"D:\work\resource\AIGC\图片数据\我的素材\艺术_抽象\风景-阿里云\test",
        vl_prompt="详细的识别图中的内容，我只需要图片内容",
        llm_prompt="提取内容关键词，并用逗号隔开",
        filter_llm_prompt="保留详细的描述词，删除以上内容的风格词，保持格式不变，我只需要我提供的内容,不需要你的解释")
