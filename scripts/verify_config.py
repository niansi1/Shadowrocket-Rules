#!/usr/bin/env python3
"""Static Shadowrocket checks and first-match domain routing regressions.

Run with --refresh to check external lists, or reuse .git/rule-audit.
Repository lists are read locally; --published checks the uploaded copies too.
This does not emulate iOS, DNS, IP/GeoIP, protocol, URL or User-Agent matching.
"""

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from fnmatch import fnmatchcase
import hashlib
from http.client import HTTPException
import ipaddress
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.request import Request, urlopen
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
CONFIG = "Shadowrocket.conf"
ALIAS = "HB-Shadowrocket.conf"
OWN_URL = "https://raw.githubusercontent.com/niansi1/Shadowrocket-Rules/main/"
SOURCE_URLS = ("https://raw.githubusercontent.com/LingJingMaster/Shadowrocket-Rules/refs/heads/main/",
               "https://raw.githubusercontent.com/LingJingMaster/Shadowrocket-Rules/main/")
AI, GOOGLE, YOUTUBE = "🤖 AI 服务", "🔍 谷歌服务", "📹 油管视频"
DOMESTIC, MAIL, DNS_BLOCK = "🔒 国内服务", "📧 邮件服务", "🧱 DNS 防泄露"
BUILTINS = {"DIRECT", "PROXY", "REJECT"}
DOMAIN_TYPES = {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD", "DOMAIN-WILDCARD"}
OTHER_TYPES = {"IP-CIDR", "IP-CIDR6", "IP-ASN", "GEOIP", "USER-AGENT", "URL-REGEX", "AND"}
REMOTE_TYPES = {"RULE-SET", "DOMAIN-SET"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def lines(text):
    for number, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if line and not line.startswith(("#", ";")):
            yield number, line


def fields(line):
    """Split top-level commas, keeping logical rules and regex groups intact."""
    result, start, depth = [], 0, 0
    for index, char in enumerate(line):
        if char == "(" and (not index or line[index - 1] != "\\"):
            depth += 1
        elif char == ")" and (not index or line[index - 1] != "\\"):
            depth -= 1
        elif char == "," and depth == 0:
            result.append(line[start:index].strip())
            start = index + 1
    require(depth == 0, f"Unbalanced parentheses: {line}")
    result.append(line[start:].strip())
    return result


@dataclass(frozen=True)
class Rule:
    kind: str
    value: str
    policy: str
    source: str


def parse_rule(line, source, policy=None):
    parts = fields(line)
    kind = parts[0]
    require(kind in DOMAIN_TYPES | OTHER_TYPES | REMOTE_TYPES | {"FINAL"},
            f"{source}: unsupported rule type {kind}")
    if kind == "FINAL":
        require(policy is None and len(parts) == 2, f"{source}: invalid FINAL")
        return Rule(kind, "", parts[1], source)
    minimum = 3 if policy is None else 2
    require(len(parts) >= minimum and parts[1], f"{source}: incomplete rule")
    value = parts[1]
    target = parts[2] if policy is None else policy
    options = parts[minimum:]
    require(all(option == "no-resolve" for option in options),
            f"{source}: unsupported trailing fields: {options}")
    if kind in DOMAIN_TYPES:
        require(not re.search(r"[\s,/]", value), f"{source}: invalid domain value {value}")
        require(kind == "DOMAIN-WILDCARD" or "*" not in value, f"{source}: unexpected wildcard")
    elif kind in {"IP-CIDR", "IP-CIDR6"}:
        ipaddress.ip_network(value, strict=False)
    elif kind == "IP-ASN":
        require(value.isdigit(), f"{source}: invalid ASN {value}")
    elif kind == "GEOIP":
        require(re.fullmatch(r"[A-Z]{2}", value), f"{source}: invalid country code")
    elif kind == "URL-REGEX":
        re.compile(value)
    elif kind in REMOTE_TYPES:
        require(value.startswith("https://"), f"{source}: remote URL must use HTTPS")
    return Rule(kind, value, target, source)


def parse_config(text):
    section, sections, rules = None, {}, []
    for number, line in lines(text):
        source = f"{CONFIG}:{number}"
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1]
            require(section not in sections, f"{source}: duplicate section")
            sections[section] = {}
        elif section == "Rule":
            rules.append(parse_rule(line, source))
        elif section == "URL Rewrite":
            parts = line.split()
            require(len(parts) == 3 and parts[2] in {"301", "302", "307", "308"},
                    f"{source}: unsupported URL rewrite")
            re.compile(parts[0])
            require(parts[0] not in sections[section], f"{source}: duplicate rewrite")
            sections[section][parts[0]] = parts[1:]
        else:
            require(section is not None and "=" in line, f"{source}: expected key = value")
            key, value = (part.strip() for part in line.split("=", 1))
            require(key not in sections[section], f"{source}: duplicate key {key}")
            sections[section][key] = value
    require({"General", "Proxy", "Proxy Group", "Rule", "Host"} <= sections.keys(),
            "Missing required configuration section")
    groups = {}
    for name, value in sections["Proxy Group"].items():
        parts = fields(value)
        require(parts[0] in {"select", "url-test", "fallback", "load-balance", "random"},
                f"{name}: unsupported group type {parts[0]}")
        members, options = [], {}
        for part in parts[1:]:
            if "=" in part:
                key, option = part.split("=", 1)
                require(key not in options, f"{name}: duplicate group option {key}")
                options[key] = option
            else:
                members.append(part)
        require(members or options.get("policy-regex-filter"), f"{name}: empty group")
        if "policy-regex-filter" in options:
            re.compile(options["policy-regex-filter"])
        default = options.get("policy-select-name")
        if default:
            require(default in members, f"{name}: default {default} is not a member")
        if "select" in options:
            require(options["select"].isdigit(), f"{name}: invalid default index")
            if not options.get("policy-regex-filter"):
                require(int(options["select"]) < len(members), f"{name}: default index out of range")
        groups[name] = (parts[0], members, options)
    policies = BUILTINS | groups.keys() | sections["Proxy"].keys()
    for name, (_, members, _) in groups.items():
        for member in members:
            require(member in policies, f"{name}: undefined policy {member}")
    for rule in rules:
        require(rule.policy in policies, f"{rule.source}: undefined policy {rule.policy}")
    require(rules and rules[-1].kind == "FINAL", "FINAL must be the last rule")
    require(sum(rule.kind == "FINAL" for rule in rules) == 1, "Expected one FINAL rule")

    def visit(name, chain):
        require(name not in chain, f"Policy group cycle: {' -> '.join(chain + [name])}")
        for member in groups[name][1]:
            if member in groups:
                visit(member, chain + [name])

    for name in groups:
        visit(name, [])
    return sections, groups, rules


def normalized(content):
    return content.decode("utf-8-sig").replace("\r\n", "\n")


def own_url(url):
    for prefix in SOURCE_URLS:
        if url.startswith(prefix):
            return OWN_URL + url[len(prefix):]
    return url


def local_list(url):
    if not url.startswith(OWN_URL):
        return None
    path = (ROOT / unquote(url[len(OWN_URL):])).resolve()
    require(path.is_relative_to(ROOT) and path.suffix == ".list", f"Unsafe repository list URL: {url}")
    return path


def download(url):
    request = Request(url, headers={"User-Agent": "Shadowrocket-Rules-static-check/1.0"})
    for attempt in range(3):
        try:
            with urlopen(request, timeout=40) as response:
                return normalized(response.read())
        except (OSError, HTTPException) as error:
            if attempt == 2:
                raise OSError(f"Download failed for {url}: {error}") from error


def load_lists(rules, refresh, cache, published):
    urls = sorted({rule.value for rule in rules if rule.kind in REMOTE_TYPES})
    index_path = cache / "index.json"
    previous = json.loads(index_path.read_text(encoding="utf-8-sig")) if index_path.exists() else []
    previous_paths = {entry["url"]: ROOT / entry["path"].replace("\\", "/") for entry in previous}

    def fetch(url):
        local = local_list(url)
        if local:
            content = normalized(local.read_bytes())
            require(any(lines(content)), f"Empty repository list: {local}")
            if published:
                require(download(url) == content, f"Published list differs from local file: {url}")
            return url, content, local, "published" if published else "local"
        path = previous_paths.get(url, cache / (hashlib.sha256(url.encode()).hexdigest() + ".list"))
        cached = path.exists() and not refresh
        if cached:
            content = path.read_text(encoding="utf-8-sig")
        else:
            content = download(url)
            require(any(lines(content)), f"Empty remote list: {url}")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        require(any(lines(content)), f"Empty rule list: {url}")
        return url, content, path, "cached" if cached else "downloaded"

    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(fetch, urls))
    cache.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps([
        {"url": url, "path": str(path), "rules": sum(1 for _ in lines(content))}
        for url, content, path, mode in results if mode in {"cached", "downloaded"}
    ], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    counts = Counter(mode for _, _, _, mode in results)
    print("Rule lists: " + ", ".join(f"{count} {mode}" for mode, count in sorted(counts.items())) + ".")
    if counts["cached"]:
        print("Cached files do not prove current remote availability.")
    return {url: content for url, content, _, _ in results}


def expand(rules, contents):
    expanded = []
    for rule in rules:
        if rule.kind not in REMOTE_TYPES:
            expanded.append(rule)
            continue
        for number, line in lines(contents[rule.value]):
            source = f"{rule.value}:{number}"
            if rule.kind == "DOMAIN-SET":
                # A leading dot denotes this domain and its subdomains.
                kind = "DOMAIN-SUFFIX" if line.startswith(".") else "DOMAIN"
                entry = parse_rule(f"{kind},{line.lstrip('.')}", source, rule.policy)
            else:
                entry = parse_rule(line, source, rule.policy)
            require(entry.kind not in REMOTE_TYPES, f"{source}: nested remote lists are unsupported")
            expanded.append(entry)
    return expanded


def match(domain, rules):
    domain = domain.lower().rstrip(".")
    for rule in rules:
        value = rule.value.lower()
        if (rule.kind == "FINAL"
                or rule.kind == "DOMAIN" and domain == value
                or rule.kind == "DOMAIN-SUFFIX" and (domain == value or domain.endswith("." + value))
                or rule.kind == "DOMAIN-KEYWORD" and value in domain
                or rule.kind == "DOMAIN-WILDCARD" and fnmatchcase(domain, value)):
            return rule
    raise ValueError(f"No domain/final match for {domain}")


# Representative browser, mobile, streaming, developer and shared-service cases.
# These are deliberate expectations, not generated from the configuration itself.
AI_CASES = """
gemini.google.com gemini.google gemini.gstatic.com robinfrontend-pa.googleapis.com
geminiweb-pa.clients6.google.com
geller-pa.googleapis.com aistudio.google.com webchannel-alkalimakersuite-pa.clients6.google.com
generativelanguage.googleapis.com notebooklm.google notebooklm.google.com
notebooklm-pa.googleapis.com labstailwind.pa.googleapis.com
jules.google.com labs.google flow.google.com opal.google stitch.withgoogle.com
cloudaicompanion.googleapis.com cloudcode-pa.googleapis.com aicode.googleapis.com
antigravity.google antigravity-pa.googleapis.com deepmind.google
aiplatform.googleapis.com us-central1-aiplatform.googleapis.com europe-west4-aiplatform.googleapis.com
asia-northeast1-aiplatform.googleapis.com
""".split()
GOOGLE_CASES = """
www.google.com www.google.com.hk accounts.google.com mail.google.com gmail.com
drive.google.com docs.google.com maps.google.com photos.google.com
www.gstatic.com fonts.googleapis.com storage.googleapis.com oauth2.googleapis.com
www.googleapis.com apis.google.com lh3.googleusercontent.com
""".split()
TRANSLATE_CASES = ["translate.googleapis.com", "translate-pa.googleapis.com"]
DOMESTIC_CASES = """
www.baidu.com www.bilibili.com doubao.com www.jd.com deepseek.com deepseeksvc.com
dns.weixin.qq.com dns.weixin.qq.com.cn weixin.com
""".split()
MAIL_CASES = """
imap.gmail.com smtp.gmail.com pop.gmail.com outlook.office365.com p14-imap.mail.me.com
""".split()
NEGATIVE_CASES = """
notebooklm.google.example.com labs.google.example.org example-labs.google.com
notgemini.google.com gemini.gstatic.com.example.org notebooklm-pa.googleapis.com.example.org
aiplatform.googleapis.com.example.org us-central1-aiplatform.googleapis.com.example.org
""".split()


PRESERVED_CASES = [(domain, GOOGLE) for domain in GOOGLE_CASES + ["voice.google.com", "voice.telephony.goog"]]
PRESERVED_CASES += [(domain, YOUTUBE) for domain in TRANSLATE_CASES]
PRESERVED_CASES += [(domain, DOMESTIC) for domain in DOMESTIC_CASES]
PRESERVED_CASES += [(domain, MAIL) for domain in MAIL_CASES]
PRESERVED_CASES += [(domain, DNS_BLOCK) for domain in ["dns.jd.com", "httpdns.alicdn.com"]]
PRESERVED_CASES += [(domain, AI) for domain in ["chatgpt.com", "claude.ai", "guzzoni.apple.com", "mask.icloud.com", "apps.mzstatic.com"]]
PRESERVED_CASES += [("localhost.weixin.qq.com", "DIRECT"), ("www.apple.com", "🍏 苹果服务"),
                    ("www.hsbc.com.hk", "🏦 汇丰香港"), ("www.bochk.com", "🏦 香港银行"),
                    ("www.futuhk.com", "📈 券商服务")]
# Preserve existing YouTube/Google overlap rather than silently changing exits.
PRESERVED_CASES += [("www.youtube.com", YOUTUBE), ("rr1---sn.example.googlevideo.com", GOOGLE), ("youtubei.googleapis.com", GOOGLE)]


def check_routes(rules):
    cases = [(domain, AI) for domain in AI_CASES] + PRESERVED_CASES
    failures = []
    for domain, expected in cases:
        found = match(domain, rules)
        if found.policy != expected:
            failures.append(f"{domain}: expected {expected}, got {found.policy} ({found.source})")
    for domain in NEGATIVE_CASES:
        found = match(domain, rules)
        if found.policy == AI:
            failures.append(f"{domain}: lookalike/shared endpoint incorrectly matched AI ({found.source})")
    require(not failures, "Routing regression(s):\n  " + "\n  ".join(failures))
    print(f"Domain routing: {len(cases) + len(NEGATIVE_CASES)} representative cases passed.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="download all external lists; repository lists stay local before publishing")
    parser.add_argument("--published", action="store_true", help="also fetch published configs and repository lists and compare them with local files")
    parser.add_argument("--baseline-ref", help="compare preserved settings, lists and routes with an upstream Git revision, e.g. lingjing/main")
    parser.add_argument("--config", type=Path, default=ROOT / CONFIG)
    parser.add_argument("--cache-dir", type=Path, default=ROOT / ".git" / "rule-audit")
    args = parser.parse_args()
    require(args.config.read_bytes() == (ROOT / ALIAS).read_bytes(), "Canonical config and HB compatibility alias differ")
    sections, groups, rules = parse_config(args.config.read_text(encoding="utf-8-sig"))
    require(sections["General"].get("update-url") == OWN_URL + CONFIG,
            "update-url must point to the maintained niansi1 repository")
    ai_group = groups[AI]
    ai_default = ai_group[2].get("policy-select-name", ai_group[1][0])
    require(ai_group[0] == "select" and ai_default in groups, "AI must default to a manual node group")
    manual = groups[ai_default]
    require(manual[0] == "select" and manual[2].get("policy-regex-filter") and not manual[1],
            "AI's default must select individual filtered nodes, without an automatic child group")
    for name, expected in {GOOGLE: "🇯🇵 日本节点", MAIL: "PROXY", DNS_BLOCK: "REJECT",
                           DOMESTIC: "DIRECT", "🍏 苹果服务": "DIRECT", "🏦 汇丰香港": "DIRECT",
                           "🏦 香港银行": "DIRECT", "📈 券商服务": "🇭🇰 香港节点"}.items():
        _, members, options = groups[name]
        require(options.get("policy-select-name", members[0]) == expected, f"{name}: upstream default changed")
    for name in [ai_default, "🇺🇸 美国节点"]:
        pattern = groups[name][2]["policy-regex-filter"]
        require(re.search(pattern, "美国 01") and not re.search(pattern, "南美 智利 01"),
                f"{name}: US filter must not capture South America via bare 美")
    require(re.search(groups["🌐 其他节点"][2]["policy-regex-filter"], "南美 智利 01"),
            "Other-node filter must retain South American nodes")
    contents = load_lists(rules, args.refresh, args.cache_dir, args.published)
    if args.published:
        for filename in [CONFIG, ALIAS]:
            require(download(OWN_URL + filename) == normalized((ROOT / filename).read_bytes()),
                    f"Published config differs from local file: {filename}")
        print("Published canonical and compatibility configs match local files (normalized line endings).")
    expanded = expand(rules, contents)
    print(f"Structure: {len(groups)} policy groups and {len(expanded)} expanded rules checked.")
    skipped = Counter(rule.kind for rule in expanded if rule.kind in OTHER_TYPES)
    print("Limit: domain/final matching only; skipped " + ", ".join(f"{kind} ({count})" for kind, count in sorted(skipped.items())) + ".")
    check_routes(expanded)
    if args.baseline_ref:
        revision = subprocess.check_output(
            ["git", "rev-parse", "--verify", "--end-of-options", args.baseline_ref + "^{commit}"], cwd=ROOT, text=True).strip()
        baseline_text = subprocess.check_output(["git", "show", f"{revision}:{CONFIG}"], cwd=ROOT).decode("utf-8-sig")
        old_sections, old_groups, old_rules = parse_config(baseline_text)
        for section in old_sections.keys() - {"Rule", "Proxy Group"}:
            old = {key: value for key, value in old_sections[section].items() if key != "update-url"}
            new = {key: value for key, value in sections[section].items() if key != "update-url"}
            require(old == new, f"[{section}] changed beyond the update URL")
        for name in old_groups.keys() - {AI, "🇺🇸 美国节点", "🌐 其他节点"}:
            require(groups[name] == old_groups[name], f"{name}: group changed from upstream baseline")
        names = subprocess.check_output(["git", "ls-tree", "--name-only", revision], cwd=ROOT, text=True).splitlines()
        for name in (name for name in names if name.endswith(".list")):
            original = subprocess.check_output(["git", "show", f"{revision}:{name}"], cwd=ROOT)
            require(normalized((ROOT / name).read_bytes()) == normalized(original), f"Upstream rule copy changed: {name}")
        preserved = [(rule.kind, rule.value, rule.policy) for rule in rules
                     if not (rule.policy == AI and rule.kind in DOMAIN_TYPES)]
        original = [(rule.kind, own_url(rule.value), rule.policy) for rule in old_rules]
        require(preserved == original, "Existing rule order or policies changed from upstream")
        old_contents = {rule.value: contents[own_url(rule.value)] for rule in old_rules if rule.kind in REMOTE_TYPES}
        old_expanded = expand(old_rules, old_contents)
        for domain, _ in PRESERVED_CASES:
            require(match(domain, expanded).policy == match(domain, old_expanded).policy,
                    f"Ordinary route changed from baseline: {domain}")
        print(f"Baseline {args.baseline_ref}: original settings, rule order, copied lists, other groups and {len(PRESERVED_CASES)} service routes preserved.")
    print("PASS: static checks only; verify selected nodes and actual connections in Shadowrocket on iOS.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    try:
        main()
    except (OSError, ValueError, KeyError, re.error, subprocess.CalledProcessError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        sys.exit(1)
