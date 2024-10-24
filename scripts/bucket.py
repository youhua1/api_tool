# 获取阿里云模型字典
import re


def get_aliyun_model_dict():
    aliyun_model_dict = {
        "qwen-long": {
            "input_tokens": 0.0005,
            "output_tokens": 0.002
        },
        "qwen-vl-plus": {
            "input_tokens": 0.008,
            "output_tokens": 0.008
        },
        "qwen2-72b-instruct": {
            "input_tokens": 0.005,
            "output_tokens": 0.01
        },
    }
    return aliyun_model_dict


# 存放sdxl分辨率的字典
def get_resolution_dict(enable_sd: bool = False):
    resolution_dict_xl = {
        0.25: "512_2048",
        0.26: "512_1984",
        0.27: "512_1920",
        0.28: "512_1856",
        0.32: "579_1792",
        0.33: "579_1728",
        0.35: "579_1600",
        0.4: "640_1600",
        0.42: "640_1440",
        0.48: "704_1472",
        0.5: "704_1360",
        0.52: "704_1344",
        0.57: "768_1344",
        0.6: "768_1280",
        0.68: "832_1216",
        0.72: "832_1152",
        0.78: "896_1152",
        0.82: "896_1088",
        0.88: "960_1088",
        0.94: "960_1024",
        1: "1024_1024",
        1.07: "1024_960",
        1.13: "1088_960",
        1.21: "1088_896",
        1.29: "1152_896",
        1.38: "1152_832",
        1.46: "1216_832",
        1.67: "1280_768",
        1.75: "1344_768",
        2: "1408_704",
        2.09: "1472_704",
        2.33: "1568_672",
        2.4: "1536_640",
        2.5: "1600_640",
        2.89: "1664_579",
        3: "1728_576",
        3.11: "1792_576",
        3.62: "1856_512",
        3.75: "1920_512",
        3.88: "1984_512",
        4: "2048_512",
    }

    resolution_dict_sd = {
        0.67: "512_768",
        1: "512_512",
        1.5: "768_512",
    }
    return resolution_dict_sd if enable_sd else resolution_dict_xl


def sagemaker_params_dict(dick_info: dict,
                          template_name: str = "",
                          enable_ai_fasic_art: bool = False):
    sagemaker_params_dict = {
        "task_type": "loremode",
        "models": {
            "Stable-diffusion": [f"{dick_info['Model']}.safetensors"]
        },
        "sagemaker_endpoint_name": "$sagemaker_endpoint_name$",
        "inference_type": "Async",
        "origin_placeholder": "$origin_placeholder$",
        "user_account": "$user_account$",
        "template_id": "$temp_id$",
        "template_name": "$temp_name$",
    }

    # 获取模板类型
    if enable_ai_fasic_art:
        sagemaker_params_dict["task_type"] = "mixmode"
        sagemaker_params_dict["template_name"] = template_name

    # 获取VAE模型列表
    vae = dick_info.get("VAE", "")
    if vae:
        sagemaker_params_dict["models"]["VAE"] = [vae]

    # 获取ControlNet模型列表
    controlnet = dick_info.get("controlnet", [])
    if controlnet:
        controlnet_models_list = [
            controlnet_models_dict().get(
                controlnet_model["model"].split(" [")[0])
            for controlnet_model in controlnet if controlnet_models_dict().get(
                controlnet_model["model"].split(" [")[0]) is not None
        ]
        sagemaker_params_dict["models"]["ControlNet"] = controlnet_models_list

    # 获取Lora模型列表
    lora = dick_info.get("Lora hashes", "")
    if lora:
        sagemaker_params_dict["models"]["Lora"] = [f"{lora}.safetensors"]

    # 获取embeddings
    embeddings = dick_info.get("embeddings", [])
    if embeddings:
        embeddings_list = [
            embeddings_models_dict().get(embeddings_model.split(":")[0])
            for embeddings_model in embeddings if embeddings_models_dict().get(
                embeddings_model.split(":")[0]) is not None
        ]
        sagemaker_params_dict["models"]["embeddings"] = embeddings_list

    return sagemaker_params_dict


