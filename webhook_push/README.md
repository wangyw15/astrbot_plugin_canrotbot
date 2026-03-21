# Webhook 推送插件

## 启用插件

在 AstrBot 管理面板中：
- 转到**机器人**页面
- 创建`Webhook 推送 (webhook_push)`机器人并启用
- **查看 Webhook 链接**中获取基础回调地址

## 获取推送 Token

在聊天中发送指令`/webhook`

将返回一个专属推送 Token。

## 构建完整回调地址

使用以下格式拼接回调 URL：

```
{基础回调地址}?token={你的Token}&template={模板名}
```

### 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `token` | ✅ | 通过 `/webhook` 指令获取的 Token |
| `template` | ❌ | 消息模板名称，默认为 `default` |

### 完整示例

```
https://your-domain.com/api/platform/webhook/webhook_push?token=abc123xyz&template=default
```

## 自定义消息模板

支持使用 Jinja2 模板引擎自定义消息格式。

### 模板存放位置

在 AstrBot 数据目录下创建：

```
data/plugin_data/webhook_push/templates/
├── custom1.jinja      # 自定义模板
└── custom2.jinja      # 自定义模板
```

### 可用变量

| 变量 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `args` | dict | URL 查询参数 | `{{ args.title }}` |
| `headers` | dict | HTTP 请求头 | `{{ headers['Content-Type'] }}` |
| `body.form` | dict | POST 表单数据 | `{{ body.form.message }}` |
| `body.json` | dict | JSON 请求体 | `{{ body.json.content }}` |
| `body.text` | str | 纯文本请求体 | `{{ body.text }}` |
| `with_url` | bool | 是否发送链接 | - |

### 模板示例

### 使用自定义模板

1. 在 `data/plugin_data/webhook_push/templates/` 目录创建 `.jinja` 文件
2. 在 Webhook URL 中指定 `template` 参数：

```
https://your-domain.com/api/...?token=xxx&template=custom1
```

**注意**：模板文件查找顺序：用户目录 → 内置目录 → 默认模板
