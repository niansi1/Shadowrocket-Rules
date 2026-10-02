# Shadowrocket Rules

个人 Shadowrocket 配置，接续 [hanboyd/Shadowrocket-Rules](https://github.com/hanboyd/Shadowrocket-Rules)，原始配置基于 [LingJingMaster/Shadowrocket-Rules](https://github.com/LingJingMaster/Shadowrocket-Rules)。

## 订阅地址

```
https://raw.githubusercontent.com/niansi1/Shadowrocket-Rules/main/HB-Shadowrocket.conf
```

这是**规则配置订阅**，不包含代理节点。手机导入步骤：

1. 在 Shadowrocket 的「配置」页添加配置，粘贴上面的地址下载，然后选中启用 `HB-Shadowrocket.conf`。
2. 在「首页」添加自己的机场节点订阅，并将「全局路由」设为「配置」。
3. 在代理分组中将 `🤖 AI 服务` 选为 `🇺🇸 美国手选`，再进入美国手选组选择一个可用的美国节点。旧配置可能保留之前的组选择，请手动确认一次。
4. `🔍 谷歌服务` 默认仍为 `🇯🇵 日本节点`；已有手动选择可以继续保留。
5. 后续在「配置」页更新这份远程配置即可获取修改；配置中的 `update-url` 已指向本仓库。若原来订阅的是 hanboyd 仓库，首次需要重新添加本地址。

如果「美国手选」为空，先检查节点名称是否带有 `美国`、`US`、`USA`、`🇺🇸` 等地区标识，或在 AI 服务中选择 `PROXY` 并在首页指定一个可用节点。手选避免测速自动换节点，但机场节点的出口 IP 仍可能变化。

## Google AI 分流

Google AI 专用域名内联在主配置中，优先于宽泛 Google 规则匹配，随配置一起更新。

| 流量 | 策略 |
|---|---|
| Gemini 网页、手机端、Gemini API、AI Studio | 🤖 AI 服务 |
| NotebookLM 页面与后端 | 🤖 AI 服务 |
| Code Assist、Android Studio AI、Antigravity | 🤖 AI 服务 |
| Labs、Flow、Jules、Opal、Stitch、DeepMind | 🤖 AI 服务 |
| Vertex AI 全球及各区域 API（`*-aiplatform.googleapis.com`） | 🤖 AI 服务 |
| Google 搜索、Gmail、Drive、地图、Google Voice | 🔍 谷歌服务（原策略，默认日本） |
| Google 登录与共享资源，如 accounts、apis、普通 gstatic、googleusercontent、storage.googleapis.com | 🔍 谷歌服务（原策略） |

Google AI 域名参考 [v2fly google-deepmind](https://github.com/v2fly/domain-list-community/blob/master/data/google-deepmind)，并与 [MetaCubeX google-gemini](https://github.com/MetaCubeX/meta-rules-dat/blob/meta/geo/geosite/google-gemini.list) 交叉核对。Code Assist 与 Vertex AI 端点另参考 [Google Code Assist 文档](https://docs.cloud.google.com/gemini/docs/codeassist/set-up-gemini)及 [Vertex AI 位置文档](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/learn/locations)。

## 本次修正（2026-10-02）

- 补齐 Gemini 手机端、NotebookLM 后端、Code Assist 等原先会落入普通 Google 组的 AI 接口。
- 将 NotebookLM、Labs 的宽泛关键词改成明确域名后缀，避免相似域名误入 AI 组。
- 将 `voice.telephony.goog` 恢复普通 Google 分流；它属于 Google Voice。
- 增加美国手选组供 AI 默认使用，修复外层 `select` 仍嵌套 `url-test`、会自动切换节点的问题。美国自动测速组仍可主动选用。
- 订阅地址和配置自更新地址统一切换到 `niansi1/Shadowrocket-Rules`，补充手机导入与更新步骤。
- 修正文档中“所有银行/券商出口固定”及已不存在的 OpenAI 域名扩展说明。

## 主要调整

- **Google AI 与普通 Google 分离** — Google AI 专用域名优先走 🤖 AI 服务；普通 Google 保留原谷歌服务策略
- **其他 AI** — 继续引用上游 AI.list，覆盖 ChatGPT、Claude、Copilot、Grok 等；规则内容会随上游更新
- **AI 手动选择节点** — 默认美国手选组；银行/券商保留原策略，选择香港测速组时仍可能自动换节点
- **美国节点正则修复** — 移除过于宽泛的裸 `美` 字匹配
- **移除无必要内容** — 删除 Google Rewrite / MITM、T-Mobile Wi-Fi Calling 规则
- **大陆流量强制直连** — 同时引用 `ChinaMax_Domain.list` 域名集和 `ChinaMax.list` IP/其他规则，国内域名与中国大陆 IP 命中后直接使用 `DIRECT`，不经过可记忆选择的策略组
- **国内 HTTPDNS 直连** — 微信、京东、阿里、哔哩哔哩、美团、网易、百度等国内应用的 HTTPDNS 入口直接放行，避免拒绝后等待超时和二次解析
- **分流 DNS** — 直连与待判定域名使用 AliDNS / DNSPod 国内 DoH，失败时回退系统 DNS；代理域名由代理服务器端解析
- **启用 IPv6、优先 IPv4** — 保留双栈网络能力，减少开启 Shadowrocket 后与系统原生网络路径的差异，同时避免强制优先 IPv6
- **保留** — Tailscale TUN 排除、Apple 直连、Blackmatrix7 公共规则集

## 规则引用

本配置引用的外部规则集：

| 来源 | 用途 |
|---|---|
| [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script) | YouTube、Telegram、GitHub、Microsoft、ChinaMax 等公共规则 |
| [LingJingMaster/Shadowrocket-Rules](https://github.com/LingJingMaster/Shadowrocket-Rules) | Google、其他 AI、Apple、HSBC、银行、券商规则 |

## 使用边界与检查

- 按域名分流无法区分同一主机下的不同 HTTPS 路径。例如搜索页内的 AI 功能如果仍访问 `www.google.com`，会保留普通 Google 出口；共用登录与静态资源也不会整体切到 AI 出口。本配置不启用 MITM 解密。
- 外部规则集会独立更新。保留原 Google / YouTube 规则顺序，因此 `googlevideo.com`、`youtubei.googleapis.com` 等仍可能先命中 Google 组；Google 翻译两个显式例外也继续走油管组。
- 本次未调整国内直连、DNS、IPv6、Apple、银行、券商等原有分流。银行/券商若需要稳定节点，需另行手选实际节点；自动测速组不能保证出口稳定。
- 域名覆盖核对日期为 2026-10-02。服务新增专用域名后，需要补充规则并更新手机配置。配置不保证节点本身能解锁服务，也无法改变 Google 账号地区限制。

仓库提供规则检查脚本，展开当前外部规则并按顺序验证代表性域名：

```bash
python scripts/verify_config.py --refresh
```

它检查订阅规则可下载、策略引用及域名分流回归，不等同于 iPhone 真机测试；IP、进程、User-Agent 等匹配仍应以 Shadowrocket 连接日志为准。

## 测试文件

- `HB-Shadowrocket.conf` — 当前唯一维护的手机订阅入口
- `Shadowrocket-original.conf` — 历史上游原版配置（A/B 对照用）
- `Shadowrocket-v1~v4.conf` — 历史二分定位版本，内部更新地址可能已失效；不要作为当前订阅使用

## 上游项目

- [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script)
- [LingJingMaster/Shadowrocket-Rules](https://github.com/LingJingMaster/Shadowrocket-Rules)

## 最后更新

2026-10-02
