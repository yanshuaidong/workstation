"""
assistant 辅助决策模块接口
包含：信号、策略建议、持仓、资金曲线、市场上下文
"""

from __future__ import annotations

import json
import logging
import re
from datetime import date, datetime, timedelta

import pymysql
from flask import Blueprint, current_app, jsonify, request


assistant_bp = Blueprint("assistant", __name__)
logger = logging.getLogger(__name__)

INITIAL_CAPITAL = 30000.0
LEVERAGE = 10.0
MAX_HOLD_DAYS = 5
ACCOUNT_TYPES = ("mechanical", "llm")
STRENGTH_LEVELS = (
    (1.0, "极强"),
    (0.75, "强"),
    (0.4, "中"),
    (0.0, "弱"),
)
INDICATOR_META = {
    "MF_Edge3": {
        "label": "主力三连变起点",
        "short_desc": "主力连续三日同向变化的起始位置",
        "calc_explanation": "检查主力值是否连续 3 日同向变化，并结合起点所在区域判断这次趋势从哪里启动。",
        "default_risk": "这个指标更适合看趋势启动位置，单独使用时过滤力度有限。",
    },
    "MF_Accel": {
        "label": "趋势加速度",
        "short_desc": "第二步变化是否比第一步更猛",
        "calc_explanation": "比较连续两步主力变化幅度，若第二步变化幅度更大则视为加速，否则视为减速。",
        "default_risk": "更适合作为辅助过滤条件，不建议只凭加速或减速单独下结论。",
    },
    "MF_Duration": {
        "label": "趋势持续天数",
        "short_desc": "主力同向趋势已经持续了几天",
        "calc_explanation": "统计主力连续同向变化天数，在恰好达到 D3、D5、D7 时各触发一次。",
        "default_risk": "持续时间越长不等于越安全，后段信号也可能意味着趋势已接近尾声。",
    },
    "MS_Divergence": {
        "label": "主散背离强度",
        "short_desc": "主力与散户是否出现反向共振",
        "calc_explanation": "当主力连续走强而散户走弱，或主力连续走弱而散户走强时，按背离强度给出共振分档。",
        "default_risk": "背离更适合作为过滤器使用，仍需结合价格和趋势环境判断。",
    },
    "MF_Magnitude": {
        "label": "主力变化幅度",
        "short_desc": "连续三日主力总变化有多大",
        "calc_explanation": "统计主力三日总变化幅度，并按近 3 个月滚动分位划分为高、中、低幅度。",
        "default_risk": "幅度大说明主力动作明显，但不代表价格一定立刻延续。",
    },
    "MF_BreakZone": {
        "label": "区域突破信号",
        "short_desc": "是否从极端区域穿越关键边界",
        "calc_explanation": "观察主力是否从极端区域向外穿越关键边界，区分边界突破、区内震荡和普通区间趋势。",
        "default_risk": "不同方向可靠性不完全对称，尤其偏空时更需要结合其他指标确认。",
    },
    "Composite_Score": {
        "label": "综合评分",
        "short_desc": "多项条件加权后的总分",
        "calc_explanation": "将持续天数、加速度、边缘区启动、主散背离和幅度强度等维度做加权合成，得到综合评分。",
        "default_risk": "综合分便于快速排序，但不是未来收益承诺，仍需结合单项信号判断。",
    },
}

STRATEGY_META = {
    "1A": {
        "label_cn": "高幅度主散共振做多",
        "thesis": "想抓主力连续偏强、近三日动作较大，且散户反向配合时的偏多机会。",
    },
    "1B": {
        "label_cn": "高幅度主散共振做空",
        "thesis": "想抓主力连续偏弱、近三日动作较大，且散户反向配合时的偏空机会。",
    },
    "2A": {
        "label_cn": "D7 主散共振做空",
        "thesis": "想抓趋势后段里，主力与散户继续反向拉扯时的偏空延续机会。",
    },
    "2B": {
        "label_cn": "D7 主散共振做多",
        "thesis": "想抓趋势后段里，主力与散户继续反向拉扯时的偏多延续机会。",
    },
}


def _parse_date(value):
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        return datetime.strptime(value[:10], "%Y-%m-%d").date()
    return None


def _date_str(value):
    parsed = _parse_date(value)
    return parsed.isoformat() if parsed else None


def _parse_json(value):
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, (bytes, bytearray)):
        value = value.decode("utf-8")
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return {}
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return {"raw": value}
    return {"raw": value}


def _get_conn():
    return current_app.config["get_db_connection"]()


def _latest_table_date(cursor, table_name, column_name):
    cursor.execute(f"SELECT MAX({column_name}) AS latest_date FROM {table_name}")
    row = cursor.fetchone()
    return _date_str(row["latest_date"]) if row and row.get("latest_date") else None


def _success(data=None, message="获取成功"):
    return jsonify({"code": 0, "message": message, "data": data or {}})


def _error(message, code=1):
    return jsonify({"code": code, "message": message})


def _build_like_filter(field_name, value):
    return f"{field_name} LIKE %s", f"%{value.strip()}%"


def _format_strength_value(strength):
    if strength is None:
        return "--"
    return f"{float(strength):.2f}"


def _format_metric_value(value, digits=2):
    if value is None:
        return "--"
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def _format_metric_list(values, digits=2):
    if not values:
        return "[]"
    formatted = ", ".join(_format_metric_value(value, digits) for value in values)
    return f"[{formatted}]"


def _make_calc_section(title, items):
    return {"title": title, "items": [item for item in items if item]}


def _get_strength_level(strength):
    if strength is None:
        return "--"
    numeric = float(strength)
    for threshold, label in STRENGTH_LEVELS:
        if numeric >= threshold:
            return label
    return "弱"


