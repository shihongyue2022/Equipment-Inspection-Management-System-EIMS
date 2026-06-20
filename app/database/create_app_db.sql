-- ============================================================
-- 設備点検管理Webアプリ：DB作成・初期データ投入SQL
-- 設計書：docs/04_データベース定義書.md 準拠
-- 実行方法：mysql -u root -p < app/database/create_app_db.sql
-- ============================================================

DROP DATABASE IF EXISTS inspection_db;
CREATE DATABASE inspection_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE inspection_db;
SET NAMES utf8mb4;

-- ============================================================
-- BASEテーブル（拠点マスタ）
-- 将来実装用インターフェース：現在はEMPLOYEE.baseと連携しない
-- ============================================================
CREATE TABLE base (
    base_number VARCHAR(50) NOT NULL COMMENT '拠点番号',
    base_place  VARCHAR(50) DEFAULT NULL COMMENT '拠点名',
    PRIMARY KEY (base_number)
);

-- ============================================================
-- employeeテーブル（ユーザー情報：root・管理者・FE共通）
-- ============================================================
CREATE TABLE employee (
    id          INT          NOT NULL AUTO_INCREMENT   COMMENT 'ユーザーID',
    employee_no VARCHAR(20)  NOT NULL                  COMMENT '社員番号（例: TEC-201）',
    last_name   VARCHAR(50)  NOT NULL                  COMMENT '苗字',
    first_name  VARCHAR(50)  NOT NULL                  COMMENT '名前',
    email       VARCHAR(255) NOT NULL                  COMMENT 'メールアドレス',
    password    VARCHAR(255) NOT NULL                  COMMENT 'ハッシュ化済みパスワード',
    role        VARCHAR(10)  NOT NULL                  COMMENT 'ロール（root / admin / engineer）',
    phone       VARCHAR(20)  DEFAULT NULL              COMMENT '携帯番号（NULL許容）',
    base        VARCHAR(50)  DEFAULT NULL              COMMENT '拠点（NULL許容）',
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '登録日時',
    PRIMARY KEY (id),
    UNIQUE INDEX idx_employee_no    (employee_no),
    UNIQUE INDEX idx_employee_email (email),
    INDEX        idx_employee_role  (role)
);

-- ============================================================
-- equipmentテーブル（設備マスタ情報）
-- ============================================================
CREATE TABLE equipment (
    id                         INT          NOT NULL AUTO_INCREMENT   COMMENT '設備ID',
    name                       VARCHAR(100) NOT NULL                  COMMENT '設備名',
    location                   VARCHAR(200) NOT NULL                  COMMENT '設置場所（顧客名・拠点）',
    equipment_type             VARCHAR(50)  NOT NULL                  COMMENT '設備種別',
    manufacturer               VARCHAR(100) NOT NULL                  COMMENT '製造メーカー',
    model_number               VARCHAR(100) NOT NULL                  COMMENT '型番',
    installed_at               DATE         NOT NULL                  COMMENT '設置年月',
    inspection_interval_months INT          NOT NULL                  COMMENT '点検間隔（月）1〜12',
    assigned_user_id           INT          DEFAULT NULL              COMMENT '担当エンジニアID（NULL許容）',
    next_inspection_date       DATE         DEFAULT NULL              COMMENT '次回点検予定日（初回はNULL）',
    created_at                 DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '登録日時',
    PRIMARY KEY (id),
    INDEX idx_equipment_assigned_user   (assigned_user_id),
    INDEX idx_equipment_next_inspection (next_inspection_date),
    CONSTRAINT fk_equipment_employee
        FOREIGN KEY (assigned_user_id) REFERENCES employee (id)
        ON DELETE SET NULL
);

-- ============================================================
-- inspection_recordsテーブル（点検記録情報）
-- ============================================================
CREATE TABLE inspection_records (
    id           INT         NOT NULL AUTO_INCREMENT   COMMENT '点検記録ID',
    equipment_id INT         NOT NULL                  COMMENT '設備ID',
    engineer_id  INT         NOT NULL                  COMMENT '実施エンジニアID',
    inspected_at DATE        NOT NULL                  COMMENT '点検実施日',
    status       VARCHAR(10) NOT NULL                  COMMENT '点検ステータス（normal / watch / repair）',
    note         TEXT        DEFAULT NULL              COMMENT '備考（NULL許容）',
    created_at   DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '登録日時',
    PRIMARY KEY (id),
    INDEX idx_inspection_equipment    (equipment_id),
    INDEX idx_inspection_engineer     (engineer_id),
    INDEX idx_inspection_inspected_at (inspected_at),
    CONSTRAINT fk_inspection_equipment
        FOREIGN KEY (equipment_id) REFERENCES equipment (id)
        ON DELETE CASCADE,
    CONSTRAINT fk_inspection_engineer
        FOREIGN KEY (engineer_id) REFERENCES employee (id)
        ON DELETE RESTRICT
);


-- ============================================================
-- 初期データ：BASE（拠点マスタ）
-- ============================================================
INSERT INTO base (base_number, base_place) VALUES
    ('HUB-A01', '東雲中央サービス拠点'),
    ('HUB-B02', '水鏡西部サービス拠点'),
    ('HUB-C03', '星見北部サービス拠点');

