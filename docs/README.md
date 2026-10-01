# Python Studio 文档导航

本目录集中存放开发、架构、产品和复用指导。课程学习者入口仍是项目根目录的
`README.md`；具体学习内容、知识点和路线说明保留在 `curriculum/`，避免文档职责重叠。

## 开发与架构

| 文档 | 用途 |
| --- | --- |
| [ARCHITECTURE.md](ARCHITECTURE.md) | 程序分层、模块职责、数据模型、接口、关键调用链和调试定位 |
| [PLATFORM_ROADMAP.md](PLATFORM_ROADMAP.md) | 当前架构演进、风险和后续里程碑 |

## 产品与前端

| 文档 | 用途 |
| --- | --- |
| [FRONTEND_PRD.md](FRONTEND_PRD.md) | 浏览器端信息架构、交互、视觉、响应式和无障碍要求 |
| [UI_DESIGN_GUIDE.md](UI_DESIGN_GUIDE.md) | 布局、色彩、字体、组件、响应式和视觉验收执行指南 |
| [AI_COLLABORATION.md](AI_COLLABORATION.md) | 学习者与 AI 协作的提示层级、提问模板和代码审查约定 |

## 领域与内容制作

| 文档 | 用途 |
| --- | --- |
| [DOMAIN_AUTHORING.md](DOMAIN_AUTHORING.md) | 领域配置、检查命令和跨学科复用方式 |
| [../curriculum/README.md](../curriculum/README.md) | 默认 Python 课程入口 |
| [../curriculum/OUTLINE.md](../curriculum/OUTLINE.md) | 课程模块和总体学习路线 |
| [../curriculum/KNOWLEDGE_OUTLINE.md](../curriculum/KNOWLEDGE_OUTLINE.md) | 完整知识点清单和前置关系 |
| [../curriculum/EXERCISE_AUTHORING.md](../curriculum/EXERCISE_AUTHORING.md) | 练习文件结构、替换和维护规范 |

## 目录职责

```text
README.md                        用户入口和学习方式
docs/                            开发、架构、产品和复用指导
curriculum/                      课程路线、知识点和练习编写规范
labs/                            实验区说明
journal/                         学习复盘模板
projects/                        项目说明和验收条件
```

修改程序结构、接口或数据模型后，应同步更新 `ARCHITECTURE.md`；修改产品交互后，
应同步更新 `FRONTEND_PRD.md`；修改课程结构或练习流程后，应同步更新对应的
`curriculum/` 文档。
