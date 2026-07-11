-- ============================================================
-- 担当設備の再配分：均等な3件割り当てを参差不齐（1〜6件）に変更
-- 各拠点のエンジニアに1〜5件（一部6件）の設備をばらつきをもって割り当て
-- ============================================================
SET NAMES utf8mb4;

-- ============================================================
-- 東京本社拠点（設備ID: 1〜120, エンジニア40名）
-- 変更後の担当数パターン: [1,2,3,4,5] × 8繰り返し = 合計120件
-- ============================================================

-- user_id=3（鈴木健二）: 3件→1件　設備41,81を他へ移す
UPDATE equipment SET assigned_user_id=8  WHERE id=41;
UPDATE equipment SET assigned_user_id=9  WHERE id=81;

-- user_id=4（高橋正之）: 3件→2件　設備82を他へ移す
UPDATE equipment SET assigned_user_id=9  WHERE id=82;

-- user_id=8（渡辺敦）: 3件→4件　設備41を受け取る（上記で設定済み）
-- user_id=9（小林真司）: 3件→5件　設備81,82を受け取る（上記で設定済み）

-- user_id=11（山田太郎）: 3件→1件　設備46,86を他へ移す
UPDATE equipment SET assigned_user_id=14 WHERE id=46;
UPDATE equipment SET assigned_user_id=15 WHERE id=86;

-- user_id=12（中村恵子）: 3件→2件　設備87を他へ移す
UPDATE equipment SET assigned_user_id=15 WHERE id=87;

-- user_id=14（吉田圭一）: 3件→4件　設備46を受け取る（上記で設定済み）
-- user_id=15（木村明子）: 3件→5件　設備86,87を受け取る（上記で設定済み）

-- user_id=26（田村浩二）: 3件→1件　設備51,91を他へ移す
UPDATE equipment SET assigned_user_id=29 WHERE id=51;
UPDATE equipment SET assigned_user_id=30 WHERE id=91;

-- user_id=27（大野美和）: 3件→2件　設備92を他へ移す
UPDATE equipment SET assigned_user_id=30 WHERE id=92;

-- user_id=29（坂本陽子）: 3件→4件　設備51を受け取る（上記で設定済み）
-- user_id=30（村田達也）: 3件→5件　設備91,92を受け取る（上記で設定済み）

-- user_id=31（沢田典子）: 3件→1件　設備56,96を他へ移す
UPDATE equipment SET assigned_user_id=34 WHERE id=56;
UPDATE equipment SET assigned_user_id=35 WHERE id=96;

-- user_id=32（福田拓也）: 3件→2件　設備97を他へ移す
UPDATE equipment SET assigned_user_id=35 WHERE id=97;

-- user_id=34（川口雄一）: 3件→4件　設備56を受け取る（上記で設定済み）
-- user_id=35（宮崎亜弥）: 3件→5件　設備96,97を受け取る（上記で設定済み）

-- user_id=36（長谷川智）: 3件→1件　設備61,101を他へ移す
UPDATE equipment SET assigned_user_id=39 WHERE id=61;
UPDATE equipment SET assigned_user_id=40 WHERE id=101;

-- user_id=37（千葉義雄）: 3件→2件　設備102を他へ移す
UPDATE equipment SET assigned_user_id=40 WHERE id=102;

-- user_id=39（内田浩之）: 3件→4件　設備61を受け取る（上記で設定済み）
-- user_id=40（菊池美代子）: 3件→5件　設備101,102を受け取る（上記で設定済み）

-- user_id=41（今井博之）: 3件→1件　設備66,106を他へ移す
UPDATE equipment SET assigned_user_id=44 WHERE id=66;
UPDATE equipment SET assigned_user_id=45 WHERE id=106;

-- user_id=42（新井道子）: 3件→2件　設備107を他へ移す
UPDATE equipment SET assigned_user_id=45 WHERE id=107;

-- user_id=44（前田明子）: 3件→4件　設備66を受け取る（上記で設定済み）
-- user_id=45（原田一郎）: 3件→5件　設備106,107を受け取る（上記で設定済み）

-- user_id=46（牧野純子）: 3件→1件　設備71,111を他へ移す
UPDATE equipment SET assigned_user_id=49 WHERE id=71;
UPDATE equipment SET assigned_user_id=50 WHERE id=111;

-- user_id=47（竹内晴美）: 3件→2件　設備112を他へ移す
UPDATE equipment SET assigned_user_id=50 WHERE id=112;

