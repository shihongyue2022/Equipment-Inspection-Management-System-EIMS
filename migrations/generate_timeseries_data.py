# -*- coding: utf-8 -*-
"""
時系列点検記録データ大量生成スクリプト（統合劣化スコアモデル）

===================================================================
【解析モデル】

  d(t+1) = d(t) + δ_age · α_bathtub(age) + δ_season(month) + ε(t)
                - Δ_maint(on inspection days)

  α_bathtub(age):
    初期故障期（0〜1年）: α > 1.0  ← 試運転・初期不安定
    安定期（1〜stable_years）: α = 0.5〜0.9 ← 最も安定
    摩耗期（stable_years〜）: Weibull型で指数加速  ← 経年劣化

  δ_season:
    冷却系設備の夏（7〜9月）: +40%追加劣化
    冬季（12〜2月）: +25%追加劣化
    ポンプ系の梅雨・台風期（6〜9月）: +15%追加

  ε(t): 正規分布ノイズ。0.1%確率で突発スパイク（機器破損等）

  Δ_maint（不完全修理モデル）:
    repair: d = d × (1 - restore_rate)  ← 劣化の多くを解消するが残留疲労が残る
    watch:  d -= inspect_restore × 2.5  ← 部分的な調整・清掃
    normal: d -= inspect_restore        ← フィルター清掃等の予防保全

  ステータス判定（d の閾値）:
    d < 0.40 → 'normal'
    0.40 ≤ d < 0.72 → 'watch'
    d ≥ 0.72 → 'repair'

【統合モデルの特徴】
  - 設備ごとに1つのモデルインスタンスで全記録を生成する
  - 定期点検日に Δ_maint が適用されるので、その後の日次記録も改善される
  - 若い設備はほぼ normal、老朽設備は watch/repair が増える自然な傾向が出る

【期待分布】
  全体: normal 70〜80%、watch 18〜27%、repair 2〜5%
  精密設備（日次）: normal 65%、watch 33%、repair 2%（高頻度なので検出が多い）
  標準設備: normal 80%、watch 17%、repair 3%

実行方法:
  python migrations/generate_timeseries_data.py
===================================================================
"""

import pymysql
import random
from datetime import date, timedelta

# ==============================================================
# グローバル設定
# ==============================================================

DB_CONFIG = {
    'host':     'localhost',
    'port':     3307,
    'user':     'root',
    'password': 'rootpass',
    'database': 'inspection_db',
    'charset':  'utf8mb4',
}

TODAY            = date(2026, 6, 22)
MONITORING_START = date(2018, 1,  1)
OUTPUT_FILE      = 'migrations/timeseries_inspection_data.sql'
BATCH_SIZE       = 1000

# 日次モニタリング対象
DAILY_TYPES  = frozenset({'精密空調', 'クリーンルーム空調', '冷凍冷却装置', '冷却装置', '医療用空調'})
# 週次モニタリング対象
WEEKLY_TYPES = frozenset({'受変電設備', '地域冷暖房'})
# 夏季に高負荷の冷却系設備
COOLING_TYPES = frozenset({
    '精密空調', 'クリーンルーム空調', '冷凍冷却装置', '冷却装置',
    '医療用空調', '空調機（冷房）', '空調機（冷暖）', '全館空調', '大型空調機',
})
PUMP_TYPES = frozenset({'給排水ポンプ', '消防ポンプ'})

# ステータス判定閾値
#   0.00〜0.60: normal（許容範囲内の経年劣化）
#   0.60〜0.80: watch（要経過観察・点検頻度増加を検討）
#   0.80〜1.00: repair（安全性・性能に問題あり、要修理）
THRESH_WATCH  = 0.60   # d ≥ この値で watch
THRESH_REPAIR = 0.80   # d ≥ この値で repair

# ==============================================================
# 拠点別エンジニアIDマッピング
# ==============================================================

BASE_ENGINEERS = {
    'tokyo':    [3,4,5,8,9,11,12,13,14,15,
                 26,27,28,29,30,31,32,33,34,35,
                 36,37,38,39,40,41,42,43,44,45,
                 46,47,48,49,50,51,52,53,54,55],
    'osaka':    [6,16,17,18,19,20,
                 56,57,58,59,60,61,62,63,64,65,66,67,68,69,70],
    'nagoya':   [7,21,22,23,24,25,
                 71,72,73,74,75,76,77,78,79,80,81,82,83,84,85],
    'fukuoka':  [86,87,88,89,90,91,92,93],
    'sendai':   [94,95,96,97],
    'yokohama': [98,99,100],
}

