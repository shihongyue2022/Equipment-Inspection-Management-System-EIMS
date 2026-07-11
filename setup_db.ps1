# ==============================================================
# 設備点検管理システム - DB セットアップスクリプト (Windows PowerShell)
#
# 使用方法:
#   .\setup_db.ps1              # 時系列データが未投入の場合のみ適用する
#   .\setup_db.ps1 -Reset       # ボリュームを含め全削除してゼロから再作成する
#   .\setup_db.ps1 -Force       # 件数にかかわらず時系列データを強制再適用する
#
# 実行環境: Docker Desktop for Windows が必要
# 注意: 初回実行前に実行ポリシーの設定が必要な場合があります
#   Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
# ==============================================================

param(
    [switch]$Reset,  # ボリュームごと削除してゼロから再構築
    [switch]$Force   # 時系列データを強制再適用（既存データを上書き）
)

$CONTAINER      = "inspection_mysql"
$DB_NAME        = "inspection_db"
$DB_USER        = "root"
$DB_PASS        = "rootpass"
$TIMESERIES_SQL = "migrations/timeseries_inspection_data.sql"
$TARGET_RECORDS = 200000   # この件数を超えていれば投入済みと判断する

function Write-Step($n, $total, $msg) {
    Write-Host "[$n/$total] $msg" -ForegroundColor Yellow
}
function Write-Ok($msg)  { Write-Host "      OK: $msg" -ForegroundColor Green }
function Write-Err($msg) { Write-Host "ERROR: $msg" -ForegroundColor Red; exit 1 }

# ---- 現在の点検記録件数を返す関数 ----
function Get-RecordCount {
    $cnt = docker exec $CONTAINER bash -c `
        "mysql -u $DB_USER -p$DB_PASS $DB_NAME -N -e 'SELECT COUNT(*) FROM inspection_records;' 2>/dev/null" `
        2>$null
    if ([string]::IsNullOrWhiteSpace($cnt)) { return 0 }
    return [int]$cnt.Trim()
}

# ---- コンテナが healthy になるまで待機する関数 ----
function Wait-Healthy($maxSeconds = 480) {
    Write-Host "      DBの準備完了（inspection_records 200,000件超）を待機中..."
    Write-Host "      ※ 初回は timeseries データの読み込みに 1〜5 分かかります"
    $elapsed = 0
    while ($elapsed -lt $maxSeconds) {
        $health = docker inspect --format='{{.State.Health.Status}}' $CONTAINER 2>$null
        if ($health -eq "healthy") {
            Write-Ok "DB初期化完了 (${elapsed}秒経過)"
            return $true
        }
        Start-Sleep -Seconds 5
        $elapsed += 5
        $cnt = Get-RecordCount
        Write-Host "      待機中... ${elapsed}秒経過 / inspection_records: ${cnt}件"
    }
    Write-Err "タイムアウト (${maxSeconds}秒) - DBが完了しませんでした"
    return $false
}

Write-Host ""
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host " 設備点検管理システム - DB セットアップ" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host ""

