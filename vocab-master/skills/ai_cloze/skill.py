"""
AI 完形填空 Skill 实现
"""
import json
from skills.base import BaseSkill
from skills.ai_cloze.prompt import CLOZE_GENERATE_PROMPT


class AIClozeSkill(BaseSkill):
    name = "ai_cloze"
    description = "AI 完形填空生成 - 基于学习单词生成完形填空文章"

    async def execute(self, **kwargs) -> dict:
        """生成完形填空文章"""
        word_list = kwargs.get("word_list", [])
        if not word_list:
            return {"error": "单词列表为空"}

        # 格式化单词列表
        word_str = "\n".join([f"- {w['word']}: {w['definition']}" for w in word_list])
        prompt = CLOZE_GENERATE_PROMPT.format(word_list=word_str)

        messages = [
            {"role": "system", "content": "你是一位专业的英语教师，擅长设计完形填空练习题。请严格按照要求的JSON格式返回结果。"},
            {"role": "user", "content": prompt},
        ]

        response_text = await self.call_llm(messages, temperature=0.7, max_tokens=2000)

        # 解析 JSON
        try:
            # 尝试提取 JSON 部分
            json_str = response_text
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]

            result = json.loads(json_str.strip())
            # 标记 cloze_id
            result["cloze_id"] = f"cloze_{id(self)}"
            return result
        except json.JSONDecodeError:
            # 如果解析失败，返回原始文本
            return {
                "error": "AI 返回格式解析失败",
                "raw_response": response_text,
                "title": "完形填空",
                "article": response_text,
                "blanks": [],
            }
