#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "httpx[socks]",
#   "beautifulsoup4",
#   "lxml",
# ]
# ///
"""
微信公开文章全文抓取脚本

用法：
    uv run fetch_article.py <article_url>

示例：
    uv run fetch_article.py "https://mp.weixin.qq.com/s/xxx"
"""

import asyncio
from datetime import datetime
import html as html_lib
import random
import re
import sys
from zoneinfo import ZoneInfo

import httpx
from bs4 import BeautifulSoup, Tag


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3",
    "Connection": "keep-alive",
}


async def fetch_article(article_url: str) -> dict:
    if not (
        article_url.startswith("https://mp.weixin.qq.com/s/")
        or article_url.startswith("https://mp.weixin.qq.com/s?")
    ):
        raise ValueError(
            "无效的微信文章链接，必须以 https://mp.weixin.qq.com/s/ 或 https://mp.weixin.qq.com/s? 开头"
        )

    await asyncio.sleep(random.uniform(1, 3))

    async with httpx.AsyncClient(headers=HEADERS, timeout=60, follow_redirects=True) as client:
        response = await client.get(article_url)
        response.raise_for_status()
        return parse_article(response.text, article_url)


def parse_article(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, "lxml")

    def meta_content(*selectors: str) -> str:
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                content = elem.get("content")
                if isinstance(content, str):
                    return content.strip()
        return ""

    def script_value(name: str) -> str:
        pattern = rf'''(?:var\s+|window\.){re.escape(name)}\s*=\s*(?:htmlDecode\()?(?:"([^"]*)"|'([^']*)')'''
        match = re.search(pattern, html, re.DOTALL)
        if not match:
            return ""
        value = match.group(1) if match.group(1) is not None else match.group(2)
        return html_lib.unescape(value.replace(r"\/", "/")).strip()

    title_elem = soup.find("h1", class_="rich_media_title")
    title = (
        title_elem.get_text(strip=True) if title_elem else ""
    ) or meta_content('meta[property="og:title"]') or script_value("msg_title") or "无标题"

    author_elem = soup.find("a", class_="rich_media_meta_link")
    author = (
        meta_content('meta[name="author"]', 'meta[property="og:article:author"]')
        or (author_elem.get_text(strip=True) if author_elem else "")
        or script_value("author")
        or "未知作者"
    )

    account_elem = soup.select_one("#js_name")
    account_name = (
        account_elem.get_text(strip=True) if account_elem else ""
    ) or script_value("nickname") or meta_content('meta[property="og:site_name"]')

    time_elem = soup.find("em", id="publish_time")
    publish_time = time_elem.get_text(strip=True) if time_elem else ""
    publish_timestamp = script_value("ct") or script_value("oriCreateTime")
    if not publish_time and publish_timestamp.isdigit():
        publish_time = datetime.fromtimestamp(
            int(publish_timestamp), tz=ZoneInfo("Asia/Shanghai")
        ).strftime("%Y-%m-%d %H:%M")

    description = meta_content(
        'meta[property="og:description"]', 'meta[name="description"]'
    )
    cover_image = meta_content('meta[property="og:image"]')

    content_elem = soup.find("div", class_="rich_media_content")
    if isinstance(content_elem, Tag):
        for tag in content_elem(["script", "style"]):
            tag.decompose()
        content = content_elem.get_text(separator="\n", strip=True)
        images = list(dict.fromkeys(
            img.get("data-src") or img.get("src")
            for img in content_elem.find_all("img")
            if img.get("data-src") or img.get("src")
        ))
    else:
        content = "无法获取文章内容（可能需要登录或内容已删除）"
        images = []

    word_count = len(content)
    return {
        "title": title,
        "author": author,
        "account_name": account_name,
        "publish_time": publish_time,
        "publish_timestamp": int(publish_timestamp) if publish_timestamp.isdigit() else None,
        "description": description,
        "cover_image": cover_image,
        "appmsgid": script_value("appmsgid"),
        "itemidx": script_value("itemidx"),
        "content": content,
        "url": url,
        "images": images,
        "word_count": word_count,
        "read_time_minutes": max(1, word_count // 300),
    }


async def main():
    if len(sys.argv) < 2:
        print("用法: uv run fetch_article.py <article_url>", file=sys.stderr)
        sys.exit(1)

    url = sys.argv[1]
    try:
        article = await fetch_article(url)
        print(f"# {article['title']}\n")
        print(f"**作者**: {article['author']}")
        print(f"**公众号**: {article['account_name'] or '未知公众号'}")
        print(f"**发布时间**: {article['publish_time'] or '未知'}")
        if article["appmsgid"]:
            print(f"**文章 ID**: {article['appmsgid']}")
        if article["description"]:
            print(f"**摘要**: {article['description']}")
        if article["cover_image"]:
            print(f"**封面图**: {article['cover_image']}")
        print(f"**字数**: {article['word_count']}  |  **预估阅读**: {article['read_time_minutes']} 分钟\n")
        print("---\n")
        print(article["content"])
        if article["images"]:
            print(f"\n\n**文章图片** ({len(article['images'])} 张):")
            for img_url in article["images"]:
                print(f"- {img_url}")
    except ValueError as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)
    except httpx.HTTPStatusError as e:
        print(f"HTTP 错误 {e.response.status_code}：微信反爬限制，请等待 10-30 分钟后重试", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"抓取失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