def _build_strength_explanation(indicator, strength, level, indicator_value, extra_json):
    extra_json = extra_json or {}
    if strength is None:
        return "暂无强度分数，当前只能先看触发条件本身，不能把这条信号当作强弱排序依据。"
    if indicator == "MF_Edge3":
        quantiles = extra_json.get("window_quantiles") or {}
        return (
            f"当前 strength 字段记录的是起点值 start_val = {_format_strength_value(strength)}，不是统一的强弱分。"
            f"它要和近 3 个月滚动分位比较：p10 = {_format_metric_value(quantiles.get('p10'))}，"
            f"p50 = {_format_metric_value(quantiles.get('p50'))}。"
            "看的是启动位置相对深浅，不适合直接和别的指标或别的品种横向比较。"
        )
    if indicator == "MF_Accel":
        return (
            f"当前 strength 字段就是加速度 {_format_strength_value(strength)}，计算方式是 |delta2| - |delta1|。"
            "大于 0 表示第二步更猛，小于 0 表示第二步放缓；先和 0 比，再看同一指标自己的历史分布。"
        )
    if indicator == "MF_Duration":
        return (
            f"当前 strength 字段就是连续同向天数 {_format_strength_value(strength)}。"
            "它是阶段值，不是收益预测分；重点看现在处在 D3、D5 还是 D7。"
        )
    if indicator == "MS_Divergence":
        return (
            f"当前 strength 字段就是背离分 {_format_strength_value(strength)}，"
            "计算为 |主力平均变化| + |散户平均变化|。分数越大说明主散反向拉扯越明显，适合在同一指标内部做相对排序。"
        )
    if indicator == "MF_Magnitude":
        quantiles = extra_json.get("window_quantiles") or {}
        return (
            f"当前 strength 字段就是三日总变化幅度 {_format_strength_value(strength)}，"
            f"要和近 3 个月滚动 p25 = {_format_metric_value(quantiles.get('p25'))}、"
            f"p75 = {_format_metric_value(quantiles.get('p75'))} 对比。"
            "它衡量动作大小，适合和该品种自己的近期分布比较。"
        )
    if indicator == "MF_BreakZone":
        return (
            f"当前 strength 字段是离散档位 {_format_strength_value(strength)}：2 代表边界突破，1 代表极端区内震荡，0 代表普通区间趋势。"
            "这种值更适合按档位理解，不需要做精细数值比较。"
        )
    if indicator == "Composite_Score":
        return (
            f"当前 strength 字段就是综合得分 {_format_strength_value(strength)}，归类为“{level}”。"
            "它由持续天数、加速度、起点位置、主散背离、幅度强度五项加权而来，适合同一指标内部做排序，不直接等于未来收益率。"
        )
    return (
        f"当前强度分数为 {_format_strength_value(strength)}，归类为“{level}”。"
        "它表示这条信号在当前规则下的相对强弱，不直接等于未来收益率或胜率。"
    )


def _extract_numeric_suffix(text):
    if not text:
        return None
    match = re.search(r"([+-]?\d+(?:\.\d+)?)", str(text))
    return match.group(1) if match else None


def _to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _build_trigger_value_cn(indicator, raw_value):
    raw_value = str(raw_value or "").strip()
    numeric = _extract_numeric_suffix(raw_value)

    if indicator == "MF_Duration":
        if raw_value.startswith("D") and raw_value[1:].isdigit():
            return f"趋势持续 {raw_value[1:]} 天"
        return raw_value or "持续天数未提供"
    if indicator == "MS_Divergence":
        if "强共振" in raw_value:
            return f"主散强共振，背离分 {numeric}" if numeric else "主散强共振"
        if "弱共振" in raw_value:
            return f"主散弱共振，背离分 {numeric}" if numeric else "主散弱共振"
        return raw_value or "主散背离结果未提供"
    if indicator == "MF_Magnitude":
        if "高幅度" in raw_value:
            return f"高幅度动作，总变化 {numeric}" if numeric else "高幅度动作"
        if "中幅度" in raw_value:
            return f"中幅度动作，总变化 {numeric}" if numeric else "中幅度动作"
        if "低幅度" in raw_value:
            return f"低幅度动作，总变化 {numeric}" if numeric else "低幅度动作"
        return raw_value or "主力变化幅度未提供"
    return raw_value or "未提供"


def _build_trigger_meaning(indicator, direction, raw_value):
    side = "偏多" if direction == "LONG" else "偏空"
    raw_value = str(raw_value or "").strip()

    if indicator == "MF_Duration":
        if raw_value == "D7":
            return f"说明当前 {side}趋势已经走到后段，趋势完整，但也要防止后段拥挤。"
        if raw_value == "D5":
            return f"说明当前 {side}趋势处在延续段，方向一致性较好。"
        if raw_value == "D3":
            return f"说明当前 {side}趋势刚进入启动段，还在早期确认阶段。"
    if indicator == "MS_Divergence":
        if raw_value.startswith("强共振"):
            return "说明主散背离较强，主力与散户方向相反且拉扯明显。"
        if raw_value.startswith("弱共振"):
            return "说明主散背离已经出现，但强度还不算特别突出。"
    if indicator == "MF_Magnitude":
        if raw_value.startswith("高幅度"):
            return "说明主力近三日动作较大，这次信号不只是方向一致，资金动作也更明显。"
        if raw_value.startswith("中幅度"):
            return "说明主力动作中等，趋势有延续，但爆发力一般。"
        if raw_value.startswith("低幅度"):
            return "说明主力动作偏小，趋势虽成立，但力度一般。"

    meta = INDICATOR_META.get(indicator, {})
    return meta.get("short_desc", "表示当前规则条件已被触发。")


def _build_trigger_how_to_read(indicator):
    if indicator == "MF_Duration":
        return "持续天数是阶段信号，不是收益分。通常先区分 D3、D5、D7 所处阶段，再决定是跟随还是防拥挤。"
    if indicator == "MS_Divergence":
        return "背离分越大，说明主力和散户反向拉扯越明显。更适合同一指标内部比较，不建议拿去和别的指标硬比。"
    if indicator == "MF_Magnitude":
        return "幅度看的是动作大小，不是方向本身。最好和该品种自己的近期分布比较，而不是跨品种比较。"
    return "建议结合该指标自己的历史分布做相对判断。"


def _build_trigger_explanations(trigger_indicators, direction):
    explanations = []
    for indicator, raw_value in (trigger_indicators or {}).items():
        meta = INDICATOR_META.get(indicator, {})
        explanations.append(
            {
                "indicator": indicator,
                "label_cn": meta.get("label", indicator),
                "short_desc": meta.get("short_desc", "辅助判断当前信号的结构特征"),
                "value_raw": raw_value,
                "value_cn": _build_trigger_value_cn(indicator, raw_value),
                "meaning": _build_trigger_meaning(indicator, direction, raw_value),
                "how_to_read": _build_trigger_how_to_read(indicator),
            }
        )
    return explanations


def _build_operation_action(strategy, direction, composite_score):
    score = _to_float(composite_score) or 0.0

    if strategy in ("2A", "2B"):
        strong_label = "可继续关注做多" if direction == "LONG" else "可继续关注做空"
        normal_label = "可继续观察" if direction == "LONG" else "可继续观察"
        return {
            "label": strong_label if score >= 1.0 else normal_label,
            "reason": (
                "趋势已经进入后段，当前更适合顺着已形成方向继续跟踪，但不建议脱离风险控制去追高追空。"
                if score >= 1.0
                else "后段信号已经出现，但综合分不算特别高，更适合继续观察确认。"
            ),
        }

    preferred_label = "可关注偏多机会" if direction == "LONG" else "可关注偏空机会"
    fallback_label = "可继续观察"
    return {
        "label": preferred_label if score >= 0.8 else fallback_label,
        "reason": (
            "主力动作和主散背离同时成立，说明这条机会具备一定完整度，可以放进优先观察名单。"
            if score >= 0.8
            else "触发条件成立，但综合分不算靠前，更适合先观察再决定。"
        ),
    }