-- ============================================================
-- 初期データ：EMPLOYEE（ユーザー情報）
-- 初期ログイン用パスワード：
--   SYS-001: root-demo-2026
--   ADM-101: admin-demo-2026
--   TECユーザー: engineer-demo-2026
--   DEMO-901: viewer-demo-2026
-- 注意：以下は架空のデモデータです。本番環境では必ず削除または変更してください。

INSERT INTO employee (employee_no, last_name, first_name, email, password, role, phone, base) VALUES
    ('SYS-001',  '統括',   '管理者', 'root@eims-demo.example',       'scrypt:32768:8:1$W7jRCOnjGGmU9RlX$ab06e41960c24dafb232cbec8ca82a314f102170b2ab3103ff6d21e7b4a8e54c3cf193b59b9fc41b39d50ccd9f1a1e024009e12993ca48cc56346d1bcb64b6fa', 'root',     NULL,            NULL),
    ('ADM-101',  '運用',   '管理者', 'admin@eims-demo.example',      'scrypt:32768:8:1$tYJYl08h8Hqh6f9H$406ff89f0ade3cd6b3046c42f7eddadea394f30b37685d4a8658fb3c76fab2e2cf55e4374f77f4d16447f4d6c6126066b746493a7e9a77a33a447690bbabb95f', 'admin',    NULL,            NULL),
    ('TEC-201',  '朝霧',   '湊',     'minato.asagiri@eims-demo.example', 'scrypt:32768:8:1$X1shFYxaoOp2Un5S$4bc6b8687b23ca6a56090e24dd1486f0638500cc3521871352b7ffd2b7a121207c763045967fa6c9c4fd5d52603437cf78d602e828e1625651b9c15a179c7a70', 'engineer', '000-1000-0201', '東雲中央サービス拠点'),
    ('TEC-214',  '月岡',   '澪',     'mio.tsukioka@eims-demo.example',   'scrypt:32768:8:1$X1shFYxaoOp2Un5S$4bc6b8687b23ca6a56090e24dd1486f0638500cc3521871352b7ffd2b7a121207c763045967fa6c9c4fd5d52603437cf78d602e828e1625651b9c15a179c7a70', 'engineer', '000-1000-0214', '東雲中央サービス拠点'),
    ('TEC-228',  '風間',   '律',     'ritsu.kazama@eims-demo.example',   'scrypt:32768:8:1$X1shFYxaoOp2Un5S$4bc6b8687b23ca6a56090e24dd1486f0638500cc3521871352b7ffd2b7a121207c763045967fa6c9c4fd5d52603437cf78d602e828e1625651b9c15a179c7a70', 'engineer', '000-2000-0228', '水鏡西部サービス拠点'),
    ('TEC-233',  '白波',   '杏',     'an.shiranami@eims-demo.example',   'scrypt:32768:8:1$X1shFYxaoOp2Un5S$4bc6b8687b23ca6a56090e24dd1486f0638500cc3521871352b7ffd2b7a121207c763045967fa6c9c4fd5d52603437cf78d602e828e1625651b9c15a179c7a70', 'engineer', '000-2000-0233', '水鏡西部サービス拠点'),
    ('TEC-247',  '森宮',   '樹',     'itsuki.morimiya@eims-demo.example','scrypt:32768:8:1$X1shFYxaoOp2Un5S$4bc6b8687b23ca6a56090e24dd1486f0638500cc3521871352b7ffd2b7a121207c763045967fa6c9c4fd5d52603437cf78d602e828e1625651b9c15a179c7a70', 'engineer', '000-3000-0247', '星見北部サービス拠点'),
    ('TEC-259',  '雪村',   '灯',     'akari.yukimura@eims-demo.example','scrypt:32768:8:1$X1shFYxaoOp2Un5S$4bc6b8687b23ca6a56090e24dd1486f0638500cc3521871352b7ffd2b7a121207c763045967fa6c9c4fd5d52603437cf78d602e828e1625651b9c15a179c7a70', 'engineer', '000-3000-0259', '星見北部サービス拠点'),
    ('DEMO-901', '体験',   '利用者', 'viewer@eims-demo.example',    'scrypt:32768:8:1$OZyefxLXVxTle0XG$25d769b9e23bc6fea79314e49abdc098a5270dd36f123590cab227288746a6d4613ba02e805cad3aa5ae00651a25036b487c842a5f0c9cd37d8e3411f56e90b2', 'engineer', NULL,            NULL);


-- ============================================================
-- 初期データ：EQUIPMENT（設備マスタ）
-- 注意：企業名、施設名、メーカー名、型番はすべて架空です。

