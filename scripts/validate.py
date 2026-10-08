#!/usr/bin/env python3
"""thinking-toolbox 结构验收脚本。

纯标准库零依赖。校验 12 项结构约束，是本技能唯一的验收入口。
用法：
    python3 scripts/validate.py                 # 全量
    python3 scripts/validate.py --only fm-name section-balance
    python3 scripts/validate.py --verbose

退出码：0=无 FAIL（WARN 仍算通过）/ 1=有 FAIL / 2=用法错误
刻意不提供 --fix：批量内容改动须显式执行并用 git diff 审计，否则"改了什么"不可见。
"""

import argparse
import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SUBSKILLS = BASE / "subskills"
MAIN_SKILL = BASE / "SKILL.md"
SEEDS_JSON = BASE / "references" / "seeds.json"

FIVE_SECTIONS = ["核心思想", "分析步骤", "关键问题清单", "输出要求", "何时不适用"]
EXTRA_SECTIONS_OK = {"深入读取", "Reference Index", "参考索引"}

# 各段条目数合理区间（下限, 上限）。0 表示不限制。
SECTION_RANGE = {
    "核心思想": (4, 6),
    "分析步骤": (5, 7),
    "关键问题清单": (5, 8),
    "输出要求": (3, 5),
    # 分工句写在「何时不适用」段，随分工对数增长，上限放宽到 8
    "何时不适用": (3, 8),
}

FILLER_WORDS = [
    "多角度", "本质上是", "综合来看", "这个很重要", "首先要意识到",
    "众所周知", "不言而喻", "显而易见", "总的来说",
]

results = []  # (status, check_id, message)


def record(status, check_id, message=""):
    results.append((status, check_id, message))


def read(path):
    return path.read_text(encoding="utf-8")


def parse_frontmatter(text):
    """最小 frontmatter 解析：取顶层标量键与折叠块原始行。不依赖 PyYAML。"""
    if not text.startswith("---"):
        return {}, ""
    end = text.find("\n---", 3)
    if end == -1:
        return {}, ""
    block = text[3:end]
    fm, desc_lines = {}, []
    current = None
    for line in block.splitlines():
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if m:
            current = m.group(1)
            fm[current] = m.group(2).strip()
        elif current:
            desc_lines.append(line.strip())
    return fm, " ".join(desc_lines).strip()


def subskill_dirs():
    if not SUBSKILLS.is_dir():
        return []
    return sorted(d for d in SUBSKILLS.iterdir() if d.is_dir())


def parse_sections(text):
    """返回 [(标题, 正文)]，只取 ## 级。"""
    parts, cur, buf = [], None, []
    for line in text.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            if cur is not None:
                parts.append((cur, "\n".join(buf)))
            cur, buf = m.group(1).strip(), []
        elif cur is not None:
            buf.append(line)
    if cur is not None:
        parts.append((cur, "\n".join(buf)))
    return parts


def bullet_count(body):
    """统计条目数：`- ` 无序项与 `1. ` 有序项都算。"""
    return len([ln for ln in body.splitlines()
                if re.match(r"^\s*(?:[-*]\s+\S|\d+[.)]\s+\S)", ln)])


_ZH_CACHE = None


def _zh_name_map():
    """{目录名: 中文名}，从各文件的一级标题取。"""
    global _ZH_CACHE
    if _ZH_CACHE is None:
        m = {}
        for d in subskill_dirs():
            f = d / "SKILL.md"
            if f.is_file():
                mm = re.search(r"^#\s+(.+?)\s*$", read(f), re.M)
                if mm:
                    m[d.name] = mm.group(1).strip()
        _ZH_CACHE = m
    return _ZH_CACHE


# ---------- 检查项 ----------