def _build_operation_score_explanation(composite_score):
    score = _to_float(composite_score) or 0.0
    if score >= 1.2:
        strength_tag = "较完整"
    elif score >= 1.0:
        strength_tag = "中等偏强"
    elif score >= 0.8:
        strength_tag = "可跟踪"
    else:
        strength_tag = "偏观察"

    return {
        "score_value": score,
        "score_text": f"综合分 {score:.2f}，当前属于“{strength_tag}”区间。",
        "usage_tip": "综合分主要用于同页排序，帮助你先看哪条规则更完整，不建议跨策略、跨指标把它当成统一胜率分。",
        "threshold_tip": "经验上可把 0.8 以上视为值得跟踪，1.0 左右视为相对更完整，但它仍是规则分，不是未来收益率。",
    }


def _build_operation_risk_note(strategy, direction):
    if strategy in ("2A", "2B"):
        return "这类 D7 信号属于趋势后段，越完整不等于越安全，仍要防止拥挤、衰减和尾段反转。"
    if direction == "LONG":
        return "这类做多候选依赖主力持续偏强与主散背离共振，若后续主力转弱，信号完整度会快速下降。"
    return "这类做空候选依赖主力持续偏弱与主散背离共振，若后续主力回升，信号完整度会快速下降。"


def _build_operation_summary(strategy_meta, trigger_explanations, action_advice):
    trigger_text = "，".join(item["value_cn"] for item in trigger_explanations[:2])
    thesis = strategy_meta.get("thesis", "")
    return f"{trigger_text}。{thesis}{action_advice['reason']}"


def _build_operation_explanation(strategy, direction, trigger_indicators, composite_score):
    strategy_meta = {
        "code": strategy,
        **STRATEGY_META.get(
            strategy,
            {
                "label_cn": strategy,
                "thesis": "当前策略的业务意图尚未补充。",
            },
        ),
    }
    trigger_explanations = _build_trigger_explanations(trigger_indicators, direction)
    action_advice = _build_operation_action(strategy, direction, composite_score)
    score_explanation = _build_operation_score_explanation(composite_score)
    return {
        "strategy_meta": strategy_meta,
        "action_advice": action_advice,
        "trigger_explanations": trigger_explanations,
        "score_explanation": score_explanation,
        "risk_note": _build_operation_risk_note(strategy, direction),
        "summary": _build_operation_summary(strategy_meta, trigger_explanations, action_advice),
    }


def _build_indicator_display_value(indicator, indicator_value):
    raw_value = (indicator_value or "").strip()
    if not raw_value:
        fallback_map = {
            "MF_BreakZone": "未提供分档，需结合主力区域位置判断",
            "Composite_Score": "暂无综合分展示",
        }
        return fallback_map.get(indicator, "暂无触发值说明")

    if indicator == "Composite_Score":
        return f"综合得分 {raw_value}"
    if indicator == "MF_Accel":
        number = _extract_numeric_suffix(raw_value)
        if "加速" in raw_value:
            return f"加速型（加速度 {number}）" if number else "加速型"
        if "减速" in raw_value:
            return f"减速型（加速度 {number}）" if number else "减速型"
    if indicator == "MS_Divergence":
        number = _extract_numeric_suffix(raw_value)
        if "强共振" in raw_value:
            return f"强共振（背离分 {number}）" if number else "强共振"
        if "弱共振" in raw_value:
            return f"弱共振（背离分 {number}）" if number else "弱共振"
    if indicator == "MF_Magnitude":
        number = _extract_numeric_suffix(raw_value)
        if any(keyword in raw_value for keyword in ("高幅度", "中幅度", "低幅度")):
            label = raw_value.split("(")[0]
            return f"{label}（总变化 {number}）" if number else label
    if indicator == "MF_Duration":
        return f"趋势持续 {raw_value[1:]} 天" if raw_value.startswith("D") else raw_value
    return raw_value


def _build_judgement_title(indicator, direction, indicator_value, strength):
    side = "偏多" if direction == "LONG" else "偏空"
    raw_value = (indicator_value or "").strip()
    level = _get_strength_level(strength)

    if indicator == "MF_Accel":
        trend_word = "延续" if "加速" in raw_value else "观察"
        return f"{side}{trend_word}"
    if indicator == "MF_BreakZone":
        if "穿越" in raw_value:
            return f"{side}突破有效"
        if "震荡" in raw_value:
            return f"{side}信号存疑"
        return f"{side}趋势延续"
    if indicator == "Composite_Score":
        if strength is not None and float(strength) >= 1.0:
            return f"{side}共识较强"
        return f"{side}可跟踪"
    if indicator == "MS_Divergence":
        return f"{side}背离成立"
    if indicator == "MF_Magnitude":
        return f"{side}资金动作明显"
    if indicator == "MF_Duration":
        return f"{side}趋势已形成"
    if indicator == "MF_Edge3":
        return f"{side}起势信号"
    return f"{side}{level}信号"


def _build_judgement_reason(indicator, direction, indicator_value):
    side_subject = "主力连续走强" if direction == "LONG" else "主力连续走弱"
    raw_value = (indicator_value or "").strip()

    if indicator == "MF_Accel":
        if "加速" in raw_value:
            return f"{side_subject}，且第二步变化幅度大于第一步，说明趋势正在加速。"
        if "减速" in raw_value:
            return f"{side_subject}，但第二步变化幅度小于第一步，说明趋势动能在放缓。"
    if indicator == "MF_BreakZone":
        if "穿越底部边界" in raw_value:
            return "主力从底部极端区域向上穿越关键边界，说明偏多修复开始出现。"
        if "穿越顶部边界" in raw_value:
            return "主力从顶部极端区域向下穿越关键边界，说明偏空突破开始出现。"
        if "极端区内震荡" in raw_value:
            return "主力仍停留在极端区域内，没有形成清晰的边界突破。"
        if raw_value:
            return f"{side_subject}，当前属于“{raw_value}”状态。"
    if indicator == "Composite_Score":
        return "持续天数、加速度、边缘区启动、主散背离和幅度强度共同加权后，当前综合评分已达到可跟踪区间。"
    if indicator == "MS_Divergence":
        return f"{side_subject}，同时散户资金方向相反，形成主散背离。"
    if indicator == "MF_Magnitude":
        return f"{side_subject}，且近三日主力总变化幅度已经进入更明显的分档。"
    if indicator == "MF_Duration":
        return f"{side_subject}，趋势已经持续到“{raw_value or '当前分档'}”阶段。"
    if indicator == "MF_Edge3":
        return f"{side_subject}，并且起始位置落在“{raw_value or '当前区域'}”，可帮助判断这轮趋势从哪里启动。"
    return f"{side_subject}，并触发了 {indicator} 的当前判断条件。"


def _derive_duration_phase(streak_length):
    try:
        length = int(float(streak_length))
    except (TypeError, ValueError):
        return "趋势阶段"
    if length <= 3:
        return "启动段"
    if length <= 5:
        return "延续段"
    return "后段"


def _extract_duration_series(extra_json, context_series, streak_length):
    values = extra_json.get("values") or []
    deltas = extra_json.get("deltas") or []
    if values:
        return values, deltas

    try:
        length = max(int(float(streak_length)), 0)
    except (TypeError, ValueError):
        length = 0
    if not context_series or not length:
        return values, deltas

    main_force_values = []
    for item in context_series[-length:]:
        value = item.get("main_force")
        if value is None:
            return [], []
        main_force_values.append(float(value))
    if len(main_force_values) < length:
        return [], []

    deltas = [
        float(main_force_values[idx] - main_force_values[idx - 1])
        for idx in range(1, len(main_force_values))
    ]
    return main_force_values, deltas