def base_of(eq_id):
    if   1   <= eq_id <= 120: return 'tokyo'
    elif 121 <= eq_id <= 183: return 'osaka'
    elif 184 <= eq_id <= 246: return 'nagoya'
    elif 247 <= eq_id <= 270: return 'fukuoka'
    elif 271 <= eq_id <= 282: return 'sendai'
    elif 283 <= eq_id <= 291: return 'yokohama'
    return 'tokyo'

def pick_eng(assigned_uid, base_name):
    """80%は担当エンジニア、20%は同拠点の同僚を選ぶ"""
    pool = BASE_ENGINEERS[base_name]
    if assigned_uid and random.random() < 0.80:
        return assigned_uid
    return random.choice(pool)

# ==============================================================
# 設備タイプ別劣化パラメータ
# ==============================================================
#   base_rate      : 1日あたりの基本劣化量（小さくすることで分布を現実的に保つ）
#   weibull_shape  : 摩耗期の加速指数（バスタブ曲線の右裾）
#   stable_years   : 安定期の長さ（年）
#   repair_restore : 修理後のスコア削減率（不完全修理モデル）
#   inspect_restore: 通常点検後の微小改善量

TYPE_PARAMS = {
    # base_rate : 1日あたり劣化量（↑ほど劣化が速い）
    # inspect_restore: 通常点検で改善される量（< 月次buildup で常にd↑）
    #   watch_inspect = inspect_restore × 2.5 が月次buildupを上回ると
    #   watch領域でスコアが下降（THRESH_WATCH付近で振動）→ 現実的な分布に
    # 設計目標: normal≈70%, watch≈25%, repair≈5%
    '精密空調':           {'base_rate': 0.000840, 'weibull_shape': 2.5, 'stable_years': 6.0,  'repair_restore': 0.65, 'inspect_restore': 0.010},
    'クリーンルーム空調': {'base_rate': 0.000760, 'weibull_shape': 2.5, 'stable_years': 7.0,  'repair_restore': 0.70, 'inspect_restore': 0.010},
    '冷凍冷却装置':       {'base_rate': 0.000800, 'weibull_shape': 2.2, 'stable_years': 7.0,  'repair_restore': 0.62, 'inspect_restore': 0.010},
    '冷却装置':           {'base_rate': 0.000760, 'weibull_shape': 2.0, 'stable_years': 8.0,  'repair_restore': 0.60, 'inspect_restore': 0.010},
    '医療用空調':         {'base_rate': 0.000720, 'weibull_shape': 2.5, 'stable_years': 8.0,  'repair_restore': 0.72, 'inspect_restore': 0.010},
    '受変電設備':         {'base_rate': 0.000600, 'weibull_shape': 3.0, 'stable_years': 12.0, 'repair_restore': 0.55, 'inspect_restore': 0.010},
    '地域冷暖房':         {'base_rate': 0.000680, 'weibull_shape': 2.0, 'stable_years': 10.0, 'repair_restore': 0.58, 'inspect_restore': 0.010},
    '空調機（冷房）':     {'base_rate': 0.000660, 'weibull_shape': 2.0, 'stable_years': 8.0,  'repair_restore': 0.60, 'inspect_restore': 0.010},
    '空調機（冷暖）':     {'base_rate': 0.000660, 'weibull_shape': 2.0, 'stable_years': 8.0,  'repair_restore': 0.60, 'inspect_restore': 0.010},
    '全館空調':           {'base_rate': 0.000620, 'weibull_shape': 1.8, 'stable_years': 9.0,  'repair_restore': 0.58, 'inspect_restore': 0.010},
    '大型空調機':         {'base_rate': 0.000700, 'weibull_shape': 2.2, 'stable_years': 8.0,  'repair_restore': 0.62, 'inspect_restore': 0.010},
    'ボイラー':           {'base_rate': 0.000740, 'weibull_shape': 2.5, 'stable_years': 7.0,  'repair_restore': 0.65, 'inspect_restore': 0.010},
    '換気設備':           {'base_rate': 0.000520, 'weibull_shape': 1.8, 'stable_years': 10.0, 'repair_restore': 0.55, 'inspect_restore': 0.010},
    '消防ポンプ':         {'base_rate': 0.000480, 'weibull_shape': 1.5, 'stable_years': 12.0, 'repair_restore': 0.55, 'inspect_restore': 0.010},
    '給排水ポンプ':       {'base_rate': 0.000560, 'weibull_shape': 2.0, 'stable_years': 10.0, 'repair_restore': 0.58, 'inspect_restore': 0.010},
}
DEFAULT_PARAMS = {
    'base_rate': 0.000640, 'weibull_shape': 2.0, 'stable_years': 9.0,
    'repair_restore': 0.60, 'inspect_restore': 0.010,
}

