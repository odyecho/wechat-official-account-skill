# 微信公众号文章阅读工具

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

> Claude Code Skill：读取微信公众号文章内容。支持搜索公开文章、抓取全文、管理自己的公众号。

## ✨ 特性

- 🔍 **搜索公开文章**：通过搜狗微信搜索公众号文章
- 📄 **抓取全文**：获取任意微信文章的完整内容
- 🏢 **官方 API**：管理自己的公众号文章（需配置凭据）
- 🚀 **零配置运行**：使用 `uv run` 自动安装依赖，无需手动管理环境

## 📦 安装

确保已安装 [uv](https://docs.astral.sh/uv/)：

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 验证安装
which uv
```

克隆仓库：

```bash
git clone https://github.com/odyecho/wechat-official-account-skill.git
cd wechat-official-account-skill
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

### 获取文章全文

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
export WECHAT_APPID=wx1234567890abcdef
export WECHAT_SECRET=abcdef1234567890abcdef1234567890
```

**获取凭据**：登录 [微信公众平台](https://mp.weixin.qq.com) → 开发 → 基本配置

**使用示例**：

```bash
# 验证配置
uv run scripts/wechat_api.py account_info

# 列出文章
uv run scripts/wechat_api.py list_articles 0 20

# 读取具体文章
uv run scripts/wechat_api.py get_article BM_Vc7hXXX
```

## 📚 完整文档

详见 [SKILL.md](./SKILL.md)，包含：
- 详细使用说明
- 反爬限制处理
- 常见错误解决方案
- API 配额说明

## 🤝 作为 Claude Code Skill 使用

将此目录添加到 Claude Code 的 skills 目录：

```bash
ln -s $(pwd) ~/.claude/skills/wechat-official-account
```

然后在 Claude Code 中使用：

```
/wechat-official-account
```

## ⚠️ 注意事项

- **反爬限制**：搜索和抓取频率过快会触发限制，建议每次间隔至少 30 秒
- **API 配额**：官方 API 素材管理接口每日限制 10 次
- **只读功能**：本工具仅支持读取，不支持发布或修改内容
- **适用范围**：仅限微信公众号文章，不支持朋友圈/群聊内容

## 📝 脚本说明

| 脚本 | 功能 | 依赖 |
|------|------|------|
| `scripts/search_articles.py` | 搜狗微信搜索 | httpx, beautifulsoup4, lxml |
| `scripts/fetch_article.py` | 抓取公开文章全文（URL）| httpx, beautifulsoup4, lxml |
| `scripts/wechat_api.py` | 官方 API：账号信息、文章列表、按 media_id 读全文 | httpx, beautifulsoup4, lxml |

依赖通过 PEP 723 内联元数据声明，`uv run` 首次运行自动安装。

## 📄 License

[MIT License](./LICENSE)

Copyright (c) 2026 42ailab

## 🙏 致谢

- 微信公众平台 API
- 搜狗微信搜索
- Claude Code Skill 系统