def _fetch_signal_context_series(cursor, variety_id, signal_date, days=12, cache=None):
    cache_key = (int(variety_id), _date_str(signal_date) or str(signal_date), int(days))
    if cache is not None and cache_key in cache:
        return cache[cache_key]

    cursor.execute(
        """
        SELECT trade_date, main_force, retail
        FROM (
            SELECT trade_date, main_force, retail
            FROM fut_strength
            WHERE variety_id = %s
              AND trade_date <= %s
            ORDER BY trade_date DESC
            LIMIT %s
        ) recent
        ORDER BY trade_date ASC
        """,
        (int(variety_id), _date_str(signal_date) or str(signal_date), int(days)),
    )
    rows = cursor.fetchall()
    series = [
        {
            "trade_date": _date_str(row["trade_date"]),
            "main_force": float(row["main_force"]) if row["main_force"] is not None else None,
            "retail": float(row["retail"]) if row["retail"] is not None else None,
        }
        for row in rows
    ]
    if cache is not None:
        cache[cache_key] = series
    return series


def _build_calc_sections(indicator, direction, indicator_value, strength, extra_json, context_series=None):
    extra_json = extra_json or {}
    raw_value = (indicator_value or "").strip() or "当前结果"
    quantiles = extra_json.get("window_quantiles") or {}

    if indicator == "MF_Edge3":
        values = extra_json.get("values") or []
        start_value = extra_json.get("start_value", strength)
        return [
            _make_calc_section(
                "1. 用了哪些数据",
                [
                    f"近 3 日主力值：{_format_metric_list(values)}" if values else None,
                    f"起点值 start_val = {_format_metric_value(start_value)}",
                    f"近 3 个月滚动分位：p10 = {_format_metric_value(quantiles.get('p10'))}，p50 = {_format_metric_value(quantiles.get('p50'))}，p90 = {_format_metric_value(quantiles.get('p90'))}",
                ],
            ),
            _make_calc_section(
                "2. 怎么算",
                [
                    "先检查主力是否满足严格 3 连同向：LONG 看 v0 < v1 < v2，SHORT 看 v0 > v1 > v2。",
                    f"当前 start_val = {_format_metric_value(start_value)}。",
                    "LONG 分区规则：start_val < p10 为极端底部；p10 <= start_val < p50 为普通底部；start_val >= p50 为中性偏高。",
                    "SHORT 分区规则：start_val > p90 为极端顶部；p50 < start_val <= p90 为普通顶部；start_val <= p50 为中性偏低。",
                ],
            ),
            _make_calc_section(
                "3. 算出来多少",
                [
                    f"当前方向：{direction}",
                    f"起点值 = {_format_metric_value(start_value)}，结果分区 = {raw_value}",
                    f"strength 字段 = {_format_strength_value(strength)}",
                ],
            ),
            _make_calc_section(
                "4. 结果怎么看",
                [
                    "这个结果是相对位置，不是绝对大小。",
                    "要和该品种近 3 个月滚动窗口自己的历史分位比较，不适合直接跨品种比较。",
                    "普通底部表示起点已经落在近期偏低区域，但还没有低到极端底部。",
                ],
            ),
        ]

    if indicator == "MF_Accel":
        delta1 = extra_json.get("delta1")
        delta2 = extra_json.get("delta2")
        acceleration = extra_json.get("acceleration", strength)
        return [
            _make_calc_section(
                "1. 用了哪些数据",
                [
                    f"第一步主力变化 delta1 = {_format_metric_value(delta1)}",
                    f"第二步主力变化 delta2 = {_format_metric_value(delta2)}",
                ],
            ),
            _make_calc_section(
                "2. 怎么算",
                [
                    "先确认主力已经满足严格 3 连同向。",
                    f"加速度 = |delta2| - |delta1| = |{_format_metric_value(delta2)}| - |{_format_metric_value(delta1)}| = {_format_metric_value(acceleration)}",
                    "加速度 > 0 记为加速，加速度 <= 0 记为减速。",
                ],
            ),
            _make_calc_section(
                "3. 算出来多少",
                [
                    f"当前结果 = {raw_value}",
                    f"strength 字段 = {_format_strength_value(strength)}",
                ],
            ),
            _make_calc_section(
                "4. 结果怎么看",
                [
                    "先看它和 0 的关系：大于 0 是趋势加速，小于 0 是趋势放缓。",
                    "这个值没有统一绝对阈值，更适合同一指标内部做相对比较。",
                ],
            ),
        ]

    if indicator == "MF_Duration":
        streak_length = extra_json.get("streak_length", raw_value[1:] if raw_value.startswith("D") else raw_value)
        values, deltas = _extract_duration_series(extra_json, context_series, streak_length)
        duration_phase = _derive_duration_phase(streak_length)
        return [
            _make_calc_section(
                "1. 用了哪些数据",
                [
                    f"用于判定的连续主力值：{_format_metric_list(values)}" if values else "主力值的连续同向变化序列。",
                    f"当前连续同向天数 = {_format_metric_value(streak_length, 0)}",
                ],
            ),
            _make_calc_section(
                "2. 怎么算",
                [
                    "按 signals.py 里的 _streak_info 逻辑，逐日检查相邻两天主力变化方向是否保持一致，并向前累计。",
                    f"相邻变化 = {_format_metric_list(deltas)}" if deltas else None,
                    "只有在刚好达到 D3、D5、D7 时触发一次，不会每天重复记同一个档位。",
                ],
            ),
            _make_calc_section(
                "3. 算出来多少",
                [
                    f"当前结果 = {raw_value}",
                    f"strength 字段 = {_format_strength_value(strength)}",
                    f"当前处在 {duration_phase}",
                ],
            ),
            _make_calc_section(
                "4. 结果怎么看",
                [
                    "它反映趋势走到了哪个阶段，不是绝对强弱分。",
                    "通常先区分 D3 的启动段、D5 的延续段、D7 的后段，再结合别的信号判断是否拥挤。",
                    "这个结果更适合和同一品种自己的连续段历史比较，而不是跨品种直接比大小。",
                ],
            ),
        ]

    if indicator == "MS_Divergence":
        main_force_delta_avg = extra_json.get("main_force_delta_avg")
        retail_delta_avg = extra_json.get("retail_delta_avg")
        divergence_score = extra_json.get("divergence_score", strength)
        divergence_type = extra_json.get("divergence_type", raw_value)
        return [
            _make_calc_section(
                "1. 用了哪些数据",
                [
                    f"主力近两步平均变化 = {_format_metric_value(main_force_delta_avg)}",
                    f"散户近两步平均变化 = {_format_metric_value(retail_delta_avg)}",
                ],
            ),
            _make_calc_section(
                "2. 怎么算",
                [
                    "先确认主力已经满足严格 3 连同向。",
                    "再看散户是否反向变化：LONG 希望散户走弱，SHORT 希望散户走强。",
                    f"背离分 = |主力平均变化| + |散户平均变化| = {_format_metric_value(divergence_score)}",
                ],
            ),
            _make_calc_section(
                "3. 算出来多少",
                [
                    f"当前结果 = {divergence_type}",
                    f"背离分 = {_format_metric_value(divergence_score)}",
                    f"strength 字段 = {_format_strength_value(strength)}",
                ],
            ),
            _make_calc_section(
                "4. 结果怎么看",
                [
                    "先看主散是否真的反向，再看背离分大小。",
                    "这个分数越大，说明主散拉扯越明显；适合同一指标内部排序，不建议跨指标直接比较。",
                ],
            ),
        ]

    if indicator == "MF_Magnitude":
        magnitude = extra_json.get("magnitude", strength)
        magnitude_type = extra_json.get("magnitude_type", raw_value)
        return [
            _make_calc_section(
                "1. 用了哪些数据",
                [
                    f"主力 3 日总变化幅度 = {_format_metric_value(magnitude)}",
                    f"近 3 个月滚动分位：p25 = {_format_metric_value(quantiles.get('p25'))}，p75 = {_format_metric_value(quantiles.get('p75'))}",
                ],
            ),
            _make_calc_section(
                "2. 怎么算",
                [
                    "先确认主力已经满足严格 3 连同向。",
                    f"幅度定义为 |v2 - v0| = {_format_metric_value(magnitude)}。",
                    "若幅度 >= p75，记为高幅度；若幅度 >= p25 且 < p75，记为中幅度；否则记为低幅度。",
                ],
            ),
            _make_calc_section(
                "3. 算出来多少",
                [
                    f"当前结果 = {magnitude_type}",
                    f"strength 字段 = {_format_strength_value(strength)}",
                ],
            ),
            _make_calc_section(
                "4. 结果怎么看",
                [
                    "这看的是动作大小，不是方向本身。",
                    "要和该品种近 3 个月滚动分布比较；同样是 10，不同品种或不同阶段含义可能不一样。",
                ],
            ),
        ]

    if indicator == "MF_BreakZone":
        values = extra_json.get("values") or []
        zone_type = extra_json.get("zone_type", raw_value)
        return [
            _make_calc_section(
                "1. 用了哪些数据",
                [
                    f"近 3 日主力值：{_format_metric_list(values)}" if values else None,
                    f"底部/顶部边界：p10 = {_format_metric_value(quantiles.get('p10'))}，p90 = {_format_metric_value(quantiles.get('p90'))}",
                ],
            ),
            _make_calc_section(
                "2. 怎么算",
                [
                    "LONG 看是否从底部极端区向上穿越 p10；SHORT 看是否从顶部极端区向下穿越 p90。",
                    "LONG：v0 < p10 且 v2 >= p10 记为穿越底部边界；v0 < p10 且 v2 < p10 记为极端区内震荡；否则是普通区间 3 连升。",
                    "SHORT：v0 > p90 且 v2 <= p90 记为穿越顶部边界；v0 > p90 且 v2 > p90 记为极端区内震荡；否则是普通区间 3 连降。",
                ],
            ),
            _make_calc_section(
                "3. 算出来多少",
                [
                    f"当前结果 = {zone_type}",
                    f"strength 字段 = {_format_strength_value(strength)}",
                ],
            ),
            _make_calc_section(
                "4. 结果怎么看",
                [
                    "这是档位型结果：2 是边界突破，1 是极端区内震荡，0 是普通区间趋势。",
                    "重点看有没有穿越边界，不要把 2、1、0 当成线性收益分。",
                ],
            ),
        ]

    if indicator == "Composite_Score":
        components = extra_json.get("components") or {}
        duration_score = components.get("duration_score", 0)
        accel_score = components.get("accel_score", 0)
        edge_score = components.get("edge_score", 0)
        divergence_score = components.get("divergence_score", 0)
        magnitude_score = components.get("magnitude_score", 0)
        computed_total = (
            duration_score * 0.30
            + accel_score * 0.20
            + edge_score * 0.20
            + divergence_score * 0.20
            + magnitude_score * 0.10
        )
        return [
            _make_calc_section(
                "1. 用了哪些数据",
                [
                    f"连续天数档位 = {_format_metric_value(extra_json.get('streak_length'), 0)}",
                    f"边缘区阈值：p10 = {_format_metric_value(quantiles.get('edge_p10'))}，p20 = {_format_metric_value(quantiles.get('edge_p20'))}，p80 = {_format_metric_value(quantiles.get('edge_p80'))}，p90 = {_format_metric_value(quantiles.get('edge_p90'))}",
                    f"幅度阈值：p25 = {_format_metric_value(quantiles.get('magnitude_p25'))}，p75 = {_format_metric_value(quantiles.get('magnitude_p75'))}；当前幅度 = {_format_metric_value(extra_json.get('current_magnitude'))}",
                ],
            ),
            _make_calc_section(
                "2. 怎么算",
                [
                    "综合分 = 持续天数 x 0.30 + 加速度 x 0.20 + 起点位置 x 0.20 + 主散背离 x 0.20 + 幅度强度 x 0.10。",
                    "各子项先离散打分，再按固定权重加总。",
                    "权重分别是 duration 0.30、accel 0.20、edge 0.20、divergence 0.20、magnitude 0.10。",
                ],
            ),
            _make_calc_section(
                "3. 算出来多少",
                [
                    f"duration({duration_score} x 0.30) = {duration_score * 0.30:.2f}",
                    f"accel({accel_score} x 0.20) = {accel_score * 0.20:.2f}",
                    f"edge({edge_score} x 0.20) = {edge_score * 0.20:.2f}",
                    f"divergence({divergence_score} x 0.20) = {divergence_score * 0.20:.2f}",
                    f"magnitude({magnitude_score} x 0.10) = {magnitude_score * 0.10:.2f}",
                    f"加总得到 {computed_total:.2f}；展示值 = {raw_value}；strength 字段 = {_format_strength_value(strength)}",
                ],
            ),
            _make_calc_section(
                "4. 结果怎么看",
                [
                    "综合分更适合在同一指标内部做排序，通常先和 1.0 左右这样的经验分界一起看。",
                    "它是规则打分，不是未来收益率；更适合回答“当前这条信号在这套规则里有多完整”。",
                ],
            ),
        ]

    return [
        _make_calc_section("1. 用了哪些数据", ["当前接口没有提供更多结构化明细。"]),
        _make_calc_section("2. 怎么算", ["按当前指标规则计算。"]),
        _make_calc_section("3. 算出来多少", [f"当前结果 = {raw_value}"]),
        _make_calc_section("4. 结果怎么看", ["建议结合该指标自己的历史表现做相对判断。"]),
    ]