# ==============================================================
# 劣化スコアモデルクラス
# ==============================================================

class DegradationModel:
    """
    設備劣化スコアモデル。
    バスタブ曲線（初期故障→安定期→摩耗期）+ 季節負荷 + 突発スパイク + 不完全修理。
    """

    def __init__(self, eq_type, installed_at):
        self.p         = TYPE_PARAMS.get(eq_type, DEFAULT_PARAMS)
        self.eq_type   = eq_type
        self.installed = installed_at
        # 製造バラつきを模擬した初期スコア（0.02〜0.12程度）
        self.d = max(0.02, min(0.12, 0.05 + abs(random.gauss(0, 0.03))))

    def alpha_bathtub(self, age_years):
        """
        バスタブ曲線の加速係数。
          初期故障期（0〜1年）:  1.8 → 0.8 に線形減少
          安定期（1〜stable_years）: 0.6 → 0.9 に緩やかに増加
          摩耗期（stable_years〜）: Weibull加速
        """
        p = self.p
        if age_years < 0.5:
            return 1.8 - age_years * 2.0          # 1.8 → 0.8
        if age_years < 1.0:
            return 0.8 - (age_years - 0.5) * 0.4  # 0.8 → 0.6
        if age_years < p['stable_years']:
            t = (age_years - 1.0) / (p['stable_years'] - 1.0)
            return 0.6 + t * 0.3                   # 0.6 → 0.9
        else:
            # 摩耗期: Weibull型加速 (比較的穏やか)
            wear_y = age_years - p['stable_years']
            scale  = 6.0
            shape  = p['weibull_shape']
            w_rate = (shape / scale) * (max(wear_y, 0.01) / scale) ** (shape - 1)
            return 0.9 + w_rate * 0.6              # 最大で 1.5〜2.0 程度

    def delta_season(self, d):
        """季節による追加劣化量"""
        m    = d.month
        base = self.p['base_rate']
        if self.eq_type in COOLING_TYPES and m in (7, 8, 9):
            return base * 0.40   # 冷却系の夏季高負荷
        if self.eq_type in COOLING_TYPES and m in (6, 10):
            return base * 0.15
        if self.eq_type == 'ボイラー' and m in (12, 1, 2):
            return base * 0.35
        if self.eq_type in PUMP_TYPES and m in (6, 7, 8, 9):
            return base * 0.15
        return 0.0

    def epsilon(self):
        """確率的ノイズ（突発スパイク含む）"""
        if random.random() < 0.001:
            return abs(random.gauss(0.15, 0.04))   # 突発故障スパイク（0.1%）
        return random.gauss(0, self.p['base_rate'] * 0.50)

    def step(self, current_date):
        """1日分の劣化スコアを更新する"""
        age   = (current_date - self.installed).days / 365.0
        alpha = self.alpha_bathtub(age)
        delta = self.p['base_rate'] * alpha + self.delta_season(current_date) + self.epsilon()
        self.d = max(0.0, min(1.0, self.d + delta))
        return self.d

    def apply_maintenance(self, status):
        """点検・修理の効果を劣化スコアに反映する（不完全修理モデル）"""
        p = self.p
        if status == 'repair':
            self.d = max(0.04, self.d * (1.0 - p['repair_restore']))
        elif status == 'watch':
            self.d = max(0.0, self.d - p['inspect_restore'] * 2.5)
        else:
            self.d = max(0.0, self.d - p['inspect_restore'])

    def status(self, clamp_repair=False):
        """劣化スコアからステータスを返す。clamp_repair=True で repair を watch にクランプ"""
        if self.d >= THRESH_REPAIR and not clamp_repair:
            return 'repair'
        if self.d >= THRESH_WATCH:
            return 'watch'
        return 'normal'