def wd1_4_params_dict(wd1_4_threshold: str = 0.85):
    wd1_4_params_dict = {
        "task": "tagger",
        "params": {
            "image": "$origin_base64_placeholder$",
            "model": "wd-v1-4-moat-tagger.v2",
            "threshold": wd1_4_threshold,
        },
    }
    return wd1_4_params_dict


def i2i_params_dict_ai_fasic_art(dick_info: dict):
    i2i_params_dict = {
        "task": "img2img",
        "params": {
            "override_settings": {
                "CLIP_stop_at_last_layers": 2
            },
            "init_images": ["$origin_base64_placeholder$"],
            "prompt": f"{dick_info['prompt']},$tagger_placeholder$,",
            "negative_prompt": dick_info["Negative prompt"],
            "seed": -1,
            "subseed": -1,
            "subseed_strength": 0,
            "seed_resize_from_h": -1,
            "seed_resize_from_w": -1,
            "sampler_name": dick_info["Sampler"],
            "batch_size": 1,
            "n_iter": 1,
            "steps": int(dick_info["Steps"]),
            "cfg_scale": float(dick_info["CFG scale"]),
            "width": 666,
            "height": 667,
        },
    }

    # 获得VAE模型列表
    vae = dick_info.get("VAE", "")
    if vae:
        i2i_params_dict["params"]["VAE"] = vae
        
    # 获得resize_mode
    resize_mode = dick_info.get("resize_mode", 1)
    i2i_params_dict["params"]["resize_mode"] = resize_mode

    # 获得denoising_strength
    denoising_strength = dick_info.get("Denoising strength", 0.4)
    i2i_params_dict["params"]["denoising_strength"] = denoising_strength

    # 获得ControlNet列表
    controlnet_list = dick_info.get("controlnet", [])
    if controlnet_list:
        i2i_params_dict["params"].setdefault(
            "alwayson_scripts",
            {}).setdefault("controlnet",
                           {}).setdefault("args", controlnet_list)

    # 获得ADetailer列表
    adetailer_dict = dick_info.get("ADetailer", [])
    if adetailer_dict:
        adetailer_dict = adetailer_dict[0]
        i2i_params_dict["params"].setdefault(
            "alwayson_scripts", {}).setdefault("ADetailer", {}).setdefault(
                "args",
                [
                    True,
                    False,
                    {
                        "ad_model":
                        adetailer_dict["ADetailer model"],
                        "ad_prompt":
                        "",
                        "ad_negative_prompt":
                        "",
                        "ad_confidence":
                        adetailer_dict["ADetailer confidence"],
                        "ad_dilate_erode":
                        adetailer_dict["ADetailer dilate erode"],
                        "ad_mask_blur":
                        adetailer_dict["ADetailer mask blur"],
                        "ad_denoising_strength":
                        adetailer_dict["ADetailer denoising strength"],
                        "ad_inpaint_only_masked":
                        adetailer_dict["ADetailer inpaint only masked"],
                        "ad_inpaint_only_masked_padding":
                        adetailer_dict["ADetailer inpaint padding"],
                    },
                ],
            )

    return i2i_params_dict


