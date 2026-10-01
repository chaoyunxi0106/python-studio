# Python Studio 1.0

Python Studio 是一个本地优先、由 AI 驱动的学习工作台。1.0 发行版只保留平台框架，不内置课程、知识大纲、练习题、个人进度或 API 密钥。

首次使用时，你需要：

1. 配置自己的 AI API。
2. 输入学习科目、目标或材料。
3. 让 AI 生成知识大纲、知识点、讲解、练习和评估内容。
4. 在本地持续学习，所有进度和生成结果只保存在本机。

## 环境要求

- Python 3.11 或更高版本
- DeepSeek 或 OpenAI 兼容接口
- 现代浏览器

## 启动

```powershell
cd python-studio_1.0
python studio.py doctor
python studio.py serve --port 8765
```

然后打开：

```text
http://127.0.0.1:8765
```

## 启动排查

如果页面仍显示旧课程、旧历史记录或已配置的 API，通常不是 1.0 读取了旧数据，而是旧版服务仍占用端口，浏览器继续连接到了旧进程。

启动前请确认：

1. VS Code 打开的是 `python-studio_1.0` 文件夹本身。
2. 终端运行 `python studio.py doctor`，输出的 `Project:` 路径必须以 `python-studio_1.0` 结尾。
3. `http://127.0.0.1:8765` 没有其他 Python Studio 服务正在运行。
4. 如果 8765 已被占用，先停止旧终端中的服务，或使用 `python studio.py serve --port 8766`。

PowerShell 可以检查端口占用：

```powershell
Get-NetTCPConnection -LocalPort 8765 -State Listen
```

## 首次配置

1. 打开网页左侧的“设置”。
2. 在“模型”页填写 API 密钥、Base URL、模型名称、超时和历史记录上限。
3. 保存后使用“测试”确认连接正常。
4. 打开“工坊 > 编译”。
5. 输入学习科目和已有材料，或只填写科目主题。
6. 系统让 AI 生成课程蓝图，并将知识点物化为可练习的任务。

API 配置也可以写入项目根目录的 `.env`：

```text
DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_TIMEOUT_SECONDS=60
COMPANION_HISTORY_LIMIT=40
DEEPSEEK_PROXY=
```

`.env` 已从 Git 中排除，API 密钥不会发送到浏览器。

## 从零创建科目

平台不要求你预先准备课程文件。推荐工作流：

1. 在“工坊 > 编译”输入科目名称和知识材料。
2. AI 生成课程目标、模块、知识点、学习活动和评估策略。
3. 平台根据蓝图生成正式练习。
4. 在“练习”中完成代码题、选择题、文本题、证明题或反思题。
5. 在“档案”中查看记录、薄弱点和补练建议。
6. 在“伴学”中围绕具体题目继续提问。

AI 创建、修改或读取练习时，内部 `exercise_id` 由平台管理。AI 应先自行读取上下文或创建新练习，不要求用户手工提供内部 ID。

## 本地数据

生成的科目、练习、进度和数据库位于：

```text
subjects/<subject-id>/
```

以下内容不会进入版本库：

- `.env`
- `**/data/`
- `**/progress.json`
- 缓存目录
- 本地备份历史

## 项目结构

```text
dashboard/                 网页界面
docs/                      架构、前端和协作规范
domains/                   通用领域配置
src/python_studio/         平台核心代码
tests/                     自动化测试
curriculum/                默认工作区空课程骨架
exercises/                 默认工作区练习题目录
subjects/                  用户生成的独立科目工作区
studio.py                  本地启动入口
network_check.py           网络连接诊断
```

## 常用命令

```powershell
python studio.py list
python studio.py next
python studio.py progress
python studio.py validate
python studio.py serve --port 8765
python -m pytest -q
```

## 设计原则

- 平台提供通用学习流程，不预置具体学科答案。
- 课程、题目和学习内容由用户配置的 AI 从零生成。
- 本地数据与源码分离，方便安全上传和协作。
- AI 负责生成和建议，用户负责理解、验证和最终判断。

## License

This project is licensed under the MIT License. See `LICENSE`.

更多说明见 `docs/README.md`、`docs/ARCHITECTURE.md` 和 `docs/UI_DESIGN_GUIDE.md`。
