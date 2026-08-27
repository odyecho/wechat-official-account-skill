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
微信公众号官方 API 工具脚本

需要环境变量：WECHAT_APPID 和 WECHAT_SECRET

用法：
    uv run wechat_api.py account_info
    uv run wechat_api.py list_articles [offset] [count]    # 旧素材（较早发布的图文）
    uv run wechat_api.py get_article <media_id>            # 读旧素材全文
    uv run wechat_api.py list_drafts [offset] [count]      # 草稿箱（最新创作）
    uv run wechat_api.py get_draft <media_id>              # 读草稿全文
    uv run wechat_api.py list_published [offset] [count]   # 已发布记录（需微信认证）

示例：
    uv run wechat_api.py account_info
    uv run wechat_api.py list_articles 0 10
    uv run wechat_api.py get_article BM_Vc7hXXX
    uv run wechat_api.py list_drafts 0 20
    uv run wechat_api.py list_published 0 10
"""

import sys
import os
import asyncio
import time
import httpx
from bs4 import BeautifulSoup

BASE_URL = "https://api.weixin.qq.com/cgi-bin"

# 错误码说明
ERROR_CODES = {
    40001: "AppSecret 错误或不正确，请检查 WECHAT_SECRET 是否正确",
    40002: "不合法的凭证类型",
    40013: "不合法的 AppID，请检查 WECHAT_APPID 是否正确",
    41001: "缺少 access_token 参数",
    42001: "access_token 超期，已自动重试",
    45009: "调用接口超出限制（素材管理每日 10 次），请明天再试",
    48001: "API 未授权：多为公众号未通过微信认证（如发布/草稿高级接口），需先完成微信认证",
    50001: "用户未授权该 API",
}


def check_env():
    appid = os.environ.get("WECHAT_APPID")
    secret = os.environ.get("WECHAT_SECRET")
    if not appid or not secret:
        print("错误：缺少环境变量", file=sys.stderr)
        print("  export WECHAT_APPID=your_app_id", file=sys.stderr)
        print("  export WECHAT_SECRET=your_app_secret", file=sys.stderr)
        sys.exit(1)
    return appid, secret


async def get_access_token(appid: str, secret: str) -> str:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{BASE_URL}/token", params={
            "grant_type": "client_credential",
            "appid": appid,
            "secret": secret,
        })
        r.raise_for_status()
        data = r.json()
        if "access_token" not in data:
            code = data.get("errcode", 0)
            msg = ERROR_CODES.get(code, data.get("errmsg", "未知错误"))
            print(f"获取 token 失败 (errcode={code}): {msg}", file=sys.stderr)
            sys.exit(1)
        return data["access_token"]


async def api_post(token: str, endpoint: str, body: dict, fatal: bool = True) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{BASE_URL}/{endpoint}",
            params={"access_token": token},
            json=body,
        )
        r.raise_for_status()
        data = r.json()
        code = data.get("errcode", 0)
        if code != 0:
            msg = ERROR_CODES.get(code, data.get("errmsg", "未知错误"))
            if not fatal:
                # 交由调用方自行处理（如对 48001 做专项提示）
                return data
            print(f"API 错误 (errcode={code}): {msg}", file=sys.stderr)
            sys.exit(1)
        return data


async def api_get(token: str, endpoint: str, params: dict = None) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(
            f"{BASE_URL}/{endpoint}",
            params={"access_token": token, **(params or {})},
        )
        r.raise_for_status()
        data = r.json()
        code = data.get("errcode", 0)
        if code != 0:
            msg = ERROR_CODES.get(code, data.get("errmsg", "未知错误"))
            print(f"API 错误 (errcode={code}): {msg}", file=sys.stderr)
            sys.exit(1)
        return data


def html_to_text(html: str) -> str:
    """将 HTML 内容转换为纯文本"""
    if not html:
        return ""
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)


async def cmd_account_info():
    appid, secret = check_env()
    token = await get_access_token(appid, secret)
    data = await api_get(token, "material/get_materialcount")
    print("# 公众号账号信息\n")
    print(f"**AppID**: {appid}")
    print(f"**API 状态**: 正常（token 获取成功）\n")
    print("## 素材统计")
    print(f"- 图片素材: {data.get('image_count', 0)} 个")
    print(f"- 语音素材: {data.get('voice_count', 0)} 个")
    print(f"- 视频素材: {data.get('video_count', 0)} 个")
    print(f"- 图文素材: {data.get('news_count', 0)} 篇\n")
    print("## API 配额说明")
    print("- access_token 获取: 2000次/天")
    print("- 素材管理接口: 10次/天")


async def cmd_list_articles(offset: int, count: int):
    appid, secret = check_env()
    token = await get_access_token(appid, secret)
    data = await api_post(token, "material/batchget_material", {
        "type": "news",
        "offset": offset,
        "count": min(count, 20),
    })

    items = data.get("item", [])
    total = data.get("total_count", 0)

    print(f"# 文章列表（共 {total} 篇，当前显示第 {offset+1}–{offset+len(items)} 篇）\n")

    for item in items:
        media_id = item.get("media_id", "")
        update_time = time.strftime(
            "%Y-%m-%d %H:%M:%S",
            time.localtime(item.get("update_time", 0))
        )
        news_items = item.get("content", {}).get("news_item", [])
        for news in news_items:
            print(f"## {news.get('title', '（无标题）')}")
            print(f"**media_id**: `{media_id}`")
            print(f"**作者**: {news.get('author', '未知')}  |  **更新时间**: {update_time}")
            print(f"**摘要**: {news.get('digest', '')}")
            print(f"**原文链接**: {news.get('content_source_url', '')}\n")


async def cmd_get_article(media_id: str):
    appid, secret = check_env()
    token = await get_access_token(appid, secret)
    data = await api_post(token, "material/get_material", {"media_id": media_id})

    news_items = data.get("news_item", [])
    if not news_items:
        print(f"错误：未找到 media_id={media_id} 对应的文章", file=sys.stderr)
        sys.exit(1)

    news = news_items[0]
    content_html = news.get("content", "")
    content_text = html_to_text(content_html)
    word_count = len(content_text)

    print(f"# {news.get('title', '无标题')}\n")
    print(f"**作者**: {news.get('author', '未知')}")
    print(f"**字数**: {word_count}  |  **预估阅读**: {max(1, word_count // 300)} 分钟")
    print(f"**原文链接**: {news.get('content_source_url', '')}\n")
    print("---\n")
    print(content_text)


def _fmt_ts(ts: int) -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts)) if ts else "?"


async def cmd_list_drafts(offset: int, count: int):
    """列出草稿箱中的文章（含最新创作，未认证号也可用）"""
    appid, secret = check_env()
    token = await get_access_token(appid, secret)
    data = await api_post(token, "draft/batchget", {
        "offset": offset,
        "count": min(count, 20),
        "no_content": 1,
    })

    items = data.get("item", [])
    total = data.get("total_count", 0)

    print(f"# 草稿列表（共 {total} 篇，当前显示第 {offset+1}–{offset+len(items)} 篇）\n")

    for item in items:
        media_id = item.get("media_id", "")
        update_time = _fmt_ts(item.get("update_time", 0))
        news_items = item.get("content", {}).get("news_item", [])
        for news in news_items:
            print(f"## {news.get('title', '（无标题）')}")
            print(f"**media_id**: `{media_id}`")
            print(f"**作者**: {news.get('author', '未知')}  |  **更新时间**: {update_time}")
            print(f"**摘要**: {news.get('digest', '')}\n")


async def cmd_get_draft(media_id: str):
    """按 media_id 读取草稿全文（draft/get）"""
    appid, secret = check_env()
    token = await get_access_token(appid, secret)
    data = await api_post(token, "draft/get", {"media_id": media_id})

    news_items = data.get("news_item", [])
    if not news_items:
        print(f"错误：未找到 media_id={media_id} 对应的草稿", file=sys.stderr)
        sys.exit(1)

    news = news_items[0]
    content_text = html_to_text(news.get("content", ""))
    word_count = len(content_text)

    print(f"# {news.get('title', '无标题')}\n")
    print(f"**作者**: {news.get('author', '未知')}")
    print(f"**字数**: {word_count}  |  **预估阅读**: {max(1, word_count // 300)} 分钟\n")
    print("---\n")
    print(content_text)


async def cmd_list_published(offset: int, count: int):
    """列出已正式发布的文章（需微信认证，未认证号会遇 48001）"""
    appid, secret = check_env()
    token = await get_access_token(appid, secret)
    data = await api_post(token, "freepublish/batchget", {
        "offset": offset,
        "count": min(count, 20),
        "no_content": 1,
    }, fatal=False)

    code = data.get("errcode", 0)
    if code != 0:
        if code == 48001:
            print("⚠️ 发布接口未授权（48001）：该公众号未通过微信认证，无法通过 API 查询已发布列表。", file=sys.stderr)
            print("  替代方案：登录微信开发者平台「发表记录」查看，或提供文章链接用 fetch_article.py 抓取全文。", file=sys.stderr)
        else:
            msg = ERROR_CODES.get(code, data.get("errmsg", "未知错误"))
            print(f"API 错误 (errcode={code}): {msg}", file=sys.stderr)
        return

    items = data.get("item", [])
    total = data.get("total_count", 0)

    print(f"# 已发布列表（共 {total} 篇，当前显示第 {offset+1}–{offset+len(items)} 篇）\n")

    for item in items:
        update_time = _fmt_ts(item.get("update_time", 0))
        news_items = item.get("content", {}).get("news_item", [])
        for news in news_items:
            url = news.get("url", "")
            print(f"## {news.get('title', '（无标题）')}")
            print(f"**发布时间**: {update_time}")
            print(f"**文章链接**: {url}\n")


async def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "account_info":
        await cmd_account_info()
        return

    # 带 offset/count 的列表命令
    list_commands = {
        "list_articles": cmd_list_articles,
        "list_drafts": cmd_list_drafts,
        "list_published": cmd_list_published,
    }
    if cmd in list_commands:
        offset = int(sys.argv[2]) if len(sys.argv) > 2 else 0
        count = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        await list_commands[cmd](offset, count)
        return

    # 带 media_id 的单篇读取命令
    read_commands = {
        "get_article": cmd_get_article,
        "get_draft": cmd_get_draft,
    }
    if cmd in read_commands:
        if len(sys.argv) < 3:
            print("错误：请提供 media_id 参数", file=sys.stderr)
            print(f"用法: uv run wechat_api.py {cmd} <media_id>", file=sys.stderr)
            sys.exit(1)
        await read_commands[cmd](sys.argv[2])
        return

    print(f"未知命令: {cmd}", file=sys.stderr)
    print("可用命令: account_info | list_articles | get_article | list_drafts | get_draft | list_published", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
