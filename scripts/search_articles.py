#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "httpx",
#   "beautifulsoup4",
#   "lxml",
# ]
# ///
"""
微信公开文章搜索脚本（via 搜狗微信搜索）

用法：
    uv run search_articles.py <关键词> [公众号名称] [数量]

示例：
    uv run search_articles.py "人工智能"
    uv run search_articles.py "ChatGPT" "机器之心" 5
"""

import sys
import asyncio
import random
import re
import httpx
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3",
    "Referer": "https://weixin.sogou.com/",
    "Connection": "keep-alive",
}


async def search_articles(query: str, account_name: str = None, limit: int = 10) -> list:
    await asyncio.sleep(random.uniform(1, 3))

    params = {"query": query, "type": 2, "page": 1, "ie": "utf8"}
    if account_name:
        params["account"] = account_name

    async with httpx.AsyncClient(headers=HEADERS, timeout=30, follow_redirects=True) as client:
        response = await client.get("https://weixin.sogou.com/weixin", params=params)
        if response.status_code == 403:
            raise RuntimeError("搜狗反爬限制触发，请等待 5-30 分钟后重试")
        response.raise_for_status()
        return parse_results(response.text, limit)


def parse_results(html: str, limit: int) -> list:
    soup = BeautifulSoup(html, "lxml")
    results = []

    for item in soup.find_all("div", class_="news-box")[:limit]:
        title_link = item.find("h3", {}).find("a") if item.find("h3") else None
        if not title_link:
            continue

        title = title_link.get_text(strip=True)
        url = title_link.get("href", "")

        account_elem = item.find("a", class_="account")
        account = account_elem.get_text(strip=True) if account_elem else "未知公众号"

        digest_elem = item.find("p", class_="txt-info")
        digest = digest_elem.get_text(strip=True) if digest_elem else ""

        time_elem = item.find("span", class_="s2")
        publish_time = re.sub(r"[^\d\-\s:]", "", time_elem.get_text(strip=True)).strip() if time_elem else ""

        results.append({
            "title": title,
            "account": account,
            "url": url,
            "digest": digest,
            "publish_time": publish_time,
        })

    return results


async def main():
    if len(sys.argv) < 2:
        print("用法: uv run search_articles.py <关键词> [公众号名称] [数量]", file=sys.stderr)
        sys.exit(1)

    query = sys.argv[1]
    account_name = sys.argv[2] if len(sys.argv) > 2 else None
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10

    try:
        results = await search_articles(query, account_name, limit)
        if not results:
            print("未找到相关文章（可能触发反爬，或关键词无结果）")
            return

        print(f"共找到 {len(results)} 篇文章：\n")
        for i, r in enumerate(results, 1):
            print(f"## {i}. {r['title']}")
            print(f"**公众号**: {r['account']}  |  **时间**: {r['publish_time']}")
            print(f"**摘要**: {r['digest']}")
            print(f"**链接**: {r['url']}\n")
    except RuntimeError as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"搜索失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
