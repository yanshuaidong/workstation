"""
国内期货主力合约实时快照
数据源：新浪财经期货实时行情（futures_zh_spot + match_main_contract）
每次运行覆盖同目录下的 futures_snapshot.json
"""

import akshare as ak
import json
import os
from datetime import datetime
import pandas as pd


def _to_num(val):
    try:
        v = float(val)
        return None if pd.isna(v) else round(v, 6)
    except (TypeError, ValueError):
        return None


def _to_int(val):
    try:
        v = float(val)
        return None if pd.isna(v) else int(v)
    except (TypeError, ValueError):
        return None


def get_futures_snapshot() -> dict:
    now = datetime.now()

    # ── 步骤 1：获取各交易所主力合约订阅字符串 ────────────────────────────
    print("  [1/3] 获取主力合约代码...")
    exchange_texts = {}
    for exch in ("dce", "czce", "shfe", "gfex", "ine"):
        try:
            exchange_texts[exch] = ak.match_main_contract(symbol=exch)
            count = len([x for x in exchange_texts[exch].split(",") if x.strip()])
            print(f"         {exch.upper():5s}: {count} 个合约")
        except Exception as e:
            print(f"  [警告] {exch} 主力合约获取失败: {e}")
            exchange_texts[exch] = ""

    try:
        cffex_text = ak.match_main_contract(symbol="cffex")
        count = len([x for x in cffex_text.split(",") if x.strip()])
        print(f"         CFFEX: {count} 个合约")
    except Exception as e:
        print(f"  [警告] cffex 主力合约获取失败: {e}")
        cffex_text = ""

    # ── 步骤 2：获取商品期货实时行情 ──────────────────────────────────────
    print("  [2/3] 拉取实时行情...")
    cf_symbol = ",".join(v for v in exchange_texts.values() if v)

    cf_df = pd.DataFrame()
    if cf_symbol:
        try:
            cf_df = ak.futures_zh_spot(symbol=cf_symbol, market="CF", adjust="0")
            print(f"         商品期货: {len(cf_df)} 条")
        except Exception as e:
            print(f"  [警告] 商品期货行情获取失败: {e}")

    ff_df = pd.DataFrame()
    if cffex_text:
        try:
            ff_df = ak.futures_zh_spot(symbol=cffex_text, market="FF", adjust="0")
            print(f"         金融期货: {len(ff_df)} 条")
        except Exception as e:
            print(f"  [警告] 金融期货行情获取失败: {e}")

    # ── 步骤 3：整合数据 ──────────────────────────────────────────────────
    print("  [3/3] 整合数据...")
    all_df = pd.concat([cf_df, ff_df], ignore_index=True) if not (cf_df.empty and ff_df.empty) else pd.DataFrame()

    results = []
    if not all_df.empty:
        for _, row in all_df.iterrows():
            record = {
                "合约名称": str(row.get("symbol", "")).strip(),
                "当前价": _to_num(row.get("current_price")),
                "最高价": _to_num(row.get("high")),
                "最低价": _to_num(row.get("low")),
            }
            results.append(record)

    return {
        "抓取时间": now.isoformat(timespec="seconds"),
        "主力合约数量": len(results),
        "数据来源": "新浪财经期货实时行情（futures_zh_spot + match_main_contract）",
        "主力合约列表": results,
    }


if __name__ == "__main__":
    print("正在获取国内期货主力合约实时数据...\n")
    data = get_futures_snapshot()

    output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "futures_snapshot.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n✓ 数据已保存 → {output_file}")
    print(f"  抓取时间    : {data['抓取时间']}")
    print(f"  主力合约数量 : {data['主力合约数量']} 个")

    items = data["主力合约列表"]
    if items:
        print("\n前 10 条数据预览:")
        fmt = "  {:<12} {:>10} {:>10} {:>10}"
        print(fmt.format("合约名称", "当前价", "最高价", "最低价"))
        print("  " + "-" * 46)
        for item in items[:10]:
            print(fmt.format(
                item.get("合约名称", "")[:10],
                str(item.get("当前价", "-")),
                str(item.get("最高价", "-")),
                str(item.get("最低价", "-")),
            ))
