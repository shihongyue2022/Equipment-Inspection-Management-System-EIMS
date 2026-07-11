# -*- coding: utf-8 -*-
"""
拠点別データ整理スクリプト
設備の担当者を同一拠点のエンジニアに再割り当てし、
ロケーション名に地域識別子を付与するUPDAL SQLを生成する。
"""

# ============================================================
# エンジニアIDと拠点の対応
# ============================================================
TOKYO   = [3, 4, 5, 8, 9, 11, 12, 13, 14, 15,
            26, 27, 28, 29, 30, 31, 32, 33, 34, 35,
            36, 37, 38, 39, 40, 41, 42, 43, 44, 45,
            46, 47, 48, 49, 50, 51, 52, 53, 54, 55]   # 40名

OSAKA   = [6, 16, 17, 18, 19, 20,
            56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70]  # 21名

NAGOYA  = [7, 21, 22, 23, 24, 25,
            71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85]  # 21名

FUKUOKA = [86, 87, 88, 89, 90, 91, 92, 93]   # 8名
SENDAI  = [94, 95, 96, 97]                    # 4名
YOKOHAMA = [98, 99, 100]                      # 3名

# ============================================================
# 設備IDを拠点ごとに割り当て（合計300件）
# 東京:120 大阪:63 名古屋:63 福岡:24 仙台:12 横浜:9 未割当:9
# ============================================================
TOKYO_EQ    = list(range(1,   121))   # 120件
OSAKA_EQ    = list(range(121, 184))   #  63件
NAGOYA_EQ   = list(range(184, 247))   #  63件
FUKUOKA_EQ  = list(range(247, 271))   #  24件
SENDAI_EQ   = list(range(271, 283))   #  12件
YOKOHAMA_EQ = list(range(283, 292))   #   9件
NONE_EQ     = list(range(292, 301))   #   9件（未割当）

# ============================================================
# 拠点別ロケーション名（建物名）
# 担当設備の場所名として使用する
# ============================================================
TOKYO_BUILDINGS = [
    "東京電力エナジーパートナー 本店ビル",
    "三菱商事 大手町本社ビル",
    "東急不動産 渋谷本社ビル",
    "日本橋データセンター",
    "品川物流センター",
    "豊洲テクノロジーセンター",
    "秋葉原工業タワー",
    "新宿住友ビル",
    "東京国際空港 整備棟",
    "港区赤坂オフィスビル",
]

OSAKA_BUILDINGS = [
    "パナソニック 大阪梅田本社ビル",
    "関西電力 大阪事業所ビル",
    "大阪市役所 本庁舎",
    "難波グランドビル",
    "大阪食品工場",
    "なんばパークス 管理棟",
    "大阪国際空港 整備センター",
]

NAGOYA_BUILDINGS = [
    "愛知トヨタ 名古屋工場",
    "中部電力 名古屋事業所",
    "名古屋栄商業ビル",
    "中部国際空港 整備センター",
    "名古屋産業センター",
    "金山テクノロジーパーク",
    "栄ミッドランドスクエア",
]

FUKUOKA_BUILDINGS = [
    "九州電力 福岡本社ビル",
    "博多物流センター",
    "天神商業ビル",
    "福岡空港 整備棟",
]

SENDAI_BUILDINGS = [
    "東北電力 仙台本社ビル",
    "仙台テクノロジーパーク",
    "仙台駅前ビジネスタワー",
]

YOKOHAMA_BUILDINGS = [
    "横浜銀行 本店ビル",
    "横浜みなとみらい管理センター",
    "横浜港湾施設 管理棟",
]

# フロア・エリアのバリエーション
FLOORS = [
    "1F", "2F", "3F", "4F", "5F", "6F", "10F",
    "B1", "B2", "屋上", "機械室", "サーバー室",
    "倉庫棟", "製造棟A", "製造棟B", "管理棟", "実験棟",
    "受変電室", "冷凍倉庫", "食品加工棟", "外来棟",
]


def make_location(buildings, floors, index):
    """建物名とフロアを組み合わせてロケーション文字列を生成する"""
    building = buildings[index % len(buildings)]
    floor    = floors[index % len(floors)]
    return f"{building} {floor}"


def generate_sql():
    """UPDATE SQLを生成して標準出力に出力する"""
    lines = []
    lines.append("-- ============================================================")
    lines.append("-- 拠点別データ整理：設備ロケーション名と担当者の一括更新")
    lines.append("-- ============================================================")
    lines.append("SET NAMES utf8mb4;")
    lines.append("")

    # 各拠点ごとにUPDATE文を生成する
    regions = [
        ("東京本社拠点", TOKYO_EQ,    TOKYO,    TOKYO_BUILDINGS),
        ("大阪拠点",     OSAKA_EQ,    OSAKA,    OSAKA_BUILDINGS),
        ("名古屋拠点",   NAGOYA_EQ,   NAGOYA,   NAGOYA_BUILDINGS),
        ("福岡拠点",     FUKUOKA_EQ,  FUKUOKA,  FUKUOKA_BUILDINGS),
        ("仙台拜点",     SENDAI_EQ,   SENDAI,   SENDAI_BUILDINGS),
        ("横浜拠点",     YOKOHAMA_EQ, YOKOHAMA, YOKOHAMA_BUILDINGS),
    ]

    for region_name, eq_ids, eng_ids, buildings in regions:
        lines.append(f"-- ---- {region_name} ----")
        for i, eq_id in enumerate(eq_ids):
            loc      = make_location(buildings, FLOORS, i)
            eng_id   = eng_ids[i % len(eng_ids)]
            # シングルクォートをエスケープする
            loc_escaped = loc.replace("'", "\\'")
            lines.append(
                f"UPDATE equipment SET location='{loc_escaped}', assigned_user_id={eng_id} WHERE id={eq_id};"
            )
        lines.append("")

    # 未割当設備（assigned_user_id = NULL、ロケーションは汎用）
    lines.append("-- ---- 未割当設備（担当者なし）----")
    MISC_BUILDINGS = ["共用設備センター", "予備機械室", "その他施設"]
    for i, eq_id in enumerate(NONE_EQ):
        loc = make_location(MISC_BUILDINGS, FLOORS, i)
        loc_escaped = loc.replace("'", "\\'")
        lines.append(
            f"UPDATE equipment SET location='{loc_escaped}', assigned_user_id=NULL WHERE id={eq_id};"
        )

    lines.append("")
    lines.append("-- 完了")

    return "\n".join(lines)


if __name__ == "__main__":
    sql = generate_sql()
    with open("migrations/rewrite_equipment_regional.sql", "w", encoding="utf-8") as f:
        f.write(sql)
    print("生成完了: migrations/rewrite_equipment_regional.sql")
    print(f"  東京:   {len(TOKYO_EQ)} 件 / {len(TOKYO)} 名")
    print(f"  大阪:   {len(OSAKA_EQ)} 件 / {len(OSAKA)} 名")
    print(f"  名古屋: {len(NAGOYA_EQ)} 件 / {len(NAGOYA)} 名")
    print(f"  福岡:   {len(FUKUOKA_EQ)} 件 / {len(FUKUOKA)} 名")
    print(f"  仙台:   {len(SENDAI_EQ)} 件 / {len(SENDAI)} 名")
    print(f"  横浜:   {len(YOKOHAMA_EQ)} 件 / {len(YOKOHAMA)} 名")
    print(f"  未割当: {len(NONE_EQ)} 件")