def check_dir_table():
    """subskills/ 目录名集合 == 主 SKILL.md 路由表首列集合（双向差集）。"""
    if not MAIN_SKILL.is_file():
        return record("FAIL", "dir-table", "SKILL.md 不存在")
    text = read(MAIN_SKILL)
    m = re.search(r"^##\s*8\.\s*subskill\s*路由表", text, re.M)
    if not m:
        return record("FAIL", "dir-table", "未找到 §8 路由表小节")
    listed = set()
    for line in text[m.end():].splitlines():
        mm = re.match(r"^\|\s*([a-z][a-z-]+)\s*\|", line)
        if mm:
            listed.add(mm.group(1))
    actual = {d.name for d in subskill_dirs()}
    for extra in sorted(listed - actual):
        record("FAIL", "dir-table", f"路由表列了 {extra}，但 subskills/{extra}/ 不存在")
    for missing in sorted(actual - listed):
        record("FAIL", "dir-table", f"subskills/{missing}/ 未出现在 §8 路由表")
    if listed == actual and actual:
        record("PASS", "dir-table", f"{len(actual)} 目录 ↔ 路由表完全一致")


def check_fm_name():
    """每个 subskill 的 frontmatter name == 目录名；主文件 name == thinking-toolbox。"""
    if MAIN_SKILL.is_file():
        fm, _ = parse_frontmatter(read(MAIN_SKILL))
        if fm.get("name") != "thinking-toolbox":
            record("FAIL", "fm-name", f"SKILL.md name={fm.get('name')!r}，应为 thinking-toolbox")
    bad = 0
    for d in subskill_dirs():
        f = d / "SKILL.md"
        if not f.is_file():
            record("FAIL", "fm-name", f"{d.name}/SKILL.md 不存在")
            bad += 1
            continue
        fm, _ = parse_frontmatter(read(f))
        if fm.get("name") != d.name:
            record("FAIL", "fm-name", f"{d.name}: name={fm.get('name')!r} ≠ 目录名")
            bad += 1
    if not bad:
        n = len(subskill_dirs())
        record("PASS", "fm-name", f"{n}/{n}")


def check_fm_keys():
    """主文件须含 name/description/agent_created/license/version；subskill 须含 name/description。"""
    if MAIN_SKILL.is_file():
        fm, _ = parse_frontmatter(read(MAIN_SKILL))
        for key in ("name", "description", "agent_created", "license", "version"):
            if key not in fm or not fm[key]:
                record("FAIL", "fm-keys", f"SKILL.md 缺少 frontmatter 字段 {key}")
    for d in subskill_dirs():
        f = d / "SKILL.md"
        if not f.is_file():
            continue
        fm, _ = parse_frontmatter(read(f))
        for key in ("name", "description"):
            if key not in fm or not fm[key]:
                record("FAIL", "fm-keys", f"{d.name}: 缺少 {key}")
    if not any(r[1] == "fm-keys" for r in results):
        record("PASS", "fm-keys", "主文件 5 键齐全，subskill 2 键齐全")


def check_fm_desc():
    """description 非空、含排除边界、长度达标。"""
    for d in subskill_dirs():
        f = d / "SKILL.md"
        if not f.is_file():
            continue
        fm, desc = parse_frontmatter(read(f))
        if not desc:
            record("FAIL", "fm-desc", f"{d.name}: description 为空")
            continue
        if not re.search(r"不适用于|不用于|不适合", desc):
            record("FAIL", "fm-desc", f"{d.name}: description 缺少排除边界（不适用于…）")
        if len(desc) < 60:
            record("WARN", "fm-desc", f"{d.name}: description 仅 {len(desc)} 字，偏短")


def check_five_sections():
    """五段齐备且顺序正确；允许额外存在 深入读取 / Reference Index。"""
    for d in subskill_dirs():
        f = d / "SKILL.md"
        if not f.is_file():
            continue
        titles = [t for t, _ in parse_sections(read(f))]
        core = [t for t in titles if t not in EXTRA_SECTIONS_OK]
        if core != FIVE_SECTIONS:
            record("FAIL", "five-sections",
                   f"{d.name}: 段标题 {core}（应为 {FIVE_SECTIONS}）")


