# X-Trend-Cleaner 🦞 (OpenClaw Skill)

一个为大模型 Agent (如 OpenClaw) 打造的 X (推特) 高级检索分析工具，完美绕过 X 的防爬与算法信息茧房。支持强力去广告、无死角提取全网任意语言的高赞/热门/最新推文，底层基于 Playwright 拦截 GraphQL 数据接口。

## ✨ 特性

- **零算法污染**：不依赖主页 "为你推荐" 的个性化信息流（摆脱语言茧房），强制扫描全球多语种内容，真正获取全网事实热点。
- **免 API Key**：不再受到高昂的 Twitter Developer API 计费或严格 Rate Line 限制，仅需提取个人的网页版 `auth_token` 即可极速查询。
- **十语种聚合**：当使用 `--type trending` 或 `--lang all` 时，后台在同一浏览器实例下并发搜索全球 10 大主流语言区块，进行无缝数据拼装、去重过滤、统一热度展示。
- **专为大模型设计 (LLM-Native)**：高度定制化的 Markdown 排板直出、丰富的交互语义映射封装，直接满足 OpenClaw 或各类 LLM Agent 上下文吸收的标准。
- **智能时间窗与互动筛选**：灵活指定 `hours`, `min-likes`, `no-retweets`，确保洗出的数据是最精华、最具时效性的干货。

---

## 🚀 快速开始

### 1. 安装依赖

该技能由于涉及无头浏览器抓包，所以要求本地运行 Python 环境并安装 Playwright 库：

```bash
# 1. 克隆/下载本技能仓库代码，进入该文件夹：
cd path/to/x-trend-cleaner

# 2. 安装 Python 核心包：
pip install -r requirements.txt

# 3. 初始化 Playwright（下载内置 Chromium 浏览器）：
playwright install chromium
```

### 2. 配置 auth_token（这是重中之重！）

不同于官方 API 密钥，由于我们采用的是网页逆向拦截，您需要提供自己账的 Cookie (`auth_token`)。我们为您提供了**自动提取**和**手动提取**两种方式：

#### 方法 A：使用内置脚本自动提取（推荐）
直接运行随附的提取脚本，按照提示在弹出的界面登录您的 X 账号即可，程序会自动将 Token 保存好：
```bash
python get_cookie.py
```

#### 方法 B：手动通过浏览器开发者工具提取
1. 在电脑浏览器（如 Chrome 或 Edge）上打开并登录 [https://x.com](https://x.com)
2. 按 `F12`（或右键点击“检查”）打开开发者工具。
3. 点击顶部标签栏的 "Application" (应用)。
4. 在左侧栏找到 **Storage** -> **Cookies** -> **https://x.com**。
5. 在左侧表格里找到名为 `auth_token` 的一列，双击它的 "Value" (值) 并复制那段长字符（通常由英文和数字混合）。
6. 回到本程序的文件夹，将复制下来的 Token 作为文本贴入随附提供的 `auth_token.txt.example` 内。
7. 【**非常重要**】将其重命名或另存为 **`auth_token.txt`** 放在 `main.py` 同级目录即可。

> **安全警告 ⚠️** 
> 随代码附带的 `.gitignore` 已经自动屏蔽了 `auth_token.txt` 文件。请在自行 Fork 或 Commit 到您自己的开源仓库时，**再三千万小心不要把带有自己真实 Token 的文本一并公开**，否则可能导致推特账号被盗号或冻结风险！

---

## 🛠️ 测试运行

您可以直接在命令提示符使用预配置的 Python 参数进行手动测试：

**示例 1：获取过去 12 小时内，全球（多语言无差别）最火的 10 条真实热门推文**
```bash
python main.py --type trending --hours 12 --sort views --limit 10
```

**示例 2：获取全语言，过去 48 小时内提及 "OpenAI" 内容的最高赞热推**
```bash
python main.py --type search --query "OpenAI" --lang all --hours 48 --sort likes --limit 5
```

---

## 🤖 接入 OpenClaw 使用指南

只要当前文件夹放置在您的 OpenClaw 指定的 Skills/扩展能力文件夹内，它就能通过随附的 `SKILL.md` 自动理解所有的入参协议和逻辑。

例如在 OpenClaw 的会话中，你只需口语化地下达指令：
> “*看看最近 5 小时内，全推特关于 DeepSeek 的高赞推文，帮我翻译一下总结*”
> “*抓一下埃隆马斯克过去两天的原创推文，不要转推*”
> “*我想看看过去三小时内，全球最热的 10 条推文都是什么？*”

---

*OpenClaw 专属生态部件。Happy Agentic Exploring! 🦞*