-- user_id=49（野田敦子）: 3件→4件　設備71を受け取る（上記で設定済み）
-- user_id=50（谷口誠一）: 3件→5件　設備111,112を受け取る（上記で設定済み）

-- user_id=51（三浦美香）: 3件→1件　設備76,116を他へ移す
UPDATE equipment SET assigned_user_id=54 WHERE id=76;
UPDATE equipment SET assigned_user_id=55 WHERE id=116;

-- user_id=52（柴田和彦）: 3件→2件　設備117を他へ移す
UPDATE equipment SET assigned_user_id=55 WHERE id=117;

-- user_id=54（石井健一）: 3件→4件　設備76を受け取る（上記で設定済み）
-- user_id=55（原智子）: 3件→5件　設備116,117を受け取る（上記で設定済み）


-- ============================================================
-- 大阪拠点（設備ID: 121〜183, エンジニア21名）
-- 変更後の担当数: 1〜6件のばらつき, 合計63件
-- ============================================================

-- user_id=6（佐藤幸子）: 3件→2件　設備142を移す
UPDATE equipment SET assigned_user_id=16 WHERE id=142;

-- user_id=16（林英二）: 3件→4件　設備142を受け取る（上記で設定済み）

-- user_id=18（山口拓也）: 3件→1件　設備145,166を移す
UPDATE equipment SET assigned_user_id=19 WHERE id=145;
UPDATE equipment SET assigned_user_id=19 WHERE id=166;

-- user_id=19（松本佳奈）: 3件→5件　設備145,166を受け取る（上記で設定済み）

-- user_id=20（井上雄介）: 3件→2件　設備147を移す
UPDATE equipment SET assigned_user_id=56 WHERE id=147;

-- user_id=56（平野修平）: 3件→4件　設備147を受け取る（上記で設定済み）

-- user_id=58（荒木正樹）: 3件→2件　設備150を移す
UPDATE equipment SET assigned_user_id=57 WHERE id=150;

-- user_id=59（飯田千明）: 3件→1件　設備151,172を移す
UPDATE equipment SET assigned_user_id=57 WHERE id=151;
UPDATE equipment SET assigned_user_id=57 WHERE id=172;

-- user_id=57（太田幸恵）: 3件→6件　設備150,151,172を受け取る（上記で設定済み）

-- user_id=61（杉本弥生）: 3件→1件　設備153,174を移す
UPDATE equipment SET assigned_user_id=60 WHERE id=153;
UPDATE equipment SET assigned_user_id=60 WHERE id=174;

-- user_id=60（土屋健司）: 3件→5件　設備153,174を受け取る（上記で設定済み）

-- user_id=63（青木由佳）: 3件→2件　設備155を移す
UPDATE equipment SET assigned_user_id=62 WHERE id=155;

-- user_id=62（浜田光雄）: 3件→4件　設備155を受け取る（上記で設定済み）

-- user_id=66（野村勝利）: 3件→2件　設備158を移す
UPDATE equipment SET assigned_user_id=64 WHERE id=158;

-- user_id=67（市川和美）: 3件→1件　設備159,180を移す
UPDATE equipment SET assigned_user_id=64 WHERE id=159;
UPDATE equipment SET assigned_user_id=68 WHERE id=180;

-- user_id=64（増田裕介）: 3件→5件　設備158,159を受け取る（上記で設定済み）
-- user_id=68（奥田翼）: 3件→4件　設備180を受け取る（上記で設定済み）


-- ============================================================
-- 名古屋拠点（設備ID: 184〜246, エンジニア21名）
-- 変更後の担当数: 1〜6件のばらつき, 合計63件
-- ============================================================

-- user_id=21（木下香織）: 3件→2件　設備227を移す
UPDATE equipment SET assigned_user_id=7  WHERE id=227;

-- user_id=7（伊藤雅人）: 3件→4件　設備227を受け取る（上記で設定済み）

-- user_id=23（藤原真理）: 3件→1件　設備208,229を移す
UPDATE equipment SET assigned_user_id=22 WHERE id=208;
UPDATE equipment SET assigned_user_id=22 WHERE id=229;

-- user_id=22（岡田浩二）: 3件→5件　設備208,229を受け取る（上記で設定済み）

-- user_id=25（橋本千春）: 3件→2件　設備210を移す
UPDATE equipment SET assigned_user_id=24 WHERE id=210;

-- user_id=24（西村孝文）: 3件→4件　設備210を受け取る（上記で設定済み）

