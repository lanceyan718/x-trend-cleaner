import asyncio
import urllib.parse
from playwright.async_api import async_playwright


class PlaywrightInterceptor:
    """
    X (Twitter) GraphQL 底层拦截器。
    通过 Playwright 无头浏览器挂载 Cookie，直接拦截 X 向服务器发出的
    SearchTimeline / UserTweets GraphQL 数据包，跳过 DOM 层的广告和算法干预。
    """

    # 全球聚合时默认并发的语言列表 (精简为 5 种最活跃语言以提高账号安全性)
    DEFAULT_LANGS = ["en", "zh", "ja", "ko", "es"]

    def __init__(self, auth_token: str):
        self.auth_token = auth_token

    # ──────────────────────────────────────────────
    # 底层：单页面拦截
    # ──────────────────────────────────────────────

    async def _intercept_page(self, context, url: str, scroll_rounds: int = 10, settle_time: int = 4):
        """
        在已有的浏览器上下文中打开一个页面，拦截 GraphQL 响应，滚动加载，返回 JSON 列表。
        """
        intercepted = []
        page = await context.new_page()

        async def on_response(response):
            if "graphql" in response.url and (
                "SearchTimeline" in response.url
                or "UserTweets" in response.url
                or "HomeTimeline" in response.url
            ):
                try:
                    if response.status == 200:
                        data = await response.json()
                        intercepted.append(data)
                except Exception as e:
                    print(f"  [拦截警告] 解码失败: {e}")

        page.on("response", on_response)

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            print(f"  [导航警告] {e}")

        # 模拟用户滚动，触发懒加载分页
        try:
            await page.wait_for_timeout(3000)
            for _ in range(scroll_rounds):
                if page.is_closed():
                    break
                try:
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                except Exception as e:
                    # 如果执行环境被销毁（比如跳转了），忽略并继续
                    break
                await page.wait_for_timeout(2000)
            
            if not page.is_closed():
                await page.wait_for_timeout(settle_time * 1000)
        finally:
            if not page.is_closed():
                await page.close()
                
        return intercepted

    # ──────────────────────────────────────────────
    # 浏览器上下文管理（复用 Cookie）
    # ──────────────────────────────────────────────

    async def _create_context(self, playwright):
        """创建并返回注入了 auth_token Cookie 的浏览器上下文。"""
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context()
        if self.auth_token:
            await context.add_cookies([{
                "name": "auth_token",
                "value": self.auth_token,
                "domain": ".x.com",
                "path": "/",
                "secure": True,
                "httpOnly": True,
                "sameSite": "None",
            }])
        return browser, context

    # ──────────────────────────────────────────────
    # 公开接口：关键词搜索（单语言）
    # ──────────────────────────────────────────────

    async def search_tweets(self, query: str, tab: str = "top"):
        """
        对给定的完整搜索表达式执行单次搜索拦截。
        query 支持所有 X 原生高级运算符（from:, lang:, min_faves: 等）。
        tab: "top" 或 "latest"
        """
        encoded = urllib.parse.quote(query)
        tab_param = "top" if tab == "top" else "live"
        url = f"https://x.com/search?q={encoded}&src=typed_query&f={tab_param}"
        print(f"  [拦截] {url}")

        async with async_playwright() as p:
            browser, context = await self._create_context(p)
            jsons = await self._intercept_page(context, url)
            await browser.close()
        return jsons

    # ──────────────────────────────────────────────
    # 公开接口：关键词搜索（多语言并发聚合）
    # ──────────────────────────────────────────────

    async def search_tweets_multi_lang(
        self, base_query: str, langs: list = None, tab: str = "top"
    ):
        """
        在单个浏览器会话内，依次对每种语言发起搜索拦截，收集所有 JSON 后返回。
        base_query: 不含 lang: 的纯搜索表达式
        langs: 语言代码列表，默认 DEFAULT_LANGS
        tab: "top" 或 "latest"
        """
        if langs is None:
            langs = self.DEFAULT_LANGS

        tab_param = "top" if tab == "top" else "live"
        all_jsons = []

        async with async_playwright() as p:
            browser, context = await self._create_context(p)

            for lang in langs:
                full_query = f"{base_query} lang:{lang}"
                encoded = urllib.parse.quote(full_query)
                url = f"https://x.com/search?q={encoded}&src=typed_query&f={tab_param}"
                print(f"  [拦截 lang:{lang}] {url}")
                jsons = await self._intercept_page(context, url, scroll_rounds=5, settle_time=3)
                all_jsons.extend(jsons)

            await browser.close()

        return all_jsons

    # ──────────────────────────────────────────────
    # 公开接口：用户时间线
    # ──────────────────────────────────────────────

    async def get_user_tweets(self, username: str):
        """
        拉取指定用户的时间线。不受语言个性化影响。
        """
        clean = username.strip().lstrip("@")
        url = f"https://x.com/{clean}"
        print(f"  [拦截用户] {url}")

        async with async_playwright() as p:
            browser, context = await self._create_context(p)
            jsons = await self._intercept_page(context, url)
            await browser.close()
        return jsons

    # ──────────────────────────────────────────────
    # 公开接口：全球热门（主页推荐流）
    # ──────────────────────────────────────────────

    async def get_trending(self):
        """
        拉取首页 "为你推荐" 信息流（HomeTimeline）。
        这是 X 算法推荐的热门内容，不需要搜索关键词。
        """
        url = "https://x.com/home"
        print(f"  [拦截首页推荐流] {url}")

        async with async_playwright() as p:
            browser, context = await self._create_context(p)
            jsons = await self._intercept_page(context, url, scroll_rounds=8, settle_time=4)
            await browser.close()
        return jsons