def _build_signal_explanation(indicator, direction, indicator_value, strength, extra_json=None, context_series=None):
    meta = INDICATOR_META.get(indicator, {})
    strength_level = _get_strength_level(strength)
    extra_json = extra_json or {}
    return {
        "indicator_label_cn": meta.get("label", indicator),
        "indicator_short_desc": meta.get("short_desc", "辅助判断当前信号的结构特征"),
        "calc_explanation": meta.get("calc_explanation", "根据当前信号规则生成的辅助判断说明。"),
        "indicator_display_value": _build_indicator_display_value(indicator, indicator_value),
        "strength_level": strength_level,
        "strength_explanation": _build_strength_explanation(indicator, strength, strength_level, indicator_value, extra_json),
        "judgement_title": _build_judgement_title(indicator, direction, indicator_value, strength),
        "judgement_reason": _build_judgement_reason(indicator, direction, indicator_value),
        "calc_sections": _build_calc_sections(indicator, direction, indicator_value, strength, extra_json, context_series),
        "risk_note": meta.get("default_risk", "该信号仅用于辅助理解，不能替代完整交易判断。"),
    }


@assistant_bp.route("/assistant/signals", methods=["GET"])
def get_assistant_signals():
    conn = _get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        signal_date = request.args.get("date", "").strip() or _latest_table_date(cursor, "assistant_signals", "signal_date")
        variety_id = request.args.get("variety_id", "").strip()
        variety_name = request.args.get("variety_name", "").strip()
        indicator = request.args.get("indicator", "").strip()
        direction = request.args.get("direction", "").strip()

        where_clauses = []
        params = []
        if signal_date:
            where_clauses.append("signal_date = %s")
            params.append(signal_date)
        if variety_id:
            where_clauses.append("variety_id = %s")
            params.append(int(variety_id))
        if variety_name:
            clause, value = _build_like_filter("variety_name", variety_name)
            where_clauses.append(clause)
            params.append(value)
        if indicator:
            where_clauses.append("indicator = %s")
            params.append(indicator)
        if direction:
            where_clauses.append("direction = %s")
            params.append(direction)

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        cursor.execute(
            f"""
            SELECT
                id, signal_date, variety_id, variety_name, indicator,
                direction, triggered, strength, extra_json, created_at
            FROM assistant_signals
            {where_sql}
            ORDER BY signal_date DESC, variety_id, indicator, direction
            """,
            params,
        )
        rows = cursor.fetchall()

        signals = []
        context_cache = {}
        for row in rows:
            extra = _parse_json(row["extra_json"])
            strength = float(row["strength"]) if row["strength"] is not None else None
            indicator_value = extra.get("indicator_value", "")
            context_series = None
            if row["indicator"] == "MF_Duration":
                context_series = _fetch_signal_context_series(
                    cursor,
                    row["variety_id"],
                    row["signal_date"],
                    days=12,
                    cache=context_cache,
                )
            explanation = _build_signal_explanation(
                row["indicator"],
                row["direction"],
                indicator_value,
                strength,
                extra,
                context_series,
            )
            signals.append(
                {
                    "id": row["id"],
                    "signal_date": _date_str(row["signal_date"]),
                    "variety_id": row["variety_id"],
                    "variety_name": row["variety_name"],
                    "indicator": row["indicator"],
                    "direction": row["direction"],
                    "triggered": int(row["triggered"] or 0),
                    "strength": strength,
                    "indicator_value": indicator_value,
                    "extra_json": extra,
                    "created_at": row["created_at"].strftime("%Y-%m-%d %H:%M:%S") if row["created_at"] else "",
                    **explanation,
                }
            )

        return _success(
            {
                "date": signal_date,
                "signals": signals,
                "total": len(signals),
            }
        )
    except Exception as exc:
        logger.error("获取辅助信号失败: %s", exc)
        return _error(f"获取失败: {exc}")
    finally:
        cursor.close()
        conn.close()


