"""
增量同步脚本：将腾讯云比阿里云多的数据同步到阿里云
策略：对每张有差异的表，从腾讯云 SELECT 全部数据，与阿里云对比后 INSERT IGNORE 写入
可安全重复执行（幂等）
"""
import pymysql
from datetime import datetime
import sys

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

# 需要同步的表及其主键/唯一键信息
# (table_name, pk_columns, strategy)
# strategy: 'insert_ignore' = INSERT IGNORE（适用于有自增/唯一键的表）
# strategy: 'upsert' = 先检查后插入（适用于有复合主键但无自增ID的表）
TABLES_TO_SYNC = [
    # ========== 历史行情表（trade_date 为主键） ==========
    ("hist_adm", ["trade_date"], "insert_ignore"),
    ("hist_agm", ["trade_date"], "insert_ignore"),
    ("hist_alm", ["trade_date"], "insert_ignore"),
    ("hist_am", ["trade_date"], "insert_ignore"),
    ("hist_aom", ["trade_date"], "insert_ignore"),
    ("hist_apm", ["trade_date"], "insert_ignore"),
    ("hist_aum", ["trade_date"], "insert_ignore"),
    ("hist_bbm", ["trade_date"], "insert_ignore"),
    ("hist_bcm", ["trade_date"], "insert_ignore"),
    ("hist_bm", ["trade_date"], "insert_ignore"),
    ("hist_brm", ["trade_date"], "insert_ignore"),
    ("hist_bum", ["trade_date"], "insert_ignore"),
    ("hist_bzm", ["trade_date"], "insert_ignore"),
    ("hist_cfm", ["trade_date"], "insert_ignore"),
    ("hist_cjm", ["trade_date"], "insert_ignore"),
    ("hist_cm", ["trade_date"], "insert_ignore"),
    ("hist_csm", ["trade_date"], "insert_ignore"),
    ("hist_cum", ["trade_date"], "insert_ignore"),
    ("hist_cym", ["trade_date"], "insert_ignore"),
    ("hist_ebm", ["trade_date"], "insert_ignore"),
    ("hist_ecm", ["trade_date"], "insert_ignore"),
    ("hist_egm", ["trade_date"], "insert_ignore"),
    ("hist_fbm", ["trade_date"], "insert_ignore"),
    ("hist_fgm", ["trade_date"], "insert_ignore"),
    ("hist_fum", ["trade_date"], "insert_ignore"),
    ("hist_hcm", ["trade_date"], "insert_ignore"),
    ("hist_icm", ["trade_date"], "insert_ignore"),
    ("hist_ifm", ["trade_date"], "insert_ignore"),
    ("hist_ihm", ["trade_date"], "insert_ignore"),
    ("hist_im", ["trade_date"], "insert_ignore"),
    ("hist_imm", ["trade_date"], "insert_ignore"),
    ("hist_jdm", ["trade_date"], "insert_ignore"),
    ("hist_jm", ["trade_date"], "insert_ignore"),
    ("hist_jmm", ["trade_date"], "insert_ignore"),
    ("hist_lcm", ["trade_date"], "insert_ignore"),
    ("hist_lfm", ["trade_date"], "insert_ignore"),
    ("hist_lgm", ["trade_date"], "insert_ignore"),
    ("hist_lhm", ["trade_date"], "insert_ignore"),
    ("hist_lm", ["trade_date"], "insert_ignore"),
    ("hist_lum", ["trade_date"], "insert_ignore"),
    ("hist_mam", ["trade_date"], "insert_ignore"),
    ("hist_mm", ["trade_date"], "insert_ignore"),
    ("hist_nim", ["trade_date"], "insert_ignore"),
    ("hist_nrm", ["trade_date"], "insert_ignore"),
    ("hist_oim", ["trade_date"], "insert_ignore"),
    ("hist_opm", ["trade_date"], "insert_ignore"),
    ("hist_pbm", ["trade_date"], "insert_ignore"),
    ("hist_pfm", ["trade_date"], "insert_ignore"),
    ("hist_pgm", ["trade_date"], "insert_ignore"),
    ("hist_pkm", ["trade_date"], "insert_ignore"),
    ("hist_pm", ["trade_date"], "insert_ignore"),
    ("hist_ppfm", ["trade_date"], "insert_ignore"),
    ("hist_ppm", ["trade_date"], "insert_ignore"),
    ("hist_prm", ["trade_date"], "insert_ignore"),
    ("hist_psm", ["trade_date"], "insert_ignore"),
    ("hist_pxm", ["trade_date"], "insert_ignore"),
    ("hist_rbm", ["trade_date"], "insert_ignore"),
    ("hist_rmm", ["trade_date"], "insert_ignore"),
    ("hist_rrm", ["trade_date"], "insert_ignore"),
    ("hist_rsm", ["trade_date"], "insert_ignore"),
    ("hist_rum", ["trade_date"], "insert_ignore"),
    ("hist_sam", ["trade_date"], "insert_ignore"),
    ("hist_scm", ["trade_date"], "insert_ignore"),
    ("hist_sfm", ["trade_date"], "insert_ignore"),
    ("hist_shm", ["trade_date"], "insert_ignore"),
    ("hist_sim", ["trade_date"], "insert_ignore"),
    ("hist_smm", ["trade_date"], "insert_ignore"),
    ("hist_snm", ["trade_date"], "insert_ignore"),
    ("hist_spm", ["trade_date"], "insert_ignore"),
    ("hist_srm", ["trade_date"], "insert_ignore"),
    ("hist_ssm", ["trade_date"], "insert_ignore"),
    ("hist_tam", ["trade_date"], "insert_ignore"),
    ("hist_tfm", ["trade_date"], "insert_ignore"),
    ("hist_tlm", ["trade_date"], "insert_ignore"),
    ("hist_tm", ["trade_date"], "insert_ignore"),
    ("hist_tsm", ["trade_date"], "insert_ignore"),
    ("hist_urm", ["trade_date"], "insert_ignore"),
    ("hist_vfm", ["trade_date"], "insert_ignore"),
    ("hist_vm", ["trade_date"], "insert_ignore"),
    ("hist_wrm", ["trade_date"], "insert_ignore"),
    ("hist_ym", ["trade_date"], "insert_ignore"),
    ("hist_znm", ["trade_date"], "insert_ignore"),

    # ========== 业务表 ==========
    ("fut_daily_close", ["variety_id", "trade_date"], "insert_ignore"),
    ("fut_strength", ["id"], "insert_ignore"),
    ("news_red_telegraph", ["id"], "insert_ignore"),
    ("news_process_tracking", ["id"], "insert_ignore"),
    ("futures_events", ["id"], "insert_ignore"),
    ("trading_signals", ["id"], "insert_ignore"),
    ("trading_account_daily", ["id"], "insert_ignore"),
    ("trading_operations", ["id"], "insert_ignore"),
    ("trading_positions", ["id"], "insert_ignore"),
]

