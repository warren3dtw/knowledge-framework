#!/usr/bin/env python3
"""從全部的頁產生給 agent 讀的索引。只用標準庫。

用法：python scripts/wiki.py index（或 python scripts/build_index.py）

產生三個檔（都進 git，agent 不必執行程式也能直接讀）：
  index/OVERVIEW.md      有哪些主題、知識點、各有多少頁、怎麼查。agent 第一個讀這個
  index/catalog.jsonl    每頁一行：標題、摘要、知識點、編號、詞條、各語言關鍵字、原件位置、附帶檔路徑、可見度（share）。技能也在這裡
  index/points.json      每個知識點：各主題的入口檔、標題、摘要、各項目和它們的頁
  index/terms.json       每個詞條的各語言名稱、上下位、哪些頁提到它
"""
import json
import re
from collections import Counter, defaultdict

import core
from core import TYPES


def figure_text(rec):
    text = rec["sections"].get("圖上原文", "")
    lines = [re.sub(r"^[-*]\s*", "", l).strip() for l in text.splitlines()]
    return " / ".join(l for l in lines if l)[:400]


def entry(rec, records, colls=None):
    sid, locator = core.raw_of(rec, records)
    term_ids = [core.resolve(t, None, records) for t in rec.get("terms", [])]
    term_ids = [t for t in term_ids if t]
    keywords = []
    for aid in term_ids:
        keywords += core.term_names(records[aid])
    spec = TYPES[rec["type"]]
    af = core.attached_file(rec)
    item = {
        "id": rec["id"],
        "wiki": rec["wiki"],
        "type": rec["type"],
        "point": rec.get("point", ""),
        "item": rec.get("item", ""),
        "group": core.group_of_kind(rec.get("kind")) or "" if rec["type"] == "note" else "",
        "kind": rec.get("kind", ""),
        "title": rec.get("title", ""),
        "title_en": rec.get("title_en", ""),
        "summary": rec.get("summary", ""),
        "terms": [t.split(":", 1)[1] for t in term_ids],
        "keywords": list(dict.fromkeys(keywords + [spec["kinds"].get(rec.get("kind"), "")]))[:40],
        "raw": sid or "",
        "locator": locator,
        "region": rec.get("region", ""),
        "lang": rec.get("lang", []),
        "status": rec.get("status", ""),
        "share": core.share_of(rec, records, colls),
        "path": rec["rel"],
        "file": af.relative_to(core.ROOT).as_posix() if af else "",
    }
    for key in ("point", "item", "group"):
        if not item[key]:
            del item[key]
    if rec.get("origin"):
        item["origin"] = rec["origin"]
    for key in ("pair", "data", "from", "against", "see_also", "uses"):
        refs = [core.resolve(r, rec["wiki"], records) for r in rec.get(key, [])]
        if any(refs):
            item[key] = [r for r in refs if r]
    if rec["type"] == "data" and af and af.exists():
        rows = core.read_data(rec)
        item["columns"] = list(rows[0].keys()) if rows else []
        item["rows"] = len(rows)
        first = item["columns"][0] if item["columns"] else None
        if first:
            item["first_column_values"] = list(dict.fromkeys(r[first] for r in rows))[:40]
    if rec["type"] == "figure":
        for key in ("sheet", "detail_no", "scale", "revision", "issue_status"):
            if rec.get(key):
                item[key] = rec[key]
        item["figure_text"] = figure_text(rec)
    if rec.get("file") and rec["type"] == "note":
        item["file"] = rec["file"]
        item["language"] = rec.get("language", "")
        item["verified"] = rec.get("verified", "")
    if rec["type"] == "skill":
        for key in ("version", "description"):
            item[key] = rec.get(key, "")
        item["points"] = rec.get("points", [])
    if rec["type"] == "raw":
        for key in ("format", "url", "license", "project", "original"):
            if rec.get(key):
                item[key] = rec[key]
    return item


