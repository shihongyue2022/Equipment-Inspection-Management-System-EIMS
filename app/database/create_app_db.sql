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
    INDEX        idx_employee_role  (role),
    INDEX        idx_employee_base  (base)
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
    INDEX idx_inspection_latest       (equipment_id, inspected_at, id),
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

-- 以降の大量デモデータを再現可能な形で生成するための連番テーブル。
-- 初期データ投入後に削除するため、アプリケーションのスキーマには残らない。
CREATE TABLE seed_sequence (
    n INT NOT NULL,
    PRIMARY KEY (n)
);

-- ============================================================
-- maintenance_recordsテーブル（修理対応のライフサイクル）
-- ============================================================
CREATE TABLE maintenance_records (
    id                   INT          NOT NULL AUTO_INCREMENT COMMENT '修理対応ID',
    equipment_id         INT          NOT NULL                COMMENT '設備ID',
    source_inspection_id INT          DEFAULT NULL            COMMENT '起点となった点検記録ID',
    engineer_id          INT          NOT NULL                COMMENT '対応担当者ID',
    status               VARCHAR(20)  NOT NULL                COMMENT 'planned / in_progress / completed / cancelled',
    action               VARCHAR(255) NOT NULL                COMMENT '作業内容',
    started_at           DATE         DEFAULT NULL            COMMENT '着手日',
    completed_at         DATE         DEFAULT NULL            COMMENT '完了日',
    result               TEXT         DEFAULT NULL            COMMENT '対応結果',
    note                 TEXT         DEFAULT NULL            COMMENT '備考',
    created_at           DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '登録日時',
    PRIMARY KEY (id),
    UNIQUE INDEX uq_maintenance_source_inspection (source_inspection_id),
    INDEX idx_maintenance_equipment (equipment_id),
    INDEX idx_maintenance_engineer (engineer_id),
    INDEX idx_maintenance_status (status),
    INDEX idx_maintenance_completed_at (completed_at),
    CONSTRAINT fk_maintenance_equipment
        FOREIGN KEY (equipment_id) REFERENCES equipment (id) ON DELETE CASCADE,
    CONSTRAINT fk_maintenance_inspection
        FOREIGN KEY (source_inspection_id) REFERENCES inspection_records (id) ON DELETE SET NULL,
    CONSTRAINT fk_maintenance_engineer
        FOREIGN KEY (engineer_id) REFERENCES employee (id) ON DELETE RESTRICT
);

INSERT INTO seed_sequence (n)
SELECT
    ones.d + tens.d * 10 + hundreds.d * 100 + thousands.d * 1000 + 1
FROM
    (SELECT 0 d UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4
     UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) ones
CROSS JOIN
    (SELECT 0 d UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4
     UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) tens
CROSS JOIN
    (SELECT 0 d UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4
     UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) hundreds
CROSS JOIN
    (SELECT 0 d UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4
     UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) thousands
WHERE ones.d + tens.d * 10 + hundreds.d * 100 + thousands.d * 1000 < 5000;

-- 拠点を合計25件まで拡張する。名称はすべて架空。
INSERT INTO base (base_number, base_place)
SELECT
    CONCAT('HUB-', LPAD(n + 3, 3, '0')),
    CONCAT(
        CASE MOD(n - 1, 11)
            WHEN 0 THEN '青海' WHEN 1 THEN '花園' WHEN 2 THEN '高峰'
            WHEN 3 THEN '朝凪' WHEN 4 THEN '夕映' WHEN 5 THEN '若竹'
            WHEN 6 THEN '銀河' WHEN 7 THEN '潮見' WHEN 8 THEN '緑丘'
            WHEN 9 THEN '桜川' ELSE '天城'
        END,
        LPAD(FLOOR((n - 1) / 11) + 1, 2, '0'),
        'サービス拠点'
    )
FROM seed_sequence
WHERE n <= 22;

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

-- 管理者を合計9名まで拡張する（既存1名 + 追加8名）。
INSERT INTO employee (employee_no, last_name, first_name, email, password, role, phone, base)
SELECT
    CONCAT('ADM-', LPAD(n + 101, 3, '0')),
    '運用',
    CONCAT('管理者', LPAD(n + 1, 2, '0')),
    CONCAT('admin', LPAD(n + 1, 2, '0'), '@eims-demo.example'),
    'scrypt:32768:8:1$tYJYl08h8Hqh6f9H$406ff89f0ade3cd6b3046c42f7eddadea394f30b37685d4a8658fb3c76fab2e2cf55e4374f77f4d16447f4d6c6126066b746493a7e9a77a33a447690bbabb95f',
    'admin',
    CONCAT('000-9000-', LPAD(n + 101, 4, '0')),
    CONCAT(
        CASE MOD(n - 1, 11)
            WHEN 0 THEN '青海' WHEN 1 THEN '花園' WHEN 2 THEN '高峰'
            WHEN 3 THEN '朝凪' WHEN 4 THEN '夕映' WHEN 5 THEN '若竹'
            WHEN 6 THEN '銀河' ELSE '潮見'
        END,
        '01サービス拠点'
    )