LOG_FILE = "/Users/zxxk/ysd/ysdproject/workstation/temp/sync_log.txt"


def log(msg):
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def get_connection(cfg):
    return pymysql.connect(**cfg)


def get_columns(cur, table):
    """获取表的所有列名"""
    cur.execute(f"DESCRIBE `{table}`")
    return [row[0] for row in cur.fetchall()]


def sync_table_insert_ignore(table, pk_cols):
    """策略1: INSERT IGNORE - 从腾讯云查询所有数据，逐批插入阿里云
    自动处理两库列不一致的情况（只取公共列）
    """
    tc_conn = get_connection(TENCENT_CONFIG)
    ali_conn = get_connection(ALI_CONFIG)
    tc_cur = tc_conn.cursor()
    ali_cur = ali_conn.cursor()

    try:
        # 获取两边的列，取交集
        ali_cols = get_columns(ali_cur, table)
        tc_cols = get_columns(tc_cur, table)
        common_cols = [c for c in ali_cols if c in tc_cols]

        if len(common_cols) < len(ali_cols):
            missing = set(ali_cols) - set(common_cols)
            log(f"  [WARN] 阿里云有 {len(ali_cols)} 列，腾讯云有 {len(tc_cols)} 列，取交集 {len(common_cols)} 列")
            log(f"  [WARN] 阿里云多出的列（将使用默认值）: {missing}")

        col_list = ", ".join(f"`{c}`" for c in common_cols)
        placeholders = ", ".join(["%s"] * len(common_cols))

        # 获取阿里云已有的主键集合
        pk_col_list = ", ".join(f"`{c}`" for c in pk_cols)
        if pk_cols:
            ali_cur.execute(f"SELECT {pk_col_list} FROM `{table}`")
            existing_pks = set(tuple(row) for row in ali_cur.fetchall())
        else:
            existing_pks = set()
        log(f"  [PK] 阿里云已有 {len(existing_pks)} 个主键")

        # 从腾讯云读取数据（只取公共列）
        select_cols = ", ".join(f"`{c}`" for c in common_cols)
        tc_cur.execute(f"SELECT {select_cols} FROM `{table}`")
        tc_rows = tc_cur.fetchall()
        log(f"  [TC] 腾讯云共 {len(tc_rows)} 行")

        # 筛选阿里云缺失的行
        missing = []
        for row in tc_rows:
            pk = tuple(row[common_cols.index(c)] for c in pk_cols)
            if pk not in existing_pks:
                missing.append(row)

        if not missing:
            log(f"  [OK] 无需同步")
            return

        log(f"  [SYNC] 需同步 {len(missing)} 行")

        # 分批插入（每批 500 行）
        BATCH = 500
        inserted = 0
        for i in range(0, len(missing), BATCH):
            batch = missing[i:i + BATCH]
            values_clause = ", ".join([f"({placeholders})" for _ in batch])
            flat_values = [val for row in batch for val in row]
            sql = f"INSERT IGNORE INTO `{table}` ({col_list}) VALUES {values_clause}"
            ali_cur.execute(sql, flat_values)
            ali_conn.commit()
            inserted += ali_cur.rowcount
            log(f"  [BATCH] {i // BATCH + 1}/{(len(missing) - 1) // BATCH + 1} 已写入 {ali_cur.rowcount} 行")

        log(f"  [DONE] {table}: 共写入 {inserted} 行")

    except Exception as e:
        ali_conn.rollback()
        log(f"  [ERROR] {table}: {e}")
        raise
    finally:
        tc_cur.close()
        tc_conn.close()
        ali_cur.close()
        ali_conn.close()


