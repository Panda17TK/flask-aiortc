import logging
from dataclasses import dataclass
from typing import Mapping

from flask import Flask, jsonify, request

DEFAULT_DEVELOPER_MESSAGE = ""
DEFAULT_CODE = "000"

logger = logging.getLogger(__name__)
app = Flask(__name__)


def init_app(app: Flask) -> None:
    # 例外ハンドラの登録
    app.register_error_handler(400, validation_exception_handler)
    app.register_error_handler(404, not_found_handler)


@dataclass(frozen=True)
class Error:
    developer_message: str = ""
    code: str = "000"

    def to_response(self) -> Mapping:
        return {
            "code": self.code,
            "developer_message": self.developer_message,
        }


@app.errorhandler(400)
def validation_exception_handler(exc):
    """リクエストパラメータのバリデーションエラーハンドラー"""
    logger.info(exc)
    errors = [Error(developer_message=str(exc))]
    return jsonify({"errors": [error.to_response() for error in errors]}), 400


@app.errorhandler(404)
def not_found_handler(exc):
    """404のエラーハンドラー"""
    error = Error(
        developer_message="Not found",
        code=DEFAULT_CODE,
    )
    return jsonify({"errors": [error.to_response()]}), 404
