#!/usr/bin/env python3
"""
每日打卡辅助脚本：
- 询问日期（默认今天），生成/更新对应的 YYYY_MM_DD.md
- 逐项输入 技术 / 健身 / 英语 细节，写入 markdown 引用行
- 可选自动 git add / commit / push
"""

from __future__ import annotations

import subprocess
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent

TEMPLATE_HEAD = "# {date_slash}\n\n"

TEMPLATE_BODY = (
    "## 技术\n\n"
    "> 细节：{tech}\n\n"
    "## 健身\n\n"
    "> 细节：{fit}\n\n"
    "## 英语\n\n"
    "> 细节：{eng}\n"
)


def prompt(msg: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    val = input(f"{msg}{suffix}: ").strip()
    return default if (default is not None and val == "") else val


def parse_date(text: str) -> date:
    return datetime.strptime(text, "%Y-%m-%d").date()


def load_existing_details(path: Path) -> dict[str, str]:
    """Very small parser to reuse已存在的细节内容（如果有）。"""
    if not path.exists():
        return {}
    lines = path.read_text(encoding="utf-8").splitlines()
    sections = {"## 技术": "tech", "## 健身": "fit", "## 英语": "eng"}
    current = None
    details: dict[str, str] = {}
    for line in lines:
        if line in sections:
            current = sections[line]
            continue
        if current and line.startswith(">"):
            details[current] = line.lstrip(">").strip().removeprefix("细节：").strip()
            current = None
    return details


def write_file(path: Path, d: date, tech: str, fit: str, eng: str) -> None:
    content = TEMPLATE_HEAD.format(date_slash=d.strftime("%Y/%m/%d"))
    content += TEMPLATE_BODY.format(tech=tech, fit=fit, eng=eng)
    path.write_text(content, encoding="utf-8")


def confirm(msg: str, default: bool = False) -> bool:
    suffix = " [Y/n]" if default else " [y/N]"
    val = input(f"{msg}{suffix} ").strip().lower()
    if not val:
        return default
    return val in {"y", "yes"}


def git(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)


def main() -> None:
    date_input = prompt("日期 (YYYY-MM-DD，留空为今天)", default=date.today().strftime("%Y-%m-%d"))
    try:
        d = parse_date(date_input)
    except ValueError:
        raise SystemExit("日期格式错误，应为 YYYY-MM-DD")

    fname = d.strftime("%Y_%m_%d.md")
    path = ROOT / fname

    existing = load_existing_details(path)

    tech = prompt("技术细节", default=existing.get("tech", ""))
    fit = prompt("健身细节", default=existing.get("fit", ""))
    eng = prompt("英语细节", default=existing.get("eng", ""))

    write_file(path, d, tech, fit, eng)
    print(f"已写入 {path.relative_to(ROOT)}")

    if not confirm("是否 git add / commit / push 提交到远程？"):
        return

    commit_msg = f"chore: daily log {d.strftime('%Y-%m-%d')}"
    add = git(["git", "add", fname])
    if add.returncode != 0:
        print(add.stderr or add.stdout)
        raise SystemExit(add.returncode)

    commit = git(["git", "commit", "-m", commit_msg])
    if commit.returncode != 0:
        # 可能是没有改动
        print(commit.stderr or commit.stdout)
        raise SystemExit(commit.returncode)
    print(commit.stdout.strip())

    push = git(["git", "push"])
    if push.returncode != 0:
        print(push.stderr or push.stdout)
        raise SystemExit(push.returncode)
    print(push.stdout.strip())


if __name__ == "__main__":
    main()

