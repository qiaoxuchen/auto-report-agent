# 🤖 Auto Report Agent: Your Intelligent Work Summary Companion

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Containerized-blue)](https://www.docker.com/)
<!-- [![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md) -->
<!-- [![GitHub issues](https://img.shields.io/github/issues/your-username/auto-report-agent)](https://github.com/your-username/auto-report-agent/issues) -->

**告别繁琐的手动报告！Auto Report Agent 是一个基于 AI 的自动化工作汇报生成器。它能智能地从您的屏幕活动、文件变更和跨平台沟通数据中提取信息，为您自动生成精准、详尽的日报、周报、月报、季度报告乃至年终总结，并支持定时邮件发送。**

## 🌟 核心亮点 (Core Highlights)

*   **全方位数据采集 (Holistic Data Collection):** 集成屏幕内容分析、本地文件系统监控与主流办公平台（飞书、企业微信等）API，构建完整的个人工作数据画像。
*   **智能内容推断 (Intelligent Content Inference):** 运用 OCR 和文件系统事件分析，自动识别和归纳您的核心工作内容，无需手动输入。
*   **多源数据融合 (Multi-source Data Fusion):** 打通不同工具和平台的数据孤岛，将分散的信息整合为连贯的工作脉络。
*   **自动化报告生成 (Automated Report Generation):** 基于强大的模板引擎或可扩展的 AI 分析模型，将原始数据转化为结构化、可读性强的工作报告。
*   **灵活分发机制 (Flexible Distribution):** 支持通过电子邮件等多种方式，按预设时间自动分发报告，确保信息及时传达。
*   **容器化部署 (Containerized Deployment):** 基于 Docker 的设计，确保了环境的一致性和部署的便捷性。

## 🚀 快速开始 (Quick Start)

### 📋 前置要求 (Prerequisites)

*   **Docker** 和 **Docker Compose** (推荐用于隔离和简化部署)
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
    *   `file_monitor.watch_path`: 指向您希望监控的**本地工作目录**的**绝对路径**。
    *   `email.*`: 您的 SMTP 服务器信息和邮箱凭据，用于发送报告。
    *   (可选) `lark.*`: 您的飞书应用凭证，用于集成日程和消息。

3.  **启动服务:**
    ```bash
    # 使用 Docker Compose 构建并启动容器
    docker-compose up --build
    ```
    Agent 将根据您的配置开始运行。您可以在 `data/logs/` 中查看日志，在 `data/reports/` 中找到生成的报告。

4.  **停止服务:**
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
    *   **API 集成 (`LarkDataAgent`)**: (示例) 通过飞书 API 获取日程、消息等信息。
2.  **数据聚合 (`DataAggregator`)**: 所有 Agent 收集到的数据都会被发送到这个中心进行存储和管理。
3.  **报告生成 (`ReportGeneratorAgent`)**:
    *   根据调度器 (`APScheduler`) 的指令，在预定时间触发报告生成任务。
    *   从 `DataAggregator` 中提取所需时间范围内的数据。
    *   使用 `Jinja2` 模板引擎将数据渲染成预定义格式的报告。
4.  **报告分发 (`ReportGeneratorAgent`)**:
    *   将生成的报告内容通过 `smtplib` 发送到指定的电子邮件地址。

## 🛠️ 技术栈 (Tech Stack)

*   **核心语言**: Python 3.10+
*   **容器化**: Docker, Docker Compose
*   **屏幕捕获与OCR**: `Pillow`, `pytesseract`
*   **文件系统监控**: `watchdog`
*   **API集成**: `lark-oapi` (飞书示例)
*   **任务调度**: `APScheduler`
*   **报告渲染**: `Jinja2`
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