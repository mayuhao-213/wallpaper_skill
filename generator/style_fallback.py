import os
import yaml
from typing import Dict, Any
from dotenv import load_dotenv
from google import genai


load_dotenv()


class StyleFallbackGenerator:
    """
    当用户指定的 style_key 不在 styles.yaml 中时：
    1. 不硬回退到默认风格
    2. 让大模型基于用户风格描述生成一个合理的 prompt
    """

    def __init__(self, styles_config_path: str = "config/styles.yaml") -> None:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("❌ 未找到 GOOGLE_API_KEY")

        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.5-flash"

        self.styles = {}
        if os.path.exists(styles_config_path):
            with open(styles_config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
                self.styles = config.get("styles", {})

    def has_style(self, style_key: str) -> bool:
        return style_key in self.styles

    def build_fallback_prompt(
        self,
        requested_style: str,
        image_description: str,
    ) -> Dict[str, Any]:
        """
        当 style 不存在时，调用 Gemini 生成一个合理的 prompt。
        """
        style_names = {
            k: v.get("name", k)
            for k, v in self.styles.items()
        }

        prompt = f"""
            You are an expert AI wallpaper prompt designer.

            Known style library:
            {style_names}

            User requested a style that is NOT in the style library:
            "{requested_style}"

            Image description:
            "{image_description}"

            Please create a strong wallpaper generation plan for this requested style.

            Return JSON only:
            {{
            "style_name": "...",
            "style_key": "...",
            "prompt": "...",
            "negative_prompt": "...",
            "creativity": "Low | Medium | High",
            "reasoning": "..."
            }}
            """

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config={"response_mime_type": "application/json"},
            )
            result = yaml.safe_load(response.text)

            return {
                "style_name": result.get("style_name", requested_style),
                "style_key": result.get("style_key", requested_style.lower().replace(" ", "_")),
                "prompt": result.get("prompt", image_description),
                "negative_prompt": result.get("negative_prompt", "low quality, blurry, text, watermark"),
                "creativity": result.get("creativity", "Medium"),
                "reasoning": result.get("reasoning", "LLM-generated fallback style prompt."),
                "is_fallback": True,
                "requested_style": requested_style,
            }

        except Exception as e:
            print(f"⚠️ [Fallback] 大模型生成 fallback prompt 失败: {e}")
            return {
                "style_name": requested_style,
                "style_key": requested_style.lower().replace(" ", "_"),
                "prompt": f"Create a wallpaper in {requested_style} style. {image_description}",
                "negative_prompt": "low quality, blurry, text, watermark",
                "creativity": "Medium",
                "reasoning": "Fallback prompt built by local template because LLM call failed.",
                "is_fallback": True,
                "requested_style": requested_style,
            }