# ==============================================================
# メモプール
# ==============================================================

NOTES = {
    'dn': [
        '通常稼働中。異常なし。',          '設定温度到達。動作良好。',
        '稼働状況確認。正常。',            '日常点検完了。問題なし。',
        '運転音・振動ともに正常範囲内。',  '冷媒圧力・温度ともに正常。',
        '電流値正常。稼働継続。',          '排水・ドレン確認。異常なし。',
        '温度・湿度設定値通り。問題なし。', '冷却水温度正常。循環良好。',
        'フィルター差圧正常。風量良好。',  '設定値内で安定稼働中。',
        '各部目視点検。異常なし。',        '運転電流・電圧値正常。',
    ],
    'dw': [
        '温度が設定値より+2℃高め。継続監視。',
        '圧力がやや上昇傾向。次回確認要。',
        '振動音がわずかに増加。要観察。',
        '電流値が基準上限に近い。過負荷注意。',
        '冷媒圧力やや低下。継続監視中。',
        '設定温度に達しない傾向あり。フィルター確認要。',
        '排水量がやや増加傾向。原因調査中。',
        '運転音がいつもより大きめ。注意して観察継続。',
    ],
    'fn': [
        'フィルター清掃済。冷媒圧力正常。',
        '定期点検完了。各部正常。',
        '各部目視点検。腐食なし。正常。',
        'ベルト張力確認OK。グリースアップ実施。',
        '冷却水水質確認OK。基準値内。',
        '試運転・負荷テスト実施。異常なし。',
        '全体清掃・点検完了。動作良好。',
        '電気系統チェック。絶縁抵抗正常。',
        '潤滑油補充。各回転部正常動作確認。',
        '安全弁・圧力計動作確認。正常範囲内。',
        'エアフィルター交換実施。動作良好。',
        '冷媒量・油量チェック。全て正常。',
        'ファンベルト・プーリー確認。異常なし。',
        'ドレンパン清掃済み。水漏れなし。',
        '清掃・注油実施。次回点検予定通り。',
        '各電気接続部の締め付け確認。問題なし。',
        '熱交換器清掃完了。効率確認済み。',
        'フィン清掃実施。熱交換効率改善。正常稼働中。',
        '定期点検完了。冷媒量・圧力ともに正常範囲内。',
        'HEPAフィルター差圧確認OK。清浄度基準内。',
        '精密温度制御確認。加湿器フィルター清掃。',
        '電流値・電圧値確認。正常稼働中。',
        '絶縁抵抗測定実施。正常値確認。稼働継続。',
        'ドレン配管清掃実施。詰まりなし。',
        '各ダンパー開閉確認。動作良好。',
    ],
    'fw': [
        '振動音が若干増加。次回点検で継続確認要。異常には至らず。',
        'フィルター目詰まり傾向。次回交換推奨。動作は正常範囲内。',
        'パッキン劣化傾向。次回交換検討。',
        '冷媒圧力やや低下。次回要確認。',
        '外装に錆発生（軽微）。経過観察。',
        'ベルトわずかに摩耗。経過観察。',
        '冷却水pH値が基準上限に近い。調整要。',
        '電流値がやや高め。過負荷に注意。',
        '冷却効率が若干低下傾向。継続監視。',
        '排水口に汚れ蓄積。次回清掃要。',
        '加湿エレメントの劣化傾向あり。次回に交換推奨。動作は正常範囲内。',
        '冷媒量がやや減少傾向。次回補充検討。',
    ],
    'fr': [
        '熱交換器亀裂確認。緊急修理実施。',
        'ベルト摩耗を確認。部品発注済み。交換予定。',
        'ドレンポンプ故障。水漏れ発生。修理中。',
        '制御基板故障。メーカーサポート対応中。',
        '安全弁作動。圧力異常。緊急停止実施。',
        '電気系統異常。専門業者対応中。',
        'ポンプ異常停止。原因調査中。',
        'コンプレッサー異常音確認。部品交換実施。',
        '冷媒漏れ確認。緊急修理実施。補充後正常稼働へ。',
        'モーター過熱確認。冷却ファン交換実施。',
    ],
    'fuw': [
        '前回watchのフォロー点検。改善傾向あり。継続監視。',
        '前回watchの確認点検。現状維持。引き続き経過観察。',
        'フォローアップ点検。部品交換後、安定稼働中。',
        '修理後確認点検。正常稼働中。次回定期点検まで継続監視。',
    ],
    'fur': [
        '修理完了確認点検。正常稼働に復帰。',
        '緊急修理後の確認点検。復旧確認。部品動作正常。',
        '修理後継続確認点検。引き続き週次確認継続。',
        '専門業者修理後の確認。問題なし。通常運転再開。',
    ],
}

