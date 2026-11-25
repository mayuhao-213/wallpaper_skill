import os
import json
import argparse
from typing import Any, Dict, List, Optional

from services.static_wallpaper_service import StaticWallpaperService
from services.live_wallpaper_service import LiveWallpaperService
from utils.env_utils import check_google_api_key


class WallpaperSkill:
    """
    Wallpaper Skill 统一入口
    支持三种模式：
    - static: 只生成静态壁纸
    - live:   基于已有静态壁纸生成动态脚本 / 视频
    - both:   先生成静态壁纸，再基于结果继续生成动态脚本 / 视频
    """

    def __init__(self) -> None:
        self.static_service = StaticWallpaperService()
        self.live_service = LiveWallpaperService()

    def run_static(
        self,
        image_path: str,
        count: int = 1,
        styles: Optional[List[str]] = None,
        output_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self.static_service.generate(
            image_path=image_path,
            count=count,
            styles=styles,
            output_dir=output_dir,
        )

    def run_live(
        self,
        image_path: str,
        generate_video: bool = False,
    ) -> Dict[str, Any]:
        return self.live_service.generate(
            image_path=image_path,
            generate_video=generate_video,
        )

    def run_both(
        self,
        image_path: str,
        count: int = 1,
        styles: Optional[List[str]] = None,
        output_dir: Optional[str] = None,
        generate_video: bool = False,
    ) -> Dict[str, Any]:
        static_result = self.run_static(
            image_path=image_path,
            count=count,
            styles=styles,
            output_dir=output_dir,
        )

        if not static_result.get("success"):
            return {
                "success": False,
                "mode": "both",
                "message": "静态壁纸阶段失败，无法继续生成动态壁纸。",
                "static_result": static_result,
                "live_results": [],
            }

        live_results: List[Dict[str, Any]] = []

        for item in static_result.get("results", []):
            generated_image_path = item.get("image_path")
            if not generated_image_path:
                live_results.append({
                    "success": False,
                    "mode": "live",
                    "message": "静态壁纸未生成成功，跳过动态壁纸阶段。",
                    "source_image": None,
                    "video_generated": False,
                    "video_path": None,
                })
                continue

            live_result = self.run_live(
                image_path=generated_image_path,
                generate_video=generate_video,
            )
            live_results.append(live_result)

        overall_success = static_result.get("success") and any(
            item.get("success") for item in live_results
        )

        return {
            "success": overall_success,
            "mode": "both",
            "message": "静态 + 动态流程执行完成。",
            "static_result": static_result,
            "live_results": live_results,
        }

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        统一入口，供 CLI / OpenClaw 后续接入使用。

        payload 示例：
        {
          "mode": "static",
          "image_path": "examples/demo_inputs/garden_ghibli_pure.png",
          "count": 1,
          "styles": ["makoto_shinkai"],
          "output_dir": "examples/demo_outputs/test_case",
          "generate_video": false
        }
        """
        mode = (payload.get("mode") or "static").strip().lower()
        image_path = payload.get("image_path")

        if not image_path:
            return {
                "success": False,
                "mode": mode,
                "message": "缺少必填参数 image_path。",
            }

        if not os.path.exists(image_path):
            return {
                "success": False,
                "mode": mode,
                "message": f"输入图片不存在: {image_path}",
            }

        if mode == "static":
            return self.run_static(
                image_path=image_path,
                count=payload.get("count", 1),
                styles=payload.get("styles"),
                output_dir=payload.get("output_dir"),
            )

        if mode == "live":
            return self.run_live(
                image_path=image_path,
                generate_video=payload.get("generate_video", False),
            )

        if mode == "both":
            return self.run_both(
                image_path=image_path,
                count=payload.get("count", 1),
                styles=payload.get("styles"),
                output_dir=payload.get("output_dir"),
                generate_video=payload.get("generate_video", False),
            )

        return {
            "success": False,
            "mode": mode,
            "message": f"不支持的 mode: {mode}，可选值为 static / live / both。",
        }


def format_result(result: Dict[str, Any]) -> str:
    """
    将结果格式化为更易读的 JSON 字符串。
    """
    return json.dumps(result, ensure_ascii=False, indent=2)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Wallpaper Skill Runner")

    parser.add_argument("--mode", default="static", choices=["static", "live", "both"])
    parser.add_argument("--image", required=True, help="输入图片路径")
    parser.add_argument("--count", type=int, default=1, help="静态壁纸数量，默认 1")
    parser.add_argument("--styles", nargs="*", default=None, help="可选：指定风格列表")
    parser.add_argument("--output-dir", default=None, help="静态壁纸输出目录")
    parser.add_argument("--video", action="store_true", help="live / both 模式下是否真正生成视频")

    return parser.parse_args()


def build_payload_from_args(args: argparse.Namespace) -> Dict[str, Any]:
    return {
        "mode": args.mode,
        "image_path": args.image,
        "count": args.count,
        "styles": args.styles,
        "output_dir": args.output_dir or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "runtime", "outputs", "openclaw_runs"
        ),
        "generate_video": args.video,
    }


def main() -> None:
    env_check = check_google_api_key()
    if not env_check["ok"]:
        print(env_check["message"])
        return

    args = parse_args()
    payload = build_payload_from_args(args)

    skill = WallpaperSkill()
    result = skill.run(payload)

    print("\n" + "=" * 80)
    print("WALLPAPER SKILL RESULT")
    print("=" * 80)
    print(format_result(result))


if __name__ == "__main__":
    main()