@assistant_bp.route("/assistant/operations", methods=["GET"])
def get_assistant_operations():
    conn = _get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        signal_date = request.args.get("date", "").strip() or _latest_table_date(cursor, "assistant_operations", "signal_date")
        account_type = request.args.get("account_type", "mechanical").strip() or "mechanical"
        variety_id = request.args.get("variety_id", "").strip()
        variety_name = request.args.get("variety_name", "").strip()
        strategy = request.args.get("strategy", "").strip()
        direction = request.args.get("direction", "").strip()

        where_clauses = []
        params = []
        if signal_date:
            where_clauses.append("signal_date = %s")
            params.append(signal_date)
        if account_type:
            where_clauses.append("account_type = %s")
            params.append(account_type)
        if variety_id:
            where_clauses.append("variety_id = %s")
            params.append(int(variety_id))
        if variety_name:
            clause, value = _build_like_filter("variety_name", variety_name)
            where_clauses.append(clause)
            params.append(value)
        if strategy:
            where_clauses.append("strategy = %s")
            params.append(strategy)
        if direction:
            where_clauses.append("direction = %s")
            params.append(direction)

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        cursor.execute(
            f"""
            SELECT
                id, signal_date, variety_id, variety_name, strategy,
                direction, extra_json, account_type, executed, created_at
            FROM assistant_operations
            {where_sql}
            ORDER BY signal_date DESC, created_at DESC, id DESC
            """,
            params,
        )
        rows = cursor.fetchall()

        operations = []
        for row in rows:
            extra = _parse_json(row["extra_json"])
            composite_score = float(extra.get("composite_score", 0.0))
            trigger_indicators = extra.get("trigger_indicators", {})
            operation_explanation = _build_operation_explanation(
                row["strategy"],
                row["direction"],
                trigger_indicators,
                composite_score,
            )
            operations.append(
                {
                    "id": row["id"],
                    "signal_date": _date_str(row["signal_date"]),
                    "variety_id": row["variety_id"],
                    "variety_name": row["variety_name"],
                    "strategy": row["strategy"],
                    "direction": row["direction"],
                    "account_type": row["account_type"],
                    "executed": int(row["executed"] or 0),
                    "strategy_label": extra.get("strategy_label", ""),
                    "trigger_indicators": trigger_indicators,
                    "composite_score": composite_score,
                    "extra_json": extra,
                    "created_at": row["created_at"].strftime("%Y-%m-%d %H:%M:%S") if row["created_at"] else "",
                    **operation_explanation,
                }
            )

        return _success(
            {
                "date": signal_date,
                "account_type": account_type,
                "operations": operations,
                "total": len(operations),
            }
        )
    except Exception as exc:
        logger.error("获取操作建议失败: %s", exc)
        return _error(f"获取失败: {exc}")
    finally:
        cursor.close()
        conn.close()


