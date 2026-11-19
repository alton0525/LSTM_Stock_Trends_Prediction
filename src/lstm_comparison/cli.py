"""Command-line entry points; help and validation use only the standard library."""

import argparse
import json
import sys

from .config import ConfigError, load_config


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="python -m lstm_comparison",
        description="LSTM 股票價格比較研究；目前提供設定檢查。",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    for name, description in (
        ("validate-config", "檢查 JSON 設定與解析資料路徑，不下載或訓練"),
        ("download", "下載行情快照（Commit 2 尚未實作）"),
        ("run", "執行模型比較（Commit 5 尚未實作）"),
    ):
        command = commands.add_parser(name, help=description, description=description)
        command.add_argument("--config", required=True, help="JSON 設定檔路徑")
    report = commands.add_parser(
        "report", help="產生研究報告（Commit 7 尚未實作）"
    )
    report.add_argument("--run-dir", required=True, help="實驗目錄")
    args = parser.parse_args(argv)

    if args.command == "validate-config":
        try:
            config = load_config(args.config)
        except ConfigError as error:
            print(f"設定錯誤：{error}", file=sys.stderr)
            return 2
        print("設定檢查通過；尚未下載資料或訓練模型。")
        print(json.dumps(config, ensure_ascii=False, indent=2))
        return 0

    commit = {"download": 2, "run": 5, "report": 7}[args.command]
    print(
        f"{args.command} 尚未實作；將於 Commit {commit} 提供，未執行任何研究工作。",
        file=sys.stderr,
    )
    return 1
