# DBセットアップ手順

担当：せきさん

---

## Docker を使う場合（推奨）

### 前提

Docker Desktop がインストールされていない場合は、PowerShell（管理者）で以下を実行：

```powershell
winget install Docker.DockerDesktop
```

インストール後、**PCを再起動**してDocker Desktopを起動してください。
accountでlogin in必要がないです。

### 手順

**① MySQLコンテナを起動する**

プロジェクトルートで実行：

```powershell
docker compose up -d
```

初回起動時に自動で以下が完了します：
- MySQLコンテナの起動
- `inspection_db` データベースの作成
- テーブルの作成・初期データの投入

**② 起動確認**

```powershell
docker compose ps
```

`STATUS` 列が `healthy` になれば完了です。

---

### よく使うコマンド

| 操作 | コマンド |
|------|---------|
| DB起動 | `docker compose up -d` |
| DB停止 | `docker compose stop` |
| DBを完全削除してリセット | `docker compose down -v` |
| ログ確認 | `docker compose logs db` |

> `docker compose down -v` は `-v` オプションでデータも消えます。注意してください。
---

### テーブルが作られていない場合のリセット手順

MySQLの初期化SQLは**初回起動時（データが空のとき）しか実行されない**。
SQLファイルを修正した場合や、テーブルが存在しない場合は以下でリセットする：

```powershell
# コンテナとデータボリュームを完全削除
docker compose down -v

# 再起動（初期化SQLが再実行される）
docker compose up -d
```

`healthy` になったら確認：

```powershell
docker exec -it inspection_mysql mysql -u root -prootpass inspection_db -e "SHOW TABLES;"
```

---

### データベースの中身を確認する

**① コンテナの中に入る**

```powershell
docker exec -it inspection_mysql mysql -u root -prootpass inspection_db
```

**② よく使うSQLコマンド**

```sql
-- テーブル一覧を表示
SHOW TABLES;

-- 従業員データを確認
SELECT * FROM employee;

-- 設備データを確認
SELECT * FROM equipment;

-- 点検記録を確認
SELECT * FROM inspection_records;

-- MySQLを終了
EXIT;
```

**③ コンテナを経由せず1行で確認する場合**

```powershell
# 例：employeeテーブルを確認
docker exec -it inspection_mysql mysql -u root -prootpass inspection_db -e "SELECT * FROM employee;"
```

---

## ファイル構成

| ファイル | 役割 |
|---------|------|
| `docker-compose.yml` | DockerでMySQLを起動する定義ファイル |
| `app/database/create_app_db.sql` | DB・テーブル作成・初期データSQL（変更禁止） |
| `app/database/config.py` | Flaskアプリが使うDB接続設定 |