def i2i_params_dict_explore(dick_info: dict):
    i2i_params_dict = {
        "task": "img2img",
        "origin_prompt": "$origin_prompt$",
        "magic_prompt": 199,
        "params": {
            "override_settings": {
                "CLIP_stop_at_last_layers": 2
            },
            "init_images": ["$origin_base64_placeholder$"],
            "prompt": f"{dick_info['prompt']}$prompt_placeholder$,",
            "negative_prompt":
            f"$negative_prompt_placeholder$,{dick_info['Negative prompt']}",
            "seed": 200,
            "subseed": -1,
            "subseed_strength": 0,
            "seed_resize_from_h": -1,
            "seed_resize_from_w": -1,
            "sampler_name": dick_info["Sampler"],
            "batch_size": 1,
            "n_iter": 1,
            "steps": 201,
            "cfg_scale": 202,
            "width": 203,
            "height": 204,
            "denoising_strength": 205,
        },
    }

    # 获得VAE模型列表
    vae = dick_info.get("VAE", "")
    if vae:
        i2i_params_dict["params"]["VAE"] = vae

    # 获得resize_mode
    resize_mode = dick_info.get("resize_mode", 1)
    i2i_params_dict["params"]["resize_mode"] = resize_mode

    # # 获得ControlNet列表
    # controlnet_list = dick_info.get("controlnet", [])
    # if controlnet_list:
    #     i2i_params_dict["params"].setdefault(
    #         "alwayson_scripts",
    #         {}).setdefault("controlnet",
    #                        {}).setdefault("args", controlnet_list)

    # # 获得ADetailer列表
    # adetailer_dict = dick_info.get("ADetailer", [])
    # if adetailer_dict:
    #     adetailer_dict = adetailer_dict[0]
    #     i2i_params_dict["params"].setdefault(
    #         "alwayson_scripts", {}).setdefault("ADetailer", {}).setdefault(
    #             "args",
    #             [
    #                 True,
    #                 False,
    #                 {
    #                     "ad_model":
    #                     adetailer_dict["ADetailer model"],
    #                     "ad_prompt":
    #                     "",
    #                     "ad_negative_prompt":
    #                     "",
    #                     "ad_confidence":
    #                     adetailer_dict["ADetailer confidence"],
    #                     "ad_dilate_erode":
    #                     adetailer_dict["ADetailer dilate erode"],
    #                     "ad_mask_blur":
    #                     adetailer_dict["ADetailer mask blur"],
    #                     "ad_denoising_strength":
    #                     adetailer_dict["ADetailer denoising strength"],
    #                     "ad_inpaint_only_masked":
    #                     adetailer_dict["ADetailer inpaint only masked"],
    #                     "ad_inpaint_only_masked_padding":
    #                     adetailer_dict["ADetailer inpaint padding"],
    #                 },
    #             ],
    #         )

    return i2i_params_dict


def t2i_params_dict_ai_fasic_art(dick_info: dict):
    t2i_params_dict = {
        "task": "txt2img",
        "params": {
            "override_settings": {
                "CLIP_stop_at_last_layers": 2
            },
            "prompt": f"{dick_info['prompt']},$tagger_placeholder$,",
            "negative_prompt": dick_info['Negative prompt'],
            "seed": -1,
            "subseed": -1,
            "subseed_strength": 0,
            "seed_resize_from_h": -1,
            "seed_resize_from_w": -1,
            "sampler_name": dick_info["Sampler"],
            "batch_size": 1,
            "n_iter": 1,
            "steps": int(dick_info["Steps"]),
            "cfg_scale": float(dick_info["CFG scale"]),
            "width": 666,
            "height": 667,
            "enable_hr": False,
            "hr_second_pass_steps": 0,
            "hr_scale": 2,
            "hr_upscaler": "8x_NMKD-Superscale_150000_G",
            "denoising_strength": 0.4,
        },
    }

    # 获得VAE模型列表
    vae = dick_info.get("VAE", "")
    if vae:
        t2i_params_dict["params"]["VAE"] = vae

    # 获得ControlNet列表
    controlnet_list = dick_info.get("controlnet", [])
    if controlnet_list:
        t2i_params_dict["params"].setdefault(
            "alwayson_scripts",
            {}).setdefault("controlnet",
                           {}).setdefault("args", controlnet_list)

    # 获得ADetailer列表
    adetailer_dict = dick_info.get("ADetailer", [])
    if adetailer_dict:
        adetailer_dict = adetailer_dict[0]
        t2i_params_dict["params"].setdefault(
            "alwayson_scripts", {}).setdefault("ADetailer", {}).setdefault(
                "args",
                [
                    True,
                    False,
                    {
                        "ad_model":
                        adetailer_dict["ADetailer model"],
                        "ad_prompt":
                        "",
                        "ad_negative_prompt":
                        "",
                        "ad_confidence":
                        adetailer_dict["ADetailer confidence"],
                        "ad_dilate_erode":
                        adetailer_dict["ADetailer dilate erode"],
                        "ad_mask_blur":
                        adetailer_dict["ADetailer mask blur"],
                        "ad_denoising_strength":
                        adetailer_dict["ADetailer denoising strength"],
                        "ad_inpaint_only_masked":
                        adetailer_dict["ADetailer inpaint only masked"],
                        "ad_inpaint_only_masked_padding":
                        adetailer_dict["ADetailer inpaint padding"],
                    },
                ],
            )

    return t2i_params_dict