# ================================================================
# -Reset モード: ボリューム削除 → 再起動 → healthcheck待ち
# ================================================================
if ($Reset) {
    Write-Step 1 3 "コンテナとボリュームを完全削除します..."
    docker compose down -v
    if ($LASTEXITCODE -ne 0) { Write-Err "docker compose down に失敗しました" }
    Write-Ok "削除完了"

    Write-Host ""
    Write-Step 2 3 "コンテナを起動します（init SQL が自動実行されます）..."
    docker compose up -d
    if ($LASTEXITCODE -ne 0) { Write-Err "docker compose up に失敗しました" }

    Write-Host ""
    Write-Step 3 3 "healthcheck 完了を待機します..."
    Wait-Healthy | Out-Null
}
# ================================================================
# 通常モード: 件数チェック → 未投入なら適用
# ================================================================
else {
    # コンテナを起動する（起動済みの場合は何もしない）
    $running = docker ps --filter "name=$CONTAINER" --filter "status=running" -q
    if (-not $running) {
        Write-Step 1 3 "コンテナを起動します..."
        docker compose up -d
        if ($LASTEXITCODE -ne 0) { Write-Err "docker compose up に失敗しました" }
        Start-Sleep -Seconds 5
    } else {
        Write-Step 1 3 "コンテナはすでに起動中です"
        Write-Ok $CONTAINER
    }

    # 現在の件数を確認する
    Write-Host ""
    Write-Step 2 3 "inspection_records の件数を確認します..."
    $count = Get-RecordCount
    Write-Host "      現在の件数: $count 件（目標: $TARGET_RECORDS 件超）"

    if (-not $Force -and $count -gt $TARGET_RECORDS) {
        Write-Ok "時系列データはすでに投入済みです（スキップ）"
        Write-Host "      強制再投入するには .\setup_db.ps1 -Force を使用してください"
    } else {
        if ($Force) { Write-Host "      -Force 指定のため再投入します..." }

        if (-not (Test-Path $TIMESERIES_SQL)) {
            Write-Err "$TIMESERIES_SQL が見つかりません。先に python migrations/generate_timeseries_data.py を実行してください"
        }

        Write-Host ""
        Write-Step 3 3 "時系列点検データをコンテナにコピーして適用します..."
        Write-Host "      ファイルコピー中 ($TIMESERIES_SQL → /tmp/timeseries.sql)..."
        docker cp $TIMESERIES_SQL "${CONTAINER}:/tmp/timeseries.sql"
        if ($LASTEXITCODE -ne 0) { Write-Err "ファイルのコピーに失敗しました" }

        Write-Host "      MySQL に適用中（1〜3分かかります）..."
        docker exec $CONTAINER bash -c "mysql -u $DB_USER -p$DB_PASS --default-character-set=utf8mb4 $DB_NAME < /tmp/timeseries.sql" 2>&1 `
            | Where-Object { $_ -notmatch "Warning|insecure" }
        if ($LASTEXITCODE -ne 0) { Write-Err "SQL の適用に失敗しました" }
        Write-Ok "適用完了"

        # データ投入完了後に web コンテナも起動する
        # （depends_on: service_healthy は起動時にしか評価されないため手動で起動が必要）
        Write-Host ""
        Write-Host "      web コンテナを起動します..."
        docker compose up -d web
        if ($LASTEXITCODE -ne 0) { Write-Host "      web の起動に失敗しました（手動で docker compose up -d web を実行してください）" -ForegroundColor DarkYellow }
        else { Write-Ok "web コンテナ起動完了" }
    }
}

# ================================================================
# 完了確認
# ================================================================
Write-Host ""
Write-Host "==== セットアップ完了 ====" -ForegroundColor Green
Write-Host ""
Write-Host "【点検記録 ステータス分布】"
docker exec $CONTAINER bash -c "mysql -u $DB_USER -p$DB_PASS --default-character-set=utf8mb4 $DB_NAME -e 'SELECT status, FORMAT(COUNT(*),0) AS 件数 FROM inspection_records GROUP BY status;'" 2>&1 `
    | Where-Object { $_ -notmatch "Warning|insecure" }
Write-Host ""
Write-Host "【設備数 / 社員数】"
docker exec $CONTAINER bash -c "mysql -u $DB_USER -p$DB_PASS --default-character-set=utf8mb4 $DB_NAME -e 'SELECT (SELECT COUNT(*) FROM equipment WHERE deleted_at IS NULL) AS 設備数, (SELECT COUNT(*) FROM employee WHERE deleted_at IS NULL) AS 社員数;'" 2>&1 `
    | Where-Object { $_ -notmatch "Warning|insecure" }
Write-Host ""
Write-Host "アプリURL: http://localhost:5000" -ForegroundColor Cyan