def check_section_balance():
    """逐文件逐段核对条目数区间——不排序去重，能发现个别文件失衡。"""
    warns = 0
    for d in subskill_dirs():
        f = d / "SKILL.md"
        if not f.is_file():
            continue
        for title, body in parse_sections(read(f)):
            rng = SECTION_RANGE.get(title)
            if not rng:
                continue
            n = bullet_count(body)
            lo, hi = rng
            if n < lo or n > hi:
                record("WARN", "section-balance",
                       f"{d.name}: {title} {n} 条（建议 {lo}~{hi}）")
                warns += 1
    if not warns:
        record("PASS", "section-balance", "各文件各段条目数均在区间内")


def check_length_limit():
    """输出要求段须同时含 限长 / ≤300 / ≤150。"""
    for d in subskill_dirs():
        f = d / "SKILL.md"
        if not f.is_file():
            continue
        for title, body in parse_sections(read(f)):
            if title != "输出要求":
                continue
            if "限长" not in body:
                record("FAIL", "length-limit", f"{d.name}: 输出要求段缺「限长」字段")
            elif "≤300" not in body:
                record("FAIL", "length-limit", f"{d.name}: 缺 ≤300 默认限长")
            elif "≤150" not in body:
                record("FAIL", "length-limit", f"{d.name}: 缺 ≤150 全部模式限长")


def check_division_symmetry():
    """收集「与 X 的分工」对：覆盖率 <90% 报 WARN，任何单向对报 FAIL。

    分工句写在「何时不适用」段（也可能在 frontmatter description），
    因此扫描全文而非只扫 description。
    """
    declared = {}  # model -> set(peer)
    for d in subskill_dirs():
        f = d / "SKILL.md"
        if not f.is_file():
            continue
        text = read(f)
        # 只认中文名的分工句：与XX的分工 / 与XX思维的分工
        cn_names = _zh_name_map()
        peers = set()
        # 允许"概率思维（贝叶斯）"这类带括号注释的名字：先剥掉括号再匹配
        for frag in re.findall(r"与([一-鿿（()]+?)的分工", text):
            core = re.sub(r"[（(].*?[)）]", "", frag)
            for name, zname in cn_names.items():
                z_core = re.sub(r"[（(].*?[)）]", "", zname)
                # 精确匹配，或括号剥除后匹配，或一方是另一方的前缀（"概率思维" ⊂ "概率思维（贝叶斯)"）
                if (zname == frag or z_core == core
                        or zname.startswith(frag) or frag.startswith(z_core)):
                    peers.add(name)
        declared[d.name] = peers

    covered = {m for m, ps in declared.items() if ps}
    n = len(declared)
    if n == 0:
        return
    # 单向对：A 声明了 B，B 没声明 A
    for model, peers in sorted(declared.items()):
        for peer in sorted(peers):
            if peer in declared and model not in declared[peer]:
                record("FAIL", "division-symmetry",
                       f"{model} 声明与 {peer} 分工，但 {peer} 未反向声明")
    pct = 100 * len(covered) / n
    if pct < 90:
        missing = sorted(set(declared) - covered)
        record("WARN", "division-symmetry",
               f"覆盖率 {pct:.0f}%（{len(covered)}/{n}），缺：{', '.join(missing)}")
    else:
        record("PASS", "division-symmetry", f"覆盖率 {pct:.0f}%（{len(covered)}/{n}），无单向对")


def check_refs_route():
    """SKILL.md 引用的 references/*.md 必须存在；存在的 reference 必须被提及（无孤儿）。"""
    for d in subskill_dirs():
        f = d / "SKILL.md"
        if not f.is_file():
            continue
        text = read(f)
        mentioned = set(re.findall(r"references/([A-Za-z0-9._-]+\.md)", text))
        refdir = d / "references"
        existing = {p.name for p in refdir.glob("*.md")} if refdir.is_dir() else set()
        for name in sorted(mentioned - existing):
            record("FAIL", "refs-route", f"{d.name} 提及 references/{name}，但文件不存在")
        for name in sorted(existing - mentioned):
            record("FAIL", "refs-route", f"{d.name}/references/{name} 未被 SKILL.md 提及（孤儿）")


