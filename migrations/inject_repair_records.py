# -*- coding: utf-8 -*-
"""
MTBR算出用の修理記録を複数設備に追加するスクリプト。
対象：repair件数が0〜1件の設備（interval_months >= 2）。
各設備に2〜3件の修理記録を、既存レコードの間隔に収まる形で挿入する。
"""

import pymysql
from datetime import date, timedelta
import random

random.seed(99)

DB_CONFIG = {
    'host':     'localhost',
    'port':     3307,
    'user':     'root',
    'password': 'rootpass',
    'database': 'inspection_db',
    'charset':  'utf8mb4',
}

REPAIR_NOTES = [
    '熱交換器に亀裂確認。緊急修理実施。部品交換後正常稼働に復帰。',
    'コンプレッサー異常音確認。専門業者対応。部品交換実施済み。',
    '冷媒漏れ確認。緊急修理実施。補充後正常稼働確認。',
    '電気系統異常発生。絶縁不良箇所を特定し修理。正常復帰確認。',
    'ドレンポンプ故障。交換対応済み。正常稼働に復帰。',
    'ベルト摩耗による異常停止。交換対応済み。',
    '制御基板故障。メーカー対応にて修理完了。正常稼働確認。',
    'モーター過熱。冷却ファン交換で正常復帰。',
]

def find_insertable_dates(dates_sorted, min_gap, num_inserts, start, end):
    """
    既存レコードの間隔を考慮して、新規挿入可能な日付リストを返す。
    既存日付から min_gap 以上離れた位置に挿入する。
    """
    result = []
    all_dates = sorted(dates_sorted)

    for i in range(len(all_dates) - 1):
        d_prev = all_dates[i]
        d_next = all_dates[i + 1]
        gap = (d_next - d_prev).days

        # 前後ともに min_gap 以上離れた位置があるか確認
        earliest = d_prev + timedelta(days=min_gap)
        latest   = d_next - timedelta(days=min_gap)

        if earliest <= latest and start <= earliest <= end:
            # この区間の中央付近を使う
            mid = earliest + timedelta(days=(latest - earliest).days // 2)
            if mid not in all_dates:
                result.append(mid)
                all_dates.append(mid)
                all_dates.sort()
                if len(result) >= num_inserts:
                    break

    return result


def main():
    conn = pymysql.connect(**DB_CONFIG)
    cur  = conn.cursor()

    # 対象設備の取得
    cur.execute('''
        SELECT e.id, e.inspection_interval_months, e.assigned_user_id,
               SUM(ir.status = "repair") AS repairs
        FROM equipment e
        JOIN inspection_records ir ON ir.equipment_id = e.id
        WHERE e.deleted_at IS NULL AND e.inspection_interval_months >= 2
        GROUP BY e.id
        HAVING repairs <= 1 AND COUNT(ir.id) >= 10
        ORDER BY e.inspection_interval_months DESC, e.id
        LIMIT 20
    ''')
    targets = cur.fetchall()
    print(f'対象設備: {len(targets)} 件')

    total_inserted = 0

    for (eq_id, interval_months, engineer_id, current_repairs) in targets:
        # 既存の点検日を取得
        cur.execute(
            'SELECT inspected_at FROM inspection_records WHERE equipment_id=%s ORDER BY inspected_at',
            (eq_id,)
        )
        existing_dates = [row[0] for row in cur.fetchall()]
        if not existing_dates:
            continue

        min_gap   = max(14, round(interval_months * 30 * 0.4))
        # 既存修理が1件ならあと2件、0件なら3件追加する
        need      = 3 - int(current_repairs)
        start_d   = existing_dates[0] + timedelta(days=min_gap)
        end_d     = date(2026, 1, 1)

        insert_dates = find_insertable_dates(existing_dates, min_gap, need, start_d, end_d)

        for d in insert_dates:
            note = random.choice(REPAIR_NOTES)
            cur.execute(
                '''INSERT INTO inspection_records
                   (equipment_id, engineer_id, inspected_at, expected_inspection_date, status, note)
                   VALUES (%s, %s, %s, NULL, "repair", %s)''',
                (eq_id, engineer_id, d.isoformat(), note)
            )
            total_inserted += 1
            print(f'  設備{eq_id}: {d} に repair 追加')

    conn.commit()
    print(f'\n完了: {total_inserted} 件挿入')
    conn.close()


if __name__ == '__main__':
    main()