INSERT INTO equipment (name, location, equipment_type, manufacturer, model_number, installed_at, inspection_interval_months, assigned_user_id, next_inspection_date) VALUES
    ('中央棟サーバー室冷房機',       '蒼葉テクノセンター 中央棟2F',   '空調機（冷房）',     '北辰空調工業', 'HC-720A',      '2019-04-01', 3, 5, '2026-08-08'),
    ('研修棟会議室空調機',           '蒼葉テクノセンター 研修棟3F',   '空調機（冷暖）',     '北辰空調工業', 'HT-410R',      '2020-07-01', 6, 5, '2026-11-12'),
    ('地下搬入口換気ユニット',       '蒼葉テクノセンター 地下1F',     '換気設備',           '雲雀設備製作所', 'HV-32S',       '2017-09-01', 3, 3, '2026-06-28'),
    ('組立ライン冷却装置A',          '光輪精機 第一製造棟 Aライン',   '冷却装置',           '瑞穂冷熱技研', 'MC-110A',      '2018-10-01', 1, 6, '2026-06-12'),
    ('組立ライン冷却装置B',          '光輪精機 第一製造棟 Bライン',   '冷却装置',           '瑞穂冷熱技研', 'MC-110B',      '2018-10-01', 1, 6, '2026-06-12'),
    ('成形ライン循環冷却装置',       '光輪精機 第二製造棟 成形区画',  '冷却装置',           '瑞穂冷熱技研', 'MC-145C',      '2021-03-01', 1, 6, '2026-06-20'),
    ('管理棟屋上大型空調機',         '月白オフィスパーク 管理棟屋上', '大型空調機',         '蒼星機工',     'AS-2000X',     '2016-06-01', 6, 4, '2026-11-15'),
    ('交流ホール全館空調',           '月白オフィスパーク 交流棟1F',   '全館空調',           '蒼星機工',     'AS-680M',      '2021-03-01', 3, 4, '2026-08-10'),
    ('低温倉庫冷却ユニット',         '白樺フーズ 低温物流棟',         '冷凍冷却装置',       '瑞穂冷熱技研', 'MF-320L',      '2015-04-01', 1, 7, '2026-06-03'),
    ('計算機室精密空調A',            '星雲データラボ 計算機棟A',      '精密空調',           '北辰空調工業', 'HP-90A',       '2022-08-01', 1, 8, '2026-06-05'),
    ('計算機室精密空調B',            '星雲データラボ 計算機棟B',      '精密空調',           '北辰空調工業', 'HP-90B',       '2022-08-01', 1, 8, '2026-06-05'),
    ('複合施設熱源プラント',         '虹丘スクエア 地下機械室',       '地域冷暖房',         '蒼星機工',     'AP-2400T',     '2014-04-01', 3, 5, '2026-07-01'),
    ('研究室陽圧空調設備',           '若葉メディカル研究所 研究棟',   '医療用空調',         '雲雀設備製作所', 'HM-70P',       '2021-01-01', 1, 9, '2026-06-01'),
    ('無菌包装室クリーン空調',       '白樺フーズ 品質管理棟',         'クリーンルーム空調', '雲雀設備製作所', 'HC-150C',      '2020-04-01', 2, 6, '2026-06-20'),
    ('配送棟大型換気装置',           '風見ロジスティクス 配送棟2F',   '換気設備',           '雲雀設備製作所', 'HV-65W',       '2019-10-01', 6, 4, '2026-11-25');

INSERT INTO inspection_records (equipment_id, engineer_id, inspected_at, status, note) VALUES
    (1,  5, '2026-05-08', 'normal', '吸込フィルターを清掃し、冷媒圧力が基準範囲内であることを確認。'),
    (2,  5, '2026-05-12', 'normal', 'ドレン配管と送風動作を確認。漏水および異音なし。'),
    (4,  6, '2026-05-12', 'normal', '循環水の濁度とポンプ圧力を確認。いずれも基準内。'),
    (5,  6, '2026-05-12', 'watch',  '運転時の振動値が前回より上昇。次回点検で軸受け部を再測定する。'),
    (7,  4, '2026-05-15', 'normal', '屋外熱交換器と圧縮機の動作を確認。異常なし。'),
    (6,  6, '2026-05-20', 'normal', '定期点検を完了し、循環系ストレーナーを交換。'),
    (8,  4, '2026-05-10', 'repair', '送風ベルトに亀裂を確認。交換部品を手配し、設備を低負荷運転に切り替えた。'),
    (14, 6, '2026-04-20', 'normal', '差圧計と室内清浄度を測定。管理基準を満たしている。'),
    (9,  7, '2026-05-03', 'normal', '庫内温度、冷媒量、霜取り運転を確認。異常なし。'),
    (10, 8, '2026-05-05', 'normal', '温湿度制御の追従性を確認し、加湿器フィルターを清掃。'),
    (11, 8, '2026-05-05', 'watch',  '加湿エレメントに軽度の劣化を確認。次回定期点検で交換予定。'),
    (15, 4, '2026-05-25', 'normal', '担当者応援として実施。ベルト張力調整と軸受けへの給脂を完了。'),
    (12, 5, '2026-04-01', 'normal', '熱源ポンプと制御盤を点検。次回点検は7月初旬を予定。');

-- 初期SQLで作成したスキーマをAlembicの初期版として記録する。
CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL,
    PRIMARY KEY (version_num)
);
INSERT INTO alembic_version (version_num) VALUES ('b28638c85152');
