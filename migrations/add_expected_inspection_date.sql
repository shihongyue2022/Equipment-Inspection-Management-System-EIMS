-- inspection_records に期限遵守履歴追跡用カラムを追加する
-- 点検登録時点の next_inspection_date を記録し、期限超過か否かを後から判定できるようにする

ALTER TABLE inspection_records
    ADD COLUMN expected_inspection_date DATE NULL
        COMMENT '点検登録時点でのnext_inspection_date（期限遵守の履歴追跡用）'
        AFTER inspected_at;