def t2i_params_dict_explore(dick_info: dict):
    t2i_params_dict = {
        "task": "txt2img",
        "origin_prompt": "$origin_prompt$",
        "magic_prompt": 199,
        "params": {
            "override_settings": {
                "CLIP_stop_at_last_layers": 2
            },
            "prompt": f"{dick_info['prompt']},$prompt_placeholder$,",
            "negative_prompt":
            f"$negative_prompt_placeholder$,{dick_info['Negative prompt']}",
            "seed": 200,
            "subseed": -1,
            "subseed_strength": 0,
            "seed_resize_from_h": -1,
            "seed_resize_from_w": -1,
            "sampler_name": dick_info["Sampler"],
            "batch_size": 1,
            "n_iter": 1,
            "steps": 201,
            "cfg_scale": 202,
            "width": 203,
            "height": 204,
            "enable_hr": False,
            "hr_second_pass_steps": 0,
            "hr_scale": 2,
            "hr_upscaler": "8x_NMKD-Superscale_150000_G",
            "denoising_strength": 0.4,
        },
    }

    # 获得VAE模型列表
    vae = dick_info.get("VAE", "")
    if vae:
        t2i_params_dict["params"]["VAE"] = vae

    # # 获得ControlNet列表
    # controlnet_list = dick_info.get("controlnet", [])
    # if controlnet_list:
    #     t2i_params_dict["params"].setdefault(
    #         "alwayson_scripts",
    #         {}).setdefault("controlnet",
    #                        {}).setdefault("args", controlnet_list)

    # # 获得ADetailer列表
    # adetailer_dict = dick_info.get("ADetailer", [])
    # if adetailer_dict:
    #     adetailer_dict = adetailer_dict[0]
    #     t2i_params_dict["params"].setdefault(
    #         "alwayson_scripts", {}).setdefault("ADetailer", {}).setdefault(
    #             "args",
    #             [
    #                 True,
    #                 False,
    #                 {
    #                     "ad_model":
    #                     adetailer_dict["ADetailer model"],
    #                     "ad_prompt":
    #                     "",
    #                     "ad_negative_prompt":
    #                     "",
    #                     "ad_confidence":
    #                     adetailer_dict["ADetailer confidence"],
    #                     "ad_dilate_erode":
    #                     adetailer_dict["ADetailer dilate erode"],
    #                     "ad_mask_blur":
    #                     adetailer_dict["ADetailer mask blur"],
    #                     "ad_denoising_strength":
    #                     adetailer_dict["ADetailer denoising strength"],
    #                     "ad_inpaint_only_masked":
    #                     adetailer_dict["ADetailer inpaint only masked"],
    #                     "ad_inpaint_only_masked_padding":
    #                     adetailer_dict["ADetailer inpaint padding"],
    #                 },
    #             ],
    #         )

    return t2i_params_dict


def extra_single_image_params_dict():
    extra_single_image_params_dict = {
        "task": "extra-single-image",
        "params": {
            "resize_mode": 1,
            "image": "$extra_placeholder$",
            "upscaling_resize_w": 666,
            "upscaling_resize_h": 667,
            "upscaling_crop": True,
            "upscaler_1": "8x_NMKD-Superscale_150000_G",
        },
    }
    return extra_single_image_params_dict


def cont_face_params_dict():
    cont_face_params_dict = {
        "task": "count_faces",
        "origin_placeholder": "$origin_placeholder$",
        "params": {
            "input_image": "$origin_base64_placeholder$"
        },
    }
    return cont_face_params_dict


