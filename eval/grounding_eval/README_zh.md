# 评估说明

在这里，我们列出了所有的评估代码。由于每个模型的图像处理和动作空间各不相同，我们按照模型对评估代码进行了分类整理。

## 通用通知

### 第一步
请首先下载相应的图像，并替换空文件夹`eval/grounding_eval/dataset/images`。

### 第二步
我们建议使用 vLLM 作为大多数开源模型（除了 InternVL）推理的引擎，以确保推理速度。具体命令如下：
```bash
python -m vllm.entrypoints.openai.api_server --model /path/to/your/model --served-model-name name_of_your_model --tensor-parallel-size 4
```

### 第三步
修改脚本中的`json_data_path`变量为您的数据集 JSONL 文件的路径，然后运行脚本：
```bash
python your_evaluation_script_name.py
```

## 特殊模型通知

### InternVL 系列
对于 InternVL 系列模型，我们依赖其开源仓库中提供的模型加载代码进行推理。在运行评估代码之前，您需要克隆 InternVL 开源仓库并安装依赖项。然后，将推理代码放置在路径`InternVL/internvl_chat/eval`下。
之后，运行以下命令：
```bash
torchrun --nproc_per_node=8 path/to/your/evaluate_script.py --checkpoint ${CHECKPOINT} --dynamic
```

### 带有定位功能的 GPT-4o
对于 GPT-4o，除了测试其直接定位能力外，我们还使用 Omni-parser 在图像的组件上绘制边界框，让 GPT-4o选择 最相似的边界框，然后计算 IoU。

要复现这一结果，您需要首先使用 Omni-parser 处理图像，将脚本`grounding_eval/GPT-4o/process_image.py`放置在以下位置：
```
Omniparser
    ├──docs
    ...
    ├──weights
    ├──utils
    └──process_image.py
```
运行代码并将标注后的图像和边界框保存在`your/path/to/annotated/image`。

最后，将脚本中的`image_data_path`变量修改为`your/path/to/annotated/image`，并运行代码。