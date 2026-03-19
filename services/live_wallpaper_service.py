import os
from typing import Any, Dict, Optional

from generator.motion_director import MotionDirector
from utils.env_utils import require_google_api_key
from utils.input_resolver import resolve_input_image
from utils.video_to_gif import convert_mp4_to_gif
class LiveWallpaperService:
    """
    动态壁纸服务：
    - 基于已有静态图生成动态脚本
    - 可选是否真正生成视频
    """

    def __init__(self) -> None:
        require_google_api_key()
        self.director = MotionDirector()

    def generate(
        self,
        image_path: str,
        generate_video: bool = False,
    ) -> Dict[str, Any]:
        try:
            resolved_image_path = resolve_input_image(image_path, copy_to_runtime=False)
        except Exception as e:
            return {
                "success": False,
                "mode": "live",
                "message": f"输入图片解析失败: {e}",
            }

        print("\n🎬 [LiveService] 开始动态壁纸流程...")

        motion_result = self.director.create_motion_script(image_path)
        if not motion_result:
            return {
                "success": False,
                "mode": "live",
                "message": "动态脚本生成失败。",
            }

        result: Dict[str, Any] = {
            "success": True,
            "mode": "live",
            "message": "动态脚本生成完成。",
            "source_image": motion_result.get("source_image"),
            "style_detected": motion_result.get("style_detected"),
            "video_prompt": motion_result.get("video_prompt"),
            "video_generated": False,
            "video_path": None,
        }

        if generate_video:
            ok = self.director.generate_video(
                image_path=motion_result["source_image"],
                video_prompt=motion_result["video_prompt"],
            )
            result["video_generated"] = bool(ok)

            if ok:
                source_image = motion_result["source_image"]

                if source_image.endswith(".png"):
                    raw_mp4_path = source_image.replace(".png", "_raw.mp4")
                elif source_image.endswith(".jpg") or source_image.endswith(".jpeg"):
                    raw_mp4_path = os.path.splitext(source_image)[0] + "_raw.mp4"
                else:
                    raw_mp4_path = os.path.splitext(source_image)[0] + "_raw.mp4"

                try:
                    gif_path = convert_mp4_to_gif(raw_mp4_path)
                    result["message"] = "动态壁纸 GIF 生成完成。"
                    result["video_path"] = gif_path
                except Exception as e:
                    result["message"] = f"动态视频已生成，但 GIF 转换失败：{e}"
                    result["video_path"] = raw_mp4_path
            else:
                result["message"] = "动态脚本已生成，但视频生成失败。"

        return result