FROM seed_sequence
WHERE n <= 8;

-- エンジニアを合計140名まで拡張する（既存7名 + 追加133名）。
-- 氏名・電話番号・メールアドレスはすべて架空のデモ値。
INSERT INTO employee (employee_no, last_name, first_name, email, password, role, phone, base)
SELECT
    CONCAT('TEC-', LPAD(n + 299, 3, '0')),
    CASE MOD(n - 1, 20)
        WHEN 0 THEN '青木' WHEN 1 THEN '石川' WHEN 2 THEN '上野' WHEN 3 THEN '江波'
        WHEN 4 THEN '大庭' WHEN 5 THEN '神谷' WHEN 6 THEN '北原' WHEN 7 THEN '黒瀬'
        WHEN 8 THEN '小森' WHEN 9 THEN '佐伯' WHEN 10 THEN '篠原' WHEN 11 THEN '高瀬'
        WHEN 12 THEN '千葉' WHEN 13 THEN '長峰' WHEN 14 THEN '西沢' WHEN 15 THEN '早川'
        WHEN 16 THEN '藤森' WHEN 17 THEN '松浦' WHEN 18 THEN '水野' ELSE '吉岡'
    END,
    CASE MOD(FLOOR((n - 1) / 20) + n, 15)
        WHEN 0 THEN '葵' WHEN 1 THEN '樹' WHEN 2 THEN '海斗' WHEN 3 THEN '楓'
        WHEN 4 THEN '咲良' WHEN 5 THEN '匠' WHEN 6 THEN '翼' WHEN 7 THEN '直'
        WHEN 8 THEN '陽菜' WHEN 9 THEN '真琴' WHEN 10 THEN '悠' WHEN 11 THEN '凛'
        WHEN 12 THEN '蓮' WHEN 13 THEN '和花' ELSE '颯太'
    END,
    CONCAT('engineer', LPAD(n + 7, 3, '0'), '@eims-demo.example'),
    'scrypt:32768:8:1$X1shFYxaoOp2Un5S$4bc6b8687b23ca6a56090e24dd1486f0638500cc3521871352b7ffd2b7a121207c763045967fa6c9c4fd5d52603437cf78d602e828e1625651b9c15a179c7a70',
    'engineer',
    CONCAT('000-', LPAD(4000 + MOD(n - 1, 25) * 100, 4, '0'), '-', LPAD(n, 4, '0')),
    CASE MOD(n - 1, 25)
        WHEN 0 THEN '東雲中央サービス拠点'
        WHEN 1 THEN '水鏡西部サービス拠点'
        WHEN 2 THEN '星見北部サービス拠点'
        ELSE CONCAT(
            CASE MOD(MOD(n - 1, 25) - 3, 11)
                WHEN 0 THEN '青海' WHEN 1 THEN '花園' WHEN 2 THEN '高峰'
                WHEN 3 THEN '朝凪' WHEN 4 THEN '夕映' WHEN 5 THEN '若竹'
                WHEN 6 THEN '銀河' WHEN 7 THEN '潮見' WHEN 8 THEN '緑丘'
                WHEN 9 THEN '桜川' ELSE '天城'
            END,
            LPAD(FLOOR((MOD(n - 1, 25) - 3) / 11) + 1, 2, '0'),
            'サービス拠点'
        )
    END
FROM seed_sequence
WHERE n <= 133;


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

