-- ============================================================
-- MTBR算出用の修理記録を追加する
-- inject_repair_records.py で生成したデータを恒久化したもの
-- 対象：定期点検記録内のrepairが0〜1件だった設備（interval_months >= 2）
-- ============================================================
SET NAMES utf8mb4;

INSERT INTO inspection_records (equipment_id, engineer_id, inspected_at, expected_inspection_date, status, note) VALUES (15, 30, '2019-06-20', NULL, 'repair', '制御基板故障。メーカー対応にて修理完了。正常稼働確認。');
INSERT INTO inspection_records (equipment_id, engineer_id, inspected_at, expected_inspection_date, status, note) VALUES (15, 30, '2019-12-14', NULL, 'repair', '制御基板故障。メーカー対応にて修理完了。正常稼働確認。');
INSERT INTO inspection_records (equipment_id, engineer_id, inspected_at, expected_inspection_date, status, note) VALUES (36, 51, '2023-01-22', NULL, 'repair', '電気系統異常発生。絶縁不良箇所を特定し修理。正常復帰確認。');
INSERT INTO inspection_records (equipment_id, engineer_id, inspected_at, expected_inspection_date, status, note) VALUES (36, 51, '2023-07-15', NULL, 'repair', '冷媒漏れ確認。緊急修理実施。補充後正常稼働確認。');
INSERT INTO inspection_records (equipment_id, engineer_id, inspected_at, expected_inspection_date, status, note) VALUES (1, 3, '2018-08-14', NULL, 'repair', '電気系統異常発生。絶縁不良箇所を特定し修理。正常復帰確認。');
INSERT INTO inspection_records (equipment_id, engineer_id, inspected_at, expected_inspection_date, status, note) VALUES (1, 3, '2018-11-14', NULL, 'repair', '電気系統異常発生。絶縁不良箇所を特定し修理。正常復帰確認。');
INSERT INTO inspection_records (equipment_id, engineer_id, inspected_at, expected_inspection_date, status, note) VALUES (8, 13, '2020-07-12', NULL, 'repair', '冷媒漏れ確認。緊急修理実施。補充後正常稼働確認。');
INSERT INTO inspection_records (equipment_id, engineer_id, inspected_at, expected_inspection_date, status, note) VALUES (8, 13, '2020-10-05', NULL, 'repair', 'コンプレッサー異常音確認。専門業者対応。部品交換実施済み。');
INSERT INTO inspection_records (equipment_id, engineer_id, inspected_at, expected_inspection_date, status, note) VALUES (8, 13, '2020-12-29', NULL, 'repair', 'ドレンポンプ故障。交換対応済み。正常稼働に復帰。');
INSERT INTO inspection_records (equipment_id, engineer_id, inspected_at, expected_inspection_date, status, note) VALUES (28, 43, '2022-06-16', NULL, 'repair', '制御基板故障。メーカー対応にて修理完了。正常稼働確認。');
INSERT INTO inspection_records (equipment_id, engineer_id, inspected_at, expected_inspection_date, status, note) VALUES (28, 43, '2022-09-16', NULL, 'repair', 'コンプレッサー異常音確認。専門業者対応。部品交換実施済み。');
INSERT INTO inspection_records (equipment_id, engineer_id, inspected_at, expected_inspection_date, status, note) VALUES (28, 43, '2022-12-18', NULL, 'repair', 'モーター過熱。冷却ファン交換で正常復帰。');
INSERT INTO inspection_records (equipment_id, engineer_id, inspected_at, expected_inspection_date, status, note) VALUES (45, 9, '2022-09-02', NULL, 'repair', '電気系統異常発生。絶縁不良箇所を特定し修理。正常復帰確認。');
INSERT INTO inspection_records (equipment_id, engineer_id, inspected_at, expected_inspection_date, status, note) VALUES (45, 9, '2022-11-29', NULL, 'repair', '制御基板故障。メーカー対応にて修理完了。正常稼働確認。');
INSERT INTO inspection_records (equipment_id, engineer_id, inspected_at, expected_inspection_date, status, note) VALUES (45, 9, '2023-03-04', NULL, 'repair', '電気系統異常発生。絶縁不良箇所を特定し修理。正常復帰確認。');
INSERT INTO inspection_records (equipment_id, engineer_id, inspected_at, expected_inspection_date, status, note) VALUES (57, 32, '2020-06-10', NULL, 'repair', 'ベルト摩耗による異常停止。交換対応済み。');
INSERT INTO inspection_records (equipment_id, engineer_id, inspected_at, expected_inspection_date, status, note) VALUES (57, 32, '2020-09-10', NULL, 'repair', '制御基板故障。メーカー対応にて修理完了。正常稼働確認。');
INSERT INTO inspection_records (equipment_id, engineer_id, inspected_at, expected_inspection_date, status, note) VALUES (65, 40, '2020-07-14', NULL, 'repair', '電気系統異常発生。絶縁不良箇所を特定し修理。正常復帰確認。');
INSERT INTO inspection_records (equipment_id, engineer_id, inspected_at, expected_inspection_date, status, note) VALUES (65, 40, '2020-10-12', NULL, 'repair', '冷媒漏れ確認。緊急修理実施。補充後正常稼働確認。');
INSERT INTO inspection_records (equipment_id, engineer_id, inspected_at, expected_inspection_date, status, note) VALUES (65, 40, '2021-01-16', NULL, 'repair', 'モーター過熱。冷却ファン交換で正常復帰。');
INSERT INTO inspection_records (equipment_id, engineer_id, inspected_at, expected_inspection_date, status, note) VALUES (79, 54, '2018-06-10', NULL, 'repair', '冷媒漏れ確認。緊急修理実施。補充後正常稼働確認。');
INSERT INTO inspection_records (equipment_id, engineer_id, inspected_at, expected_inspection_date, status, note) VALUES (79, 54, '2018-09-08', NULL, 'repair', 'ベルト摩耗による異常停止。交換対応済み。');
INSERT INTO inspection_records (equipment_id, engineer_id, inspected_at, expected_inspection_date, status, note) VALUES (79, 54, '2018-12-05', NULL, 'repair', 'コンプレッサー異常音確認。専門業者対応。部品交換実施済み。');
INSERT INTO inspection_records (equipment_id, engineer_id, inspected_at, expected_inspection_date, status, note) VALUES (82, 9, '2018-05-13', NULL, 'repair', 'コンプレッサー異常音確認。専門業者対応。部品交換実施済み。');
INSERT INTO inspection_records (equipment_id, engineer_id, inspected_at, expected_inspection_date, status, note) VALUES (82, 9, '2018-08-05', NULL, 'repair', 'モーター過熱。冷却ファン交換で正常復帰。');
INSERT INTO inspection_records (equipment_id, engineer_id, inspected_at, expected_inspection_date, status, note) VALUES (93, 28, '2022-07-10', NULL, 'repair', 'ベルト摩耗による異常停止。交換対応済み。');
INSERT INTO inspection_records (equipment_id, engineer_id, inspected_at, expected_inspection_date, status, note) VALUES (93, 28, '2022-10-13', NULL, 'repair', '制御基板故障。メーカー対応にて修理完了。正常稼働確認。');
INSERT INTO inspection_records (equipment_id, engineer_id, inspected_at, expected_inspection_date, status, note) VALUES (93, 28, '2023-01-16', NULL, 'repair', '熱交換器に亀裂確認。緊急修理実施。部品交換後正常稼働に復帰。');
INSERT INTO inspection_records (equipment_id, engineer_id, inspected_at, expected_inspection_date, status, note) VALUES (20, 35, '2020-04-25', NULL, 'repair', 'ドレンポンプ故障。交換対応済み。正常稼働に復帰。');
INSERT INTO inspection_records (equipment_id, engineer_id, inspected_at, expected_inspection_date, status, note) VALUES (20, 35, '2020-06-24', NULL, 'repair', '熱交換器に亀裂確認。緊急修理実施。部品交換後正常稼働に復帰。');
INSERT INTO inspection_records (equipment_id, engineer_id, inspected_at, expected_inspection_date, status, note) VALUES (20, 35, '2020-08-24', NULL, 'repair', '制御基板故障。メーカー対応にて修理完了。正常稼働確認。');
