import os
import time
from typing import Optional

from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image

from utils.utils import load_image_safe


load_dotenv()


class ImageGenerator:
    def __init__(self) -> None:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("❌ 未找到 GOOGLE_API_KEY")

        self.client = genai.Client(api_key=api_key)

        # 静态壁纸生成模型
        self.image_model = "imagen-4.0-generate-001"
        # 参考图重绘模型
        self.ref_image_model = "gemini-3-pro-image-preview"

    def _build_output_path(
        self,
        image_path: str,
        style_key: str,
        output_dir: Optional[str] = None,
        extension: str = ".png",
    ) -> str:
        """
        统一生成输出路径。

        新逻辑：
        - 如果传了 output_dir：
            output_dir / <base_name> / <base_name>_gen_<style_key>_<timestamp>.png

        兼容旧逻辑：
        - 如果没传 output_dir：
            尝试把路径中的 inputs 替换成 outputs
            否则退回到 image_path 所在目录下的 outputs 子目录
        """
        timestamp = int(time.time())
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        filename = f"{base_name}_gen_{style_key}_{timestamp}{extension}"

        if output_dir:
            target_dir = os.path.join(output_dir, base_name)
            os.makedirs(target_dir, exist_ok=True)
            return os.path.join(target_dir, filename)

        # ===== 兼容旧项目逻辑 =====
        normalized_path = image_path.replace("\\", "/")

        if "/inputs/" in normalized_path:
            output_base = normalized_path.replace("/inputs/", "/outputs/")
            output_base = os.path.splitext(output_base)[0]
            target_dir = output_base
        else:
            parent_dir = os.path.dirname(image_path)
            target_dir = os.path.join(parent_dir, "outputs", base_name)

        os.makedirs(target_dir, exist_ok=True)
        return os.path.join(target_dir, filename)

    def _save_response_image(
        self,
        response,
        image_path: str,
        style_key: str,
        output_dir: Optional[str] = None,
    ) -> Optional[str]:
        """
        从模型响应中提取图片并保存。
        同时兼容不同模型返回格式。
        """
        save_path = self._build_output_path(
            image_path=image_path,
            style_key=style_key,
            output_dir=output_dir,
            extension=".png",
        )

        try:
            # 情况 1：Imagen 返回 generated_images
            if hasattr(response, "generated_images") and response.generated_images:
                generated_image = response.generated_images[0]
                if hasattr(generated_image, "image") and generated_image.image:
                    generated_image.image.save(save_path)
                    print(f"✅ 图片已保存: {save_path}")
                    return save_path

            # 情况 2：Gemini 多模态返回 candidates.parts.inline_data
            if hasattr(response, "candidates") and response.candidates:
                for candidate in response.candidates:
                    content = getattr(candidate, "content", None)
                    if not content:
                        continue
                    parts = getattr(content, "parts", [])
                    for part in parts:
                        inline_data = getattr(part, "inline_data", None)
                        if inline_data and getattr(inline_data, "data", None):
                            from io import BytesIO

                            image = Image.open(BytesIO(inline_data.data))
                            image.save(save_path)
                            print(f"✅ 图片已保存: {save_path}")
                            return save_path

            print("⚠️ 未在响应中找到可保存的图片数据。")
            return None

        except Exception as e:
            print(f"❌ 保存图片失败: {e}")
            return None

    def generate(
        self,
        image_path: str,
        prompt_data: dict,
        output_dir: Optional[str] = None,
    ) -> Optional[str]:
        """
        纯 prompt 生成静态壁纸。
        """
        style_name = prompt_data.get("style_name", "Unknown Style")
        style_key = prompt_data.get("style_key", "unknown_style")
        prompt = prompt_data.get("prompt", "")
        negative_prompt = prompt_data.get("negative_prompt", "")

        full_prompt = prompt
        if negative_prompt:
            full_prompt = f"{prompt} --no {negative_prompt}"

        print(f"\n🖼️ [Generate] 风格: {style_name}")
        print(f"📝 Prompt: {full_prompt}")

        try:
            response = self.client.models.generate_images(
                model=self.image_model,
                prompt=full_prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="9:16",
                ),
            )
            return self._save_response_image(
                response=response,
                image_path=image_path,
                style_key=style_key,
                output_dir=output_dir,
            )

        except Exception as e:
            print(f"❌ generate() 调用失败: {e}")
            return None

    def generate_with_ref_image(
        self,
        image_path: str,
        prompt_data: dict,
        output_dir: Optional[str] = None,
    ) -> Optional[str]:
        """
        基于参考图进行风格化生成。
        """
        style_name = prompt_data.get("style_name", "Unknown Style")
        style_key = prompt_data.get("style_key", "unknown_style")
        prompt = prompt_data.get("prompt", "")
        negative_prompt = prompt_data.get("negative_prompt", "")
        creativity = prompt_data.get("creativity", "Medium")

        print(f"\n🖼️ [Ref Generate] 风格: {style_name}")
        print(f"🎚️ Creativity: {creativity}")

        try:
            input_image = load_image_safe(image_path)

            if creativity.lower() == "low":
                control_instruction = (
                    "Keep the original subject, pose, composition, and structure very closely. "
                    "Only restyle lighting, texture, color mood, and artistic rendering."
                )
            elif creativity.lower() == "high":
                control_instruction = (
                    "Use the reference image only as loose inspiration. "
                    "You may reinterpret the scene creatively while preserving the main subject identity."
                )
            else:
                control_instruction = (
                    "Preserve the main subject and overall composition, "
                    "but allow moderate stylization in environment, lighting, and details."
                )

            full_prompt = (
                f"{control_instruction}\n\n"
                f"Style transformation prompt:\n{prompt}\n\n"
                f"Avoid: {negative_prompt}"
            )

            response = self.client.models.generate_content(
                model=self.ref_image_model,
                contents=[full_prompt, input_image],
            )

            return self._save_response_image(
                response=response,
                image_path=image_path,
                style_key=style_key,
                output_dir=output_dir,
            )

        except Exception as e:
            print(f"❌ generate_with_ref_image() 调用失败: {e}")
            return None