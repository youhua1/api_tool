from openai import OpenAI
import os
from IPython.display import Image, display
from scripts.utils import image_to_base64


def openai_main(
        MODEL="gpt-4o",
        OPENAI_API_KEY="sk-akerAJ3KVYGyX82s718b50AfBb9c4764998987DcCc1c67E4",
        IMAGE_PATH=""):

    # 将这里换成你在便携AI聚合API后台生成的令牌
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
    # 这里将官方的接口访问地址替换成便携AI聚合API的入口地址
    os.environ["OPENAI_BASE_URL"] = "https://api.bianxieai.com/v1"
    client = OpenAI()

    try:
        # 解析图片
        display(Image(IMAGE_PATH))
    except Exception as e:
        print(f"Error: {e}")
        return
    base64_image = image_to_base64(IMAGE_PATH)
    if base64_image is None:
        return

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            # {"role": "system", "content": "You are ChatGPT, a large language model trained by OpenAI."},
            {
                "role":
                "user",
                "content": [{
                    "type":
                    "text",
                    "text":
                    "Help me identify key words in the picture and separate them with commas"
                }, {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_image}"
                    }
                }]
            }
        ],
        temperature=0.7,
    )

    print(response.choices[0].message.content)


def openai_batch_main(openai_batch_json_path: str):
    # 将这里换成你在便携AI聚合API后台生成的令牌
    os.environ[
        "OPENAI_API_KEY"] = "sk-akerAJ3KVYGyX82s718b50AfBb9c4764998987DcCc1c67E4"
    # 这里将官方的接口访问地址替换成便携AI聚合API的入口地址
    os.environ["OPENAI_BASE_URL"] = "https://api.bianxieai.com/v1"
    client = OpenAI()

    batch_input_file = client.files.create(file=open(openai_batch_json_path,
                                                     "rb"),
                                           purpose="batch")
    print(batch_input_file)
    batch_input_file_id = batch_input_file.id

    client.batches.create(input_file_id=batch_input_file_id,
                          endpoint="/v1/chat/completions",
                          completion_window="24h",
                          metadata={"description": "nightly eval job"})
