import os
import sys
import json
import argparse

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils.env_utils import check_google_api_key
from services.static_wallpaper_service import StaticWallpaperService
from services.live_wallpaper_service import LiveWallpaperService


def print_title(title: str) -> None:
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def test_env_check() -> None:
    print_title("TEST 1: API KEY CHECK")
    result = check_google_api_key()
    print(result["message"])
    print(f"OK: {result['ok']}")


def test_service_init() -> None:
    print_title("TEST 2: SERVICE INITIALIZATION")

    try:
        StaticWallpaperService()
        print("✅ StaticWallpaperService 初始化成功")
    except Exception as e:
        print(f"❌ StaticWallpaperService 初始化失败: {e}")

    try:
        LiveWallpaperService()
        print("✅ LiveWallpaperService 初始化成功")
    except Exception as e:
        print(f"❌ LiveWallpaperService 初始化失败: {e}")


def run_static_case(case_name: str, payload: dict) -> None:
    print_title(f"STATIC CASE: {case_name}")

    service = StaticWallpaperService()
    result = service.generate(
        image_path=payload["image_path"],
        count=payload.get("count", 1),
        styles=payload.get("styles"),
        output_dir=payload.get("output_dir"),
    )

    print(f"success: {result.get('success')}")
    print(f"message: {result.get('message')}")
    print(f"description: {result.get('description')}")
    print(f"reasoning: {result.get('reasoning')}")

    for idx, item in enumerate(result.get("results", []), 1):
        print(f"\n[{idx}]")
        print(f"style_key: {item.get('style_key')}")
        print(f"style_name: {item.get('style_name')}")
        print(f"is_fallback: {item.get('is_fallback')}")
        print(f"requested_style: {item.get('requested_style')}")
        print(f"image_path: {item.get('image_path')}")
        print(f"caption: {item.get('caption')}")


def run_live_case(case_name: str, payload: dict) -> None:
    print_title(f"LIVE CASE: {case_name}")

    service = LiveWallpaperService()
    result = service.generate(
        image_path=payload["image_path"],
        generate_video=payload.get("generate_video", False),
    )

    print(f"success: {result.get('success')}")
    print(f"message: {result.get('message')}")
    print(f"style_detected: {result.get('style_detected')}")
    print(f"video_prompt: {result.get('video_prompt')}")
    print(f"video_generated: {result.get('video_generated')}")
    print(f"video_path: {result.get('video_path')}")


def run_demo_file(demo_file: str, case_name: str = None) -> None:
    if not os.path.exists(demo_file):
        print(f"❌ demo 文件不存在: {demo_file}")
        return

    with open(demo_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    cases = data.get("demo_cases", [])
    if not cases:
        print("⚠️ demo_cases 为空")
        return

    for case in cases:
        name = case.get("name", "unnamed_case")
        service_type = case.get("service")
        payload = case.get("input", {})

        if case_name and name != case_name:
            continue

        if service_type == "static":
            run_static_case(name, payload)
        elif service_type == "live":
            run_live_case(name, payload)
        else:
            print(f"⚠️ 未知 service 类型: {service_type}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Wallpaper Skill Tests")
    parser.add_argument("--demo", help="demo_input.json 路径")
    parser.add_argument("--case", help="只运行指定 case 名称")
    args = parser.parse_args()

    test_env_check()
    test_service_init()

    if args.demo:
        run_demo_file(args.demo, args.case)


if __name__ == "__main__":
    main()