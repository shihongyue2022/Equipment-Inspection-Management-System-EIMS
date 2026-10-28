# E_T.ECH — 設備点検管理Webアプリ

AKK空調設備株式会社向けの設備点検管理Webアプリです。  
フィールドエンジニア（FE）が点検結果を登録し、管理者がリアルタイムで把握できます。

---

## 目次

1. [前提条件（新PCへのセットアップ）](#1-前提条件新pcへのセットアップ)
2. [Dockerデプロイ（推奨・最速手順）](#2-dockerデプロイ推奨最速手順)
3. [ローカル開発環境（Notebook・開発用）](#3-ローカル開発環境notebook開発用)
4. [確認用アカウント](#4-確認用アカウント)
5. [環境変数一覧](#5-環境変数一覧)
6. [よく使うコマンド](#6-よく使うコマンド)
7. [ディレクトリ構成](#7-ディレクトリ構成)
8. [DBのリセット・確認手順](#8-dbのリセット確認手順)
9. [トラブルシューティング](#9-トラブルシューティング)
10. [テストの実行方法](#10-テストの実行方法)

---

## 1. 前提条件（新PCへのセットアップ）

### Docker Desktop（必須）

PowerShell（管理者）で実行するか、公式サイトからインストーラーをダウンロードします。

```powershell
winget install Docker.DockerDesktop
```

> インストール後は **PCを再起動** し、Docker Desktop を起動してください。  
> Docker アカウントへのログインは不要です。

### Python 3.12以上（Notebook・ローカル開発時のみ必要）

```powershell
winget install Python.Python.3.12
```

### Git

```powershell
winget install Git.Git
```

---

## 2. Dockerデプロイ（推奨・最速手順）

新PCでゼロから動かす場合はこの手順だけで完結します。

### ① リポジトリをクローンする

```powershell
git clone <リポジトリURL>
cd E_T.ECH
```

### ② .env ファイルを作成する

`.env.example` が存在しない場合は以下の内容で `.env` を作成します。

```
DB_HOST=localhost
DB_PORT=3307
DB_USER=root
DB_PASSWORD=rootpass
DB_NAME=inspection_db
SECRET_KEY=dev-secret-change-in-production
```

> `.env` は `.gitignore` に含まれているためリポジトリには存在しません。  
> 本番環境では `SECRET_KEY` を推測困難な文字列に変更してください。

### ③ コンテナを起動する

```powershell
docker compose up -d
```

初回起動時は自動で以下が完了します：
- MySQL コンテナの起動
- `inspection_db` データベースの作成
- テーブルの作成・初期データの投入（スキーマ + 社員・設備データ）
- **時系列点検データ 254,502件の投入**（1〜3分かかります）
- Flask アプリコンテナのビルドと起動

> **ポイント：** `docker-entrypoint-initdb.d/` に2つのSQLがマウントされています。  
> - `01_schema_and_data.sql` → スキーマ + 基本データ  
> - `02_timeseries.sql` → 時系列点検記録（46倍データ）  
> ボリュームが**初回作成時のみ**自動実行されます。  
>
> **healthcheck が `healthy` になるまでの目安：1〜5分**  
> MySQL の healthcheck が inspection_records の件数（20万超）を確認してから `healthy` になるため、  
> Flask アプリは全データ投入完了後に起動します。  
> `docker compose ps` で `inspection_mysql` が `healthy` になるまでお待ちください。

### ③'（別手順） セットアップスクリプトを使う

ボリューム作成済みの場合や、時系列データだけ再適用したい場合は `setup_db.ps1` を使います。

```powershell
# 時系列データのみを現在のDBに適用する（スキーマは変更しない）
.\setup_db.ps1

# ボリュームを含めてゼロから完全リセット → 全データを再投入
.\setup_db.ps1 -Reset
```

> 初回実行前に PowerShell 実行ポリシーを設定してください：  
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

### ④ 起動確認

```powershell
docker compose ps
```

両コンテナの `STATUS` が以下になれば完了です。

| コンテナ | STATUS |
|---------|--------|
| `inspection_mysql` | `healthy` |
| `inspection_web` | `Up` |

### ① Python 仮想環境を作成する

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### ② 依存ライブラリをインストールする

```powershell
pip install -r requirements.txt
```

### ③ DB だけ Docker で起動する

```powershell
docker compose up -d db
docker compose ps
```

`inspection_mysql` の `STATUS` が `healthy` になるまで待ちます。

```text
実行フロー：
MySQL起動 → DB設定 → 接続関数 → DTO → DAO → Service → Flask Route → テスト → ブラウザ確認
```

最後のセルが Flask ログイン画面の URL を出力します（例：`http://127.0.0.1:5001/login`）。

### run.pyをローカルで起動する

```powershell
python run.py
```

Running on urlでアクセスできます。

---

## 4. 確認用アカウント

| 種別 | 社員番号 | パスワード | ロール | 表示範囲 |
|------|---------|-----------|--------|---------|
| ROOT管理者 | `ROOT-000` | `root1234` | `root` | 全設備・管理機能 |
| 管理者 | `ENG-000` | `admin1234` | `admin` | 全設備・管理機能 |
| フィールドエンジニア | `ENG-008` | `password1234` | `engineer` | 自分の担当設備 |
| 学習用エンジニア | `DEMO-001` | `demo1234` | `engineer` | ログインフロー確認用 |

---

## 5. 環境変数一覧

| 変数名 | ローカル開発 | Dockerコンテナ内 | 説明 |
|--------|------------|----------------|------|
| `DB_HOST` | `localhost` | `db` | MySQLのホスト名 |
| `DB_PORT` | `3307` | `3306` | MySQLのポート番号 |
| `DB_USER` | `root` | `root` | MySQLユーザー名 |
| `DB_PASSWORD` | `rootpass` | `rootpass` | MySQLパスワード |
| `DB_NAME` | `inspection_db` | `inspection_db` | データベース名 |
| `SECRET_KEY` | 任意の文字列 | **必ず変更する** | Flaskセッション署名用キー |

> Docker コンテナ内では `DB_HOST=db`・`DB_PORT=3306` が自動的に設定されます（`docker-compose.yml` で定義）。

---

## 6. よく使うコマンド

### Docker 操作

| 操作 | コマンド |
|------|---------|
| 全コンテナ起動 | `docker compose up -d` |
| DBのみ起動 | `docker compose up -d db` |
| 全コンテナ停止 | `docker compose stop` |
| 全コンテナ停止・削除 | `docker compose down` |
| データも含めて完全リセット | `docker compose down -v` |
| Webのみ再ビルドして起動 | `docker compose up -d --build web` |
| 全コンテナのログ確認 | `docker compose logs -f` |
| Webのログ確認 | `docker compose logs -f web` |
| DBのログ確認 | `docker compose logs -f db` |
| コンテナの状態確認 | `docker compose ps` |

### DB 操作

| 操作 | コマンド |
|------|---------|
| MySQL に接続する | `docker exec -it inspection_mysql mysql -u root -prootpass inspection_db` |
| テーブル一覧を確認する | `docker exec -it inspection_mysql mysql -u root -prootpass inspection_db -e "SHOW TABLES;"` |
| employee テーブルを確認する | `docker exec -it inspection_mysql mysql -u root -prootpass inspection_db -e "SELECT id, employee_no, role FROM employee;"` |
| equipment テーブルを確認する | `docker exec -it inspection_mysql mysql -u root -prootpass inspection_db -e "SELECT id, name, next_inspection_date FROM equipment;"` |

### Python 仮想環境

| 操作 | コマンド（PowerShell） |
|------|----------------------|
| 仮想環境を作成する | `python -m venv venv` |
| 仮想環境を有効化する | `.\venv\Scripts\Activate.ps1` |
| 依存ライブラリをインストールする | `pip install -r requirements.txt` |
| 依存ライブラリを更新する | `pip install -r requirements.txt --upgrade` |

---

## 7. ディレクトリ構成

Gitで管理されているファイルに基づく主な構成です。migrations/ と tests/ の内容は省略しています。ローカルで作成する `.env`、仮想環境、キャッシュなどは含みません。

```text
Equipment-Inspection-Management-System-EIMS/
├── app/
│   ├── accounts/
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── auth/
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── common/
│   │   ├── __init__.py
│   │   └── auth.py
│   ├── dao/
│   │   ├── __init__.py
│   │   ├── dao.py
│   │   ├── equipment_dao.py
│   │   ├── inspection_dao.py
│   │   └── user_dao.py
│   ├── dashboard/
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── create_app_db.sql
│   ├── dto/
│   │   ├── __init__.py
│   │   ├── equipment_dto.py
│   │   ├── inspection_dto.py
│   │   └── user_dto.py
│   ├── equipment/
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── inspections/
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── maintenance/
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── accounts.py
│   │   ├── dashboard.py
│   │   ├── equipment.py
│   │   ├── inspection.py
│   │   └── maintenance.py
│   ├── static/
│   │   ├── vendor/
│   │   │   ├── tabler/
│   │   │   │   ├── css/
│   │   │   │   │   └── tabler.min.css
│   │   │   │   ├── js/
│   │   │   │   │   └── tabler.min.js
│   │   │   │   └── LICENSE
│   │   │   └── tabler-icons/
│   │   │       ├── fonts/
│   │   │       │   ├── tabler-icons.ttf
│   │   │       │   ├── tabler-icons.woff
│   │   │       │   └── tabler-icons.woff2
│   │   │       ├── LICENSE
│   │   │       └── tabler-icons.min.css
│   │   ├── .gitkeep
│   │   ├── e_team.png
│   │   ├── et_ech_white.png
│   │   ├── logo.png
│   │   └── style.css
│   ├── templates/
│   │   ├── account/
│   │   │   ├── detail.html
│   │   │   ├── list.html
│   │   │   ├── my_password.html
│   │   │   └── new.html
│   │   ├── equipment/
│   │   │   ├── detail.html
│   │   │   ├── edit.html
│   │   │   ├── list.html
│   │   │   └── new.html
│   │   ├── errors/
│   │   │   ├── 404.html
│   │   │   └── 500.html
│   │   ├── inspection/
│   │   │   └── new.html
│   │   ├── maintenance/
│   │   │   └── form.html
│   │   ├── partials/
│   │   │   └── group_chart_row.html
│   │   ├── recycle_bin/
│   │   │   └── index.html
│   │   ├── .gitkeep
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── login.html
│   │   └── session_timeout.html
│   ├── views/
│   │   ├── .gitkeep
│   │   ├── __init__.py
│   │   ├── account_view.py
│   │   ├── auth_view.py
│   │   ├── dashboard_view.py
│   │   ├── equipment.py
│   │   ├── error_view.py
│   │   ├── inspection_view.py
│   │   ├── notification_view.py
│   │   └── recycle_bin_view.py
│   ├── __init__.py
│   ├── config.py
│   ├── constants.py
│   ├── extensions.py
│   ├── forms.py
│   ├── models.py
│   └── utils.py
├── migrations/                  # DBマイグレーション（詳細省略）
├── tests/                       # 自動テスト（詳細省略）
├── .dockerignore
├── .env.example
├── .gitignore
├── Dockerfile
├── README.md
├── THIRD_PARTY_NOTICES.md
├── docker-compose.cloud-db.yml
├── docker-compose.yml
├── pytest.ini
├── requirements.txt
├── run.py
└── setup_db.ps1
```


---

## 8. DBのリセット・確認手順

### 最速リセット（スクリプト推奨）

```powershell
# ボリュームを含めてゼロから再作成（スキーマ + 全データ自動投入）
.\setup_db.ps1 -Reset
```

### 手動でリセットする場合

MySQL の初期化 SQL は**ボリューム初回作成時のみ実行**されます。  
SQL ファイルを修正した場合やテーブルが存在しない場合は以下でリセットします。

```powershell
# コンテナとデータボリュームを完全削除
docker compose down -v

# 再起動（初期化SQLが再実行される。1〜3分かかる）
docker compose up -d
```

`healthy` になったらテーブルを確認します。

```powershell
docker exec -it inspection_mysql mysql -u root -prootpass inspection_db -e "SHOW TABLES;"
```

### MySQL に直接接続して操作する

```powershell
docker exec -it inspection_mysql mysql -u root -prootpass inspection_db
```

接続後は通常の MySQL コマンドが使えます。

```sql
-- テーブル一覧
SHOW TABLES;

-- 従業員データを確認
SELECT id, employee_no, last_name, first_name, role FROM employee;

-- 設備データを確認
SELECT id, name, next_inspection_date FROM equipment;

-- 点検記録を確認
SELECT * FROM inspection_records ORDER BY inspected_at DESC LIMIT 10;

-- 終了
EXIT;
```

---

## 9. トラブルシューティング

| エラー | 主な原因 | 対処法 |
|--------|---------|--------|
| `Connection refused` | MySQL 未起動・ポート違い | `docker compose ps` で状態確認。`DB_PORT=3307`（ローカル）/ `3306`（Docker内）を確認 |
| `Access denied` | user/password 違い | `.env` の `DB_USER`・`DB_PASSWORD` を確認 |
| `Unknown database` | DB 未初期化 | `docker compose down -v && docker compose up -d` でリセット |
| ログイン画面が表示されない | Webコンテナ未起動 | `docker compose logs web` でエラー内容を確認 |
| テンプレートが見つからない | `app/templates/` のパス問題 | `docker compose up -d --build web` で再ビルド |
| 社員番号・パスワードエラー | 初期データ未投入 | DBリセット手順を実施 |
| PowerShell で `.ps1` が実行できない | 実行ポリシーの制限 | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` を実行 |

---

## 10. テストの実行方法

テストは `unittest.mock` でDAO層をモック化しているため、**DB接続・Dockerは不要**です。  
仮想環境が有効な状態で実行してください。

### 事前準備

```powershell
# 仮想環境を有効化する（まだの場合）
.\venv\Scripts\Activate.ps1

# 依存ライブラリをインストールする（まだの場合）
pip install -r requirements.txt
```

### テストを実行する

```powershell
# すべてのテストを実行する
pytest tests/ -v
```

```powershell
# ファイルを指定して実行する
pytest tests/test_account_view.py -v
```

### 出力例

```
tests/test_account_view.py::test_list_accessible_for_root PASSED
tests/test_account_view.py::test_list_accessible_for_admin PASSED
tests/test_account_view.py::test_list_blocked_for_engineer PASSED
...
32 passed in 0.XXs
```

### テストファイル一覧

| ファイル | 対象機能 | DB接続 |
|---------|---------|--------|
| `tests/test_account_view.py` | アカウント管理ビューの権限制御（32件） | 不要（モック使用） |

> 新しいテストを追加する場合は `tests/conftest.py` のフィクスチャ（`client`・`login_as`）を使用してください。

---

## 11. TiDB Cloud を使ってローカル Docker からオンライン DB に接続する手順(PORT: 4000が禁じされない前提として使える)

本プロジェクトは、通常のローカル開発では Docker の MySQL を使用します。
この章では、Web アプリは自分の PC の Docker で動かし、DB だけ TiDB Cloud に切り替える手順を説明します。

```text
Web: ローカル Docker container（Flask）
DB : TiDB Cloud Starter（MySQL プロトコル互換）
```

この構成では、外部公開 URL は作成されません。ブラウザでは次の URL から確認します。

### 11.1 登録が必要なサービス

1. TiDB Cloud：https://www.pingcap.com/tidb-cloud-starter/  
   無料枠のクラウドデータベースを作成します。

注意：DB パスワード、TiDB の接続パスワードは Git にコミットしないでください。README にも直接書かないでください。

### 11.2 スクリーンショットの保存場所

この章のスクリーンショットは、次のフォルダに保存します。

```text
docs/images/deploy/
```

保存するファイル名は、手順ごとに固定します。画像を保存すると README 上に表示されます。

| 手順 | ファイル名 | 内容 |
|---|---|---|
| 1 | `01_tidb_starter_signup.png` | TiDB Cloud Starter の登録画面 |
| 2 | `02_tidb_project_view.png` | Project View と `Create Resource` |
| 3 | `03_tidb_create_resource_settings.png` | Starter / Project / Instance / Region / Spending Limit の設定 |
| 4 | `04_tidb_overview_active.png` | Instance Overview と `Status: Active` |
| 5 | `05_tidb_connect_parameters.png` | Connect 画面の Host / Port / Username |
| 6 | `06_powershell_import_sql.png` | PowerShell で SQL を投入した結果 |
| 7 | `07_localhost_login.png` | ログイン画面 |

> 画像にパスワードが写っている場合は、保存前に必ず塗りつぶしてください。

### 11.3 TiDB Cloud データベースを作成する

1. TiDB Cloud を開きます。

```text
https://www.pingcap.com/tidb-cloud-starter/
```

2. `Start for Free` からアカウントを作成します。
   GitHub アカウント、Google アカウント、またはメールアドレスで登録できます。

![TiDB Cloud Starter Signup](docs/images/deploy/01_tidb_starter_signup.png)

スクリーンショット内容の目安：

```text
TiDB Cloud Starter
Start for Free
Sign up / Log in
```

3. ログイン後、TiDB Cloud のコンソール画面を開きます。
   初回ログイン時は `Default Project` や `db` のような Project が既に作成されている場合があります。
   その場合は新しく Project を作らず、そのまま既存の Project を使用して構いません。

![TiDB Cloud Project View](docs/images/deploy/02_tidb_project_view.png)

スクリーンショット内容の目安：

```text
My TiDB
  Resource View / Project View
  db  Total 0 instances

右上:
  Create Resource
  Create Project
```

   画面上部で `Project View` を選択すると、Project 一覧を確認しやすくなります。
   既存 Project がある場合は、その Project の中に Resource / Instance を作成します。

   Project が 1 つも存在しない場合だけ、右上の `Create Project` から作成します。

```text
Project Name: e-tech-inspection
```

4. 右上の `Create Resource` をクリックします。
   `Create Project` ではありません。
   `Create Resource` は、TiDB の Resource / Instance / Cluster を作成するためのボタンです。

   表示される選択肢の中から、無料枠に該当する TiDB を選択します。
   画面によって名称が少し違う場合があります。次のいずれかを探してください。

```text
TiDB Cloud Starter
Starter
Serverless
TiDB Cluster
```

   既に Resource / Instance 一覧画面が表示されている場合も、作成ボタンは画面右上または中央付近にあります。

5. Plan は `Starter` を選択します。
   `From $0/month` と表示されていることを確認してください。
   `Essential`、`Premium`、`Dedicated` は有料プランなので選択しません。

6. Cloud Provider と Region を選択します。
   日本から使う場合は、次の設定で問題ありません。

```text
Cloud Provider: AWS
Region: Tokyo (ap-northeast-1)
```

7. Basic Settings を入力します。

```text
Project: 既存の Project（例: db）
Instance Name: e-tech-inspection
```

8. Capacity の `Monthly Spending Limit` は `$0.00` のままにします。
   右側の Summary で `Spending Limit: $0 / month` と表示されていることを確認してください。

9. Advanced Settings は変更しません。
   `Dual-Layer Data Encryption` はオフのままで構いません。

```text
Dual-Layer Data Encryption: Disabled
```

10. 右側の Summary を確認します。

```text
Plan: Starter
Project: db
Instance Name: e-tech-inspection
Cloud Provider: AWS
Region: Tokyo (ap-northeast-1)
Spending Limit: $0 / month
Dual-Layer Data Encryption: Disabled
```

問題なければ、右下の `Create` をクリックします。

![TiDB Cloud Create Resource Settings](docs/images/deploy/03_tidb_create_resource_settings.png)

スクリーンショット内容の目安：

```text
Create Resource
Plan: Starter
Project: db
Instance Name: e-tech-inspection
Cloud Provider: AWS
Region: Tokyo (ap-northeast-1)
Monthly Spending Limit: $0.00
Dual-Layer Data Encryption: Disabled
Create
```

11. 作成後、Overview 画面で Status を確認します。
    `Creating` の間はまだ接続できません。数分待ち、`Active` になってから次に進みます。

![TiDB Cloud Overview Active](docs/images/deploy/04_tidb_overview_active.png)

スクリーンショット内容の目安：

```text
Overview
Instance Properties
  Instance Name: e-tech-inspection
  Status: Active
  Plan: Starter
  Region: Tokyo (ap-northeast-1)
```

12. 右上の `Connect` をクリックします。

![TiDB Cloud Connect Parameters](docs/images/deploy/05_tidb_connect_parameters.png)

スクリーンショット内容の目安：

```text
Connect to e-tech-inspection
Connection Type: Public
Database: inspection_db または sys
Operating System: Windows
Connect With: General
Generate Password
Parameters:
  HOST
  PORT
  USERNAME
  PASSWORD
```

13. `Generate Password` をクリックし、DB パスワードを生成します。
    生成されたパスワードは、この後 `.env` の `DB_PASSWORD` で使用します。
    パスワードは安全な場所に保存し、Git や README には書かないでください。

14. `Parameters` に表示される次の接続情報を控えます。

```text
HOST: gateway01.ap-northeast-1.prod.aws.tidbcloud.com
PORT: 4000
USERNAME: TiDB Cloud に表示されたユーザー名
PASSWORD: Generate Password で生成したパスワード
DATABASE: 後で inspection_db を使用する
```

TiDB Cloud の Connect 画面では `DATABASE: sys` と表示される場合がありますが、本プロジェクトでは `inspection_db` を作成して使用します。

`.env` には通常、次の値を設定します。

```text
DB_HOST=gateway01.ap-northeast-1.prod.aws.tidbcloud.com
DB_PORT=4000
DB_USER=TiDB Cloud に表示されたユーザー名
DB_PASSWORD=Generate Password で生成したパスワード
DB_NAME=inspection_db
DB_SSL=true
```

### 11.4 クラウド DB にテーブルと初期データを投入する

TiDB Cloud の SQL Editor に長い SQL を貼り付ける方法もありますが、本プロジェクトでは SQL ファイルが長く、日本語コメントも含むため、ローカル PowerShell から Docker の MySQL client を使って投入する方法を推奨します。

> 注意：PowerShell の `Get-Content ... | docker run ... mysql` で流し込むと、UTF-8 の日本語が崩れて SQL エラーになる場合があります。  
> この手順では、プロジェクトフォルダを Docker コンテナにマウントし、コンテナ内から SQL ファイルを直接読み込みます。

1. PowerShell でプロジェクトルートに移動します。

```powershell
cd D:\projects\E_T.ECH
```

2. TiDB Cloud の接続情報を環境変数に設定します。
   `TIDB_PASSWORD` には、`Generate Password` で生成したパスワードを入力してください。

```powershell
$env:TIDB_HOST="gateway01.ap-northeast-1.prod.aws.tidbcloud.com"
$env:TIDB_PORT="4000"
$env:TIDB_USER="<TiDB Cloud に表示された USERNAME>"
$env:TIDB_PASSWORD="<Generate Password で生成したパスワード>"
```

3. Docker の MySQL client で DB 作成と初期 SQL 投入を行います。
   ローカルに `mysql` コマンドをインストールしていなくても、このコマンドで実行できます。

```powershell
docker run --rm -i `
  -e TIDB_HOST `
  -e TIDB_PORT `
  -e TIDB_USER `
  -e TIDB_PASSWORD `
  -v "${PWD}:/work" `
  mysql:8.0 `
  sh -c 'mysql --default-character-set=utf8mb4 --host="$TIDB_HOST" --port="$TIDB_PORT" --user="$TIDB_USER" --password="$TIDB_PASSWORD" --ssl-mode=REQUIRED < /work/app/database/create_app_db.sql'
```

実行時に次の警告が出る場合がありますが、処理が止まっていなければ問題ありません。

```text
mysql: [Warning] Using a password on the command line interface can be insecure.
```

4. テーブルが作成されたことを確認します。

```powershell
docker run --rm -i `
  -e TIDB_HOST `
  -e TIDB_PORT `
  -e TIDB_USER `
  -e TIDB_PASSWORD `
  mysql:8.0 `
  mysql `
  --host="$env:TIDB_HOST" `
  --port="$env:TIDB_PORT" `
  --user="$env:TIDB_USER" `
  --password="$env:TIDB_PASSWORD" `
  --ssl-mode=REQUIRED `
  inspection_db `
  -e "SHOW TABLES;"
```

次のようなテーブルが表示されれば成功です。

```text
base
employee
equipment
inspection_records
```

![PowerShell SQL Import Result](docs/images/deploy/06_powershell_import_sql.png)

スクリーンショット内容の目安：

```text
Tables_in_inspection_db
base
employee
equipment
inspection_records
```

5. よくあるエラーと対処方法です。

```text
mysql: The term 'mysql' is not recognized
```

ローカル PC に MySQL client が入っていない状態です。上記の `docker run ... mysql:8.0` コマンドを使用してください。

```text
ERROR 1064 ... near "????"
```

PowerShell のパイプ経由で SQL を渡したため、日本語コメントや文字列のエンコードが崩れている可能性があります。`Get-Content ... | docker run` ではなく、`-v "${PWD}:/work"` でマウントして `/work/app/database/create_app_db.sql` を直接読み込んでください。

### 11.5 ローカル Docker の Web から TiDB Cloud に接続する

Web アプリは自分の PC の Docker で起動し、DB だけ TiDB Cloud を使う構成です。

```text
ローカル PC
  Docker web container（Flask）
        |
        | SSL/TLS
        v
TiDB Cloud Starter（inspection_db）
```

この方法では、外部公開 URL は作成されません。自分の PC で確認します。

1. `.env` を TiDB Cloud 用に変更します。

```env
DB_HOST=gateway01.ap-northeast-1.prod.aws.tidbcloud.com
DB_PORT=4000
DB_USER=<TiDB Cloud に表示された USERNAME>
DB_PASSWORD=<Generate Password で生成したパスワード>
DB_NAME=inspection_db
DB_SSL=true
SECRET_KEY=dev-secret-change-in-production
```

2. ローカル MySQL コンテナは起動せず、Web コンテナだけ起動します。

```powershell
docker compose -f docker-compose.yml -f docker-compose.cloud-db.yml up -d --build web
```

3. ログを確認します。

```powershell
docker compose -f docker-compose.yml -f docker-compose.cloud-db.yml logs -f web
```

4. ブラウザでログイン画面を開きます。

Docker のログに次のような表示が出る場合があります。

```text
* Running on http://172.18.0.3:5000
```

これは Docker コンテナ内部のネットワークアドレスです。ブラウザからアクセスする場合は、通常このアドレスではなく、ポート公開されたローカル PC 側のアドレスを使用します。

```text
Docker内部のURL:
http://172.18.0.3:5000
```

`docker-compose.yml` では次のようにポートを公開しています。

```yaml
ports:
  - "5000:5000"
```

そのため、アクセスの流れは次のようになります。

```text
PC の localhost:5000
  -> Docker コンテナの 5000 番ポート
  -> Flask アプリ
```

![Localhost Login](docs/images/deploy/07_localhost_login.png)

スクリーンショット内容の目安：

```text
設備点検管理システム
ログイン
社員番号
パスワード
```

5. 初期確認用アカウントでログインします。

| ロール | 社員番号 | パスワード |
|---|---|---|
| ROOT 管理者 | `ROOT-000` | `root1234` |
| 管理者 | `ENG-000` | `admin1234` |
| エンジニア | `ENG-008` | `password1234` |
| Demo エンジニア | `DEMO-001` | `demo1234` |

6. 停止する場合は次を実行します。

```powershell
docker compose -f docker-compose.yml -f docker-compose.cloud-db.yml down
```

> 注意：この構成では DB は TiDB Cloud に保存されます。ローカルの `db_data` volume は使用しません。

### 11.6 よくあるエラー

| エラー | 主な原因 | 対応方法 |
|---|---|---|
| `Access denied` | DB ユーザー名またはパスワードが違う | `.env` の `DB_USER` / `DB_PASSWORD` を確認する |
| `Unknown database` | `inspection_db` が作成されていない | TiDB で DB を作成する、または SQL を再実行する |
| `Connection refused` | Host、Port、SSL 設定が違う | `DB_PORT=4000`、`DB_SSL=true` を確認する |
| 500 ページ | アプリは起動したが DB クエリに失敗している | `docker compose ... logs -f web` を確認する |
| ログインできない | 初期データが投入されていない | `create_app_db.sql` を実行する |

### 11.7 ローカル Docker と TiDB Cloud 接続の違い

| 環境 | データベース | DB_HOST | DB_PORT | DB_SSL |
|---|---|---|---|---|
| ローカル Docker | MySQL コンテナ | `localhost` または `db` | `3307` または `3306` | `false` |
| ローカル Docker + TiDB Cloud | TiDB Cloud | TiDB Host | `4000` | `true` |

ローカル開発では、これまでどおり Docker を使用します。

```powershell
docker compose up -d
```

Web アプリを自分の PC で確認するだけなら、ローカル Docker + TiDB Cloud で十分です。
