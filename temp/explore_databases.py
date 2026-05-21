"""
探查阿里云和腾讯云两个数据库的表结构和数据情况
结果保存到 temp/db_comparison_report.md
"""
import pymysql
from datetime import datetime

ALI_CONFIG = {
    "host": "rm-bp1u701yzm0y42oh1vo.mysql.rds.aliyuncs.com",
    "port": 3306,
    "user": "ysd",
    "password": "Yan1234567",
    "database": "futures",
    "charset": "utf8mb4",
}

TENCENT_CONFIG = {
    "host": "82.156.207.94",
    "port": 3306,
    "user": "ysd",
    "password": "@Yan1234567",
    "database": "futures",
    "charset": "utf8mb4",
}

REPORT_FILE = "/Users/zxxk/ysd/ysdproject/workstation/temp/db_comparison_report.md"


def get_connection(cfg):
    return pymysql.connect(**cfg)


def get_tables(cursor):
    cursor.execute("SHOW TABLES")
    return [row[0] for row in cursor.fetchall()]


def get_table_schema(cursor, table):
    cursor.execute(f"DESCRIBE `{table}`")
    return cursor.fetchall()


def get_row_count(cursor, table):
    cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
    return cursor.fetchone()[0]


def get_sample_rows(cursor, table, limit=5):
    cursor.execute(f"SELECT * FROM `{table}` LIMIT {limit}")
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    return columns, rows


def get_table_status(cursor, table):
    cursor.execute(f"SHOW TABLE STATUS LIKE '{table}'")
    return cursor.fetchone()


def explore_db(label, cfg):
    conn = get_connection(cfg)
    cursor = conn.cursor()
    tables = get_tables(cursor)
    result = {"tables": {}}
    for table in sorted(tables):
        schema = get_table_schema(cursor, table)
        count = get_row_count(cursor, table)
        cols, samples = get_sample_rows(cursor, table)
        status = get_table_status(cursor, table)
        result["tables"][table] = {
            "schema": schema,
            "row_count": count,
            "columns": cols,
            "samples": samples,
            "engine": status[1] if status else None,
            "create_time": status[11] if status else None,
            "data_length": status[6] if status else None,
        }
        print(f"  [{label}] {table}: {count} rows")
    cursor.close()
    conn.close()
    return result


def fmt_schema(schema_rows):
    lines = []
    for row in schema_rows:
        field, typ, null_, key, default, extra = row
        lines.append(f"  | {field:30s} | {typ:20s} | {null_:5s} | {key:4s} | {str(default):10s} |")
    return "\n".join(lines)