def pick_note(key):
    return random.choice(NOTES[key])

# ==============================================================
# 統合レコード生成関数（設備ごとに1つのモデルで全記録を生成）
# ==============================================================

def gen_equipment_records(eq_id, uid, base, eq_type, installed, interval_months):
    """
    劣化スコアモデルを使って設備1台の全点検記録を生成する。

    1日ずつ d を更新し:
      - 定期点検日: formal 記録を追加 → apply_maintenance → 次の点検日を計算
      - フォロー点検日: followup 記録を追加 → apply_maintenance
      - 日次モニタリング対象: その日の d からステータスを判定して記録
      - 週次モニタリング対象: 7日ごとに記録

    すべて同じ DegradationModel インスタンスを使うため、
    定期点検による改善が日次/週次モニタリング記録にも自然に反映される。
    """

    is_daily  = eq_type in DAILY_TYPES
    is_weekly = eq_type in WEEKLY_TYPES

    model = DegradationModel(eq_type, installed)
    recs  = []

    def jitter_days(months):
        return max(7, months * 30 + random.randint(-7, 7))

    # 次の定期点検日、フォロー点検日のセット
    next_formal_d   = installed + timedelta(days=jitter_days(interval_months))
    followup_dates  = set()
    weekly_counter  = 0

    d = installed

    while d <= TODAY:
        model.step(d)  # 1日分の劣化を進める

        if d >= next_formal_d:
            # ---- 定期点検日 ----
            st    = model.status()
            n_key = {'normal': 'fn', 'watch': 'fw', 'repair': 'fr'}[st]
            recs.append((eq_id, pick_eng(uid, base), d.isoformat(), st, pick_note(n_key)))
            model.apply_maintenance(st)

            # watchフォロー点検を予約（60%）
            if st == 'watch' and random.random() < 0.60:
                fu_d = d + timedelta(weeks=2)
                if fu_d <= TODAY:
                    followup_dates.add(fu_d)

            # repairフォロー点検を予約（週次、2〜4回）
            if st == 'repair':
                for w in range(1, random.randint(2, 4) + 1):
                    fu_d = d + timedelta(weeks=w)
                    if fu_d <= TODAY:
                        followup_dates.add(fu_d)

            next_formal_d = d + timedelta(days=jitter_days(interval_months))

        elif d in followup_dates:
            # ---- フォロー点検日 ----
            st    = model.status()
            n_key = 'fur' if st == 'normal' else 'fuw'
            recs.append((eq_id, pick_eng(uid, base), d.isoformat(), st, pick_note(n_key)))
            model.apply_maintenance(st)

        elif is_daily and d >= MONITORING_START:
            # ---- 日次モニタリング（精密設備） ----
            # 日次チェックでは repair レベルでも watch として記録する
            # （モニタリングシステムは警告を出すが即停止はしない想定）
            st = model.status(clamp_repair=True)
            n  = pick_note('dn') if st == 'normal' else pick_note('dw')
            recs.append((eq_id, pick_eng(uid, base), d.isoformat(), st, n))

        elif is_weekly and d >= MONITORING_START:
            # ---- 週次モニタリング（受変電設備・地域冷暖房） ----
            weekly_counter += 1
            if weekly_counter % 7 == 0:
                st = model.status(clamp_repair=True)
                n  = pick_note('dn') if st == 'normal' else pick_note('dw')
                recs.append((eq_id, pick_eng(uid, base), d.isoformat(), st, n))

        d += timedelta(days=1)

    return recs

