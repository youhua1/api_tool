import base64
import requests
from PIL import Image
from io import BytesIO


def filename_to_base64(filename):
    with open(filename, "rb") as fh:
        return base64.b64encode(fh.read())


img_filename = R"D:\bucket\qq\文件\MobileFile\Image_1711302920692.jpg"
url = "http://192.168.1.166:7861/sam/sam-predict"
payload = {
    "input_image": filename_to_base64(img_filename).decode(),
    "dino_enabled": True,
    "dino_text_prompt": "clothes",
    "dino_preview_checkbox": False,
}
response = requests.post(url, json=payload)
reply = response.json()
print(reply["msg"])

grid = Image.new('RGBA', (3 * 512, 3 * 512))


def paste(img, row):
    for idx, img in enumerate(img):
        img_pil = Image.open(BytesIO(base64.b64decode(img))).resize((512, 512))
        grid.paste(img_pil, (idx * 512, row * 512))


paste(reply["blended_images"], 0)
paste(reply["masks"], 1)
paste(reply["masked_images"], 2)
grid.show()
