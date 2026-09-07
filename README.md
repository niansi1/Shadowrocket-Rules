# Shadowrocket Rules

个人 Shadowrocket 配置，基于 [LingJingMaster/Shadowrocket-Rules](https://github.com/LingJingMaster/Shadowrocket-Rules) 修改。

## 订阅地址

```
https://raw.githubusercontent.com/hanboyd/Shadowrocket-Rules/main/Shadowrocket.conf
```

## 主要调整

- **Google AI 与普通 Google 分离** — Gemini、AI Studio、NotebookLM、DeepMind 等优先走 🤖 AI 服务（美国稳定节点），普通 Google 仍走日本节点
- **AI 规则扩展** — 补充 OpenAI 相关域名（oaistatsig、cdn.openaimerge、workos 等）
- **AI / 银行 / 券商稳定出口** — 使用 `select` 手动选择，避免 `url-test` 自动切换 IP
- **美国节点正则修复** — 移除过于宽泛的裸 `美` 字匹配
- **移除无必要内容** — 删除 Google Rewrite / MITM、T-Mobile Wi-Fi Calling 规则
- **大陆直连规则扩充** — 使用 Blackmatrix7 `ChinaMax` 规则集，优先匹配更完整的中国大陆域名和 IP；境外流量仍进入代理规则
- **保留** — 分流 DNS、Tailscale TUN 排除、Apple 直连、Blackmatrix7 公共规则集

## 规则引用

本配置引用的外部规则集：

| 来源 | 用途 |
|---|---|
| [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script) | Google、YouTube、Telegram、GitHub、Microsoft 等公共规则 |
| [LingJingMaster/Shadowrocket-Rules](https://github.com/LingJingMaster/Shadowrocket-Rules) | AI、Apple、HSBC、银行、券商规则 |

## 测试文件

- `Shadowrocket-original.conf` — 上游原版配置（A/B 对照用）
- `Shadowrocket-v1~v4.conf` — 二分法定位中间版本

## 上游项目

- [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script)
- [LingJingMaster/Shadowrocket-Rules](https://github.com/LingJingMaster/Shadowrocket-Rules)

## 最后更新

2026-09-07
