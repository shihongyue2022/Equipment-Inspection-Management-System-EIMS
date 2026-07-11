import json
import pymysql
from pymysql.cursors import DictCursor
from app.database.config import DB_CONFIG


class Dao:
    """全DAOクラスの基底クラス。接続の確立と切断を担当する。"""

    def __init__(self):
        """MySQLへの接続を確立し、self.conn と self.cursor を生成する。"""
        connect_options = {
            "host":        DB_CONFIG["host"],
            "port":        DB_CONFIG["port"],
            "user":        DB_CONFIG["user"],
            "password":    DB_CONFIG["password"],
            "database":    DB_CONFIG["database"],
            "charset":     DB_CONFIG["charset"],
            "cursorclass": DictCursor,
        }
        if DB_CONFIG.get("ssl"):
            connect_options["ssl"] = {}
        self.conn = pymysql.connect(**connect_options)
        self.cursor = self.conn.cursor()

    def close(self):
        """self.cursor と self.conn をクローズし、DBとの接続を切断する。"""
        self.cursor.close()
        self.conn.close()

    def __enter__(self):
        """with文でDAOを使えるようにする"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """with文を抜けたら自動でclose()を呼ぶ"""
        self.close()

    def _log_audit(self, table_name, record_id, action, old_data, changed_by, batch_id=None):
        """audit_logテーブルに操作履歴を挿入する。呼び出し元のトランザクション内で実行される。
        batch_id: 一括操作のグループID（UUID）。単件操作はNone。
        """
        sql = """
            INSERT INTO audit_log (table_name, record_id, action, old_data, changed_by, batch_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        old_data_json = json.dumps(old_data, default=str) if old_data else None
        self.cursor.execute(sql, (table_name, record_id, action, old_data_json, changed_by, batch_id))

    def _soft_delete_record(self, table_name, record_id, deleted_by):
        """指定テーブルのレコードを論理削除する共通メソッド。
        deleted_at と deleted_by を現在時刻・操作者IDで更新する。
        戻り値: 更新された行数（0の場合は対象なし）
        ※ table_name は固定文字列（DAO内のハードコード値）のみ渡すこと。
        """
        sql = """
            UPDATE {}
            SET deleted_at = NOW(), deleted_by = %s
            WHERE id = %s AND deleted_at IS NULL
        """.format(table_name)
        self.cursor.execute(sql, (deleted_by, record_id))
        return self.cursor.rowcount

    def _restore_record(self, table_name, record_id, restored_by):
        """指定テーブルの論理削除済みレコードを復元する共通メソッド。
        deleted_at と deleted_by を NULL にリセットする。
        戻り値: 更新された行数（0の場合は対象なし）
        ※ table_name は固定文字列（DAO内のハードコード値）のみ渡すこと。
        """
        sql = """
            UPDATE {}
            SET deleted_at = NULL, deleted_by = NULL
            WHERE id = %s AND deleted_at IS NOT NULL
        """.format(table_name)
        self.cursor.execute(sql, (record_id,))
        return self.cursor.rowcount
