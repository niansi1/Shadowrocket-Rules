# Shadowrocket Rules

基于 [LingJingMaster/Shadowrocket-Rules](https://github.com/LingJingMaster/Shadowrocket-Rules) 的个人配置。当前基础版本为 [`f6b1652`](https://github.com/LingJingMaster/Shadowrocket-Rules/commit/f6b1652201f2208a63a64eca932e5034b7a4acfc)，核对日期：2026-10-02。

保留该上游的默认网络策略，主要调整 Google AI 分流和 AI 节点选择。配置及八个配套 `.list` 文件均由本仓库提供。

## 手机订阅

[下载当前配置](https://raw.githubusercontent.com/niansi1/Shadowrocket-Rules/main/Shadowrocket.conf)

```text
https://raw.githubusercontent.com/niansi1/Shadowrocket-Rules/main/Shadowrocket.conf
```

1. 打开 Shadowrocket →「配置」→ `+`，粘贴上面的地址下载并选中启用。
2. 在首页添加自己的机场节点订阅，将「全局路由」设为「配置」。这份规则配置不包含节点。
3. 将 `🤖 AI 服务` 选为 `🇺🇸 美国手选`，再进入美国手选组，选择一个可用美国节点。旧配置可能保留之前的选择，请手动确认。
4. `🔍 谷歌服务` 保留上游设置，默认选择 `🇯🇵 日本节点`。
5. 后续在「配置」页更新远程配置并刷新规则集；主配置及八个配套规则由本仓库提供，其他公共规则仍从 blackmatrix7 获取。

先前提供的 [HB-Shadowrocket.conf 地址](https://raw.githubusercontent.com/niansi1/Shadowrocket-Rules/main/HB-Shadowrocket.conf) 仍可使用，内容与 `Shadowrocket.conf` 完全一致，内部 `update-url` 统一指向新主配置。

如果美国手选组为空，检查节点名称是否含 `美国`、`US`、`USA`、`🇺🇸` 等标识，或在 AI 服务中选择 `PROXY` 并在首页指定一个可用节点。手选避免测速策略自动换节点，机场节点本身仍不保证固定出口 IP。

## 分流结果

| 服务 | 默认策略 |
|---|---|
| Gemini 网页、手机端、Gemini API、AI Studio | 🤖 AI 服务 → 🇺🇸 美国手选 |
| NotebookLM、Code Assist、Android Studio AI、Antigravity | 🤖 AI 服务 → 🇺🇸 美国手选 |
| Labs、Flow、Jules、Opal、Stitch、DeepMind | 🤖 AI 服务 → 🇺🇸 美国手选 |
| Vertex AI 全球及各区域 API | 🤖 AI 服务 → 🇺🇸 美国手选 |
| 其他 AI，包括上游列出的 ChatGPT、Claude、Apple Intelligence 等 | 🤖 AI 服务 → 🇺🇸 美国手选 |
| Google 搜索、Gmail 网页、Drive、地图、Google Voice | 🔍 谷歌服务 → 🇯🇵 日本节点 |
| Google 登录、共享 API 与普通静态资源 | 🔍 谷歌服务 → 🇯🇵 日本节点 |
| Gmail 等邮件协议端点（IMAP / POP3 / SMTP） | 📧 邮件服务 → PROXY，沿用上游 |
| YouTube 及两个前置翻译 API | 📹 油管视频 → 🚀 节点选择；Google 重叠域名见下文 |
| 汇丰香港及其他香港银行 | 各银行策略组 → DIRECT，沿用上游 |
| 券商服务 | 📈 券商服务 → 🇭🇰 香港节点，沿用上游 |
| 国内服务、豆包、DeepSeek、微信 HTTPDNS 例外 | 🔒 国内服务 → DIRECT，沿用上游 |
| 其他已收录的 HTTPDNS | 🧱 DNS 防泄露 → REJECT，沿用上游 |
| Apple 普通服务 / Apple Push | 🍏 苹果服务 → DIRECT / 🍎 苹果推送 → 🚀 节点选择 |

## 相对上游的修改

- **Google AI 优先匹配**：主配置中前置 48 条 Google AI 规则，再匹配上游 `Google.list`。补齐 Gemini 手机端、NotebookLM 后端、Code Assist 等接口，避免被宽泛 Google 规则抢先匹配。
- **准确限定 AI 域名**：使用明确域名、域名后缀，以及 `*-aiplatform.googleapis.com` 的区域通配符。登录、共享 CDN、Google Voice 继续按上游普通 Google 规则处理。
- **AI 默认手选节点**：增加美国手选组，避免外层 `select` 嵌套默认 `url-test` 仍会自动换节点；美国自动测速组仍可主动选择。
- **美国节点筛选**：移除美国自动组和其他节点排除式中单独的 `美` 字，减少误选。
- **订阅归属本仓库**：主配置自更新地址和配套规则地址统一使用 `niansi1/Shadowrocket-Rules`，八个 `.list` 文件内容保持上游快照。

上游的代理 DoH、IPv6 关闭、微信 HTTPDNS 例外、邮件分流、Apple 完整域名集、汇丰默认直连、T-Mobile IP 规则，以及 Google 重写 / MITM 段均保留。Google AI 分流本身不需要 HTTPS 解密。

## 已知边界

- 同一域名下的普通页面与 AI 功能无法仅按域名拆分，例如仍使用 `www.google.com` 的搜索内 AI 功能；共用登录与资源也继续走普通 Google 出口。
- 保留上游 Google / YouTube 顺序。`googlevideo.com`、`youtubei.googleapis.com` 等与 Google 规则重叠的域名仍先命中谷歌组；两个显式翻译 API 例外仍走油管组。
- 邮件协议端点先于 Google 规则匹配，Gmail 网页与 Gmail 邮件客户端可能使用不同出口，这是上游原有行为。
- 银行、券商若手动选择自动测速组，仍可能自动换节点。配置不能保证机场节点可解锁 AI 服务，也不能改变 Google 账号地区限制。
- 本仓库配套规则是所标注上游版本的快照，后续上游修改需要同步到本仓库。blackmatrix7 的外部规则仍会独立更新；Google AI 新增域名需补充主配置。

## 检查

```bash
python scripts/verify_config.py --refresh
```

发布后可增加 `--published` 检查本仓库公开订阅和规则是否与本地文件一致。维护时可使用 `--baseline-ref lingjing/main` 对比原上游的普通 Google 与其他保留策略。

检查脚本验证规则格式、策略引用、规则集下载及代表性域名的首条匹配结果，不模拟 iOS 的实际 DNS、IP、协议、URL 或 User-Agent 匹配。最终节点连通性请在手机中检查。

## 文件与来源

- `Shadowrocket.conf`：当前主配置。
- `HB-Shadowrocket.conf`：与主配置内容相同的兼容订阅入口。
- `AI.list`、`Google.list`、`Mail.list`、`Apple.list`、`ApplePush.list`、`HSBC_HK.list`、`HK_Banks_Direct.list`、`HK_Broker.list`：来自上述上游版本。（共八个服务规则文件。）
- 规则来源：[LingJingMaster](https://github.com/LingJingMaster/Shadowrocket-Rules)、[blackmatrix7](https://github.com/blackmatrix7/ios_rule_script)。
- Google AI 域名参考：[v2fly google-deepmind](https://github.com/v2fly/domain-list-community/blob/master/data/google-deepmind)、[MetaCubeX google-gemini](https://github.com/MetaCubeX/meta-rules-dat/blob/meta/geo/geosite/google-gemini.list)。
- API 端点参考：[Google Code Assist](https://docs.cloud.google.com/gemini/docs/codeassist/set-up-gemini)、[Vertex AI 位置文档](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/learn/locations)。

## License

MIT，保留上游许可证。
