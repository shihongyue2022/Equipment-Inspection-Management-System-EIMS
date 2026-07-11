-- ============================================================
-- マイグレーション: inspection_records に複合インデックスを追加する
-- 目的: 設備一覧の「最新点検ステータス」取得クエリを高速化する
--      MAX(id) GROUP BY equipment_id の集計が高速になる
-- 対象: inspection_records テーブル
-- ============================================================

-- 同名インデックスが既に存在する場合はエラーになるため、
-- 存在確認してから作成する
SELECT COUNT(*) INTO @idx_exists
FROM information_schema.statistics
WHERE table_schema = DATABASE()
  AND table_name = 'inspection_records'
  AND index_name = 'idx_ir_eq_id';

SET @sql = IF(@idx_exists = 0,
    'CREATE INDEX idx_ir_eq_id ON inspection_records (equipment_id, id)',
    'SELECT "Index idx_ir_eq_id already exists, skipping." AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
