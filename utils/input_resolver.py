import os
import shutil
from typing import Optional


RUNTIME_UPLOAD_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "runtime", "uploads"
)


def ensure_runtime_dirs() -> None:
    os.makedirs(RUNTIME_UPLOAD_DIR, exist_ok=True)


def _normalize_file_uri(image_path: str) -> str:
    if image_path.startswith("file://"):
        return image_path[len("file://"):]
    return image_path


def _is_local_file(image_path: str) -> bool:
    return os.path.isfile(image_path)


def _copy_to_runtime_uploads(image_path: str) -> str:
    ensure_runtime_dirs()

    filename = os.path.basename(image_path)
    if not filename:
        raise ValueError("输入图片文件名无效。")

    target_path = os.path.join(RUNTIME_UPLOAD_DIR, filename)

    # 如果源路径和目标路径相同，就直接返回
    if os.path.abspath(image_path) == os.path.abspath(target_path):
        return target_path

    shutil.copy2(image_path, target_path)
    return target_path


def resolve_input_image(image_path: str, copy_to_runtime: bool = True) -> str:
    """
    当前版本的输入解析规则：
    1. 支持普通本地路径
    2. 支持 file:// 开头的路径
    3. 默认复制到 runtime/uploads，统一后续处理路径
    """
    if not image_path or not image_path.strip():
        raise ValueError("image_path 为空。")

    normalized_path = _normalize_file_uri(image_path.strip())

    if not _is_local_file(normalized_path):
        raise FileNotFoundError(f"输入图片不存在或不是文件: {normalized_path}")

    if copy_to_runtime:
        return _copy_to_runtime_uploads(normalized_path)

    return normalized_path