# ==============================================================
# メイン処理
# ==============================================================

def main():
    random.seed(42)  # 再現可能な乱数シード

    conn = pymysql.connect(**DB_CONFIG)
    cur  = conn.cursor(pymysql.cursors.DictCursor)
    cur.execute("""
        SELECT id, equipment_type, installed_at,
               inspection_interval_months, assigned_user_id
        FROM equipment WHERE deleted_at IS NULL ORDER BY id
    """)
    equipment_list = cur.fetchall()
    cur.close()
    conn.close()

    print(f"設備数: {len(equipment_list)} 件")

    all_records = []

    for i, eq in enumerate(equipment_list, 1):
        recs = gen_equipment_records(
            eq_id          = eq['id'],
            uid            = eq['assigned_user_id'],
            base           = base_of(eq['id']),
            eq_type        = eq['equipment_type'],
            installed      = eq['installed_at'],
            interval_months = eq['inspection_interval_months'],
        )
        all_records.extend(recs)

        if i % 50 == 0 or i == len(equipment_list):
            print(f"  [{i:3d}/{len(equipment_list)}] 累計 {len(all_records):,} 件")

    current_count = 5536
    print(f"\n生成完了: {len(all_records):,} 件（現在の約 {len(all_records) // current_count} 倍）")

    # 設備ID → 日付でソート（時系列分析向け）
    print("ソート中...")
    all_records.sort(key=lambda r: (r[0], r[2]))

    print(f"SQL書き込み中: {OUTPUT_FILE}")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("-- ============================================================\n")
        f.write(f"-- 時系列点検記録データ（統合劣化スコアモデル）\n")
        f.write(f"-- 合計: {len(all_records):,} 件 / 設備数: {len(equipment_list)} 件\n")
        f.write("-- モデル: バスタブ曲線 + 季節負荷 + 突発スパイク + 不完全修理\n")
        f.write("-- ============================================================\n")
        f.write("SET NAMES utf8mb4;\n")
        f.write("SET FOREIGN_KEY_CHECKS = 0;\n\n")
        f.write("DELETE FROM inspection_records;\n\n")

        total_batches = (len(all_records) + BATCH_SIZE - 1) // BATCH_SIZE
        for batch_no, i in enumerate(range(0, len(all_records), BATCH_SIZE), 1):
            batch = all_records[i:i + BATCH_SIZE]
            vals  = []
            for (eq_id, eng_id, insp_at, status, n_text) in batch:
                vals.append(
                    f"({eq_id},{eng_id},'{insp_at}','{status}','{n_text.replace(chr(39), chr(92)+chr(39))}')"
                )
            f.write(
                "INSERT INTO inspection_records"
                "(equipment_id,engineer_id,inspected_at,status,note) VALUES\n"
            )
            f.write(",\n".join(vals))
            f.write(";\n\n")
            if batch_no % 100 == 0:
                print(f"  バッチ {batch_no}/{total_batches} 書き込み完了...")

        # next_inspection_date を最終点検日＋インターバルで更新する
        f.write("-- next_inspection_date を実際の最終点検日から再計算する\n")
        f.write("""UPDATE equipment e
JOIN (
    SELECT equipment_id, MAX(inspected_at) AS last_date
    FROM inspection_records
    GROUP BY equipment_id
) latest ON e.id = latest.equipment_id
SET e.next_inspection_date = DATE_ADD(
    latest.last_date,
    INTERVAL e.inspection_interval_months MONTH
)
WHERE e.deleted_at IS NULL;\n\n""")
        f.write("SET FOREIGN_KEY_CHECKS = 1;\n-- 完了\n")

    import os
    size_mb = os.path.getsize(OUTPUT_FILE) / 1024 / 1024
    print(f"\n出力完了: {OUTPUT_FILE} ({size_mb:.1f} MB)")

    # ステータス分布を表示する
    cnt = {'normal': 0, 'watch': 0, 'repair': 0}
    for r in all_records:
        cnt[r[3]] += 1
    total = len(all_records)
    print("\n=== ステータス分布 ===")
    for st in ('normal', 'watch', 'repair'):
        print(f"  {st:8s}: {cnt[st]:8,} 件 ({cnt[st]/total*100:.1f}%)")


if __name__ == '__main__':
    main()
