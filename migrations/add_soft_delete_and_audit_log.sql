-- ============================================================
-- マイグレーション: ソフトデリート + audit_log の追加
-- 対象テーブル: equipment / employee / inspection_records
-- ============================================================

-- ① equipment にソフトデリート列を追加する
ALTER TABLE equipment
    ADD COLUMN deleted_at  DATETIME DEFAULT NULL,
    ADD COLUMN deleted_by  INT      DEFAULT NULL,
    ADD CONSTRAINT fk_equipment_deleted_by
        FOREIGN KEY (deleted_by) REFERENCES employee(id) ON DELETE SET NULL;

-- ② employee にソフトデリート列を追加する
--    （自己参照 FK のため、deleted_by は後で追加する）
ALTER TABLE employee
    ADD COLUMN deleted_at  DATETIME DEFAULT NULL,
    ADD COLUMN deleted_by  INT      DEFAULT NULL,
    ADD CONSTRAINT fk_employee_deleted_by
        FOREIGN KEY (deleted_by) REFERENCES employee(id) ON DELETE SET NULL;

-- ③ inspection_records にソフトデリート列を追加する
ALTER TABLE inspection_records
    ADD COLUMN deleted_at  DATETIME DEFAULT NULL,
    ADD COLUMN deleted_by  INT      DEFAULT NULL,
    ADD CONSTRAINT fk_inspection_deleted_by
        FOREIGN KEY (deleted_by) REFERENCES employee(id) ON DELETE SET NULL;

-- ④ 操作履歴テーブルを新規作成する
CREATE TABLE audit_log (
    id          INT          NOT NULL AUTO_INCREMENT,
    table_name  VARCHAR(50)  NOT NULL COMMENT '操作対象テーブル名',
    record_id   INT          NOT NULL COMMENT '操作対象レコードのid',
    action      VARCHAR(10)  NOT NULL COMMENT 'DELETE / RESTORE / UPDATE',
    old_data    JSON                  COMMENT '変更前データのスナップショット（JSON形式）',
    changed_by  INT                   COMMENT '操作者のemployee.id',
    changed_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '操作日時',
    PRIMARY KEY (id),
    CONSTRAINT fk_audit_log_changed_by
        FOREIGN KEY (changed_by) REFERENCES employee(id) ON DELETE SET NULL
) COMMENT='データ操作の履歴を記録するテーブル';

-- ⑤ 検索用インデックスを追加する（ゴミ箱一覧の高速化）
CREATE INDEX idx_equipment_deleted_at          ON equipment          (deleted_at);
CREATE INDEX idx_employee_deleted_at           ON employee           (deleted_at);
CREATE INDEX idx_inspection_records_deleted_at ON inspection_records (deleted_at);
CREATE INDEX idx_audit_log_table_record        ON audit_log          (table_name, record_id);
