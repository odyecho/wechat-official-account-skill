---
name: wechat-official-account
description: >-
  Use when reading WeChat Official Account (公众号) articles and content - supports
  listing drafts and published articles, fetching full article text by media_id,
  searching public WeChat articles via Sogou, and verifying account API
  configuration
metadata:
  author: Odyssey
  title: 微信公众号文章阅读工具
  description_zh: >-
    读取微信公众号文章内容。搜索公开文章和获取全文直接运行内置脚本；管理自己的公众号（含草稿与已发布列表）需配置 WECHAT_APPID 和
    WECHAT_SECRET。
  version: 1.0.6
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

## 能力总览（先看这里）

查找公众号文章有**多条路径**，各有适用场景与限制：

| 路径 | 命令 | 看到什么 | 前提 |
|------|------|----------|------|
| 旧素材 | `list_articles` / `get_article` | 较早时期发布的图文（约 2020 年前） | 凭据 |
| 草稿箱 | `list_drafts` / `get_draft` | 最新创作与待发布内容 | 凭据 |
| 已发布记录 | `list_published` | 正式发布过的文章列表及链接 | 凭据 + **微信认证** |
| 公开抓取 | `fetch_article.py <url>` | 任意公开文章的全文 | 无需凭据，仅需链接 |

> **重点**：`list_articles` 只覆盖「永久素材」里的老图文，**看不到新发布的文章**；
> 查最新内容请用 `list_drafts`。`list_published`（发布接口）要求公众号已通过微信认证，
> 未认证号会返回 `48001`。

## 快速参考

| 工具 | 脚本 | 需要凭据 |
|------|------|----------|
| 搜索公开文章 | `uv run scripts/search_articles.py <关键词>` | 否 |
| 获取文章全文（URL）| `uv run scripts/fetch_article.py <url>` | 否 |
| 查看公众号信息 | `uv run scripts/wechat_api.py account_info` | 是 |
| 列出旧素材文章（较早发布） | `uv run scripts/wechat_api.py list_articles` | 是 |
| 按 media_id 读旧素材文章 | `uv run scripts/wechat_api.py get_article <media_id>` | 是 |
| 列出草稿（最新创作） | `uv run scripts/wechat_api.py list_drafts` | 是 |
| 按 media_id 读草稿全文 | `uv run scripts/wechat_api.py get_draft <media_id>` | 是 |
| 列出已发布记录（需认证） | `uv run scripts/wechat_api.py list_published` | 是 |

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

URL 来自搜索结果的 `链接` 字段，或用户直接提供。兼容 `/s/...` 短链接与
`/s?...` 完整参数链接。

**返回**：标题、作者、公众号、发布时间、文章 ID、摘要、封面图、正文和图片链接。

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
> 来源：[微信开发者平台](https://developers.weixin.qq.com/platform/) → 开发 → 基本配置
> （AppID / AppSecret、以及下文提到的 IP 白名单，均在此处配置）

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

### 列出文章列表（旧素材，仅较早发布）

```bash
# 获取前 10 篇
uv run scripts/wechat_api.py list_articles

# 分页：从第 11 篇开始，取 5 篇
uv run scripts/wechat_api.py list_articles 10 5
```

**返回**：标题、media_id、作者、摘要、更新时间（media_id 用于下一步读全文）

**注意**：此接口每日上限 10 次。

> ⚠️ **局限**：此接口基于「永久素材」，只覆盖较早时期发布的图文
> （约 2020 年前）。**看不到新发布的文章**；查最新内容请用 `list_drafts`。

### 按 media_id 读取文章全文（旧素材）

```bash
uv run scripts/wechat_api.py get_article BM_Vc7hXXX
```

media_id 从 `list_articles` 结果中获取。

**返回**：标题、作者、正文（HTML 已转纯文本）、字数、阅读时间

---

### 草稿箱（最新创作，未认证号也可用）

列出草稿：

```bash
uv run scripts/wechat_api.py list_drafts 0 20
```

**返回**：标题、media_id、作者、更新时间、摘要

读取草稿全文：

```bash
uv run scripts/wechat_api.py get_draft <media_id>
```

media_id 从 `list_drafts` 结果中获取。

**返回**：标题、作者、正文（纯文本）、字数、预估阅读时间

> 📌 草稿箱记录的是「最新创作/待发布」内容，是查最新文章的首选。

---

### 已发布记录（需微信认证）

```bash
uv run scripts/wechat_api.py list_published 0 10
```

**返回**：标题、发布时间、文章链接（拿到链接后可用 `fetch_article.py` 抓全文）

> ⚠️ 发布接口要求公众号**通过微信认证**；未认证号会返回 `48001`。
> 此时请改用开发者平台「发表记录」查看，或提供文章链接抓取全文。

### 典型流程：读自己公众号文章

```bash
# 第一步：验证配置
uv run scripts/wechat_api.py account_info

# 第二步：查最新创作（草稿箱）
uv run scripts/wechat_api.py list_drafts 0 20

# 第三步：读草稿全文
uv run scripts/wechat_api.py get_draft <media_id>

# 如需读较早发布的旧文，改用
# uv run scripts/wechat_api.py list_articles 0 20
# uv run scripts/wechat_api.py get_article <media_id>
```

### 常见 API 错误

| 错误码 | 原因 | 解决方案 |
|--------|------|----------|
| 40001/40013 | APPID 或 SECRET 不正确 | 检查环境变量值 |
| 45009 | 超出调用限制（10次/天）| 次日再试 |
| 48001 | 接口未授权：多为公众号未通过微信认证（如发布接口） | 完成微信认证，或改用草稿/抓取通道 |
| IP 白名单错误 | 当前 IP 未授权 | 在微信开发者平台添加当前 IP |

---

## 脚本说明

| 脚本 | 功能 | 依赖 |
|------|------|------|
| `scripts/search_articles.py` | 搜狗微信搜索 | httpx, beautifulsoup4, lxml |
| `scripts/fetch_article.py` | 抓取公开文章全文与元数据（URL）| httpx[socks], beautifulsoup4, lxml |
| `scripts/wechat_api.py` | 官方 API：账号信息、旧素材/草稿/发布列表、按 media_id 读全文 | httpx, beautifulsoup4, lxml |

依赖通过 PEP 723 内联元数据声明，`uv run` 首次运行自动安装。
