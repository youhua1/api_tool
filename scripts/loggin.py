import logging
import os


def get_logger(name: str):
    # 创建一个日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # 设置日志级别

    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    # 创建文件处理器
    os.makedirs("./log", exist_ok=True)
    file_handler = logging.FileHandler(f"./log/{name}_log.log",
                                       encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)

    # 创建一个日志格式器
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # 将格式器添加到处理器
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # 将处理器添加到日志记录器
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
