# 🤖 Auto Report Agent: Your Intelligent Work Summary Companion


[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Containerized-blue)](https://www.docker.com/)

**告别繁琐的手动报告！Auto Report Agent 是一个基于 AI 的自动化工作汇报生成器。它能智能地从您的屏幕活动、文件变更、本地文档和跨平台沟通数据中提取信息，并将所有这些多源异构数据统一输入到强大的大语言模型（如智谱AI GLM）中进行深度分析，最终为您自动生成精准、详尽的日报、周报、月报、季度报告乃至年终总结，并支持定时邮件发送。**

**说明：大模型使用的是智普GLM-4.5，GitHub地址：https://github.com/zai-org/GLM-4.5**

## 🌟 核心亮点 (Core Highlights)

*   **全方位数据采集 (Holistic Data Collection):** 集成屏幕内容分析、本地文件系统监控、文档内容读取与主流办公平台（飞书、企业微信等）API，构建完整的个人工作数据画像。
*   **智能内容推断 (Intelligent Content Inference):** 运用 OCR、文件系统事件分析和文档解析，自动识别和归纳您的核心工作内容。
*   **统一数据融合分析 (Unified Data Fusion & Analysis):** 打破数据孤岛，将所有来源的数据在大模型端进行深度融合分析，而非简单的数据拼接。
*   **大模型驱动报告 (LLM-Powered Reporting):** 利用智谱AI GLM 等大语言模型作为分析引擎，对聚合数据进行上下文理解、关联分析和自然语言生成，产出高质量报告。
*   **灵活分发机制 (Flexible Distribution):** 支持通过电子邮件等多种方式，按预设时间自动分发报告，确保信息及时传达。
*   **模块化开关控制 (Modular Switch Control):** 每个数据采集模块和报告任务均可独立启用或禁用，灵活适配不同用户需求。
*   **容器化部署 (Containerized Deployment):** 基于 Docker 的设计，确保了环境的一致性和部署的便捷性。

## 🚀 快速开始 (Quick Start)

### 📋 前置要求 (Prerequisites)

*   **Docker** 和 **Docker Compose**
    *   [安装 Docker](https://docs.docker.com/get-docker/)
    *   [安装 Docker Compose](https://docs.docker.com/compose/install/)

### 🛠️ 本地安装与配置 (Local Installation & Configuration)

1.  **克隆或下载项目:**
    ```bash
    git clone https://github.com/qiaoxuchen/auto-report-agent.git
    cd auto-report-agent
    # 或者解压您下载的 ZIP 包
    ```

2.  **配置您的环境:**
    **重要:** 在启动前，您必须根据您的环境进行配置。
    ```bash
    # 1. 复制配置模板
    cp config/config.yaml.template config/config.yaml

    # 2. 编辑配置文件
    nano config/config.yaml # 或使用您喜欢的编辑器 (e.g., vim, code)
    ```
    在 `config.yaml` 中，您需要至少配置：
    *   `data_sources.file_monitor.watch_path`: 指向您希望监控的**本地工作目录**的**绝对路径**。
    *   `data_sources.document_reader.watch_path`: 指向包含您希望分析的文档的**本地目录**。
    *   `notifications.email.*`: 您的 SMTP 服务器信息和邮箱凭据，用于发送报告。
    *   `llm.*`: **您的智谱AI GLM API Key 和模型名称 (如 `glm-4-plus`)。这是启用大模型分析功能的关键！**

3.  **准备数据目录:**
    确保 `docker-compose.yml` 中挂载的目录在您的主机上存在，例如：
    ```bash
    mkdir -p ./example_workdir ./data/documents ./data/logs ./data/reports ./data/screenshots ./data/file_logs
    ```

4.  **启动服务:**
    ```bash
    # 使用 Docker Compose 构建并启动容器
    docker-compose up --build
    ```
    Agent 将根据您的配置开始运行。您可以在 `data/logs/` 中查看日志，在 `data/reports/` 中找到生成的报告。

5.  **停止服务:**
    ```bash
    # 在运行 `docker-compose up` 的终端中按 `Ctrl+C`
    # 或者在另一个终端中运行:
    docker-compose down
    ```

## 🧠 工作原理 (How It Works)

Auto Report Agent 通过一个协调中心 (`DataAggregator`) 来管理数据流：

1.  **数据采集 (Data Collection):**
    *   **屏幕监控 (`ScreenCaptureAgent`)**: 定时截取屏幕，利用 OCR 技术提取文本信息。
    *   **文件监控 (`FileMonitorAgent`)**: 实时监听指定目录的文件创建、修改、删除事件。
    *   **文档读取 (`DocumentReaderAgent`)**: 定时扫描指定目录，读取并解析文本文件内容。
    *   **API 集成 (`LarkDataAgent`)**: (示例) 通过飞书 API 获取日程、消息等信息。
2.  **数据聚合 (`DataAggregator`)**: 所有 Agent 收集到的数据都会被发送到这个中心进行存储和时间戳管理。
3.  **统一分析 (`AnalyzerAgent`)**:
    *   根据调度器 (`APScheduler`) 的指令，在预定时间触发分析任务。
    *   **`AnalyzerAgent` 从 `DataAggregator` 中提取所需时间范围内的所有数据。**
    *   **将所有数据整合成一个结构化的请求，通过 `requests` 库发送给智谱AI GLM API。**
    *   **提示词 (Prompt) 的设计是关键，它指导大模型如何理解、关联和总结这些数据。**
    *   **接收大模型返回的自然语言报告内容。**
4.  **报告分发 (`AnalyzerAgent`)**:
    *   将生成的报告内容通过 `smtplib` 发送到指定的电子邮件地址。

## 🛠️ 技术栈 (Tech Stack)

*   **核心语言**: Python 3.11
*   **容器化**: Docker, Docker Compose
*   **屏幕捕获与OCR**: `Pillow`, `pytesseract`
*   **文件系统监控**: `watchdog`
*   **API集成**: `lark-oapi` (飞书示例)
*   **任务调度**: `APScheduler`
*   **AI分析**: `requests` (调用大模型API)
*   **邮件发送**: Python 内置 `smtplib` 和 `email`
*   **配置管理**: `PyYAML`

## 🤝 贡献 (Contributing)

我们热烈欢迎任何形式的贡献！

*   **报告 Bug**: 请在 [Issues](https://github.com/your-username/auto-report-agent/issues) 中提交。
*   **提出新功能**: 请在 [Issues](https://github.com/your-username/auto-report-agent/issues) 中发起讨论。
*   **提交代码**: 欢迎 Fork 项目并提交 Pull Request。

请查看 [CONTRIBUTING.md](CONTRIBUTING.md) (如果存在) 了解更多详情。

## 📄 许可证 (License)

本项目采用 MIT 许可证。详情请见 [LICENSE.txt](LICENSE.txt) 文件。

## 💬 联系方式 (Contact)

如果您有任何问题或建议，请通过 [xuchenqiaovip@gmail.com](mailto:your-email@example.com) 与我们联系。

---
*让 Auto Report Agent 成为您高效工作的得力助手！*