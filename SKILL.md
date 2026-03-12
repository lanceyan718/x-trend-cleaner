---
name: x-trend-cleaner
description: 推特 (X) 强力去广告、破除黑箱算法的纯净搜索与用户热榜工具。支持全球多语言聚合、高级搜索运算符透传、用户时间线拉取。基于 Playwright 拦截底层 GraphQL。
---

# X-Trend-Cleaner 推特纯净搜索工具

## 🌟 何时使用
当用户需要以下任何一项时，**必须调用本技能**：
- 搜索 X/Twitter 上的热门推文（支持关键词、话题、人物）
- 查看某个用户最近发了什么
- 查看全球热门推文（不需要关键词，拉取首页推荐流）
- 需要无广告、无算法干扰的纯净推文数据
- 需要全球多语言维度的热度排名（而非被算法限制在单一语言区）
- 需要精确控制搜索条件（时间窗、最低互动量、语言、排序方式等）

## 🛠️ 调用方式

运行技能目录下的 `main.py`：

```bash
python g:\cursor\.agent\skills\x-trend-cleaner\main.py --type <类型> --query "<搜索表达式>" [可选参数]
```

> ⚠️ 底层依赖无头浏览器拦截，执行耗时约 30-90 秒，请耐心等待。`--lang all` 全球聚合模式耗时更长。

## 📋 完整参数表

| 参数 | 必填 | 说明 | 默认值 |
|------|------|------|--------|
| `--type` | ✅ | `search`（关键词搜索）/ `user`（用户时间线）/ `trending`（全球热门，无需关键词） | `search` |
| `--query` | 条件必填 | 搜索词或用户名。`trending` 类型不需要此参数。**支持直接嵌入 X 原生高级搜索运算符** | - |
| `--hours` | ❌ | 时效过滤窗口（小时） | `24` |
| `--sort` | ❌ | 排序字段：`popularity_score` / `views` / `likes` / `retweets` / `replies` | `popularity_score` |
| `--limit` | ❌ | 最大返回条数 | `10` |
| `--lang` | ❌ | 语言范围：`all`（全球多语言聚合）/ `en` / `zh` / `ja` / `ko` / `de` / `fr` 等 | `all` |
| `--tab` | ❌ | 搜索标签：`top`（热门）或 `latest`（最新/时间序） | `top` |
| `--no-retweets` | ❌ | 加此 flag 排除转推 | 不排除 |
| `--min-likes` | ❌ | 最低点赞数过滤 | `0` |
| `--min-retweets` | ❌ | 最低转发数过滤 | `0` |

## 🔧 --query 支持的 X 高级搜索运算符

`--query` 参数支持**直接嵌入**以下 X 原生运算符，技能会透传到底层搜索 URL：

| 运算符 | 作用 | 示例 |
|--------|------|------|
| `from:用户名` | 只看某用户发的推文 | `"from:elonmusk AI"` |
| `to:用户名` | 只看回复给某用户的 | `"to:OpenAI"` |
| `@用户名` | 只看提及某用户的 | `"@elonmusk"` |
| `min_faves:N` | 至少 N 个点赞 | `"openclaw min_faves:100"` |
| `min_retweets:N` | 至少 N 个转发 | `"AI min_retweets:50"` |
| `since:YYYY-MM-DD` | 从某日起 | `"openclaw since:2026-03-10"` |
| `until:YYYY-MM-DD` | 到某日止 | `"openclaw until:2026-03-12"` |
| `-filter:replies` | 排除回复 | `"from:elonmusk -filter:replies"` |
| `-filter:retweets` | 排除转推 | `"AI -filter:retweets"` |
| `filter:media` | 只含图片/视频 | `"openclaw filter:media"` |
| `OR` | 逻辑或 | `"openclaw OR lobster"` |
| `"精确短语"` | 精确匹配 | `"\"open source AI\""` |

> 💡 你可以自由组合这些运算符。当 query 中已包含 `lang:` 时，`--lang` 参数会自动被忽略。

## 💡 示例调用

**1. 全球热门推文（不需要关键词）：**
```bash
python g:\cursor\.agent\skills\x-trend-cleaner\main.py --type trending --hours 5 --sort views --limit 10
```

**2. 全球 24h 热度前 10（按关键词搜索，不分语言）：**
```bash
python g:\cursor\.agent\skills\x-trend-cleaner\main.py --type search --query "openclaw" --lang all --hours 24 --sort views --limit 10
```

**3. 只看英文区热门：**
```bash
python g:\cursor\.agent\skills\x-trend-cleaner\main.py --type search --query "openclaw" --lang en --hours 24 --sort views --limit 10
```