-- 設備を合計1,200台まで拡張する（既存15台 + 追加1,185台）。
-- 追加設備は追加エンジニア133名へ均等に割り当てる。
INSERT INTO equipment (
    name, location, equipment_type, manufacturer, model_number,
    installed_at, inspection_interval_months, assigned_user_id, next_inspection_date
)
SELECT
    CONCAT(
        CASE MOD(s.n - 1, 12)
            WHEN 0 THEN '屋上空調機' WHEN 1 THEN '精密空調ユニット'
            WHEN 2 THEN '循環冷却装置' WHEN 3 THEN '給排気ユニット'
            WHEN 4 THEN '冷凍倉庫設備' WHEN 5 THEN 'クリーン空調設備'
            WHEN 6 THEN '熱源ポンプ' WHEN 7 THEN '除湿ユニット'
            WHEN 8 THEN '外気処理機' WHEN 9 THEN '排熱回収装置'
            WHEN 10 THEN '恒温恒湿装置' ELSE '局所換気設備'
        END,
        ' ', LPAD(s.n, 4, '0')
    ),
    CONCAT(
        e.base, ' 管轄・架空顧客', LPAD(MOD(s.n - 1, 240) + 1, 3, '0'),
        ' 第', MOD(s.n - 1, 5) + 1, '施設 ', MOD(s.n - 1, 8) + 1, 'F'
    ),
    CASE MOD(s.n - 1, 12)
        WHEN 0 THEN '大型空調機' WHEN 1 THEN '精密空調' WHEN 2 THEN '冷却装置'
        WHEN 3 THEN '換気設備' WHEN 4 THEN '冷凍冷却装置' WHEN 5 THEN 'クリーンルーム空調'
        WHEN 6 THEN '熱源設備' WHEN 7 THEN '除湿設備' WHEN 8 THEN '外気処理設備'
        WHEN 9 THEN '熱回収設備' WHEN 10 THEN '恒温恒湿設備' ELSE '局所換気設備'
    END,
    CASE MOD(s.n - 1, 8)
        WHEN 0 THEN '北辰空調工業' WHEN 1 THEN '雲雀設備製作所'
        WHEN 2 THEN '瑞穂冷熱技研' WHEN 3 THEN '蒼星機工'
        WHEN 4 THEN '朝日環境システム' WHEN 5 THEN '白峰熱工'
        WHEN 6 THEN '東雲機電' ELSE '若草エンジニアリング'
    END,
    CONCAT(
        CASE MOD(s.n - 1, 8)
            WHEN 0 THEN 'AC' WHEN 1 THEN 'HV' WHEN 2 THEN 'CL' WHEN 3 THEN 'HP'
            WHEN 4 THEN 'DH' WHEN 5 THEN 'OA' WHEN 6 THEN 'HR' ELSE 'CT'
        END,
        '-', LPAD(1000 + s.n, 5, '0'), '-', CHAR(65 + MOD(s.n - 1, 6))
    ),
    DATE_ADD('2012-01-01', INTERVAL MOD(s.n * 37, 3650) DAY),
    CASE MOD(s.n - 1, 10)
        WHEN 0 THEN 1 WHEN 1 THEN 1 WHEN 2 THEN 2 WHEN 3 THEN 3
        WHEN 4 THEN 3 WHEN 5 THEN 3 WHEN 6 THEN 6 WHEN 7 THEN 6
        WHEN 8 THEN 12 ELSE 12
    END,
    e.id,
    DATE_ADD('2026-01-01', INTERVAL MOD(s.n * 17, 730) DAY)
FROM seed_sequence s
JOIN employee e
    ON e.employee_no = CONCAT('TEC-', LPAD(MOD(s.n - 1, 133) + 300, 3, '0'))
WHERE s.n <= 1185;

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

-- 点検記録を合計3,625件まで拡張する（既存13件 + 追加3,612件）。
-- 全追加設備に3件以上の履歴を持たせ、設備単位で意味のある状態遷移を作る。
INSERT INTO inspection_records (equipment_id, engineer_id, inspected_at, status, note)
SELECT
    eq.id,
    eq.assigned_user_id,
    DATE_SUB(
        '2026-05-31',
        INTERVAL (FLOOR((s.n - 1) / 1185) * 365 + MOD(eq.id * 13, 120)) DAY
    ),
    CASE
        WHEN MOD(eq.id, 50) = 0
             AND FLOOR((s.n - 1) / 1185) IN (0, 2) THEN 'repair'
        WHEN MOD(eq.id, 50) BETWEEN 1 AND 3
             AND FLOOR((s.n - 1) / 1185) = 1 THEN 'repair'
        WHEN MOD(eq.id, 50) BETWEEN 4 AND 6
             AND FLOOR((s.n - 1) / 1185) = 2 THEN 'watch'
        WHEN MOD(eq.id, 50) BETWEEN 4 AND 6
             AND FLOOR((s.n - 1) / 1185) = 1 THEN 'repair'
        WHEN MOD(eq.id, 50) BETWEEN 7 AND 14
             AND FLOOR((s.n - 1) / 1185) = 0 THEN 'watch'
        WHEN MOD(eq.id, 50) BETWEEN 15 AND 16
             AND FLOOR((s.n - 1) / 1185) = 0 THEN 'repair'
        WHEN MOD(eq.id, 50) BETWEEN 17 AND 19
             AND FLOOR((s.n - 1) / 1185) = 1 THEN 'watch'
        ELSE 'normal'
    END,
    CASE
        WHEN (
            (MOD(eq.id, 50) = 0 AND FLOOR((s.n - 1) / 1185) IN (0, 2))
            OR (MOD(eq.id, 50) BETWEEN 1 AND 3 AND FLOOR((s.n - 1) / 1185) = 1)
            OR (MOD(eq.id, 50) BETWEEN 4 AND 6 AND FLOOR((s.n - 1) / 1185) = 1)
            OR (MOD(eq.id, 50) BETWEEN 15 AND 16 AND FLOOR((s.n - 1) / 1185) = 0)
        ) THEN '異音と振動値超過を確認。修理対応を起票し、対象部品の交換を依頼。'
        WHEN (
            (MOD(eq.id, 50) BETWEEN 4 AND 6 AND FLOOR((s.n - 1) / 1185) = 2)
            OR (MOD(eq.id, 50) BETWEEN 7 AND 14 AND FLOOR((s.n - 1) / 1185) = 0)
            OR (MOD(eq.id, 50) BETWEEN 17 AND 19 AND FLOOR((s.n - 1) / 1185) = 1)
        ) THEN '振動値に上昇傾向あり。次回点検で再測定し、悪化時は修理へ移行する。'
        WHEN MOD(eq.id, 3) = 0 THEN 'フィルター清掃、運転電流および温度差を確認。すべて基準範囲内。'
        WHEN MOD(eq.id, 3) = 1 THEN '配管、ドレン、ベルト張力を点検。漏れ、異音および異常振動なし。'
        ELSE '制御盤と安全装置の動作試験を実施し、正常動作を確認。'
    END