-- user_id=73（島田英里）: 3件→1件　設備213,234を移す
UPDATE equipment SET assigned_user_id=71 WHERE id=213;
UPDATE equipment SET assigned_user_id=71 WHERE id=234;

-- user_id=71（武田紗也香）: 3件→5件　設備213,234を受け取る（上記で設定済み）

-- user_id=75（永田直子）: 3件→2件　設備236を移す
UPDATE equipment SET assigned_user_id=74 WHERE id=236;

-- user_id=77（辻美紀）: 3件→1件　設備217,238を移す
UPDATE equipment SET assigned_user_id=74 WHERE id=217;
UPDATE equipment SET assigned_user_id=74 WHERE id=238;

-- user_id=74（松田龍之介）: 3件→6件　設備217,236,238を受け取る（上記で設定済み）

-- user_id=79（横山友則）: 3件→2件　設備219を移す
UPDATE equipment SET assigned_user_id=80 WHERE id=219;

-- user_id=81（大塚晃）: 3件→1件　設備221,242を移す
UPDATE equipment SET assigned_user_id=80 WHERE id=221;
UPDATE equipment SET assigned_user_id=78 WHERE id=242;

-- user_id=80（中島聖子）: 3件→5件　設備219,221を受け取る（上記で設定済み）
-- user_id=78（久保大輔）: 3件→4件　設備242を受け取る（上記で設定済み）

-- user_id=84（向井美智子）: 3件→2件　設備224を移す
UPDATE equipment SET assigned_user_id=83 WHERE id=224;

-- user_id=83（江口一夫）: 3件→4件　設備224を受け取る（上記で設定済み）


-- ============================================================
-- 福岡拠点（設備ID: 247〜270, エンジニア8名）
-- 変更後の担当数: 1〜6件のばらつき, 合計24件
-- ============================================================

-- user_id=86（南賢治）: 3件→2件　設備255を移す
UPDATE equipment SET assigned_user_id=90 WHERE id=255;

-- user_id=87（斎藤康弘）: 3件→1件　設備256,264を移す
UPDATE equipment SET assigned_user_id=88 WHERE id=256;
UPDATE equipment SET assigned_user_id=92 WHERE id=264;

-- user_id=89（大西秀行）: 3件→2件　設備258を移す
UPDATE equipment SET assigned_user_id=92 WHERE id=258;

-- user_id=91（河野純平）: 3件→1件　設備260,268を移す
UPDATE equipment SET assigned_user_id=88 WHERE id=260;
UPDATE equipment SET assigned_user_id=92 WHERE id=268;

-- user_id=88（藤井由樹）: 3件→5件　設備256,260を受け取る（上記で設定済み）
-- user_id=90（堀理恵）: 3件→4件　設備255を受け取る（上記で設定済み）
-- user_id=92（星亮太）: 3件→6件　設備258,264,268を受け取る（上記で設定済み）


-- ============================================================
-- 仙台拠点（設備ID: 271〜282, エンジニア4名）
-- 変更後の担当数: 1,5,2,4件, 合計12件
-- ============================================================

-- user_id=94（杉山広明）: 3件→1件　設備275,279を移す
UPDATE equipment SET assigned_user_id=95 WHERE id=275;
UPDATE equipment SET assigned_user_id=97 WHERE id=279;

-- user_id=96（門田健二）: 3件→2件　設備277を移す
UPDATE equipment SET assigned_user_id=95 WHERE id=277;

-- user_id=95（多田佳奈）: 3件→5件　設備275,277を受け取る（上記で設定済み）
-- user_id=97（伊東美智代）: 3件→4件　設備279を受け取る（上記で設定済み）


-- ============================================================
-- 横浜拠点（設備ID: 283〜291, エンジニア3名）
-- 変更後の担当数: 1,5,3件, 合計9件
-- ============================================================

-- user_id=98（門脇正博）: 3件→1件　設備286,289を移す
UPDATE equipment SET assigned_user_id=99 WHERE id=286;
UPDATE equipment SET assigned_user_id=99 WHERE id=289;

-- user_id=99（丸山香織）: 3件→5件　設備286,289を受け取る（上記で設定済み）
-- user_id=100（末永俊行）: 変更なし（3件のまま）

-- ============================================================
-- 全担当者の再配分が完了した後、areaを担当者の拠点に基づいて設定する
-- 担当者未設定の設備は area = NULL のまま（エリア未設定として表示される）
-- ============================================================
UPDATE equipment e
INNER JOIN employee emp ON e.assigned_user_id = emp.id
SET e.area = emp.base
WHERE e.deleted_at IS NULL;

-- 完了
