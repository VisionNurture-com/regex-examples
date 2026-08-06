#!/usr/bin/env python3
"""測定結果に添える環境情報を集めて JSON で出す。

測定値だけを載せても、どの環境で測ったか分からなければ読者は再現できない。
このスクリプトの出力を、各測定結果の env フィールドに埋め込む。
"""

import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path

RESULTS_DIR = Path(__file__).parent / "results"


def cmd_version(args: list[str]) -> str | None:
    """コマンドの版を 1 行で取る。無ければ None を返す。"""
    if shutil.which(args[0]) is None:
        return None
    try:
        out = subprocess.run(args, capture_output=True, text=True, timeout=15)
    except (subprocess.TimeoutExpired, OSError):
        return None
    text = (out.stdout or out.stderr).strip()
    return text.splitlines()[0] if text else None


def collect() -> dict:
    return {
        "os": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "cpu": platform.processor() or platform.machine(),
        "runtimes": {
            "python": sys.version.split()[0],
            "node": cmd_version(["node", "--version"]),
            "go": cmd_version(["go", "version"]),
            "rustc": cmd_version(["rustc", "--version"]),
            "dotnet": cmd_version(["dotnet", "--version"]),
            # macOS の素の grep は環境によって別実装に差し替わっていることがあるため
            # 記事が対象とするシステム grep をフルパスで見る
            "grep": cmd_version(["/usr/bin/grep", "--version"]),
            "sed": cmd_version(["/usr/bin/sed", "--version"]),
            "pcre2grep": cmd_version(["pcre2grep", "--version"]),
        },
    }


def main() -> None:
    env = collect()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (RESULTS_DIR / "env.json").write_text(
        json.dumps(env, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(env, ensure_ascii=False, indent=2))
    print(f"\n書き出し: {RESULTS_DIR / 'env.json'}")


if __name__ == "__main__":
    main()
