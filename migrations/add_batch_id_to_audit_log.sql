-- ============================================================
-- マイグレーション: audit_log に batch_id カラムを追加する
-- 目的: 一括編集の「元に戻す」機能のためにバッチIDで操作をグループ化する
-- ============================================================

-- ① batch_id カラムを追加する（UUID文字列 36文字）
ALTER TABLE audit_log
    ADD COLUMN batch_id VARCHAR(36) DEFAULT NULL COMMENT '一括操作のグループID（UUID）。単件操作はNULL';

-- ② action の最大長を20に拡張する（BULK_UPDATE / BULK_REVERT に対応）
ALTER TABLE audit_log
    MODIFY COLUMN action VARCHAR(20) NOT NULL COMMENT 'DELETE / RESTORE / UPDATE / HARD_DELETE / BULK_UPDATE / BULK_REVERT';

-- ③ batch_id で高速に一括取得するためのインデックスを追加する
CREATE INDEX idx_audit_log_batch_id ON audit_log (batch_id);
