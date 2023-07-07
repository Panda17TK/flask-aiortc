import os
from pathlib import Path

from pydantic import BaseSettings


class Settings(BaseSettings):
    LOG_LEVEL: str  # ログのレベルを指定するための設定変数

    class Config:
        try:
            env = os.environ["APP_CONFIG_FILE"]  # 環境変数 "APP_CONFIG_FILE" の値を取得し、環境設定ファイルの指定に使用する
            env_file = Path(__file__).parent / f"config/{env}.env"  # 環境設定ファイルのパスを指定する
            case_sensitive = True  # 環境変数の値の大文字と小文字を区別する
        except KeyError:
            pass