from __future__ import annotations

from typing import Any

from src.api.models.request import ChatMessage


class ContextBuilder:
    def build(
        self,
        messages: list[ChatMessage],
        *,
        original_user_message: str,
        organized_search_results: str,
    ) -> list[dict[str, Any]]:
        output = [message.model_dump(exclude_none=True) for message in messages]
        combined = (
            "===== 用户问题 =====\n"
            f"{original_user_message}\n\n"
            "===== 参考信息（来自搜索结果）=====\n"
            f"{organized_search_results}\n\n"
            "===== 回答要求 =====\n"
            "1. 优先回答用户的问题\n"
            "2. 搜索结果仅作为辅助知识的参考来源\n"
            "3. 如果搜索结果有助于回答问题，可以引用；如果不相关或不可靠，忽略搜索结果，使用你自己的知识回答\n"
            "4. 回答要自然流畅，不要刻意提及“根据搜索结果”"
        )
        for index in range(len(output) - 1, -1, -1):
            if output[index].get("role") == "user":
                output[index]["content"] = combined
                return output
        output.append({"role": "user", "content": combined})
        return output
