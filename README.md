# LexiMind: AI-Powered TOEFL English Learning Web App  
# LexiMind：基于 AI 的托福英语学习 Web 应用

## 1. Project Overview · 项目概述

LexiMind is a web-based application designed to assist TOEFL learners in improving vocabulary, phrase usage, and writing skills through structured interactions with large language model APIs. The system enforces a strict prompt-command format to minimize token usage and ensure predictable outputs.

LexiMind 是一个基于 Web 的应用，旨在通过与大语言模型的结构化交互，帮助托福学习者提升词汇、短语使用和写作能力。系统采用严格的指令格式来减少 token 消耗并保证输出的可控性。

---

## 2. Core Design Principle · 核心设计原则

All user inputs must follow predefined command patterns. Inputs that do not match any valid pattern will be rejected by the backend without invoking the LLM API.

所有用户输入必须符合预定义的指令格式。不符合格式的输入将被后端直接拒绝，不调用大模型 API。

---

## 3. Command System · 指令系统

| Command · 指令 | Function · 功能 | Output · 输出 |
| :--- | :--- | :--- |
| `$ word` | Explain a single word in English only · 纯英文解释单词 | Meaning (EN), Usage (TOEFL context), Example sentences · 英文释义、托福语境用法、例句 |
| `$cn word` | Word explanation + Chinese translation · 单词解释并附带中文翻译 | Same as `$` + Chinese translation · 在 `$` 基础上增加中文翻译 |
| `$cmp "word1" "word2" ...` | Discrimination and analysis of word/phrase usages · 词语/短语用法辨析 | Comparison of meanings, nuances, and example contexts · 含义、细微差别及语境对比 |
| `$$ phrase` | Explain a phrase (multiple words) in English · 纯英文解释短语 | Meaning (EN), Usage, Example sentences · 英文释义、用法、例句 |
| `$$cn phrase` | Phrase explanation + Chinese translation · 短语解释并附带中文翻译 | Same as `$$` + Chinese translation · 在 `$$` 基础上增加中文翻译 |
| `$$$ text` | Writing improvement · 写作润色与修改 | Suggestions for improvement + Revised sample version · 修改建议、优化后的范文 |
| `daily-reading` | Generate a daily English reading passage · 生成每日英语阅读 | A short English article + Source attribution · 一篇英文短文、标注出处 |
| `> prompt` | General-purpose query · 通用问答 | Flexible model response · 自由交互回答 |

> **Note · 注**：  
> The `$cmp` command requires at least two arguments; phrases must be wrapped in quotes.  
> `$cmp` 命令要求至少提供两个参数，短语参数需使用引号包裹。  

---

## 4. System Behavior & Prompt Strategy · 系统行为与提示词策略

- **Backend parsing** · 后端解析  
  The backend parses user input, identifies the command type, and rejects any input that does not match a valid pattern.  
  后端解析用户输入并识别指令类型，不符合格式的输入将被直接拒绝。

- **LLM invocation** · 大模型调用  
  Only valid commands trigger an LLM API call. Each command maps to a predefined prompt template to ensure:  
  仅合法指令会触发大模型 API 调用。每种指令对应固定的 Prompt 模板，以实现：
  - Consistent output structure · 输出结构统一
  - Reduced token usage · 减少 token 消耗
  - Controlled model behavior · 控制模型行为

- **Response & Storage** · 响应与存储  
  The LLM response is returned to the frontend and simultaneously logged in the database.  
  大模型返回结果发送至前端，同时写入数据库记录。

---

## 5. System Architecture · 系统架构

LexiMind runs as a local Python web server that serves both the API endpoints and static frontend files. No external web server or container runtime is required.

LexiMind 以一个本地 Python Web 服务器运行，同时提供 API 接口与静态前端文件。无需外部 Web 服务器或容器运行时。

| Layer · 层级 | Technology · 技术 | Responsibility · 职责 |
| :--- | :--- | :--- |
| **Frontend · 前端** | Static HTML + JavaScript | User interface, HTTP requests to backend · 用户界面，通过 HTTP 调用后端 API |
| **Backend · 后端** | Python (Flask / FastAPI) | Serves static files, command parsing, LLM API calls, response formatting, DB operations · 托管静态文件、指令解析、大模型 API 调用、结果格式化、数据库操作 |
| **Database · 数据库** | SQLite | Store word queries, user history, daily articles · 存储词汇记录、用户历史、每日文章 |
| **LLM Integration · 大模型接入** | DeepSeek-V3 (primary) via SiliconCloud API<br>Gemini 1.5 Flash (optional) | Provide language intelligence · 提供语言智能 |