@assistant_bp.route("/assistant/positions", methods=["GET"])
def get_assistant_positions():
    conn = _get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        account_type = request.args.get("account_type", "").strip()
        where_clauses = ["p.status = 'open'"]
        params = []
        if account_type:
            where_clauses.append("p.account_type = %s")
            params.append(account_type)

        cursor.execute(
            f"""
            SELECT
                p.id,
                p.account_type,
                p.variety_id,
                p.variety_name,
                p.direction,
                p.open_date,
                p.open_price,
                p.size_pct,
                p.strategy,
                latest.trade_date AS latest_trade_date,
                latest.close_price AS current_price,
                latest.main_force,
                latest.retail,
                (
                    SELECT COUNT(1)
                    FROM fut_daily_close fd
                    WHERE fd.variety_id = p.variety_id
                      AND fd.trade_date >= p.open_date
                      AND fd.trade_date <= latest.trade_date
                ) AS holding_days
            FROM assistant_positions p
            LEFT JOIN (
                SELECT
                    s.variety_id,
                    s.trade_date,
                    s.main_force,
                    s.retail,
                    c.close_price
                FROM fut_strength s
                INNER JOIN fut_daily_close c
                    ON s.variety_id = c.variety_id
                   AND s.trade_date = c.trade_date
                INNER JOIN (
                    SELECT variety_id, MAX(trade_date) AS latest_trade_date
                    FROM fut_strength
                    GROUP BY variety_id
                ) latest_lookup
                    ON s.variety_id = latest_lookup.variety_id
                   AND s.trade_date = latest_lookup.latest_trade_date
            ) latest
                ON p.variety_id = latest.variety_id
            WHERE {" AND ".join(where_clauses)}
            ORDER BY p.account_type, p.open_date, p.id
            """,
            params,
        )
        rows = cursor.fetchall()

        positions = []
        for row in rows:
            current_price = float(row["current_price"]) if row["current_price"] is not None else None
            open_price = float(row["open_price"])
            direction_sign = 1 if row["direction"] == "LONG" else -1
            floating_pnl_pct = None
            floating_pnl_amount = None
            if current_price is not None and open_price:
                raw_return = direction_sign * ((current_price - open_price) / open_price)
                floating_pnl_pct = raw_return * LEVERAGE * 100
                floating_pnl_amount = INITIAL_CAPITAL * float(row["size_pct"]) * floating_pnl_pct / 100

            holding_days = int(row["holding_days"] or 0)
            positions.append(
                {
                    "id": row["id"],
                    "account_type": row["account_type"],
                    "variety_id": row["variety_id"],
                    "variety_name": row["variety_name"],
                    "direction": row["direction"],
                    "open_date": _date_str(row["open_date"]),
                    "open_price": open_price,
                    "current_price": current_price,
                    "size_pct": float(row["size_pct"]),
                    "strategy": row["strategy"],
                    "latest_trade_date": _date_str(row["latest_trade_date"]),
                    "main_force": float(row["main_force"]) if row["main_force"] is not None else None,
                    "retail": float(row["retail"]) if row["retail"] is not None else None,
                    "holding_days": holding_days,
                    "remaining_days": max(0, MAX_HOLD_DAYS - holding_days),
                    "floating_pnl_pct": round(floating_pnl_pct, 4) if floating_pnl_pct is not None else None,
                    "floating_pnl_amount": round(floating_pnl_amount, 4) if floating_pnl_amount is not None else None,
                }
            )

        return _success(
            {
                "account_type": account_type or "all",
                "positions": positions,
                "total": len(positions),
            }
        )
    except Exception as exc:
        logger.error("获取当前持仓失败: %s", exc)
        return _error(f"获取失败: {exc}")
    finally:
        cursor.close()
        conn.close()


@assistant_bp.route("/assistant/positions/history", methods=["GET"])
def get_assistant_position_history():
    conn = _get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        account_type = request.args.get("account_type", "").strip()
        limit = min(max(int(request.args.get("limit", 100)), 1), 500)

        where_clauses = ["status = 'closed'"]
        params = []
        if account_type:
            where_clauses.append("account_type = %s")
            params.append(account_type)

        cursor.execute(
            f"""
            SELECT
                id, account_type, variety_id, variety_name, direction,
                open_date, open_price, close_date, close_price,
                size_pct, pnl_pct, strategy, created_at
            FROM assistant_positions
            WHERE {" AND ".join(where_clauses)}
            ORDER BY close_date DESC, id DESC
            LIMIT %s
            """,
            [*params, limit],
        )
        rows = cursor.fetchall()

        history = []
        for row in rows:
            history.append(
                {
                    "id": row["id"],
                    "account_type": row["account_type"],
                    "variety_id": row["variety_id"],
                    "variety_name": row["variety_name"],
                    "direction": row["direction"],
                    "open_date": _date_str(row["open_date"]),
                    "open_price": float(row["open_price"]),
                    "close_date": _date_str(row["close_date"]),
                    "close_price": float(row["close_price"]) if row["close_price"] is not None else None,
                    "size_pct": float(row["size_pct"]),
                    "pnl_pct": float(row["pnl_pct"]) if row["pnl_pct"] is not None else None,
                    "strategy": row["strategy"],
                    "created_at": row["created_at"].strftime("%Y-%m-%d %H:%M:%S") if row["created_at"] else "",
                }
            )

        return _success(
            {
                "account_type": account_type or "all",
                "history": history,
                "total": len(history),
            }
        )
    except Exception as exc:
        logger.error("获取历史持仓失败: %s", exc)
        return _error(f"获取失败: {exc}")
    finally:
        cursor.close()
        conn.close()


@assistant_bp.route("/assistant/account/curve", methods=["GET"])
def get_assistant_account_curve():
    conn = _get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        start_date = request.args.get("start_date", "").strip()
        end_date = request.args.get("end_date", "").strip()
        account_type = request.args.get("account_type", "").strip()

        where_clauses = []
        params = []
        if start_date:
            where_clauses.append("record_date >= %s")
            params.append(start_date)
        if end_date:
            where_clauses.append("record_date <= %s")
            params.append(end_date)
        if account_type:
            where_clauses.append("account_type = %s")
            params.append(account_type)

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        cursor.execute(
            f"""
            SELECT record_date, account_type, equity, cash, position_val, daily_pnl
            FROM assistant_account_daily
            {where_sql}
            ORDER BY record_date, account_type
            """,
            params,
        )
        rows = cursor.fetchall()

        curves = {key: [] for key in ACCOUNT_TYPES}
        for row in rows:
            curves.setdefault(row["account_type"], []).append(
                {
                    "record_date": _date_str(row["record_date"]),
                    "equity": float(row["equity"]),
                    "cash": float(row["cash"]),
                    "position_val": float(row["position_val"]),
                    "daily_pnl": float(row["daily_pnl"]),
                }
            )

        return _success(
            {
                "account_type": account_type or "all",
                "curves": curves,
            }
        )
    except Exception as exc:
        logger.error("获取资金曲线失败: %s", exc)
        return _error(f"获取失败: {exc}")
    finally:
        cursor.close()
        conn.close()


