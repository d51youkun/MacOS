"""レシピJSON → main.swift / Info.plist / meta.env を書き出す。"""

import json
import pathlib
import shlex
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TPL = ROOT / "templates"


def render(spec):
    sub = {
        "__APP_NAME__": spec["name"],
        "__STRUCT__": spec["struct"],
        "__TAGLINE__": spec["tagline"],
        "__ACCENT__": spec["accent"],
        "__SECOND__": spec["second"],
        "__SYMBOL__": spec["symbol"],
        "__VERSION__": spec["version"],
        "__MIN_MACOS__": spec["min_macos"],
        "__BUNDLE_ID__": spec["bundle_id"],
        "__EXEC__": spec["slug"],
    }
    out = {}
    for name, tpl in (("main.swift", "main.swift.tmpl"), ("Info.plist", "Info.plist.tmpl")):
        text = (TPL / tpl).read_text(encoding="utf-8")
        for key, val in sub.items():
            text = text.replace(key, str(val))
        out[name] = text
    return out


def main():
    spec_path = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "build/spec.json")
    dest = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else "build")
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    spec.setdefault("bundle_id", f"com.example.{spec['slug']}")
    dest.mkdir(parents=True, exist_ok=True)

    for name, text in render(spec).items():
        (dest / name).write_text(text, encoding="utf-8")

    env = {
        "APP_NAME": spec["name"],
        "SLUG": spec["slug"],
        "VERSION": spec["version"],
        "MIN_MACOS": spec["min_macos"],
    }
    (dest / "meta.env").write_text(
        "".join(f"{k}={shlex.quote(str(v))}\n" for k, v in env.items()), encoding="utf-8"
    )
    print(f"rendered → {dest}")


if __name__ == "__main__":
    main()
