import asyncio
import os
import sys
import re
import argparse
from core_interceptor import PlaywrightInterceptor
from data_cleaner import DataCleaner


# ──────────────────────────────────────────────
# 工具函数
# ──────────────────────────────────────────────

def get_auth_token() -> str:
    token_path = os.path.join(os.path.dirname(__file__), "auth_token.txt")
    if os.path.exists(token_path):
        with open(token_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return os.getenv("TWITTER_AUTH_TOKEN", "")


def _query_has_operator(query: str, op: str) -> bool:
    """检查 query 中是否已经包含了某个运算符（如 'lang:'）。"""
    return bool(re.search(rf"(?:^|\s)-?{re.escape(op)}", query, re.IGNORECASE))


def format_markdown(cleaned_tweets: list, sort_by: str = "") -> str:
    if not cleaned_tweets:
        return (
            "未找到符合条件的推文。\n\n"
            "*可能原因：设定时间窗内无人发布匹配内容，或关键词/运算符过于严格。*"
        )

    lines = [f"### 共提取 {len(cleaned_tweets)} 条纯净推文 (按 {sort_by} 排序)：\n"]
    for i, t in enumerate(cleaned_tweets, 1):
        # 时间显示
        age = t['age_hours']
        if age < 1:
            time_str = f"{int(age * 60)} 分钟前"
        else:
            time_str = f"{age} 小时前"

        # 文本截断（保留完整性）
        text = t['text'].replace('\n', '\n> ')
        if len(text) > 300:
            text = text[:297] + "..."

        lines.append(f"**{i}. {t['author']} (@{t['handle']})** 发布于 {time_str}\n")
        lines.append(f"> {text}\n")
        lines.append(
            f"❤️ 点赞: {t['likes']} | "
            f"🔁 转发: {t['retweets']} | "
            f"💬 回复: {t['replies']} | "
            f"👁️ 浏览量: {t['views']} "
            f"🔗 [原推链接]({t['url']})"
        )
        lines.append("\n---\n")
    return "\n".join(lines)


# ──────────────────────────────────────────────
# 核心调度逻辑
# ──────────────────────────────────────────────

async def run_cleaner_task(
    query_type: str,
    query: str,
    hours: float = 24.0,
    sort_by: str = "popularity_score",
    limit: int = 10,
    lang: str = "all",
    tab: str = "top",
    no_retweets: bool = False,
    min_likes: int = 0,
    min_retweets: int = 0,
) -> str:
    auth_token = get_auth_token()
    if not auth_token:
        return "错误: 未找到 auth_token。请在技能目录创建 auth_token.txt 或设置 TWITTER_AUTH_TOKEN 环境变量。"

    interceptor = PlaywrightInterceptor(auth_token)

    # ── 构建最终传给拦截器的搜索表达式 ──
    final_query = query.strip()

    # 追加 -filter:retweets（如果用户指定且 query 中尚未包含）
    if no_retweets and not _query_has_operator(final_query, "filter:retweets"):
        final_query += " -filter:retweets"

    # ── 分发到不同拦截路径 ──
    raw_jsons = []
    search_kw = final_query  # 用于 DataCleaner 的关键词校验

    if query_type == "trending":
        # 全球热门：用多语言宽泛搜索代替个性化首页推荐流
        # HomeTimeline 受账户语言偏好影响，改用 SearchTimeline 跨语言聚合
        min_faves_val = max(50, min_likes)  # 至少 50 赞的才算热门
        broad_query = f"min_faves:{min_faves_val}"
        if no_retweets:
            broad_query += " -filter:retweets"
        print(f"🦞 正在拉取全球热门推文 (时间窗: {hours}h, 最低赞: {min_faves_val}) ...")
        raw_jsons = await interceptor.search_tweets_multi_lang(broad_query, tab=tab)
        search_kw = ""  # 热门推荐流不做关键词过滤

    elif query_type == "user":
        # 用户时间线：不受语言影响，直接拉取
        print(f"🦞 正在拉取用户 @{query} 的时间线 (时间窗: {hours}h) ...")
        raw_jsons = await interceptor.get_user_tweets(query)
        search_kw = ""  # 用户时间线不做关键词过滤

    elif query_type == "search":
        print(f"🦞 正在搜索: '{final_query}' (时间窗: {hours}h, 语言: {lang}, 标签: {tab}) ...")

        if lang == "all":
            # 全球多语言聚合
            # 如果用户 query 中已经手动指定了 lang:，尊重用户选择，退回单次搜索
            if _query_has_operator(final_query, "lang:"):
                print("  [提示] query 中已包含 lang: 运算符，跳过多语言聚合，按单次搜索执行。")
                raw_jsons = await interceptor.search_tweets(final_query, tab=tab)
            else:
                raw_jsons = await interceptor.search_tweets_multi_lang(final_query, tab=tab)
        else:
            # 单语言：自动在 query 后追加 lang:xx（如果用户未手动指定）
            if not _query_has_operator(final_query, "lang:"):
                final_query += f" lang:{lang}"
            raw_jsons = await interceptor.search_tweets(final_query, tab=tab)
    else:
        return f"不支持的查询类型: {query_type}。请使用 search、user 或 trending。"

    # ── 数据清洗 ──
    cleaner = DataCleaner(search_query=search_kw, time_window_hours=hours)

    all_raw = []
    for j in raw_jsons:
        all_raw.extend(cleaner.extract_tweets_from_graphql(j))

    cleaned = cleaner.clean_and_build(
        all_raw,
        sort_by=sort_by,
        limit=limit,
        min_likes=min_likes,
        min_retweets=min_retweets,
    )

    print(f"🦞 拦截完毕：原始 {len(all_raw)} 条 → 清洗后 {len(cleaned)} 条")
    return format_markdown(cleaned, sort_by=sort_by)


# ──────────────────────────────────────────────
# OpenClaw 技能入口（Python import 调用）
# ──────────────────────────────────────────────

def execute_skill(
    query_type: str,
    query: str,
    hours: float = 24,
    sort_by: str = "popularity_score",
    limit: int = 10,
    lang: str = "all",
    tab: str = "top",
    no_retweets: bool = False,
    min_likes: int = 0,
    min_retweets: int = 0,
) -> str:
    """OpenClaw skill 入口。可被 OpenClaw 执行框架直接 import 调用。"""
    return asyncio.run(
        run_cleaner_task(
            query_type, query, hours, sort_by, limit,
            lang, tab, no_retweets, min_likes, min_retweets,
        )
    )


# ──────────────────────────────────────────────
# CLI 入口
# ──────────────────────────────────────────────

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="X-Trend-Cleaner：推特纯净搜索与热榜工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 全球 24h 热度前 10
  python main.py --type search --query "openclaw" --lang all --sort views --limit 10

  # 全球热门推文（不需要关键词）
  python main.py --type trending --hours 5 --sort views --limit 10

  # 英文区搜索
  python main.py --type search --query "AI agents" --lang en --hours 48

  # 用户时间线
  python main.py --type user --query "elonmusk" --hours 48

  # 高级运算符透传
  python main.py --type search --query "from:elonmusk AI -filter:replies" --lang en
        """,
    )
    parser.add_argument(
        "--type", choices=["search", "user", "trending"], default="search",
        help="查询类型：search（关键词搜索）/ user（用户时间线）/ trending（全球热门，无需关键词）",
    )
    parser.add_argument("--query", default="", help="搜索词/用户名，支持 X 高级搜索运算符。trending 类型不需要此参数")
    parser.add_argument("--hours", type=float, default=24.0, help="时效过滤窗口（小时），默认 24")
    parser.add_argument(
        "--sort",
        choices=["popularity_score", "views", "likes", "retweets", "replies", "quotes"],
        default="popularity_score",
        help="排序字段，默认 popularity_score（综合热度）",
    )
    parser.add_argument("--limit", type=int, default=10, help="最大返回条数，默认 10")
    parser.add_argument(
        "--lang", default="all",
        help="搜索语言：all（全球多语言聚合）、en、zh、ja、ko、de、fr 等，默认 all",
    )
    parser.add_argument(
        "--tab", choices=["top", "latest"], default="top",
        help="搜索标签：top（热门）或 latest（最新），默认 top",
    )
    parser.add_argument(
        "--no-retweets", action="store_true",
        help="排除转推（自动追加 -filter:retweets）",
    )
    parser.add_argument("--min-likes", type=int, default=0, help="最低点赞数过滤，默认 0")
    parser.add_argument("--min-retweets", type=int, default=0, help="最低转发数过滤，默认 0")

    args = parser.parse_args()

    result = asyncio.run(
        run_cleaner_task(
            query_type=args.type,
            query=args.query,
            hours=args.hours,
            sort_by=args.sort,
            limit=args.limit,
            lang=args.lang,
            tab=args.tab,
            no_retweets=args.no_retweets,
            min_likes=args.min_likes,
            min_retweets=args.min_retweets,
        )
    )
    print("\n\n" + result)