FROM seed_sequence s
JOIN equipment eq ON eq.id = 16 + MOD(s.n - 1, 1185)
WHERE s.n <= 3612;

-- 要修理点検ごとに修理対応を作成する。
-- 後続点検がある過去障害は「完了」、最新障害は「対応予定」として時系列を成立させる。
INSERT INTO maintenance_records (
    equipment_id, source_inspection_id, engineer_id, status, action,
    started_at, completed_at, result, note
)
SELECT
    ir.equipment_id,
    ir.id,
    ir.engineer_id,
    CASE WHEN EXISTS (
        SELECT 1 FROM inspection_records later
        WHERE later.equipment_id = ir.equipment_id
          AND (later.inspected_at > ir.inspected_at
               OR (later.inspected_at = ir.inspected_at AND later.id > ir.id))
    ) THEN 'completed' ELSE 'planned' END,
    CASE MOD(ir.equipment_id, 3)
        WHEN 0 THEN '軸受けおよび駆動ベルト交換'
        WHEN 1 THEN '制御センサー交換と校正'
        ELSE '送風モーター交換と試運転'
    END,
    CASE WHEN EXISTS (
        SELECT 1 FROM inspection_records later
        WHERE later.equipment_id = ir.equipment_id AND later.inspected_at > ir.inspected_at
    ) THEN DATE_ADD(ir.inspected_at, INTERVAL 2 DAY) ELSE NULL END,
    CASE WHEN EXISTS (
        SELECT 1 FROM inspection_records later
        WHERE later.equipment_id = ir.equipment_id AND later.inspected_at > ir.inspected_at
    ) THEN DATE_ADD(ir.inspected_at, INTERVAL 7 DAY) ELSE NULL END,
    CASE WHEN EXISTS (
        SELECT 1 FROM inspection_records later
        WHERE later.equipment_id = ir.equipment_id AND later.inspected_at > ir.inspected_at
    ) THEN '部品交換後の試運転と再測定を実施し、基準値内への復帰を確認。' ELSE NULL END,
    '点検記録から自動生成された架空の修理対応。'
FROM inspection_records ir
WHERE ir.status = 'repair';

-- 追加設備の次回点検日は、最新点検日と設備ごとの点検周期から再計算する。
UPDATE equipment eq
JOIN (
    SELECT equipment_id, MAX(inspected_at) AS latest_inspected_at
    FROM inspection_records
    WHERE equipment_id >= 16
    GROUP BY equipment_id
) latest ON latest.equipment_id = eq.id
SET eq.next_inspection_date = DATE_ADD(
    latest.latest_inspected_at,
    INTERVAL eq.inspection_interval_months MONTH
)
WHERE eq.id >= 16;

-- 基本デモデータ5,000件に加え、要修理点検へ対応する修理ライフサイクルを投入する。
DROP TABLE seed_sequence;

-- 初期SQLで作成したスキーマをAlembicの初期版として記録する。
CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL,
    PRIMARY KEY (version_num)
);
INSERT INTO alembic_version (version_num) VALUES ('f2c84d6a190e');
