import os
from typing import Any, Dict, List, Optional

from generator.analyzer import ImageAnalyzer
from generator.prompt_mixer import PromptMixer
from generator.generator import ImageGenerator
from generator.style_fallback import StyleFallbackGenerator
from utils.env_utils import require_google_api_key
from utils.input_resolver import resolve_input_image

class StaticWallpaperService:
    """
    静态壁纸服务：
    - 默认走 analyzer 推荐风格
    - 支持用户指定 styles
    - 指定风格不存在时，调用 LLM 生成 fallback prompt
    """

    def __init__(self) -> None:
        require_google_api_key()
        self.analyzer = ImageAnalyzer()
        self.mixer = PromptMixer()
        self.generator = ImageGenerator()
        self.style_fallback = StyleFallbackGenerator()

    @staticmethod
    def _normalize_count(count: int) -> int:
        if count < 1:
            return 1
        if count > 3:
            return 3
        return count

    @staticmethod
    def _clean_styles(styles: Optional[List[str]]) -> List[str]:
        if not styles:
            return []
        cleaned = []
        for style in styles:
            style = style.strip()
            if style:
                cleaned.append(style)
        return cleaned

    @staticmethod
    def _build_caption(
        style_name: str,
        style_key: str,
        description: str,
        creativity: str,
        fallback: bool = False,
        ) -> str:
        source_note = "This style was generated from a custom user request." if fallback else "This style was selected from the built-in style library."
        short_desc = description.strip() if description else "A visually interesting uploaded image."
        if len(short_desc) > 120:
            short_desc = short_desc[:117] + "..."

        return (
            f"Style: {style_name} ({style_key}). "
            f"Creativity: {creativity}. "
            f"{source_note} "
            f"Original scene summary: {short_desc}"
        )

    def _build_prompt_data(
        self,
        style_key: str,
        description: str,
        ) -> Dict[str, Any]:
        """
        如果 style_key 在风格库中，正常 mix_prompt。
        如果不在，走 LLM fallback。
        """
        if self.style_fallback.has_style(style_key):
            prompt_data = self.mixer.mix_prompt(style_key, description)
            prompt_data["creativity"] = "Medium"
            prompt_data["is_fallback"] = False
            prompt_data["requested_style"] = style_key
            prompt_data["reasoning"] = "Matched built-in style library."
            return prompt_data

        fallback_data = self.style_fallback.build_fallback_prompt(
            requested_style=style_key,
            image_description=description,
        )
        return fallback_data

    def generate(
        self,
        image_path: str,
        count: int = 1,
        styles: Optional[List[str]] = None,
        output_dir: Optional[str] = None,
        ) -> Dict[str, Any]:

        try:
            resolved_image_path = resolve_input_image(image_path, copy_to_runtime=True)
        except Exception as e:
            return {
                "success": False,
                "mode": "static",
                "message": f"输入图片解析失败: {e}",
                "results": [],
            }

        count = self._normalize_count(count)
        styles = self._clean_styles(styles)

        print("\n🚀 [StaticService] 开始静态壁纸生成...")

        analysis_result = self.analyzer.analyze_and_recommend(resolved_image_path, top_k=count)
        description = analysis_result.get("description", "A nice photo")
        reasoning = analysis_result.get("reasoning", "")
        recommendations = analysis_result.get("recommendations", [])

        selected_items: List[Dict[str, str]] = []

        if styles:
            selected_items = [{"style_key": style, "creativity": "Medium"} for style in styles[:count]]
            reasoning = "User-specified styles."
        else:
            selected_items = recommendations[:count]

        if not selected_items:
            return {
                "success": False,
                "mode": "static",
                "message": "没有得到可用的风格。",
                "description": description,
                "reasoning": reasoning,
                "results": [],
            }

        results: List[Dict[str, Any]] = []

        for item in selected_items:
            style_key = item.get("style_key")
            creativity = item.get("creativity", "Medium")

            if not style_key:
                continue

            print(f"🎨 [StaticService] 正在处理风格: {style_key}")

            prompt_data = self._build_prompt_data(style_key=style_key, description=description)
            prompt_data["creativity"] = prompt_data.get("creativity", creativity)

            image_output_path = self.generator.generate_with_ref_image(
                image_path=resolved_image_path,
                prompt_data=prompt_data,
                output_dir=output_dir,
            )

            result_item = {
                "style_key": prompt_data.get("style_key", style_key),
                "style_name": prompt_data.get("style_name", style_key),
                "creativity": prompt_data.get("creativity", creativity),
                "prompt": prompt_data.get("prompt", ""),
                "negative_prompt": prompt_data.get("negative_prompt", ""),
                "reasoning": prompt_data.get("reasoning", reasoning),
                "is_fallback": prompt_data.get("is_fallback", False),
                "requested_style": prompt_data.get("requested_style", style_key),
                "image_path": image_output_path,
                "caption": self._build_caption(
                    style_name=prompt_data.get("style_name", style_key),
                    style_key=prompt_data.get("style_key", style_key),
                    description=description,
                    creativity=prompt_data.get("creativity", creativity),
                    fallback=prompt_data.get("is_fallback", False),
                ),
            }
            results.append(result_item)

        success = any(item.get("image_path") for item in results)

        return {
            "success": success,
            "mode": "static",
            "message": "静态壁纸生成完成。" if success else "静态壁纸生成失败。",
            "input_image": resolved_image_path,
            "description": description,
            "reasoning": reasoning,
            "results": results,
        }