def reactor_params_dict(enable_cont_face: bool):
    reactor_params_dict = {
        "task": "reactor",
        "params": {
            "source_image": "$origin_base64_placeholder$",
            "target_image": "$reactor_placeholder$",
            "source_faces_index": [0],
            "face_index": [0],
            "upscaler": "None",
            "scale": 1,
            "upscale_visibility": 1,
            "face_restorer": "CodeFormer",
            "restorer_visibility": 1,
            "codeformer_weight": 0.8,
            "restore_first": 1,
            "model": "inswapper_128.onnx",
            "gender_source": 0,
            "gender_target": 0,
            "save_to_file": 0,
            "result_file_path": "",
            "device": "CUDA",
            "mask_face": 0,
            "select_source": 0,
            "face_model": "None",
            "source_folder": "",
            "random_image": 0,
            "upscale_force": 0,
            "det_thresh": 0.5,
            "det_maxnum": 0,
        },
    }
    if enable_cont_face:
        reactor_params_dict["params"]["source_faces_index"] = [
            "$facecount_placeholder$"
        ]
        reactor_params_dict["params"]["face_index"] = [
            "$facecount_placeholder$"
        ]
    return reactor_params_dict


def controlnet_models_dict():
    controlnet_modles_dict = {
        "control_v11f1e_sd15_tile": "control_v11f1e_sd15_tile.pth",
        "control_v11p_sd15_lineart": "control_v11p_sd15_lineart.pth",
        "control_v11p_sd15_depth": "control_v11p_sd15_depth.pth",
        "control_v11p_sd15_softedge": "control_v11p_sd15_softedge.pth",
        "control_v11p_sd15_canny": "control_v11p_sd15_canny.pth",
        "control_v11p_sd15_openpose": "control_v11p_sd15_openpose.pth",
        "ip-adapter-faceid-plus_sd15": "ip-adapter-faceid-plus_sd15.pth",
        "ip-adapter-faceid-plusv2_sd15": "ip-adapter-faceid-plusv2_sd15.pth",
        "ip-adapter-full-face_sd15": "ip-adapter-full-face_sd15.pth",
        "ip-adapter-plus-face_sd15": "ip-adapter-plus-face_sd15.pth",
        "ip-adapter-faceid-portrait_sd15": "can not use",
    }
    return controlnet_modles_dict


def embeddings_models_dict():
    embeddings_models_dict = {
        "bad-hands-5": "bad-hands-5.pt",
        "badhandv4": "badhandv4.pt",
        "bhands-neg": "bhands-neg.pt",
        "CyberRealistic_Negative": "CyberRealistic_Negative.pt",
        "CyberRealistic_Negative_v2": "CyberRealistic_Negative_v2.pt",
        "CyberRealistic_Negative_v3": "CyberRealistic_Negative_v3.pt",
        "EasyNegative": "EasyNegative.safetensors",
        "EasyNegativeV2": "EasyNegativeV2.safetensors",
        "negative_hand-neg": "negative_hand-neg.pt",
        "ng_deepnegative_v1_75t": "ng_deepnegative_v1_75t.pt",
        "verybadimagenegative_v1.3": "verybadimagenegative_v1.3.pt",
    }
    return embeddings_models_dict


def base64_json_dict(data_dict: dict, models_path: str, image_url: str):
    base64_json_dict = {
        "task": "mixmode",
        "models": {
            "Stable-diffusion": [{
                "model_name":
                str(
                    models_path.get(
                        re.sub(
                            r'\.(safetensors|pt|ckpt)$', '',
                            data_dict["sagemaker_params"]["models"]
                            ["Stable-diffusion"][0]),
                        "",
                    ))
            }],
            "VAE": [{
                "model_name":
                data_dict.get("sagemaker_params").get("models").get(
                    "VAE", ["vae-ft-mse-840000-ema-pruned.safetensors"])[0]
            }],
        },
        "origin_placeholder": image_url,
        "payload": data_dict["sd_params"],
    }
    return base64_json_dict