def get_hist_tables_from_db():
    """从阿里云获取所有 hist_ 开头的表"""
    conn = get_connection(ALI_CONFIG)
    cur = conn.cursor()
    cur.execute("SHOW TABLES LIKE 'hist\\_%'")
    tables = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return sorted(tables)


def main():
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write(f"增量同步日志 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 60 + "\n")

    log("开始同步...\n")

    total_start = datetime.now()

    # 先同步业务表（非 hist_ 表）
    biz_tables = [(t, p, s) for t, p, s in TABLES_TO_SYNC if not t.startswith("hist_")]
    hist_tables = [(t, p, s) for t, p, s in TABLES_TO_SYNC if t.startswith("hist_")]

    log(f"--- 业务表（共 {len(biz_tables)} 张）---")
    for table, pk_cols, strategy in biz_tables:
        log(f"\n>>> 同步 {table} ...")
        try:
            sync_table_insert_ignore(table, pk_cols)
        except Exception as e:
            log(f"  !! 跳过 {table}: {e}")
            continue

    log(f"\n--- 历史行情表（共 {len(hist_tables)} 张）---")
    for table, pk_cols, strategy in hist_tables:
        log(f"\n>>> 同步 {table} ...")
        try:
            sync_table_insert_ignore(table, pk_cols)
        except Exception as e:
            log(f"  !! 跳过 {table}: {e}")
            continue

    elapsed = (datetime.now() - total_start).total_seconds()
    log(f"\n{'=' * 60}")
    log(f"同步完成！总耗时 {elapsed:.1f} 秒")
    log(f"日志已保存: {LOG_FILE}")


if __name__ == "__main__":
    main()