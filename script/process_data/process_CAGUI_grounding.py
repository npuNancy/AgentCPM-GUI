{
    "messages": [
        {"role": "system", "content": "<system>"},
        {"role": "user", "content": "<query1>"},
        {"role": "assistant", "content": "<response1>"},
        {"role": "user", "content": "<query2>"},
        {"role": "assistant", "content": "<response2>"},
    ]
}
{
    "messages": [
        {"role": "user", "content": "<image><image>两张图片有什么区别"},
        {"role": "assistant", "content": "前一张是小猫，后一张是小狗"},
    ],
    "images": ["/xxx/x.jpg", "/xxx/x.png"],
}


import re
import os
import json
import base64
from PIL import Image


def read_jsonl(file_path):
    """
    读取 JSONL 文件并解析为 Python 字典列表
    :param file_path: JSONL 文件路径
    :return: 包含所有 JSON 对象的列表
    """
    data = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            data.append(json.loads(line.strip()))
    return data


def encode_image(image_path):
    """
    将图片文件编码为 base64 字符串
    :param image_path: 图片文件路径
    :return: base64编码的图片字符串，图片宽度w，图片高度h
    """
    image = Image.open(image_path)
    w, h = image.width, image.height
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8"), w, h


def get_image_size(image_path):
    image = Image.open(image_path)
    return image.width, image.height


def bbox2text():
    json_data_path = "data/CAGUI/CAGUI_grounding/code/ocr.jsonl"

    data = read_jsonl(json_data_path)
    res = []
    for item in data:
        sys_prompt = """你是一个GUI组件文字识别的专家，擅长根据组件的边界框（bounding box）描述输出对应的文字。你的任务是根据给定的GUI截图和图中某个组件的边界框输出组件的中的文字。\n输入：屏幕截图，边界框的绝对坐标<x_min, y_min, x_max, y_max>的格式表示\n输出：组件中的文本,注意是文字而非坐标！\n示例输出一：可口可乐。\n示例输出二：关注"""

        image_path = item["image"]
        image_path = image_path.replace("grounding_eval/dataset/", "")
        image_path = os.path.join(image_base_dir, image_path)

        w, h = get_image_size(image_path)

        messages_train = {
            "messages": [
                {"role": "system", "content": sys_prompt},
                {
                    "role": "user",
                    "content": f"<image>当前屏幕的尺寸为{w}*{h}，屏幕上某一组件的边界框：{item['abs_position']}",
                },
                {"role": "assistant", "content": item["text"]},
            ],
            "images": [image_path],
        }

        """
        # 推理用的格式
        base64_image, w, h = encode_image(image_path)
        messages_infer = [
            {"role": "system", "content": sys_prompt},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                        },
                    },
                    {
                        "type": "text", "text": "当前屏幕的尺寸为{}*{}，屏幕上某一组件的边界框：{}".format(w, h, item["abs_position"])
                    },
                ],
            },
            {"role": "assistant", "content": "前一张是小猫，后一张是小狗"},
        ]
        """

        res.append(messages_train)

    save_path = os.path.join(save_dir, "bbox2text.jsonl")
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=4)