> **Note · 注**：  
> For simplicity, the application only provides access to DeepSeek-V3 by default. If you need to use other LLMs, please modify the relevant frontend and backend files after downloading.  
> 出于简便性考虑，应用默认仅提供DeepSeek-V3的接入。如需使用其他大模型，请下载完成后自行修改前后端相关文件。

---

## 6. API Design · API 设计

**Endpoint · 端点**：`POST /api/query`

**Request Example · 请求示例**：
```json
{
  "input": "$ abandon"
}
```

**Success Response · 成功响应**：
```json
{
  "result": "LLM output"
}
```

**Error Response (Invalid Format) · 错误响应（格式非法）**：
```json
{
  "error": "Invalid command format"
}
```

---

## 7. Security & Rate Limiting · 安全性与限流策略

- API keys stored in environment variables, never exposed to frontend · API key 使用环境变量存储，前端不可见  
- Basic rate limiting per IP · 基于 IP 的基础请求限流  
- Input length restrictions · 输入长度限制  
- No sensitive credentials in Git repository · 敏感信息不进入版本控制

---

## 8. Deployment & Uninstallation · 部署与卸载方式

The application can be run locally with only Python and pip. No Docker or Nginx required.

应用仅需 Python 和 pip 即可本地运行，无需 Docker 或 Nginx。

**Prerequisites · 环境要求**：
- Python 3.10 or higher
- pip (included with Python)

---

### Getting the Distribution · 获取发行版

The release files are located in the `Distribution/` folder of the repository.  
You only need to download that folder to run LexiMind.

发行版文件位于仓库的 `Distribution/` 目录中。您只需下载该文件夹即可运行 LexiMind。

**Option 1: Clone the entire repository (recommended for developers)**  
**选项 1：克隆整个仓库（推荐开发者）**
```bash
git clone https://github.com/Littlebanbrick/LexiMind.git
cd LexiMind/Distribution
```

**Option 2: Sparse checkout (only download the Distribution folder)**  
**选项 2：稀疏检出（仅下载 Distribution 文件夹）**
```bash
git clone --filter=blob:none --no-checkout https://github.com/Littlebanbrick/LexiMind.git
cd LexiMind
git sparse-checkout init --cone
git sparse-checkout set Distribution
git checkout main
cd Distribution
```

---

### Local Startup · 本地启动

#### All Platforms (Windows / macOS / Linux)

1. Open a terminal (Command Prompt / PowerShell on Windows, Terminal on macOS / Linux) in the `Distribution/` folder.  
   在 `Distribution/` 文件夹中打开终端（Windows 使用命令提示符或 PowerShell，macOS / Linux 使用终端）。

2. Run the Python launcher script:  
   运行 Python 启动脚本：
   ```bash
   python run.py
   ```
   (On some systems you may need to use `python3` instead of `python`.)  
   （在某些系统上可能需要使用 `python3` 而非 `python`。）

The script will automatically:
- Check that Python 3.10+ is available
- Create a Python virtual environment (`venv/`)
- Install required dependencies from `requirements.txt`
- Prompt you to enter your DeepSeek API key (first run only)
- Start the backend server at `http://127.0.0.1:5000`
- Open the application in your default browser once the server is ready

启动脚本将自动完成以下操作：
- 检查 Python 3.10+ 是否可用
- 创建 Python 虚拟环境 (`venv/`)
- 从 `requirements.txt` 安装所需依赖
- 首次运行时提示输入 DeepSeek API 密钥
- 在 `http://127.0.0.1:5000` 启动后端服务
- 等待服务就绪后自动在默认浏览器中打开应用

