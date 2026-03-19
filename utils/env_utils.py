import os
from typing import Dict
from dotenv import load_dotenv


load_dotenv()


def check_google_api_key() -> Dict[str, str]:
    """
    检查 GOOGLE_API_KEY 是否存在，并返回统一结构。
    """
    api_key = os.getenv("GOOGLE_API_KEY", "").strip()
    if api_key:
        return {
            "ok": True,
            "message": "GOOGLE_API_KEY 已配置。"
        }

    return {
        "ok": False,
        "message": (
            "未检测到 GOOGLE_API_KEY。\n"
            "请在项目根目录创建 .env 文件，并加入：\n"
            "GOOGLE_API_KEY=your_real_api_key\n\n"
            "注意：\n"
            "1. 不要把真实 key 放进 .env.example\n"
            "2. 请把 .env 加入 .gitignore\n"
        )
    }


def require_google_api_key() -> None:
    """
    强校验：如果没配置 key，直接抛错。
    """
    result = check_google_api_key()
    if not result["ok"]:
        raise ValueError(result["message"])