def check_refs_size():
    """reference 行数应在 40~250；低于下限疑似占位，高于上限建议拆分。"""
    for d in subskill_dirs():
        refdir = d / "references"
        if not refdir.is_dir():
            continue
        for p in sorted(refdir.glob("*.md")):
            n = len(read(p).splitlines())
            if n < 40:
                record("WARN", "refs-size", f"{p.relative_to(BASE)} 仅 {n} 行，疑似占位")
            elif n > 250:
                record("WARN", "refs-size", f"{p.relative_to(BASE)} {n} 行，建议拆分")


def check_seeds():
    """按 references/seeds.json 的字面锚点逐条 grep。"""
    if not SEEDS_JSON.is_file():
        record("WARN", "seeds", "references/seeds.json 不存在，跳过")
        return
    seeds = json.loads(read(SEEDS_JSON))
    fails = 0
    for name, items in seeds.items():
        if name.startswith("_"):  # 注释键，不是模型
            continue
        d = SUBSKILLS / name
        if not d.is_dir():
            record("FAIL", "seeds", f"seeds.json 列了 {name}，但目录不存在")
            fails += 1
            continue
        blob = "\n".join(read(p) for p in sorted(d.rglob("*.md")))
        for anchor in items:
            if anchor not in blob:
                record("FAIL", "seeds", f"{name}: 缺失种子「{anchor}」")
                fails += 1
    if not fails:
        real = [k for k in seeds if not k.startswith("_")]
        record("PASS", "seeds", f"{len(real)} 个模型的种子锚点全部命中")


def check_no_filler():
    """核心思想段命中套话词表 → WARN。"""
    hits = 0
    for d in subskill_dirs():
        f = d / "SKILL.md"
        if not f.is_file():
            continue
        for title, body in parse_sections(read(f)):
            if title != "核心思想":
                continue
            for word in FILLER_WORDS:
                if word in body:
                    record("WARN", "no-filler", f"{d.name}: 核心思想含套话词「{word}」")
                    hits += 1
    if not hits:
        record("PASS", "no-filler", "未检出套话词")


CHECKS = [
    ("dir-table", check_dir_table),
    ("fm-name", check_fm_name),
    ("fm-keys", check_fm_keys),
    ("fm-desc", check_fm_desc),
    ("five-sections", check_five_sections),
    ("section-balance", check_section_balance),
    ("length-limit", check_length_limit),
    ("division-symmetry", check_division_symmetry),
    ("refs-route", check_refs_route),
    ("refs-size", check_refs_size),
    ("seeds", check_seeds),
    ("no-filler", check_no_filler),
]


def main():
    ap = argparse.ArgumentParser(description="thinking-toolbox 结构验收")
    ap.add_argument("--only", nargs="+", action="extend", metavar="ID",
                    help="只跑指定检查，可重复：--only fm-name --only seeds")
    ap.add_argument("--verbose", action="store_true", help="打印全部明细（含 PASS）")
    args = ap.parse_args()

    selected = CHECKS
    if args.only:
        wanted = set(args.only)
        unknown = wanted - {cid for cid, _ in CHECKS}
        if unknown:
            print(f"未知检查项：{', '.join(sorted(unknown))}", file=sys.stderr)
            print(f"可用：{', '.join(cid for cid, _ in CHECKS)}", file=sys.stderr)
            return 2
        selected = [(cid, fn) for cid, fn in CHECKS if cid in wanted]

    for _, fn in selected:
        fn()

    n_dir = len(subskill_dirs())
    print(f"thinking-toolbox validate · {n_dir} subskills\n")
    for status, cid, msg in results:
        if status == "PASS":
            print(f"PASS {cid:<20} {msg}")
        elif status == "WARN":
            print(f"WARN {cid:<20} {msg}")
        else:
            print(f"FAIL {cid:<20} {msg}")
    if args.verbose:
        print()
        for status, cid, msg in results:
            print(f"  [{status}] {cid}: {msg}")

    n_fail = sum(1 for s, _, _ in results if s == "FAIL")
    n_warn = sum(1 for s, _, _ in results if s == "WARN")
    print(f"\n总计：{len(selected)} 项检查 · {n_fail} FAIL · {n_warn} WARN")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())