@assistant_bp.route("/assistant/account/summary", methods=["GET"])
def get_assistant_account_summary():
    conn = _get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        requested_date = request.args.get("date", "").strip()
        summary = {}
        for account_type in ACCOUNT_TYPES:
            if requested_date:
                cursor.execute(
                    """
                    SELECT record_date, equity, cash, position_val, daily_pnl
                    FROM assistant_account_daily
                    WHERE account_type = %s
                      AND record_date <= %s
                    ORDER BY record_date DESC
                    LIMIT 1
                    """,
                    (account_type, requested_date),
                )
            else:
                cursor.execute(
                    """
                    SELECT record_date, equity, cash, position_val, daily_pnl
                    FROM assistant_account_daily
                    WHERE account_type = %s
                    ORDER BY record_date DESC
                    LIMIT 1
                    """,
                    (account_type,),
                )
            snapshot = cursor.fetchone()
            if snapshot:
                cursor.execute(
                    """
                    SELECT COUNT(1) AS cnt
                    FROM assistant_positions
                    WHERE account_type = %s AND status = 'open'
                    """,
                    (account_type,),
                )
                open_positions = cursor.fetchone()["cnt"]
                summary[account_type] = {
                    "record_date": _date_str(snapshot["record_date"]),
                    "equity": float(snapshot["equity"]),
                    "cash": float(snapshot["cash"]),
                    "position_val": float(snapshot["position_val"]),
                    "daily_pnl": float(snapshot["daily_pnl"]),
                    "open_positions": int(open_positions),
                }
            else:
                summary[account_type] = {
                    "record_date": None,
                    "equity": INITIAL_CAPITAL,
                    "cash": INITIAL_CAPITAL,
                    "position_val": 0.0,
                    "daily_pnl": 0.0,
                    "open_positions": 0,
                }

        return _success({"summary": summary})
    except Exception as exc:
        logger.error("获取账户摘要失败: %s", exc)
        return _error(f"获取失败: {exc}")
    finally:
        cursor.close()
        conn.close()


@assistant_bp.route("/assistant/market-context", methods=["GET"])
def get_assistant_market_context():
    conn = _get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        variety_id = request.args.get("variety_id", "").strip()
        if not variety_id:
            return _error("缺少 variety_id 参数")
        days = min(max(int(request.args.get("days", 10)), 3), 60)
        end_date = request.args.get("end_date", "").strip()
        if not end_date:
            cursor.execute(
                """
                SELECT MAX(trade_date) AS latest_date
                FROM fut_strength
                WHERE variety_id = %s
                """,
                (int(variety_id),),
            )
            row = cursor.fetchone()
            end_date = _date_str(row["latest_date"]) if row and row.get("latest_date") else None

        cursor.execute(
            """
            SELECT
                s.variety_id,
                COALESCE(v.name, CAST(s.variety_id AS CHAR)) AS variety_name,
                s.trade_date,
                s.main_force,
                s.retail,
                c.close_price
            FROM fut_strength s
            INNER JOIN fut_daily_close c
                ON s.variety_id = c.variety_id
               AND s.trade_date = c.trade_date
            LEFT JOIN fut_variety v
                ON s.variety_id = v.id
            WHERE s.variety_id = %s
              AND s.trade_date <= %s
            ORDER BY s.trade_date DESC
            LIMIT %s
            """,
            (int(variety_id), end_date, days),
        )
        rows = list(reversed(cursor.fetchall()))
        series = [
            {
                "trade_date": _date_str(row["trade_date"]),
                "main_force": float(row["main_force"]),
                "retail": float(row["retail"]),
                "close_price": float(row["close_price"]),
            }
            for row in rows
        ]
        variety_name = rows[0]["variety_name"] if rows else ""

        return _success(
            {
                "variety_id": int(variety_id),
                "variety_name": variety_name,
                "end_date": end_date,
                "days": days,
                "series": series,
            }
        )
    except Exception as exc:
        logger.error("获取市场上下文失败: %s", exc)
        return _error(f"获取失败: {exc}")
    finally:
        cursor.close()
        conn.close()


@assistant_bp.route("/assistant/variety-list", methods=["GET"])
def variety_list():
    """获取有 contracts_symbol 映射的品种列表（用于K线展示品种选择器）。"""
    conn = _get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute(
            "SELECT id, name, contracts_symbol FROM fut_variety "
            "WHERE contracts_symbol IS NOT NULL AND contracts_symbol != '' "
            "ORDER BY id"
        )
        rows = cursor.fetchall()
        return _success({"varieties": [
            {"id": row["id"], "name": row["name"], "contracts_symbol": row["contracts_symbol"]}
            for row in rows
        ]})
    except Exception as exc:
        logger.error("获取品种列表失败: %s", exc)
        return _error(f"获取失败: {exc}")
    finally:
        cursor.close()
        conn.close()


@assistant_bp.route("/assistant/variety-kline", methods=["GET"])
def variety_kline():
    """
    获取品种K线 + 主力/散户指数。
    参数：variety_id（必填），start_date，end_date（可选，默认近60天）。
    K线以 hist_{contracts_symbol.lower()} 表为主，指数以 fut_strength LEFT JOIN。
    """
    variety_id = request.args.get("variety_id")
    if not variety_id:
        return _error("variety_id 不能为空")

    today = date.today()
    default_start = (today - timedelta(days=60)).isoformat()
    start_date = request.args.get("start_date") or default_start
    end_date = request.args.get("end_date") or today.isoformat()

    conn = _get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute(
            "SELECT id, name, contracts_symbol FROM fut_variety WHERE id = %s",
            (int(variety_id),)
        )
        variety = cursor.fetchone()
        if not variety or not variety["contracts_symbol"]:
            return _error("品种不存在或未配置 contracts_symbol")

        symbol = variety["contracts_symbol"].lower()
        table = f"hist_{symbol}"

        cursor.execute(
            f"SELECT trade_date, open_price, high_price, low_price, close_price, volume "
            f"FROM {table} "
            f"WHERE trade_date >= %s AND trade_date <= %s "
            f"ORDER BY trade_date ASC",
            (start_date, end_date),
        )
        kline_rows = cursor.fetchall()

        cursor.execute(
            "SELECT trade_date, main_force, retail FROM fut_strength "
            "WHERE variety_id = %s AND trade_date >= %s AND trade_date <= %s "
            "ORDER BY trade_date ASC",
            (int(variety_id), start_date, end_date),
        )
        strength_rows = cursor.fetchall()
        strength_map = {_date_str(r["trade_date"]): r for r in strength_rows}

        kline = []
        strength = []
        for row in kline_rows:
            dt = _date_str(row["trade_date"])
            kline.append({
                "trade_date": dt,
                "open":   float(row["open_price"]),
                "high":   float(row["high_price"]),
                "low":    float(row["low_price"]),
                "close":  float(row["close_price"]),
                "volume": int(row["volume"]),
            })
            s = strength_map.get(dt)
            strength.append({
                "trade_date": dt,
                "main_force": float(s["main_force"]) if s and s["main_force"] is not None else None,
                "retail":     float(s["retail"])     if s and s["retail"]     is not None else None,
            })

        return _success({
            "variety": {"id": variety["id"], "name": variety["name"]},
            "kline":   kline,
            "strength": strength,
        })
    except Exception as exc:
        logger.error("获取品种K线失败: %s", exc)
        return _error(f"获取失败: {exc}")
    finally:
        cursor.close()
        conn.close()