def text2bbox():
    json_data_path = "data/CAGUI/CAGUI_grounding/code/ocr.jsonl"

    data = read_jsonl(json_data_path)
    res = []
    for item in data:
        schema = {
            "type": "object",
            "properties": {
                "POINT": {
                    "type": "array",
                    "description": "数组第一个元素为横坐标x，第二个元素为纵坐标y",
                    "items": {"type": "integer", "minimum": 0, "maximum": 1000},
                    "minItems": 2,
                    "maxItems": 2,
                }
            },
            "required": ["POINT"],
            "additionalProperties": False,
        }
        sys_prompt = "# Role\n你是一个GUI组件定位的专家，擅长输出图片上文本对应的坐标。# Task\n你的任务是根据给定的GUI截图和图中某个文本输出该文本的坐标。\n输入：屏幕截图，文本描述\n输出：文本的绝对坐标的中心点，以<x,y>为格式，使用<>定位，其中不能存在任何非坐标字符，注意中心点应当是两个坐标而不是四个。\n# Rule\n- 输出操作必须遵循Schema约束\n# Schema\n"
        sys_prompt += json.dumps(schema)

        image_path = item["image"]
        image_path = image_path.replace("grounding_eval/dataset/", "")
        image_path = os.path.join(image_base_dir, image_path)

        w, h = get_image_size(image_path)

        abs_position_str = item["abs_position"]  # "<x1, y1, x2, y2>"
        abs_position = re.findall(r"\d+", abs_position_str)  # ["x1", "y1", "x2", "y2"]
        abs_position = [int(x) for x in abs_position]  # [x1, y1, x2, y2]
        center_x = int((abs_position[0] + abs_position[2]) / 2)
        center_y = int((abs_position[1] + abs_position[3]) / 2)
        point = {"POINT": [center_x, center_y]}

        messages_train = {
            "messages": [
                {"role": "system", "content": sys_prompt},
                {
                    "role": "user",
                    "content": f"<image>当前屏幕的尺寸为{w}*{h}，屏幕上的文本：{item['text']}",
                },
                {"role": "assistant", "content": json.dumps(point)},
            ],
            "images": [image_path],
        }

        res.append(messages_train)

    save_path = os.path.join(save_dir, "text2point.jsonl")
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=4)


def fun2bbox():
    json_data_path = "data/CAGUI/CAGUI_grounding/code/cap.jsonl"

    data = read_jsonl(json_data_path)
    res = []
    for item in data:
        schema = {
            "type": "object",
            "properties": {
                "POINT": {
                    "type": "array",
                    "description": "数组第一个元素为横坐标x，第二个元素为纵坐标y",
                    "items": {"type": "integer", "minimum": 0, "maximum": 1000},
                    "minItems": 2,
                    "maxItems": 2,
                }
            },
            "required": ["POINT"],
            "additionalProperties": False,
        }
        sys_prompt = "# Role\n你是一个GUI组件定位的专家，擅长根据组件的功能描述输出对应的坐标。# Task\n你的任务是根据给定的GUI截图和图中某个组件的功能描述输出组件的坐标。\n输入：屏幕截图，功能描述\n输出：该功能边界框的绝对坐标的中心点，以<x,y>为格式，使用<>定位，其中不能存在任何非坐标字符，注意中心点应当是两个坐标而不是四个。\n# Rule\n- 输出操作必须遵循Schema约束\n# Schema\n"
        sys_prompt += json.dumps(schema)

        image_path = item["image"]
        image_path = image_path.replace("grounding_eval/dataset/", "")
        image_path = image_path.replace("images", "images/cap")
        image_path = os.path.join(image_base_dir, image_path)

        w, h = get_image_size(image_path)

        abs_position_str = item["abs_position"]  # "<x1, y1, x2, y2>"
        abs_position = re.findall(r"\d+", abs_position_str)  # ["x1", "y1", "x2", "y2"]
        abs_position = [int(x) for x in abs_position]  # [x1, y1, x2, y2]
        center_x = int((abs_position[0] + abs_position[2]) / 2)
        center_y = int((abs_position[1] + abs_position[3]) / 2)
        point = {"POINT": [center_x, center_y]}

        messages_train = {
            "messages": [
                {"role": "system", "content": sys_prompt},
                {
                    "role": "user",
                    "content": f"<image>当前屏幕的尺寸为{w}*{h}，屏幕上某一组件的功能描述：{item['text']}",
                },
                {"role": "assistant", "content": json.dumps(point)},
            ],
            "images": [image_path],
        }

        res.append(messages_train)

    save_path = os.path.join(save_dir, "fun2point.jsonl")
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    save_dir = "data/CAGUI_grounding"
    image_base_dir = "/data4/yanxiaokai/Models/modelscope/datasets/OpenBMB/CAGUI/CAGUI_grounding"
    bbox2text()
    text2bbox()
    fun2bbox()
