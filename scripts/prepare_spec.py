"""どのレシピ(JSON)をビルドするか決めて build/spec.json に固定する。"""

import json
import os
import re
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
FENCE = re.compile(r"```(?:json)?\s*(.+?)```", re.S)

DEFAULTS = {
    "version": "1.0.0",
    "tagline": "Built on GitHub Actions",
    "accent": "#FF6B35",
    "second": "#FFB03A",
    "symbol": "paperplane.fill",
    "min_macos": "13.0",
}

FORBIDDEN = set('<>"\'/\\`\n\r\t$')


def die(msg):
    print(f"::error::{msg}")
    sys.exit(1)


def pick_from_issue(body):
    for block in FENCE.findall(body or ""):
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and "name" in data:
            return data
    die("Issue 本文に ```json ブロックが見つからないか、JSON が壊れています")


def pick_from_path(path):
    p = pathlib.Path(path)
    if not p.exists():
        die(f"レシピが見つかりません: {path}")
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        die(f"JSON が壊れています: {path} ({e})")


def main():
    event = os.environ.get("GITHUB_EVENT_NAME", "workflow_dispatch")

    if event == "issues":
        spec = pick_from_issue(os.environ.get("ISSUE_BODY"))
        source = f"Issue #{os.environ.get('GITHUB_EVENT_ISSUE_NUMBER', '?')}"
    elif event == "push":
        files = [f for f in os.environ.get("CHANGED_SPECS", "").split() if f]
        spec = pick_from_path(files[0] if files else "specs/hello.json")
        source = files[0] if files else "specs/hello.json"
    else:
        path = os.environ.get("INPUT_SPEC") or "specs/hello.json"
        spec = pick_from_path(path)
        source = path

    name = str(spec.get("name") or "My App").strip()
    if not name or len(name) > 40:
        die("name は 1〜40文字にしてください")
    if FORBIDDEN & set(name):
        die('name に < > " \' / \\ ` $ は使えません')

    merged = {**DEFAULTS, **{k: v for k, v in spec.items() if v not in (None, "")}}
    merged["name"] = name

    slug = re.sub(r"[^a-z0-9]+", "-", str(merged.get("bundle_id", "")).split(".")[-1].lower()).strip("-")
    if not slug:
        slug = "app"
    merged["slug"] = slug[:32]
    merged["struct"] = "".join(w.capitalize() for w in slug.split("-") if w) + "App"

    for key in ("accent", "second"):
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", str(merged[key])):
            die(f"{key} は #RRGGBB 形式で指定してください")
    if not re.fullmatch(r"\d+\.\d+(\.\d+)?", str(merged["version"])):
        die("version は 1.0 や 1.2.3 の形式にしてください")
    if not re.fullmatch(r"\d+\.\d+", str(merged["min_macos"])):
        die("min_macos は 13.0 の形式にしてください")

    build = ROOT / "build"
    build.mkdir(exist_ok=True)
    (build / "spec.json").write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")

    out = pathlib.Path(os.environ.get("GITHUB_OUTPUT", os.devnull))
    with out.open("a", encoding="utf-8") as fh:
        fh.write(f"spec=build/spec.json\nname={merged['name']}\n")
        fh.write(f"slug={merged['slug']}\nversion={merged['version']}\n")
        fh.write(f"source={source}\n")

    print(f"spec: {source} → build/spec.json ({merged['name']} v{merged['version']})")


if __name__ == "__main__":
    main()
