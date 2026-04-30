---
name: wechat-official-account
description: >-
  Use when reading WeChat Official Account (公众号) articles and content - supports
  listing articles, fetching full article text by media_id, searching public
  WeChat articles via Sogou, and verifying account API configuration
metadata:
  author: 42ailab
  title: 微信公众号文章阅读工具
  description_zh: 读取微信公众号文章内容。搜索公开文章和获取全文直接运行内置脚本；管理自己的公众号需配置 WECHAT_APPID 和 WECHAT_SECRET。
  version: 1.0.1
  license: MIT
---

# 微信公众号文章阅读工具

## 概述

两条数据通道，均通过 `uv run` 直接运行脚本，无需安装任何 MCP Server：

- **搜索通道**（无需凭据）：搜索公开文章、抓取任意文章全文
- **官方 API 通道**（需要 `WECHAT_APPID` + `WECHAT_SECRET`）：管理自己的公众号

## 使用时机

- 搜索公开文章 → `search_articles.py`
- 获取某篇文章全文（已有 URL）→ `fetch_article.py`
- 查看/列出/读取自己管理的公众号文章 → `wechat_api.py`

不适用于：发布或修改内容（只读）、朋友圈/群聊内容。

## 快速参考

| 工具 | 脚本 | 需要凭据 |
|------|------|----------|
| 搜索公开文章 | `uv run scripts/search_articles.py <关键词>` | 否 |
| 获取文章全文（URL）| `uv run scripts/fetch_article.py <url>` | 否 |
| 查看公众号信息 | `uv run scripts/wechat_api.py account_info` | 是 |
| 列出文章列表 | `uv run scripts/wechat_api.py list_articles` | 是 |
| 按 media_id 读文章 | `uv run scripts/wechat_api.py get_article <media_id>` | 是 |

**运行前提**：已安装 `uv`（`which uv` 验证）。脚本内置依赖声明，首次运行自动安装。

---

## 搜索通道（无需配置）

### 搜索公开文章

```bash
# 基本搜索
uv run scripts/search_articles.py "人工智能"

# 限定公众号
uv run scripts/search_articles.py "ChatGPT" "机器之心"

# 指定数量（默认 10）
uv run scripts/search_articles.py "大模型" "" 5
```

**返回**：文章标题、公众号名称、发布时间、摘要、文章 URL

**反爬注意**：频率过快触发限制，每次间隔至少 30 秒；被封锁后等待 5-30 分钟。

### 获取文章全文

```bash
uv run scripts/fetch_article.py "https://mp.weixin.qq.com/s/xxx"
```

URL 来自搜索结果的 `链接` 字段，或用户直接提供。

**反爬注意**：失败后等待 10-30 分钟重试。

### 典型流程：搜索 + 读全文

```bash
# 第一步：搜索，获取 URL
uv run scripts/search_articles.py "关键词" "公众号名"

# 第二步：用搜索结果中的 URL 读全文
uv run scripts/fetch_article.py "https://mp.weixin.qq.com/s/xxx"
```

---

## 官方 API 通道（需要凭据）

> **前提**：需要微信公众号的 AppID 和 AppSecret。
> 来源：[微信公众平台](https://mp.weixin.qq.com) → 开发 → 基本配置

**一次性配置**：

```bash
# 1. 复制模板
cp scripts/../.env.example .env

# 2. 编辑 .env，填入真实值
#    WECHAT_APPID=wxYOUR_APPID_HERE
#    WECHAT_SECRET=your_appsecret_here...

# 3. 加载到当前 Shell（每次新开终端需重新执行）
source .env
```

或直接临时导出：

```bash
export WECHAT_APPID=wxYOUR_APPID_HERE
export WECHAT_SECRET=your_appsecret_here
```

### 查看公众号信息（验证配置）

```bash
uv run scripts/wechat_api.py account_info
```

**返回**：AppID、API 状态、素材数量统计、配额说明

### 列出文章列表

```bash
# 获取前 10 篇
uv run scripts/wechat_api.py list_articles

# 分页：从第 11 篇开始，取 5 篇
uv run scripts/wechat_api.py list_articles 10 5
```

**返回**：标题、media_id、作者、摘要、更新时间（media_id 用于下一步读全文）

**注意**：此接口每日上限 10 次。

### 按 media_id 读取文章全文

```bash
uv run scripts/wechat_api.py get_article BM_Vc7hXXX
```

media_id 从 `list_articles` 结果中获取。

**返回**：标题、作者、正文（HTML 已转纯文本）、字数、阅读时间

### 典型流程：读自己公众号文章

```bash
# 第一步：验证配置
uv run scripts/wechat_api.py account_info

# 第二步：获取文章列表和 media_id
uv run scripts/wechat_api.py list_articles 0 20

# 第三步：读具体文章全文
uv run scripts/wechat_api.py get_article BM_Vc7hXXX
```

### 常见 API 错误

| 错误码 | 原因 | 解决方案 |
|--------|------|----------|
| 40001/40013 | APPID 或 SECRET 不正确 | 检查环境变量值 |
| 45009 | 超出调用限制（10次/天）| 次日再试 |
| 48001 | API 功能未授权 | 在微信公众平台确认已开启开发者模式 |
| IP 白名单错误 | 当前 IP 未授权 | 在微信公众平台后台添加 IP |

---

## 脚本说明

| 脚本 | 功能 | 依赖 |
|------|------|------|
| `scripts/search_articles.py` | 搜狗微信搜索 | httpx, beautifulsoup4, lxml |
| `scripts/fetch_article.py` | 抓取公开文章全文（URL）| httpx, beautifulsoup4, lxml |
| `scripts/wechat_api.py` | 官方 API：账号信息、文章列表、按 media_id 读全文 | httpx, beautifulsoup4, lxml |

依赖通过 PEP 723 内联元数据声明，`uv run` 首次运行自动安装。
