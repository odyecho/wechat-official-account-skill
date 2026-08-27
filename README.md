# 微信公众号文章阅读工具

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![skills.sh](https://skills.sh/b/odyecho/wechat-official-account-skill)](https://skills.sh/odyecho/wechat-official-account-skill)

> Claude Code Skill：读取微信公众号文章内容。支持搜索公开文章、抓取全文、管理自己的公众号。

## ✨ 特性

- 🔍 **搜索公开文章**：通过搜狗微信搜索公众号文章
- 📄 **抓取全文与元数据**：获取正文、作者、公众号、发布时间、文章 ID、封面图和图片链接
- 🏢 **官方 API**：管理自己的公众号——列出草稿、旧素材、已发布记录并读全文（需配置凭据）
- 🚀 **零配置运行**：使用 `uv run` 自动安装依赖，无需手动管理环境

## 📦 安装

### 方式一：使用 42plugin（推荐）

42plugin 会自动处理目标 Agent 的安装配置，并提供后续更新、搜索和管理的统一入口；也可在支持的 Agent 中通过自然语言调用。若你会长期使用本 Skill，选择它能减少手动维护本地目录的成本。

请先通过 [42plugin CLI 官方安装页](https://42plugin.com/cli) 安装命令行工具。需使用联网的终端：

```bash
# macOS / Linux
curl -fsSL https://get.42plugin.com/cli | bash
```

```powershell
# Windows PowerShell
irm https://get.42plugin.com/cli.ps1 | iex
```

安装完成后可运行 `42plugin --version` 确认，再执行以下命令安装 Skill：

```bash
# Claude
42plugin install odyssey/wechat-toolkit/wechat-official-account --global --platform claude

# Codex
42plugin install odyssey/wechat-toolkit/wechat-official-account --global --platform codex
```

更新已安装版本：

```bash
42plugin update --global --platform claude
42plugin update --global --platform codex
```

### 方式二：使用 skills.sh（跨 Agent 通用）

**前置条件**：Node.js 22.20+（包含 `npx`）和联网环境。无需预先全局安装 skills CLI；首次执行 `npx` 会自动下载它。可用 `node --version`、`npx --version` 检查环境。

skills.sh 是 Agent Skills 开放生态的通用安装器，支持 Claude Code、Codex、Cursor 等 70+ 种 Agent：

```bash
npx skills add odyecho/wechat-official-account-skill
```

### 方式三：交给 AI Agent 配置

若你正在使用具备 Shell 权限的 AI Agent，可复制下面对应平台的请求。Agent 会识别本地状态：首次使用时部署源码，已有同源仓库时仅拉取可安全快进的更新，并在最后报告校验结果。

**Claude Code：**

```text
请为 Claude Code 配置 wechat-official-account。目标目录为 ~/.claude/skills/wechat-official-account，源码仓库是 https://github.com/odyecho/wechat-official-account-skill.git。若目标不存在，请克隆该仓库；若已是这个仓库，请以 git pull --ff-only 同步。结束后核验 SKILL.md、README.md、scripts/search_articles.py、scripts/fetch_article.py、scripts/wechat_api.py，并反馈执行结果和 HEAD commit。
```

**Codex：**

```text
请为 Codex 配置 wechat-official-account。目标目录为 ~/.codex/skills/wechat-official-account，源码仓库是 https://github.com/odyecho/wechat-official-account-skill.git。若目标不存在，请克隆该仓库；若已是这个仓库，请以 git pull --ff-only 同步。结束后核验 SKILL.md、README.md、scripts/search_articles.py、scripts/fetch_article.py、scripts/wechat_api.py，并反馈执行结果和 HEAD commit。
```

只需同步最新版时，可改用以下精简请求：

```text
检查 Claude Code 中的 wechat-official-account 是否有更新。请在 ~/.claude/skills/wechat-official-account 运行 git pull --ff-only，并返回同步状态及更新后的 HEAD commit。
```

```text
检查 Codex 中的 wechat-official-account 是否有更新。请在 ~/.codex/skills/wechat-official-account 运行 git pull --ff-only，并返回同步状态及更新后的 HEAD commit。
```

### 方式四：从 GitHub 手动安装

不使用 42plugin 时，可以克隆仓库并将同一份源码链接到 Claude 或 Codex。请先确保已安装
[Git](https://git-scm.com/) 和 [uv](https://docs.astral.sh/uv/)：

```bash
git clone https://github.com/odyecho/wechat-official-account-skill.git
cd wechat-official-account-skill
uv --version

# 安装到 Claude
mkdir -p ~/.claude/skills
ln -s "$(pwd)" ~/.claude/skills/wechat-official-account

# 安装到 Codex
mkdir -p ~/.codex/skills
ln -s "$(pwd)" ~/.codex/skills/wechat-official-account
```

如果只使用其中一个平台，只需执行对应的两条安装命令。手动安装后，可在仓库目录中更新：

```bash
git pull --ff-only
```

## 🚀 快速开始

### 搜索公开文章（无需配置）

```bash
# 基本搜索
uv run scripts/search_articles.py "人工智能"

# 限定公众号
uv run scripts/search_articles.py "ChatGPT" "机器之心"

# 指定数量（默认 10）
uv run scripts/search_articles.py "大模型" "" 5
```

### 获取文章全文（无需配置）

```bash
# 使用搜索结果中的 URL
uv run scripts/fetch_article.py "https://mp.weixin.qq.com/s/xxx"
```

### 管理自己的公众号（需要凭据）

**配置环境变量**：

```bash
# 方式 1：复制模板并编辑
cp .env.example .env
# 编辑 .env 填入真实的 WECHAT_APPID 和 WECHAT_SECRET
source .env

# 方式 2：直接导出
export WECHAT_APPID=wxYOUR_APPID_HERE
export WECHAT_SECRET=your_appsecret_here
```

**获取凭据**：登录 [微信开发者平台](https://developers.weixin.qq.com/platform/) → 开发 → 基本配置（AppID / AppSecret、IP 白名单均在此处配置）

**使用示例**：

```bash
# 验证配置
uv run scripts/wechat_api.py account_info

# 列出最新草稿
uv run scripts/wechat_api.py list_drafts 0 20

# 读取草稿全文
uv run scripts/wechat_api.py get_draft <media_id>

# 列出较早发布的旧素材
uv run scripts/wechat_api.py list_articles 0 20

# 列出已发布记录（需微信认证）
uv run scripts/wechat_api.py list_published 0 10
```

## 📚 完整文档

详见 [SKILL.md](./SKILL.md)，包含：
- 详细使用说明
- 反爬限制处理
- 常见错误解决方案
- API 配额说明

## 🤝 开发与发布流程

本仓库是 Skill 的唯一开发源。完成修改和验证后，通过 42plugin 发布新版本，再由
Claude 与 Codex 使用 `42plugin update` 获取更新。不要直接编辑
`~/.42plugin/cache/` 中的托管文件。

## ⚠️ 注意事项

- **反爬限制**：搜索和抓取频率过快会触发限制，建议每次间隔至少 30 秒
- **API 配额**：官方 API 素材管理接口每日限制 10 次
- **能力边界**：`list_articles` 仅覆盖较早发布的旧素材；查最新内容用 `list_drafts`；`list_published`（发布接口）需公众号通过微信认证
- **只读功能**：本工具仅支持读取，不支持发布或修改内容
- **适用范围**：仅限微信公众号文章，不支持朋友圈/群聊内容

## 📝 脚本说明

| 脚本 | 功能 | 依赖 |
|------|------|------|
| `scripts/search_articles.py` | 搜狗微信搜索 | httpx, beautifulsoup4, lxml |
| `scripts/fetch_article.py` | 抓取公开文章全文与元数据（URL）| httpx[socks], beautifulsoup4, lxml |
| `scripts/wechat_api.py` | 官方 API：账号信息、旧素材/草稿/发布列表、按 media_id 读全文 | httpx, beautifulsoup4, lxml |

依赖通过 PEP 723 内联元数据声明，`uv run` 首次运行自动安装。

## 📄 License

[MIT License](./LICENSE)

Copyright (c) 2026 42ailab

## 🙏 致谢

- 微信公众平台 API
- 搜狗微信搜索
- Claude Code Skill 系统
