from scripts.tools.barrelling import Barrelling


if __name__ == "__main__":
    Barrelling().main_barrelling(
        # 分桶路径
        image_path=R"D:\work\resource\AIGC\图片数据\工作素材\y2k\y2k-高腰牛仔\原图\高腰牛仔",
        # 启用分桶
        enable_bucket=False,
        # 调整图片
        enable_resize_image=False,
        # 启用SD分辨率
        enable_sd=True,
    )
