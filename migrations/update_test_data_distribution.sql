-- 文字コードを明示して日本語の二重エンコードを防ぐ
SET NAMES utf8mb4;

-- ============================================================
-- テストデータ分布改善: エリア別異常件数グラフを見栄え良くする
-- 対象:
--   ① 仙台拠点・横浜拠点 に 期限超過 / 要修理 データを追加
--   ② エリア未設定（NULL area）の設備を東京本社拠点に割り当てて担当未登録を削減
-- 実行日: 2026-06-23
-- ============================================================

-- ① 仙台拠点: 2件を期限超過にする（next_inspection_date を過去日に設定）
UPDATE equipment
SET next_inspection_date = '2026-06-10'
WHERE id IN (271, 272)
  AND deleted_at IS NULL;

-- ② 仙台拠点: 2件に「要修理」の点検記録を追加する（最新レコードが repair になる）
INSERT INTO inspection_records (equipment_id, engineer_id, inspected_at, status, note)
VALUES
    (273, 96, '2026-06-18', 'repair', '部品劣化を確認。修理対応が必要。'),
    (274, 97, '2026-06-19', 'repair', '異音あり。要修理と判断。');

-- ③ 横浜拠点: 2件を期限超過にする
UPDATE equipment
SET next_inspection_date = '2026-06-13'
WHERE id IN (283, 284)
  AND deleted_at IS NULL;

-- ④ 横浜拠点: 1件に「要修理」の点検記録を追加する
INSERT INTO inspection_records (equipment_id, engineer_id, inspected_at, status, note)
VALUES
    (285, 100, '2026-06-20', 'repair', '冷媒漏れ疑い。要修理。');

-- ⑤ エリア未設定の設備（ID 292〜297）を東京本社拠点のエンジニアに割り当てる
--    担当未登録を 9件 → 3件（ID 298〜300）に削減する
UPDATE equipment
SET
    area             = '東京本社拠点',
    assigned_user_id = CASE id
        WHEN 292 THEN 3   -- 鈴木健二
        WHEN 293 THEN 4   -- 高橋正之
        WHEN 294 THEN 5   -- 田中翔
        WHEN 295 THEN 8   -- 渡辺敦
        WHEN 296 THEN 9   -- 小林真司
        WHEN 297 THEN 3   -- 鈴木健二（再割当）
    END
WHERE id IN (292, 293, 294, 295, 296, 297)
  AND deleted_at IS NULL;

-- 確認クエリ: グラフ集計と同等の SQL で結果を表示する
SELECT
    COALESCE(e.area, 'エリア未設定') AS base_name,
    COUNT(e.id)                     AS total,
    SUM(CASE WHEN e.next_inspection_date < CURDATE() THEN 1 ELSE 0 END) AS overdue,
    SUM(CASE WHEN last_ir.status = 'repair' THEN 1 ELSE 0 END)         AS repair,
    SUM(CASE WHEN e.assigned_user_id IS NULL THEN 1 ELSE 0 END)        AS unassigned
FROM equipment e
LEFT JOIN (
    SELECT ir.equipment_id, ir.status
    FROM inspection_records ir
    INNER JOIN (
        SELECT equipment_id, MAX(id) AS max_id
        FROM inspection_records
        GROUP BY equipment_id
    ) latest ON ir.id = latest.max_id
) last_ir ON last_ir.equipment_id = e.id
WHERE e.deleted_at IS NULL
GROUP BY e.area
ORDER BY
    (e.area IS NULL) ASC,
    (SUM(CASE WHEN e.next_inspection_date < CURDATE() THEN 1 ELSE 0 END)
     + SUM(CASE WHEN last_ir.status = 'repair' THEN 1 ELSE 0 END)) DESC,
    COUNT(e.id) DESC;
