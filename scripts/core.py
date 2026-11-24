"""知識庫的共用程式：讀 schema、解析檔頭、載入全部紀錄、解析代號。只用標準庫。

其他腳本都從這裡取資料，所以規則只寫在一個地方。

紀錄的代號（id）：
  詞條（term）  term:<名稱>                     例：term:clt
  主題裡的頁    <主題>:<類型>/<檔名>             例：project-demo:figure/panel-joint-001-demo-fj1-lap-joint
  技能          skill:<代號>                     例：skill:init-001（skills/init-001/SKILL.md）
  頁放在 <類型>/<知識點>/ 底下，但代號不含知識點資料夾（檔名本身已經以知識點開頭）。
同一個主題裡互相引用時，可以省略「<主題>:」，寫成 figure/panel-joint-001-demo-fj1-lap-joint。

檔名 = <知識點>-<三位數編號>-<描述>。「<知識點>-<編號>」叫做項目（item），編號全部主題共用一套，
同一項在筆記、資料、圖之間檔名完全相同；程式檔附在同名的筆記旁邊。
"""
import csv
import json
import os
import re
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = json.loads((ROOT / "schema.json").read_text(encoding="utf-8"))
TYPES = SCHEMA["types"]
DOCS = (ROOT / SCHEMA.get("docs", "docs")).resolve()  # 文件（設計、FEEDBACK、計畫）的位置，可以在知識庫外面
FOLDER_TO_TYPE = {spec["folder"]: name for name, spec in TYPES.items()}
LIST_FIELDS = {"terms", "from", "against", "data", "see_also", "pair", "aliases", "kind-of", "part-of", "lang",
               "points", "uses"}
SHARE_ORDER = list(SCHEMA["share"])[::-1]  # 由嚴到寬：private、attribution、public
SECTION_RE = re.compile(r"^## (.+?)\s*$", re.M)
CODE_FENCE = re.compile(r"```.*?```", re.S)
LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)\s]+)\)")


def parse_frontmatter(text):
    """回傳 (檔頭 dict, 內文)。只支援這個 repo 用到的寫法：key: 值、key: [a, b]、引號字串、# 註解。"""
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---", 4)
    if end == -1:
        return None, text
    fm = {}
    for line in text[4:end].splitlines():
        m = re.match(r"^([A-Za-z_][\w-]*):(.*)$", line)
        if not m:
            continue
        key, raw = m.group(1), m.group(2).strip()
        if raw.startswith('"'):
            close = raw.find('"', 1)
            value = raw[1:close] if close > 0 else raw[1:]
        else:
            value = re.sub(r"(^|\s+)#.*$", "", raw).strip()
        if key in LIST_FIELDS:
            inner = value.strip()
            if inner.startswith("[") and inner.endswith("]"):
                inner = inner[1:-1]
            fm[key] = [v.strip().strip("\"'") for v in inner.split(",") if v.strip()]
        else:
            fm[key] = value
    return fm, text[end + 4:].lstrip("\n")


def sections(body):
    """內文依「## 小節」切開。第一個小節之前的文字放在「摘要」。"""
    result, name, lines = {}, "_lead", []
    for line in body.splitlines():
        m = re.match(r"^## (.+?)\s*$", line)
        if m:
            result[name] = "\n".join(lines).strip()
            name, lines = m.group(1), []
        else:
            lines.append(line)
    result[name] = "\n".join(lines).strip()
    return {k: v for k, v in result.items() if v or k != "_lead"}


def wikis():
    """回傳 {主題名稱: 檔頭}。主題的檔頭寫在 wikis/<名稱>/WIKI.md。"""
    out = {}
    base = ROOT / "wikis"
    if not base.exists():
        return out
    for folder in sorted(p for p in base.iterdir() if p.is_dir()):
        meta_path = folder / "WIKI.md"
        meta = {}
        if meta_path.exists():
            meta, _ = parse_frontmatter(meta_path.read_text(encoding="utf-8"))
            meta = meta or {}
        meta["path"] = folder
        out[folder.name] = meta
    return out


def show_path(path):
    """給人看的路徑：知識庫裡的寫成相對於知識庫，外面的（例如文件區）寫成相對路徑。"""
    return Path(os.path.relpath(Path(path).resolve(), ROOT)).as_posix()


def record_id(path):
    rel = path.relative_to(ROOT).as_posix()
    if rel.startswith("terms/"):
        return f"term:{path.stem}"
    if rel.startswith(TYPES["skill"]["folder"] + "/"):
        return f"skill:{path.parent.name}"
    parts = rel.split("/")
    return f"{parts[1]}:{parts[2]}/{path.stem}"


ENTRY = SCHEMA["point"]["entry"]
ITEM_RE = re.compile(r"^(?P<point>[a-z0-9]+(?:-[a-z0-9]+)*?)-(?P<num>\d{%d})-(?P<desc>[a-z0-9]+(?:-[a-z0-9]+)*)$"
                     % SCHEMA["point"]["digits"])


