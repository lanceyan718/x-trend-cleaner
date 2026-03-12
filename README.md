# X-Trend-Cleaner 🦞 (OpenClaw Skill)

[Chinese Documentation (中文文档)](#-中文文档) | [English Documentation](#-english-documentation)

---

## 🇨🇳 中文文档

一个为大模型 Agent (如 OpenClaw) 打造的 X (推特) 高级检索分析工具，完美绕过 X 的防爬与算法信息茧房。支持强力去广告、无死角提取全网任意语言的高赞/热门/最新推文，底层基于 Playwright 拦截 GraphQL 数据接口。

### ✨ 特性

- **零算法污染**：不依赖主页 "为你推荐" 的个性化信息流（摆脱语言茧房），强制扫描全球多语种内容，真正获取全网事实热点。
- **免 API Key**：不再受到高昂的 Twitter Developer API 计费或严格 Rate Limit 限制，仅需提取个人的网页版 `auth_token` 即可极速查询。
- **五语种聚合**：当使用 `--type trending` 或 `--lang all` 时，后台在同一浏览器实例下并发搜索全球 5 大主流语言区块（英、中、日、韩、西），进行无缝数据拼装、去重过滤、统一热度展示。
- **专为大模型设计 (LLM-Native)**：高度定制化的 Markdown 排版直出、丰富的交互语义映射封装，直接满足 OpenClaw 或各类 LLM Agent 上下文吸收的标准。
- **智能时间窗与互动筛选**：灵活指定 `hours`, `min-likes`, `no-retweets`，确保洗出的数据是最精华、最具时效性的干货。

### 🚀 快速开始

#### 1. 安装依赖

```bash
# 1. 克隆/下载本技能仓库代码，进入该文件夹：
cd x-trend-cleaner

# 2. 安装 Python 核心包：
pip install -r requirements.txt

# 3. 初始化 Playwright（下载内置 Chromium 浏览器）：
playwright install chromium
```

#### 2. 配置 auth_token（这是重中之重！）

不同于官方 API 密钥，由于我们采用的是网页逆向拦截，您需要提供自己账号的 Cookie (`auth_token`)。我们为您提供了**自动提取**和**手动提取**两种方式：

**方法 A：使用内置脚本自动提取（推荐）**
直接运行随附的提取脚本，按照提示在弹出的界面登录您的 X 账号即可，程序会自动将 Token 保存好：
```bash
python get_cookie.py
```

**方法 B：手动通过浏览器开发者工具提取**
1. 在电脑浏览器（如 Chrome 或 Edge）上打开并登录 [https://x.com](https://x.com)
2. 按 `F12` 打开开发者工具 -> **Application** (应用) -> **Cookies** -> **https://x.com**。
3. 找到 `auth_token` 并复制它的 Value。
4. 将其贴入新建的文件 **`auth_token.txt`** 放在 `main.py` 同级目录即可。

> **安全警告 ⚠️** 强烈建议不要将带有自己真实 Token 的文本提交到任何公开仓库。

---

## 🇺🇸 English Documentation

An advanced X (Twitter) search and analysis tool designed for LLM Agents (like OpenClaw). It bypasses X's anti-scraping mechanisms and algorithmic bubbles. It supports ad-cleaning and extracts high-engagement/trending/latest tweets in any language, powered by Playwright for GraphQL interception.

### ✨ Features

- **Zero Algorithmic Bias**: Does not rely on the "For You" timeline. It performs broad multi-language scans to capture real-time global hotspots.
- **No API Key Required**: Bypass expensive Twitter Developer API costs. Uses personal web `auth_token` for high-speed queries.
- **Global Aggregation**: When using `--type trending` or `--lang all`, it concurrently searches the top 5 global languages (English, Chinese, Japanese, Korean, Spanish), deduplicating and ranking by engagement.
- **LLM-Native Design**: Optimized Markdown output ready for OpenClaw or any LLM Agent context.
- **Smart Filtering**: Custom `hours`, `min-likes`, and `no-retweets` filters ensure you only get the highest quality content.

### 🚀 Quick Start

#### 1. Installation

```bash
# 1. Clone the repo and enter the folder:
cd x-trend-cleaner

# 2. Install dependencies:
pip install -r requirements.txt

# 3. Initialize Playwright:
playwright install chromium
```

#### 2. Configure auth_token (Critical!)

Since this uses GraphQL interception, you need to provide your session's `auth_token`. We provide two ways:

**Method A: Automatic Extraction (Recommended)**
Run the built-in script, log in to your X account in the popup, and the token will be saved automatically:
```bash
python get_cookie.py
```

**Method B: Manual Extraction**
1. Log in to [https://x.com](https://x.com) in your browser.
2. Press `F12` -> **Application** -> **Cookies** -> **https://x.com**.
3. Copy the Value of `auth_token`.
4. Create a file named **`auth_token.txt`** in the root directory and paste the value there.

> **Security Warning ⚠️** Never commit your real `auth_token.txt` to a public repository.

---

## 🤖 OpenClaw Usage Guide

Place this folder in your OpenClaw skills directory. Your agent can then understand commands like:
> "*Show me the hottest DeepSeek tweets from the last 5 hours and summarize the key points.*"
> "*Catch up on Elon Musk's original tweets from the past two days, no retweets.*"