> **Important: Proxy Settings · 重要：代理设置**  
> If you are behind a corporate firewall or using a proxy, the script may fail to download dependencies.  
> Before running `run.py`, **temporarily clear your proxy environment variables**:
> 
> **Windows (Command Prompt)**:
> ```cmd
> set HTTP_PROXY=
> set HTTPS_PROXY=
> ```
> **macOS / Linux**:
> ```bash
> unset HTTP_PROXY HTTPS_PROXY
> ```
> 
> Alternatively, configure your proxy correctly in your system settings.  
> 若处于企业防火墙或代理环境下，脚本可能无法下载依赖。运行 `run.py` 前请**临时清空代理环境变量**（命令见上），或在系统设置中正确配置代理。 


> **Important: Server Connection Failure · 重要：服务器无法连接**  
> If the launcher reports "Server did not respond" or the browser cannot open `http://127.0.0.1:5000`,  
> the backend may be blocked by a firewall, or the port may be occupied. Please follow the steps below:
> 
> **1. Check Firewall (macOS & Windows)**  
> - **macOS**: Go to *System Settings > Network > Firewall > Options...* and ensure **python3** is set to **"Allow incoming connections"**.  
> - **Windows**: When first running the backend, allow **Python** through the Windows Defender Firewall pop-up.  
> - **Temporary Test**: Temporarily disable the firewall to see if the connection succeeds.
> 
> **2. Verify the Port (5000) is Free**  
> ```bash
> # macOS / Linux
> lsof -i :5000
> 
> # Windows (Command Prompt as Administrator)
> netstat -ano | findstr :5000
> ```
> If another process is using port 5000, terminate it or change the port in `backend/app.py`.
> 
> **3. Review the Server Log**  
> Open `backend/server.log` and look for Python tracebacks or error messages (e.g., missing modules, API key issues).
> 
> **4. Retry After Clearing the Environment**  
> Close the terminal, reopen it, and run the launcher again.
> 
> ---
> 若启动器提示“Server did not respond”或浏览器无法打开 `http://127.0.0.1:5000`，  
> 后端可能被防火墙阻止，或端口被占用。请按以下步骤排查：
> 
> **1. 检查防火墙（macOS 与 Windows）**  
> - **macOS**：前往 *系统设置 > 网络 > 防火墙 > 选项...*，确保 **python3** 设置为 **“允许传入连接”**。  
> - **Windows**：首次运行后端时，在 Windows Defender 防火墙弹窗中允许 **Python** 通过。  
> - **临时测试**：暂时关闭防火墙以验证连接是否恢复。
> 
> **2. 确认 5000 端口未被占用**  
> ```bash
> # macOS / Linux
> lsof -i :5000
> 
> # Windows（以管理员身份运行命令提示符）
> netstat -ano | findstr :5000
> ```
> 如有其他进程占用，请结束该进程或修改 `backend/app.py` 中的端口号。
> 
> **3. 查看服务器日志**  
> 打开 `backend/server.log`，查找 Python 错误堆栈或异常信息（例如缺少模块、API 密钥无效等）。
> 
> **4. 清理环境后重试**  
> 关闭当前终端，重新打开并再次运行启动脚本。

---

### Uninstallation · 卸载

To remove LexiMind user data (virtual environment, database, API key) while keeping the source files intact, use the provided uninstaller script.

若希望移除 LexiMind 用户数据（虚拟环境、数据库、API 密钥）而保留源代码，请使用提供的卸载脚本。

#### All Platforms (Windows / macOS / Linux)

1. Open a terminal in the `Distribution/` folder.  
   在 `Distribution/` 文件夹中打开终端。

2. Run the Python uninstaller script:  
   运行 Python 卸载脚本：
   ```bash
   python uninstall.py
   ```

3. Follow the on‑screen prompts to choose the desired cleanup level.  
   根据屏幕提示选择所需的清理级别。

The uninstaller will attempt to move files to the system trash/recycle bin first; if that fails, it will permanently delete them. It **does not** remove the Python interpreter itself.

卸载脚本会优先尝试将文件移至系统回收站；若失败则执行永久删除。脚本**不会**移除 Python 解释器本身。

After uninstalling user data, you may delete the entire `Distribution/` folder manually if you wish to remove the application completely.

卸载用户数据后，若希望完全移除应用，可手动删除整个 `Distribution/` 文件夹。

---

## 9. Expected Outcome · 预期成果

A structured, efficient AI-powered TOEFL learning tool that:

- Minimizes token usage through command-based prompts  
- Provides consistent and high-quality English explanations  
- Is easy to deploy and reproduce  
- Supports future expansion  