def record_paths(base, spec):
    """一個主題裡某個類型的所有 .md。頁（筆記、資料、圖）放在知識點資料夾裡，往下一層找。"""
    folder = base / spec["folder"]
    if spec["folder"] in PAGE_FOLDERS:
        return sorted(p for p in folder.glob("*/*.md") if p.name != ENTRY)
    return sorted(folder.glob("*.md"))


PAGE_FOLDERS = {TYPES[t]["folder"] for t in SCHEMA["pages"]}


TERMS_DIR = ROOT / TYPES["term"]["folder"]
TERM_LISTS = ("aliases", "kind-of", "part-of")


def term_files():
    """詞條依領域分檔：terms/<領域>.csv，領域代號登記在 schema.json 的 types.term.domains。"""
    return sorted(TERMS_DIR.glob("*.csv")) if TERMS_DIR.exists() else []


def load_terms():
    """詞條（term）依領域寫在 terms/<領域>.csv，一列一個；檔名就是領域（domain）。
    清單欄位（別名、上位、整體）用全形分號「；」分隔。代號 term:<名稱> 全部領域共用一套，不可重複。"""
    out = {}
    for path in term_files():
        domain = path.stem
        rel_file = path.relative_to(ROOT).as_posix()
        with path.open(encoding="utf-8", newline="") as f:
            for n, row in enumerate(csv.DictReader(f), 2):
                name = (row.get("id") or "").strip()
                if not name:
                    continue
                rec = {k: (v or "").strip() for k, v in row.items()
                       if k != "id" and k not in TERM_LISTS and (v or "").strip()}
                for k in LIST_FIELDS:
                    rec.setdefault(k, [])
                for k in TERM_LISTS:
                    rec[k] = [x.strip() for x in (row.get(k) or "").split("；") if x.strip()]
                rid = f"term:{name}"
                rec.update(type="term", title=rec.get("name_zh", name), id=rid, path=path, domain=domain,
                           rel=f"{rel_file} 第 {n} 列（{name}）", body=rec.get("summary", ""),
                           wiki=None, folder="terms", point_folder=None, name=name,
                           sections=sections(rec.get("summary", "")))
                if rid in out:
                    rec["_duplicate"] = out[rid]["rel"]
                out[rid] = rec
    return out


def load_records():
    """載入全部的頁、詞條和原件登記卡。回傳 {代號: dict}。讀檔錯誤放在 record['_load_error']。

    同一個代號出現兩次（兩個知識點資料夾有同名檔）時，記在 record['_duplicate']。
    """
    records = {}
    records.update(load_terms())
    paths = []
    paths += sorted((ROOT / TYPES["skill"]["folder"]).glob(f"*/{TYPES['skill']['entry']}"))
    for name, meta in wikis().items():
        for tname, spec in TYPES.items():
            if not spec["shared"]:
                paths += record_paths(meta["path"], spec)
    for path in paths:
        text = path.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(text)
        rid = record_id(path)
        rec = dict(fm or {})
        is_page = path.parent.parent.name in PAGE_FOLDERS and path.parent.parent.parent.parent.name == "wikis"
        is_skill = rid.startswith("skill:")
        if is_skill:
            rec["declared_name"] = rec.get("name", "")
        rec.update(id=rid, path=path, rel=path.relative_to(ROOT).as_posix(), body=body,
                   wiki=None if rid.startswith(("term:", "skill:")) else rid.split(":", 1)[0],
                   folder=path.parent.parent.name if is_page else (
                       "terms" if rid.startswith("term:") else
                       TYPES["skill"]["folder"] if is_skill else path.parent.name),
                   point_folder=path.parent.name if is_page else None,
                   name=path.parent.name if is_skill else path.stem, sections=sections(body))
        if fm is None:
            rec["_load_error"] = "沒有檔頭（檔案要以 --- 開頭）"
        for key in LIST_FIELDS:
            rec.setdefault(key, [])
        if rid in records:
            rec["_duplicate"] = records[rid]["rel"]
        records[rid] = rec
    return records


def entries():
    """知識點的入口檔。回傳 {(主題, 知識點): {path, rel, meta, body}}。"""
    out = {}
    for name, meta in wikis().items():
        for path in sorted((meta["path"] / TYPES["note"]["folder"]).glob(f"*/{ENTRY}")):
            fm, body = parse_frontmatter(path.read_text(encoding="utf-8"))
            out[(name, path.parent.name)] = {"path": path, "rel": path.relative_to(ROOT).as_posix(),
                                             "meta": fm or {}, "body": body}
    return out


def split_item(name):
    """檔名拆成 (知識點, 編號, 描述)。不合格式回傳 None。"""
    m = ITEM_RE.match(name)
    return (m.group("point"), int(m.group("num")), m.group("desc")) if m else None


