"""Offline checks for the launcher and checkout-local runtime paths."""

import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PortablePathsTests(unittest.TestCase):
    def test_launcher_uses_checkout_venv_from_another_working_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            checkout = Path(temp) / "skill with spaces"
            checkout.mkdir()
            shutil.copy2(PROJECT_ROOT / "run_skill.sh", checkout)
            interpreter = checkout / ".venv/bin/python"
            interpreter.parent.mkdir(parents=True)
            interpreter.symlink_to(sys.executable)
            (checkout / "skill.py").write_text(
                "import json, os, sys\n"
                "print(json.dumps({'cwd': os.getcwd(), 'args': sys.argv[1:]}))\n"
                "sys.exit(7)\n"
            )
            result = subprocess.run(
                ["bash", str(checkout / "run_skill.sh"), "--image", "photo with spaces.png"],
                cwd=temp, capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 7, result.stderr)
            output = json.loads(result.stdout)
            self.assertEqual(Path(output["cwd"]).resolve(), checkout.resolve())
            self.assertEqual(output["args"], ["--image", "photo with spaces.png"])
            self.assertTrue((checkout / "runtime/uploads").is_dir())
            self.assertTrue((checkout / "runtime/outputs/openclaw_runs").is_dir())

    def test_input_copy_stays_inside_the_installed_checkout(self):
        with tempfile.TemporaryDirectory() as temp:
            checkout = Path(temp) / "skill"
            utils = checkout / "utils"
            utils.mkdir(parents=True)
            module_path = utils / "input_resolver.py"
            shutil.copy2(PROJECT_ROOT / "utils/input_resolver.py", module_path)
            resolver = load_module("portable_input_resolver", module_path)
            expected_dir = checkout / "runtime/uploads"
            self.assertEqual(Path(resolver.RUNTIME_UPLOAD_DIR), expected_dir)
            photo = Path(temp) / "my photo.png"
            photo.write_bytes(b"local image fixture")
            result = Path(resolver.resolve_input_image(str(photo)))
            self.assertEqual(result, expected_dir / photo.name)
            self.assertEqual(result.read_bytes(), photo.read_bytes())

    def test_cli_defaults_output_to_its_checkout_and_keeps_explicit_output(self):
        # Avoid importing model SDKs: this test exercises only CLI path selection.
        dependencies = {}
        for name, symbol in [
            ("services.static_wallpaper_service", "StaticWallpaperService"),
            ("services.live_wallpaper_service", "LiveWallpaperService"),
            ("utils.env_utils", "check_google_api_key"),
        ]:
            module = types.ModuleType(name)
            setattr(module, symbol, object)
            dependencies[name] = module
        with patch.dict(sys.modules, dependencies):
            skill = load_module("portable_skill", PROJECT_ROOT / "skill.py")
        args = argparse.Namespace(
            mode="static", image="photo.png", count=1, styles=None,
            output_dir=None, video=False,
        )
        payload = skill.build_payload_from_args(args)
        self.assertEqual(Path(payload["output_dir"]), PROJECT_ROOT / "runtime/outputs/openclaw_runs")
        args.output_dir = "my outputs"
        self.assertEqual(skill.build_payload_from_args(args)["output_dir"], "my outputs")


if __name__ == "__main__":
    unittest.main()
