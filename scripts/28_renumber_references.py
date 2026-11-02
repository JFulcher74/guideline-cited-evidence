#!/usr/bin/env python3
"""Renumber superscript citations in order of first appearance and reorder the reference list.

Citations are Unicode superscripts (e.g. ¹, ⁴˒⁵, ⁶⁻⁹) from the Introduction onwards; author notes in
"> `[...]`" blockquotes are renumbered but do not set the order. Ranges of three or more consecutive numbers
are written with ⁻, others with ˒. The supplement is renumbered with the same map. Uncited references are
reported and kept at the end of the list.

Usage: python scripts/28_renumber_references.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "manuscript" / "draft_manuscript.md"
SUPP = ROOT / "manuscript" / "supplement.md"
SUP = "⁰¹²³⁴⁵⁶⁷⁸⁹"
PAT = re.compile(f"[{SUP}][{SUP}˒⁻]*")


def to_int(t: str) -> int:
    return int("".join(str(SUP.index(c)) for c in t))


def to_sup(n: int) -> str:
    return "".join(SUP[int(d)] for d in str(n))


def expand(tok: str) -> list:
    out = []
    for part in tok.split("˒"):
        if "⁻" in part:
            a, b = part.split("⁻")
            out += list(range(to_int(a), to_int(b) + 1))
        else:
            out.append(to_int(part))
    return out


def compress(nums) -> str:
    nums = sorted(set(nums))
    groups, i = [], 0
    while i < len(nums):
        j = i
        while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
            j += 1
        groups += [to_sup(nums[i]) + "⁻" + to_sup(nums[j])] if j - i >= 2 else [to_sup(n) for n in nums[i:j + 1]]
        i = j + 1
    return "˒".join(groups)


def main() -> None:
    s = MAIN.read_text()
    start, refs_at = s.index("## 1. Introduction"), s.index("## References")
    end_refs = s.index("\n## ", refs_at + 5)
    order = []
    for m in PAT.finditer(s[start:refs_at]):
        line_start = s.rfind("\n", 0, start + m.start()) + 1
        if s.startswith("> `", line_start):
            continue
        for n in expand(m.group()):
            if n not in order:
                order.append(n)
    rsec = s[refs_at:end_refs]
    entries = {int(m.group(1)): m.group(2) for m in re.finditer(r"^(\d+)\. (.*)$", rsec, re.M)}
    missing = [n for n in order if n not in entries]
    if missing:
        raise SystemExit(f"cited but not in the list: {missing}")
    uncited = [n for n in sorted(entries) if n not in order]
    final = order + uncited
    new = {old: i + 1 for i, old in enumerate(final)}
    sub = lambda text: PAT.sub(lambda m: compress(new[n] for n in expand(m.group())), text)
    header = rsec.split("\n")[0]
    listing = "\n".join(f"{new[o]}. {entries[o]}" for o in final)
    MAIN.write_text(sub(s[:refs_at]) + header + "\n\n" + listing + "\n" + s[end_refs:])
    SUPP.write_text(sub(SUPP.read_text()))
    print("old -> new:", {o: new[o] for o in final if o != new[o]})
    print("uncited:", uncited)


if __name__ == "__main__":
    main()