def main():
    print("=" * 60)
    print(f"开始探查数据库 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    ali = explore_db("阿里云", ALI_CONFIG)
    tencent = explore_db("腾讯云", TENCENT_CONFIG)

    ali_tables = set(ali["tables"].keys())
    tc_tables = set(tencent["tables"].keys())

    only_ali = ali_tables - tc_tables
    only_tc = tc_tables - ali_tables
    common = ali_tables & tc_tables

    # Build report
    report = []
    report.append(f"# 数据库对比报告\n")
    report.append(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    report.append(f"---\n")

    report.append(f"## 概览\n")
    report.append(f"| 指标 | 阿里云 (aliyun) | 腾讯云 (tencent) |")
    report.append(f"|------|----------------|-----------------|")
    report.append(f"| 表数量 | {len(ali_tables)} | {len(tc_tables)} |")
    report.append(f"| 独有表 | {len(only_ali)} | {len(only_tc)} |")
    report.append(f"| 共有表 | {len(common)} | {len(common)} |")
    report.append("")

    if only_ali:
        report.append(f"### 阿里云独有表 ({len(only_ali)})\n")
        for t in sorted(only_ali):
            info = ali["tables"][t]
            report.append(f"- **{t}**: {info['row_count']} 行")
        report.append("")

    if only_tc:
        report.append(f"### 腾讯云独有表 ({len(only_tc)})\n")
        for t in sorted(only_tc):
            info = tencent["tables"][t]
            report.append(f"- **{t}**: {info['row_count']} 行")
        report.append("")

    report.append(f"## 各表详情\n")
    for table in sorted(common):
        ali_info = ali["tables"][table]
        tc_info = tencent["tables"][table]

        report.append(f"---\n")
        report.append(f"### {table}\n")

        ali_count = ali_info["row_count"]
        tc_count = tc_info["row_count"]
        diff = ali_count - tc_count
        diff_str = f"{diff:+d}" if diff != 0 else "相同"
        report.append(f"- **阿里云**: {ali_count} 行 | **腾讯云**: {tc_count} 行 | **差额**: {diff_str}\n")

        if ali_info["engine"]:
            report.append(f"- 引擎: {ali_info['engine']} | 创建时间: {ali_info['create_time']}\n")

        # Schema (use ali schema, usually same)
        report.append(f"\n**表结构 (阿里云):**\n")
        report.append(f"```\n| 字段名                         | 类型                | Null  | Key  | 默认值       |\n")
        report.append(f"{fmt_schema(ali_info['schema'])}\n```\n")

        # Sample rows
        if ali_info["samples"]:
            report.append(f"\n**阿里云 示例数据 (前{len(ali_info['samples'])}行):**\n")
            report.append(f"```\n| {' | '.join(ali_info['columns'])}\n")
            for row in ali_info["samples"]:
                report.append(f"| {' | '.join(str(v)[:40] if v is not None else 'NULL' for v in row)}\n")
            report.append("```\n")

        if tc_info["samples"]:
            report.append(f"\n**腾讯云 示例数据 (前{len(tc_info['samples'])}行):**\n")
            report.append(f"```\n| {' | '.join(tc_info['columns'])}\n")
            for row in tc_info["samples"]:
                report.append(f"| {' | '.join(str(v)[:40] if v is not None else 'NULL' for v in row)}\n")
            report.append("```\n")

    # Also add details for exclusive tables
    for table in sorted(only_ali):
        info = ali["tables"][table]
        report.append(f"---\n")
        report.append(f"### {table} (仅阿里云)\n")
        report.append(f"- {info['row_count']} 行\n")
        report.append(f"\n**表结构:**\n")
        report.append(f"```\n| 字段名                         | 类型                | Null  | Key  | 默认值       |\n")
        report.append(f"{fmt_schema(info['schema'])}\n```\n")
        if info["samples"]:
            report.append(f"\n**示例数据 (前{len(info['samples'])}行):**\n")
            report.append(f"```\n| {' | '.join(info['columns'])}\n")
            for row in info["samples"]:
                report.append(f"| {' | '.join(str(v)[:40] if v is not None else 'NULL' for v in row)}\n")
            report.append("```\n")

    for table in sorted(only_tc):
        info = tencent["tables"][table]
        report.append(f"---\n")
        report.append(f"### {table} (仅腾讯云)\n")
        report.append(f"- {info['row_count']} 行\n")
        report.append(f"\n**表结构:**\n")
        report.append(f"```\n| 字段名                         | 类型                | Null  | Key  | 默认值       |\n")
        report.append(f"{fmt_schema(info['schema'])}\n```\n")
        if info["samples"]:
            report.append(f"\n**示例数据 (前{len(info['samples'])}行):**\n")
            report.append(f"```\n| {' | '.join(info['columns'])}\n")
            for row in info["samples"]:
                report.append(f"| {' | '.join(str(v)[:40] if v is not None else 'NULL' for v in row)}\n")
            report.append("```\n")

    report_text = "\n".join(report)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report_text)

    print(f"\n报告已保存到: {REPORT_FILE}")
    print(f"\n阿里云: {len(ali_tables)} 张表")
    print(f"腾讯云: {len(tc_tables)} 张表")
    print(f"共有表: {len(common)}")
    print(f"仅阿里云: {len(only_ali)} -> {sorted(only_ali)}")
    print(f"仅腾讯云: {len(only_tc)} -> {sorted(only_tc)}")

    # Show per-table row count diff
    print(f"\n共有表行数差异 (阿里云 - 腾讯云):")
    for table in sorted(common):
        diff = ali["tables"][table]["row_count"] - tencent["tables"][table]["row_count"]
        sign = "+" if diff > 0 else ""
        print(f"  {table:40s}: {sign}{diff}")


if __name__ == "__main__":
    main()