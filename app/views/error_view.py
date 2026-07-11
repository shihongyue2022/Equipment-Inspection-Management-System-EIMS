"""
エラーハンドラー
404・500 エラー発生時に対応するエラー画面を表示する
"""

import logging

from flask import render_template


# ロガーを取得する
logger = logging.getLogger(__name__)


def not_found(error):
    """
    404エラー画面を表示する
    """
    return render_template("errors/404.html"), 404


def internal_error(error):
    """
    500エラー画面を表示する
    エラー内容をログに記録し、スタックトレースはブラウザに表示しない。
    """
    # エラー内容をログファイルに記録する
    logger.error("500 Internal Server Error: %s", error, exc_info=True)

    return render_template("errors/500.html"), 500
