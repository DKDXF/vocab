"""
AI 作文优化 Skill 实现
"""
import json
from skills.base import BaseSkill
from skills.ai_writing.prompt import WRITING_OPTIMIZE_PROMPT, IMAGE_EXTRACT_PROMPT


class AIWritingSkill(BaseSkill):
    name = "ai_writing"
    description = "AI 作文优化 - 语法纠正、用词优化、句式改进、评分"

    async def execute(self, **kwargs) -> dict:
        """优化作文"""
        text = kwargs.get("text", "")
        if not text.strip():
            return {"error": "作文内容为空"}

        prompt = WRITING_OPTIMIZE_PROMPT.format(essay_text=text)
        messages = [
            {"role": "system", "content": "你是一位专业的英语写作教师，擅长修改和优化英语作文。请严格按照要求的JSON格式返回结果。"},
            {"role": "user", "content": prompt},
        ]

        response_text = await self.call_llm(messages, temperature=0.3, max_tokens=3000)

        try:
            json_str = response_text
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]

            result = json.loads(json_str.strip())
            return result
        except json.JSONDecodeError:
            return {
                "error": "AI 返回格式解析失败",
                "raw_response": response_text,
                "grammar": [],
                "vocabulary": [],
                "structure": [],
                "logic": "",
                "score": 0,
                "optimized": "",
                "feedback": "AI 返回格式异常，请重试",
            }

    async def extract_from_image(self, image_base64: str, content_type: str = "image/png") -> str:
        """使用多模态能力从图片中提取作文文字"""
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.api_base,
            )
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": IMAGE_EXTRACT_PROMPT},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{content_type};base64,{image_base64}"
                                }
                            },
                        ],
                    }
                ],
                max_tokens=2000,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            raise Exception(f"图片识别失败: {str(e)}")