def make_index(records):
    live = {rid: r for rid, r in records.items() if "_load_error" not in r and r.get("type") in TYPES}
    colls = core.wikis()
    catalog = [entry(r, live, colls) for rid, r in sorted(live.items()) if r["type"] != "term"]

    mentioned = defaultdict(list)
    for item in catalog:
        for t in item["terms"]:
            mentioned[t].append(item["id"])
    children = defaultdict(list)
    for rid, r in live.items():
        if r["type"] != "term":
            continue
        for key in ("kind-of", "part-of"):
            for parent in r.get(key, []):
                children[parent].append((key, r["name"]))
    terms = {}
    for rid, r in sorted(live.items()):
        if r["type"] != "term":
            continue
        name = r["name"]
        terms[name] = {
            "zh": r.get("name_zh", ""), "en": r.get("name_en", ""), "ja": r.get("name_ja", ""),
            "aliases": r.get("aliases", []),
            "class": r.get("kind", ""), "domain": r.get("domain", ""),
            "definition": r["sections"].get("_lead", "").split("\n")[0],
            "kind_of": r.get("kind-of", []), "part_of": r.get("part-of", []),
            "narrower": sorted(n for _, n in children[name]),
            "pages": sorted(mentioned[name]),
            "status": r.get("status", ""),
        }

    entries = core.entries()
    points = {}
    for item in catalog:
        if "point" not in item:
            continue
        p = points.setdefault(item["point"], {"wikis": {}, "items": {}})
        p["items"].setdefault(item["item"], {})[item["type"]] = item["id"]
    for (wiki, point), e in entries.items():
        p = points.setdefault(point, {"wikis": {}, "items": {}})
        p["wikis"][wiki] = {"entry": e["rel"], "title": e["meta"].get("title", ""),
                            "summary": e["meta"].get("summary", "")}
    points = {k: {"wikis": v["wikis"], "items": dict(sorted(v["items"].items()))} for k, v in sorted(points.items())}

    media = SCHEMA_PAGES = core.SCHEMA["pages"]
    counts = Counter((i["wiki"], i["type"]) for i in catalog)
    pcount = Counter(w for (w, _p) in entries)
    lines = ["# 索引總覽", "",
             "由 `scripts/wiki.py index` 產生，不要手改。agent 先讀這一頁，再依需要讀 `points.json`、`catalog.jsonl`、`terms.json`。", "",
             "## 主題", "",
             "| 主題 | 種類 | 範圍 | 知識點 | 原件 | " + " | ".join(TYPES[t]["zh"] for t in media) + " |",
             "|---|---|---|---|---|" + "---|" * len(media)]
    for name, meta in core.wikis().items():
        kind = core.SCHEMA["wiki_kinds"].get(meta.get("kind", ""), meta.get("kind", ""))
        cells = [str(pcount[name]), str(counts[(name, "raw")])] + [str(counts[(name, t)]) for t in media]
        lines.append(f"| `{name}` | {kind} | {meta.get('summary', '')} | " + " | ".join(cells) + " |")
    lines += ["", "## 知識點", "",
              "每個知識點的入口是 `wikis/<主題>/note/<知識點>/NOTE.md`，列出全部的頁和閱讀順序。編號全部主題共用。", "",
              "| 知識點 | 主題 | 標題 | 摘要 | 項目數 |", "|---|---|---|---|---|"]
    for point, p in points.items():
        for wiki, w in p["wikis"].items():
            n = sum(1 for it, pages in p["items"].items() if any(pid.startswith(wiki + ":") for pid in pages.values()))
            lines.append(f"| `{point}` | `{wiki}` | [{w['title']}](../{w['entry']}) | {w['summary']} | {n} |")
    skills = [i for i in catalog if i["type"] == "skill"]
    lines += ["", "## 技能", "",
              "技能放在 `skills/<代號>/SKILL.md`，是 agent 可以照著做的能力包。points 是它用到的知識點。", "",
              "| 技能 | 版本 | 標題 | 用到的知識點 | 可見度 | 狀態 |", "|---|---|---|---|---|---|"]
    for i in skills:
        lines.append(f"| [`{i['id'].split(':', 1)[1]}`](../{i['path']}) | {i['version']} | {i['title']} | "
                     f"{'、'.join(i['points']) or '—'} | {i['share']} | {i['status']} |")
    if not skills:
        lines.append("| — | | 目前沒有技能 | | | |")
    lines.append("")
    by_class = Counter(t["class"] for t in terms.values())
    lines += ["", f"詞條（term）共 {len(terms)} 個：" + "、".join(
        f"{TYPES['term']['kinds'].get(k, k)} {n}" for k, n in sorted(by_class.items())), "",
        "## 怎麼查", "",
        "- 用程式：`python scripts/wiki.py query search <關鍵字>`、`query point <知識點>`，說明見 `USING.md`。",
        "- 不用程式：`catalog.jsonl` 每行是一頁的 JSON，有 title、summary、keywords（含中英日名稱）、path、file。",
        "  用關鍵字篩出幾行，再打開 path 讀說明、打開 file 讀數據、圖或程式。",
        "- 專案主題預設不查。問題提到專案時才查。",
        "- share 是可見度：public 可以公開、attribution 要標出處、private 不能拿出這個 repo。由原件的授權推算。",
        "- 同一個 item（知識點-編號）的頁是同一項，pair 欄位互相列出。",
        "- 每行的 status 不是 reviewed 的，還沒經過擁有者確認。origin 是 fileback 的，是查詢後回存的頁。", ""]
    catalog_text = "".join(json.dumps(i, ensure_ascii=False) + "\n" for i in catalog)
    terms_text = json.dumps(terms, ensure_ascii=False, indent=1) + "\n"
    points_text = json.dumps(points, ensure_ascii=False, indent=1) + "\n"
    return {"OVERVIEW.md": "\n".join(lines), "catalog.jsonl": catalog_text, "points.json": points_text,
            "terms.json": terms_text}


def main(argv=None):
    records = core.load_records()
    out = core.ROOT / "index"
    out.mkdir(exist_ok=True)
    made = make_index(records)
    for old in out.iterdir():
        if old.name not in made:
            old.unlink()
    for name, text in made.items():
        (out / name).write_text(text, encoding="utf-8")
    n_terms = sum(1 for r in records.values() if r.get("type") == "term")
    print(f"已產生索引：{len(records) - n_terms} 頁，{n_terms} 個詞條")


if __name__ == "__main__":
    main()
