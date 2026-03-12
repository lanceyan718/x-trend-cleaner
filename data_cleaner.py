import json
import re
from datetime import datetime
from email.utils import parsedate_to_datetime
import pytz


class DataCleaner:
    """
    X (Twitter) GraphQL 数据清洗引擎。
    负责从原始 JSON 中提取推文、过滤广告、校验时效与相关性、去重、排序。
    """

    # X 高级搜索运算符正则，用于从 query 中剥离，只保留纯关键词
    _OPERATOR_RE = re.compile(
        r"""
        (?:^|\s)                          # 运算符前是空格或开头
        -?                                # 可选的否定前缀
        (?:
            lang:\S+                      |
            from:\S+                      |
            to:\S+                        |
            @\S+                          |
            min_faves:\d+                 |
            min_likes:\d+                 |
            min_retweets:\d+              |
            min_replies:\d+               |
            since:\S+                     |
            until:\S+                     |
            since_time:\d+                |
            until_time:\d+                |
            filter:\S+                    |
            near:\"[^\"]*\"               |
            within:\S+                    |
            geocode:\S+                   |
            place:\S+                     |
            url:\S+                       |
            list:\S+
        )
        """,
        re.VERBOSE | re.IGNORECASE,
    )

    def __init__(self, search_query: str = "", time_window_hours: float = 24):
        self.raw_query = search_query
        self.pure_keywords = self._extract_pure_keywords(search_query)
        self.time_window_hours = float(time_window_hours)

    # ──────────────────────────────────────────────
    # 静态工具方法
    # ──────────────────────────────────────────────

    @classmethod
    def _extract_pure_keywords(cls, query: str) -> str:
        """
        从包含 X 高级运算符的搜索表达式中，剥离所有运算符，
        只保留用户想搜索的纯关键词。
        例: "openclaw lang:en min_faves:100 -filter:retweets" → "openclaw"
        例: "from:elonmusk AI agents" → "AI agents"
        """
        if not query:
            return ""
        cleaned = cls._OPERATOR_RE.sub(" ", query)
        # 去除 OR 逻辑词（它不是搜索关键词本身）
        cleaned = re.sub(r"\bOR\b", " ", cleaned, flags=re.IGNORECASE)
        # 去除引号（精确匹配短语的引号保留内容）
        cleaned = cleaned.replace('"', " ")
        # 压缩空白
        cleaned = " ".join(cleaned.split()).strip()
        return cleaned.lower()

    # ──────────────────────────────────────────────
    # GraphQL JSON → 原始推文列表
    # ──────────────────────────────────────────────

    def extract_tweets_from_graphql(self, graphql_json: dict) -> list:
        """从 X SearchTimeline / UserTweets / HomeTimeline 的 GraphQL JSON 中深度提取推文对象。"""
        tweets = []
        try:
            instructions = []
            data = graphql_json.get("data", {})
            # SearchTimeline 路径
            st = data.get("search_by_raw_query", {}).get("search_timeline", {})
            if st:
                instructions = st.get("timeline", {}).get("instructions", [])
            # HomeTimeline 路径 (data.home.home_timeline_urt.instructions)
            elif "home" in data:
                urt = data["home"].get("home_timeline_urt", {})
                if urt:
                    instructions = urt.get("instructions", [])
            # UserTweets 路径（兼容 timeline 和 timeline_v2 两种结构）
            else:
                user = data.get("user", {}).get("result", {})
                tl = user.get("timeline_v2") or user.get("timeline")
                if tl and isinstance(tl, dict):
                    instructions = tl.get("timeline", {}).get("instructions", [])

            for instr in instructions:
                if instr.get("type") == "TimelineAddEntries":
                    for entry in instr.get("entries", []):
                        tweets.extend(self._parse_entry(entry))
        except Exception as e:
            print(f"  [提取警告] {e}")
        return tweets

    def _parse_entry(self, entry: dict) -> list:
        """解析单个 timeline entry，返回推文 result 对象列表。"""
        extracted = []
        content = entry.get("content", {})
        entry_type = content.get("entryType")

        if entry_type == "TimelineTimelineItem":
            ic = content.get("itemContent", {})
            if ic.get("itemType") == "TimelineTweet":
                if "promotedMetadata" in ic:
                    return extracted  # 广告，丢弃
                result = ic.get("tweet_results", {}).get("result", {})
                if result.get("__typename") == "Tweet":
                    extracted.append(result)

        elif entry_type == "TimelineTimelineModule":
            for item in content.get("items", []):
                ic = item.get("item", {}).get("itemContent", {})
                if ic.get("itemType") == "TimelineTweet":
                    if "promotedMetadata" in ic:
                        continue
                    result = ic.get("tweet_results", {}).get("result", {})
                    if result.get("__typename") == "Tweet":
                        extracted.append(result)

        return extracted

    # ──────────────────────────────────────────────
    # 清洗、过滤、排序
    # ──────────────────────────────────────────────

    def clean_and_build(
        self,
        raw_tweets: list,
        sort_by: str = "popularity_score",
        limit: int = 0,
        min_likes: int = 0,
        min_retweets: int = 0,
    ) -> list:
        """
        对原始推文列表执行：时效过滤 → 关键词相关性校验 → 互动量门槛 → 去重 → 排序 → 截断。
        """
        cleaned = []
        now_utc = datetime.now(pytz.utc)

        for raw in raw_tweets:
            try:
                legacy = raw.get("legacy", {})
                core_user = raw.get("core", {}).get("user_results", {}).get("result", {})
                user_legacy = core_user.get("legacy", {})
                user_core = core_user.get("core", {})

                created_at_str = legacy.get("created_at")
                if not created_at_str:
                    continue

                tweet_time = parsedate_to_datetime(created_at_str)
                age_hours = (now_utc - tweet_time).total_seconds() / 3600.0

                # 1. 时效过滤
                if age_hours > self.time_window_hours:
                    continue

                # 2. 提取全文（兼容长推文 note_tweet）
                full_text = legacy.get("full_text", "")
                note_tweet = (
                    raw.get("note_tweet", {})
                    .get("note_tweet_results", {})
                    .get("result", {})
                    .get("text")
                )
                if note_tweet:
                    full_text = note_tweet

                # 3. 解析作者信息（兼容新旧 User 结构）
                author_name = user_core.get("name") or user_legacy.get("name", "Unknown")
                author_handle = user_core.get("screen_name") or user_legacy.get("screen_name", "Unknown")

                # 4. 关键词相关性校验（只用纯关键词，不含运算符）
                if self.pure_keywords:
                    # 将纯关键词拆分为多个词，任意一个命中即通过
                    kw_list = self.pure_keywords.split()
                    text_lower = full_text.lower()
                    name_lower = author_name.lower()
                    handle_lower = author_handle.lower()
                    matched = any(
                        kw in text_lower or kw in name_lower or kw in handle_lower
                        for kw in kw_list
                    )
                    if not matched:
                        continue

                # 5. 互动量门槛过滤
                likes = legacy.get("favorite_count", 0)
                retweets = legacy.get("retweet_count", 0)
                if likes < min_likes:
                    continue
                if retweets < min_retweets:
                    continue

                # 6. 构建标准化输出
                item = {
                    "id": raw.get("rest_id"),
                    "author": author_name,
                    "handle": author_handle,
                    "text": full_text,
                    "created_at": created_at_str,
                    "age_hours": round(age_hours, 1),
                    "likes": likes,
                    "retweets": retweets,
                    "replies": legacy.get("reply_count", 0),
                    "quotes": legacy.get("quote_count", 0),
                    "views": int(raw.get("views", {}).get("count", 0) or 0),
                    "url": f"https://x.com/{author_handle}/status/{raw.get('rest_id')}",
                }
                # 综合热度分
                item["popularity_score"] = (
                    item["likes"] * 1
                    + item["retweets"] * 2
                    + item["replies"] * 1.5
                    + item["quotes"] * 2
                    + item["views"] * 0.01
                )
                cleaned.append(item)

            except Exception as e:
                print(f"  [清洗警告] {e}")

        # 7. 跨语言去重（同一 rest_id 只保留一条）
        cleaned = self._deduplicate(cleaned)

        # 8. 排序
        cleaned.sort(key=lambda x: x.get(sort_by, 0), reverse=True)

        # 9. 截断
        if limit and limit > 0:
            cleaned = cleaned[:limit]

        return cleaned

    @staticmethod
    def _deduplicate(tweets: list) -> list:
        """按推文 ID 去重，保留第一次出现的。"""
        seen = set()
        unique = []
        for t in tweets:
            tid = t.get("id")
            if tid and tid not in seen:
                seen.add(tid)
                unique.append(t)
        return unique