**4. 查看某用户最近发了什么：**
```bash
python g:\cursor\.agent\skills\x-trend-cleaner\main.py --type user --query "elonmusk" --hours 48 --sort views --limit 10
```

**5. 查看某用户最近发了什么（排除转推，只看原创）：**
```bash
python g:\cursor\.agent\skills\x-trend-cleaner\main.py --type user --query "elonmusk" --hours 24 --sort views --no-retweets
```

**6. 搜索某用户发的含特定关键词的推文（高级运算符）：**
```bash
python g:\cursor\.agent\skills\x-trend-cleaner\main.py --type search --query "from:elonmusk AI" --lang en --hours 72 --sort likes
```

**7. 搜索高互动量推文：**
```bash
python g:\cursor\.agent\skills\x-trend-cleaner\main.py --type search --query "AI agents min_faves:500" --lang en --hours 48 --sort views
```

**8. 最新推文（时间序而非热度）：**
```bash
python g:\cursor\.agent\skills\x-trend-cleaner\main.py --type search --query "deepseek" --lang zh --tab latest --hours 12
```

**9. 排除转推和回复，只看原创：**
```bash
python g:\cursor\.agent\skills\x-trend-cleaner\main.py --type search --query "openclaw -filter:replies" --lang all --no-retweets --hours 24
```

**10. 本地过滤低互动推文：**
```bash
python g:\cursor\.agent\skills\x-trend-cleaner\main.py --type search --query "Trump" --lang en --hours 24 --min-likes 50 --sort views
```

## 🧠 用户自然语言 → 参数映射指南

当用户用口语化的自然语言描述需求时，请按以下规则映射到对应参数：

| 用户可能说的话 | 应该使用的参数 |
|---------------|---------------|
| "我不想看转推" / "排除转推" / "只看原创" | 加 `--no-retweets` |
| "只看英文的" / "英文区" | 加 `--lang en` |
| "只看中文的" / "中文区" | 加 `--lang zh` |
| "全球的" / "不分语言" / "所有语言" | 加 `--lang all`（默认） |
| "按浏览量排" / "最多人看的" | 加 `--sort views` |
| "按点赞排" / "最多赞的" | 加 `--sort likes` |
| "按转发排" | 加 `--sort retweets` |
| "最新的" / "按时间排" | 加 `--tab latest` |
| "最热的" / "热门" / "爆款" | 加 `--tab top`（默认） |
| "只要点赞超过100的" / "至少100赞" | 加 `--min-likes 100` |
| "最近12小时" / "过去半天" | 加 `--hours 12` |
| "最近两天" / "48小时内" | 加 `--hours 48` |
| "看看某某最近发了什么" | 用 `--type user --query "用户名"` |
| "搜一下关于XX的推文" | 用 `--type search --query "XX"` |
| "给我看前5条" / "top5" | 加 `--limit 5` |
| "不要回复" / "排除回复" | 在 query 中加 `-filter:replies` |
| "全球最热" / "推特上现在什么最火" / "热门推文" | 用 `--type trending` |
| "最近几小时全球最火的推文" | 用 `--type trending --hours N --sort views` |

> 💡 **关键原则**：全部参数都可以自由组合。用户说的每个条件都对应一个参数，叠加即可。

## ⚡ `--type user` 与 `--type search --query "from:xxx"` 的区别

| | `--type user --query "elonmusk"` | `--type search --query "from:elonmusk"` |
|---|---|---|
| 底层端点 | UserTweets（用户时间线） | SearchTimeline（搜索） |
| 返回内容 | 该用户的**所有**推文 | 搜索结果中来自该用户的推文 |
| 受算法个性化影响 | ❌ 不受 | ✅ 受 |
| 可加关键词过滤 | ❌ 不能（返回所有） | ✅ 可以（如 `from:elonmusk AI`） |
| 可排除转推 | ✅ 用 `--no-retweets` | ✅ 用 `--no-retweets` 或 `-filter:retweets` |

**建议**：想看某人最近发了什么用 `--type user`，想看某人发的关于特定话题的推文用 `--type search --query "from:xxx 关键词"`。

## ⚠️ 错误排查
1. **auth_token 缺失**：运行 `get_cookie.py` 刷新 Cookie。
2. **超时/空结果**：可能是网络/代理问题，重试即可。
3. **全球聚合太慢**：`--lang all` 需要依次访问多个语言标签页，耗时较长属正常。可用 `--lang en` 等单语言加速。

