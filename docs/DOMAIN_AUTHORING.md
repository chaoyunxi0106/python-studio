# 领域迁移与复用指南

> 文档导航：[README.md](README.md)

Python Studio 的平台能力包括课程地图、练习运行、学习记录、AI 诊断、聊天和备份。
更换学科时，优先替换以下四层：

1. `studio.json`：平台名称和默认领域。
2. `domains/<domain>.json`：文件约定、检查命令和 AI 上下文。
3. `curriculum/`：知识点大纲和路线。
4. `exercises/`：题目、起始文件、测试和答案。

上下文记忆、AI 聊天、备份和维护功能无需重写。

## 领域配置

领域配置示例：

```json
{
  "id": "my_subject",
  "name": "我的学科",
  "starter_file": "starter.py",
  "test_file": "test_exercise.py",
  "solution_file": "solution.py",
  "analysis_mode": "python_ast",
  "code_extensions": [".py"],
  "primary_command": [
    "{python}",
    "-m",
    "pytest",
    "-q",
    "{test_file}"
  ],
  "fallback_command": [
    "{python}",
    "-m",
    "unittest",
    "-v",
    "{test_file}"
  ],
  "ai_context": "写给伴学 AI 的学科背景说明。"
}
```

支持的占位符：

- `{python}`：当前 Python 解释器。
- `{starter_file}`：当前练习的起始文件。
- `{test_file}`：当前练习的检查文件。

## 数据结构课程

数据结构和算法仍可使用 Python 代码作为答案。

建议：

- 使用 `data_structures.json` 作为领域模板。
- 测试重点关注时间复杂度证据、边界输入和结果正确性。
- `test_exercise.py` 可以使用 pytest 参数化。
- 对递归深度、输入规模和空间使用增加专门测试。
- `meta.json` 的 `concepts` 使用“栈”“队列”“图遍历”等稳定知识点。

## 数学优化理论

数学优化的答案可能是公式、推导和数值实验，不一定是一段 Python 函数。

建议使用 `optimization_math.json`：

- `starter.txt` 保存题目推导区或实验设计区。
- `check_optimization.py` 负责输出检查结果。
- 使用非零退出码表示失败。
- 数值答案可使用绝对误差和相对误差。
- 证明题可检查必要步骤、反例和约束条件。
- AI 上下文明确说明 KKT、凸性、对偶和证明规范。

检查脚本可以使用：

```python
import sys

def check(answer: str) -> list[str]:
    errors = []
    if "KKT" not in answer:
        errors.append("缺少 KKT 条件")
    return errors

errors = check(open("starter.txt", encoding="utf-8").read())
if errors:
    print("\n".join(errors))
    raise SystemExit(1)
print("检查通过")
```

平台会把整个检查命令视为一次通过或失败，并让 AI 根据错误输出继续诊断。

## 替换课程时保留什么

平台自身可复用的部分：

- 本地 SQLite 学习记录。
- 测试级结果和趋势。
- AI 代码或答案审查。
- 多会话聊天。
- 动态补练。
- 备份、恢复和维护。
- 知识点图谱。

需要替换的部分：

- 路线与知识点大纲。
- 练习文件约定。
- 检查命令。
- 结果解析方式。
- AI 学科提示词。

## 最小迁移步骤

1. 新增 `domains/<domain>.json`。
2. 修改 `studio.json` 的 `default_domain`。
3. 替换 `curriculum/roadmap.json` 和知识文档。
4. 创建新的 `exercises/` 内容。
5. 运行 `python studio.py validate`。
6. 运行一个示例练习检查。
7. 使用设置页确认 AI 学科上下文。
