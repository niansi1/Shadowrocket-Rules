# Shadowrocket Rules

个人 Shadowrocket 配置，基于 [LingJingMaster/Shadowrocket-Rules](https://github.com/LingJingMaster/Shadowrocket-Rules) 修改。

## 订阅地址

```
https://raw.githubusercontent.com/hanboyd/Shadowrocket-Rules/main/Shadowrocket.conf
```

## 主要调整

- **修复美国节点正则** — `US`/`USA` 加词边界，避免误匹配 `AUS` 等；移除过于宽泛的裸 `美` 字
- **AI / 银行 / 券商稳定出口** — 使用 `select` 手动选择，避免 `url-test` 自动切换 IP
- **Google AI 与普通 Google 分离** — Gemini、AI Studio、NotebookLM、DeepMind 等优先走 🤖 AI 服务（美国稳定节点），普通 Google 仍走日本节点
- **AI 规则扩展** — 补充 OpenAI 相关域名（oaistatsig、cdn.openaimerge、workos 等）
- **分流 DNS** — 国内直连走系统 DNS，代理流量走境外 DoH
- **移除无必要内容** — 删除 Google Rewrite / MITM、T-Mobile Wi-Fi Calling 规则
- **TUN 排除** — 保留 100.64.0.0/10，兼容 Tailscale 等 CGNAT 网络

## 目录结构

```
Shadowrocket.conf          # 主配置
rules/
├── AI.list                # AI 服务域名（OpenAI / Claude / Copilot / Grok / Perplexity 等）
├── HSBC.list              # 汇丰香港
├── Banking.list           # 其他香港银行（渣打、中银、恒生、虚拟银行等）
└── Broker.list            # 券商服务（富途、老虎、长桥、雪盈、盈透、Schwab）
```

## 上游项目

- [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script) — 公共规则集（Google、YouTube、Telegram、GitHub 等）
- [LingJingMaster/Shadowrocket-Rules](https://github.com/LingJingMaster/Shadowrocket-Rules) — Apple / ApplePush 规则

## 最后更新

2026-08-28