一个结构化、高效的 AI 托福学习工具，具备：

- 基于指令的低 token 消耗设计  
- 稳定高质量的输出  
- 易部署、可复现  
- 易于扩展  

---

## 10. Project Structure · 项目结构

```
LexiMind/
├── .env.example               # Environment variable template · 环境变量模板
├── .gitignore                 # Git ignore rules · Git 忽略规则
├── README.md                  # Project documentation · 项目说明文档
│
├── backend/                   # Python backend · 后端 Python 应用
│   ├── requirements.txt       # Python dependencies · Python 依赖列表
│   ├── .env                   # Actual environment variables (ignored by Git) · 实际环境变量（不上传Git）
│   ├── app.py                 # Application entry point · 应用入口
│   ├── config.py              # Configuration loader · 配置加载模块
│   ├── command_parser.py      # Command parser · 指令解析器
│   ├── llm_client.py          # LLM API client wrapper · 大模型 API 调用封装
│   ├── database.py            # SQLite database operations · SQLite 数据库操作
│   └── data/                  # Persistent data directory · 数据持久化目录
│       └── leximind.db        # SQLite database file (auto-generated) · SQLite 数据库文件
│
├── frontend/                  # Static frontend files · 前端静态文件
│   ├── index.html             # Main page · 主页面
│   ├── style.css              # Stylesheet · 样式表
│   └── script.js              # Frontend logic · 前端交互逻辑
│
├── Distribution/          # Windows / macOS / Linux Distribution · Windows / macOS / Linux发行版
|
└─- leximind_development       # Content omitted. Containerized developing workflow · 内容略。此为容器化开发工作流。
```

> **Note · 注**：The `leximind_development/` folder (containing Docker configuration) is maintained separately for containerized development workflows.  
> *`leximind_development/` 目录（包含 Docker 配置）作为容器化开发工作流单独维护。*


## Appendix: About `leximind_development/`
## 附录：关于 `leximind_development/`

The `leximind_development/` directory contains a Docker‑based development environment for LexiMind. It is **not required** for end users who simply want to run the application locally.

`leximind_development/` 目录存放了 LexiMind 基于 Docker 的开发环境。对于只想本地运行应用的最终用户而言，**该目录不是必需的**。

**Purpose · 用途**：
- Provide a containerized, reproducible setup for contributors who prefer Docker.  
  为偏好 Docker 的贡献者提供一个容器化、可复现的开发环境。  
- Isolate backend, frontend, and Nginx services during active development.  
  在活跃开发期间隔离后端、前端与 Nginx 服务。  
- Serve as a reference for users who wish to deploy LexiMind with Docker Compose.  
  为希望使用 Docker Compose 部署 LexiMind 的用户提供参考。

**Relationship to the Main Project · 与主项目的关系**：
- The core source code (`backend/`, `frontend/`) is **identical** across all distribution folders.  
  核心源代码（`backend/`、`frontend/`）在所有分发目录中**完全一致**。  
- `leximind_development/` adds Docker configuration files (`Dockerfile`, `docker-compose.yml`, `nginx/`) on top of the shared codebase.  
  `leximind_development/` 在共享代码库的基础上额外增加了 Docker 配置文件（`Dockerfile`、`docker-compose.yml`、`nginx/`）。  
- End‑user distributions (`leximind_windows/`, `leximind_macos/`, `leximind_linux/`) rely only on Python and pip, omitting Docker entirely.  
  面向最终用户的发行版（`leximind_windows/`、`leximind_macos/`、`leximind_linux/`）仅依赖 Python 与 pip，完全不包含 Docker。

**Who Should Use It · 适用人群**：
- Developers who want to test the full stack with Nginx reverse proxy.  
  希望借助 Nginx 反向代理测试全栈的开发者。  
- Anyone preferring an isolated, container‑based runtime.  
  偏好隔离式、基于容器的运行环境的用户。  
- Users who already have Docker installed and wish to avoid managing Python virtual environments manually.  
  已安装 Docker 且希望免于手动管理 Python 虚拟环境的用户。

If you are a typical user, please refer to the **Deployment** section above and use the appropriate platform‑specific launcher script.  
如果您是普通用户，请参考上方的**部署方式**章节，并使用对应平台的启动脚本。