def next_item(point, records):
    """這個知識點的下一個編號（全部主題共用一套）。"""
    used = [int(r["item"].rsplit("-", 1)[1]) for r in records.values()
            if r.get("point") == point and re.fullmatch(r".+-\d+", r.get("item", ""))]
    return f"{point}-{(max(used) + 1 if used else 1):0{SCHEMA['point']['digits']}d}"


def group_of_kind(kind):
    """筆記的種類屬於原理、做法、觀點的哪一組。"""
    for group, spec in TYPES["note"]["kind_groups"].items():
        if kind in spec["kinds"]:
            return group
    return None


def resolve(ref, wiki, records):
    """把欄位裡寫的參照解析成代號。找不到回傳 None。

    可以寫 term:clt、clt（詞條）、timber:data/clt-kmod、data/clt-kmod（同主題）。
    """
    ref = ref.strip()
    if not ref:
        return None
    if ":" in ref:
        return ref if ref in records else None
    if "/" in ref and wiki:
        rid = f"{wiki}:{ref}"
        return rid if rid in records else None
    rid = f"term:{ref}"
    return rid if rid in records else None


def raw_of(rec, records):
    """解析 raw 欄位「原件代號, 位置」。回傳 (原件登記的代號或 None, 位置)。"""
    value = rec.get("raw", "")
    if not value:
        return None, ""
    head, _, locator = value.partition(",")
    head = head.strip()
    wiki = rec.get("wiki")
    rid = head if ":" in head else (f"{wiki}:raw/{head}" if wiki else None)
    return (rid if rid in records else None), locator.strip()


def term_names(rec):
    """一個詞條所有語言的名稱和別名。"""
    names = [rec.get("name_zh", ""), rec.get("name_en", ""), rec.get("name_ja", "")]
    names += rec.get("aliases", [])
    names.append(rec["name"])
    return [n for n in dict.fromkeys(n.strip() for n in names) if n]


def read_data(rec):
    """讀資料頁的 CSV。回傳列的 list（每列一個 dict）。"""
    csv_path = rec["path"].with_suffix(".csv")
    with csv_path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def attached_file(rec):
    """頁附帶的檔案：資料頁是同名 CSV，圖是影像，筆記是程式檔（有附的話）。其他類型回傳 None。"""
    t = rec.get("type")
    if t == "data":
        return rec["path"].with_suffix(".csv")
    field = TYPES.get(t, {}).get("data_field")
    if field and rec.get(field):
        return rec["path"].parent / rec[field]
    return None


def descendants(term_id, records):
    """一個詞條和它所有的下位詞條（kind-of、part-of 指向它的）。"""
    children = {}
    for rid, rec in records.items():
        if rec.get("type") != "term":
            continue
        for key in ("kind-of", "part-of"):
            for parent in rec.get(key, []):
                pid = resolve(parent, None, records)
                if pid:
                    children.setdefault(pid, set()).add(rid)
    seen, queue = {term_id}, [term_id]
    while queue:
        for child in children.get(queue.pop(), ()):
            if child not in seen:
                seen.add(child)
                queue.append(child)
    return seen


def stricter(a, b):
    """兩個 share 取比較嚴格的。"""
    return a if SHARE_ORDER.index(a) <= SHARE_ORDER.index(b) else b


def computed_share(rec, records, wikis_meta=None, _seen=None):
    """推算一筆紀錄可不可以公開（不看它自己標的 share）。

    原件：自己標的 share，沒標當成 private。詞條：public（只是名稱），組織與專案類的詞條 private。
    專案主題的頁：private。其他頁和技能：raw 原件、from 依據、uses 技能裡最嚴格的。
    都沒有時：頁是 private；技能是 public（自己寫的技能，以它自己標的 share 為準）。
    """
    wikis_meta = wikis_meta if wikis_meta is not None else wikis()
    t = rec.get("type")
    if t == "raw":
        return rec.get("share") if rec.get("share") in SCHEMA["share"] else "private"
    if t == "term":
        return "private" if rec.get("kind") == "organization" else "public"
    if rec.get("wiki") and wikis_meta.get(rec["wiki"], {}).get("kind") == "project":
        return "private"
    _seen = set() if _seen is None else _seen
    if rec["id"] in _seen:
        return "public"
    _seen.add(rec["id"])
    found, result = False, "public"
    sid, _ = raw_of(rec, records)
    if sid:
        found, result = True, stricter(result, computed_share(records[sid], records, wikis_meta, _seen))
    for key in ("from", "uses"):
        for ref in rec.get(key, []):
            target = resolve(ref, rec.get("wiki"), records)
            if target:
                found = True
                result = stricter(result, share_of(records[target], records, wikis_meta, _seen))
    return result if found else ("public" if t == "skill" else "private")


def share_of(rec, records, wikis_meta=None, _seen=None):
    """一筆紀錄實際的可見度：推算結果和它自己標的 share 取比較嚴格的。"""
    base = computed_share(rec, records, wikis_meta, _seen)
    own = rec.get("share")
    return stricter(base, own) if own in SCHEMA["share"] and rec.get("type") != "raw" else base
