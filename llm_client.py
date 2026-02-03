"""
视觉 LLM 客户端模块
"""
import base64
from typing import Optional
from openai import OpenAI

from config import LLMConfig


class VisionLLMClient:
    """视觉 LLM 客户端"""

    SYSTEM_PROMPT = """你是一个专业的 Web 自动化助手。你的任务是根据用户的指令分析网页并执行操作。

页面上的可交互元素已被标记：
- [#ID]：文本输入框
- [@ID]：超链接  
- [$ID]：按钮或其他可交互元素
- [%ID]：图片元素

你需要根据用户的指令，输出要执行的操作。

可用的操作格式：
- CLICK [ID] - 点击指定元素
- TYPE [ID] "文本内容" - 在输入框中输入文本
- SCROLL UP/DOWN - 向上或向下滚动页面
- GOTO "URL" - 导航到指定URL
- WAIT 秒数 - 等待指定秒数（如 WAIT 5）
- PAUSE - 暂停执行，等待用户手动完成操作（用于验证码、手机验证、二维码登录等场景）
- DONE - 任务完成

重要规则：
1. 每次只输出一个操作命令，不要输出其他内容
2. 如果页面显示需要手机验证、扫码登录、验证码等需要人工介入的内容，使用 PAUSE
3. 如果页面正在加载或需要等待，使用 WAIT
4. 任务完成后使用 DONE"""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = OpenAI(
            base_url=config.api_base,
            api_key=config.api_key,
        )
        self.conversation_history = []

    def reset_conversation(self) -> None:
        """重置对话历史"""
        self.conversation_history = []

    def _encode_image(self, image_bytes: bytes) -> str:
        """将图片编码为 base64"""
        return base64.b64encode(image_bytes).decode("utf-8")

    def analyze_page(
        self,
        screenshot: bytes,
        page_text: str,
        user_instruction: str,
        current_url: str,
    ) -> str:
        """分析页面并返回下一步操作"""
        image_base64 = self._encode_image(screenshot)

        user_content = [
            {
                "type": "text",
                "text": f"""当前页面 URL: {current_url}

页面元素标记信息:
{page_text}

用户指令: {user_instruction}

请分析页面截图和元素信息，输出下一步要执行的操作。""",
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{image_base64}",
                    "detail": "high",
                },
            },
        ]

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            *self.conversation_history,
            {"role": "user", "content": user_content},
        ]

        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            max_tokens=500,
            temperature=0.1,
        )

        assistant_message = response.choices[0].message.content.strip()

        self.conversation_history.append({"role": "user", "content": user_content})
        self.conversation_history.append(
            {"role": "assistant", "content": assistant_message}
        )

        return assistant_message

    async def analyze_with_vision(self, screenshot: bytes, prompt: str) -> str:
        """使用视觉能力分析截图"""
        image_base64 = self._encode_image(screenshot)
        
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_base64}",
                            "detail": "high",
                        },
                    },
                ],
            }
        ]
        
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            max_tokens=2000,
            temperature=0.1,
        )
        
        content = response.choices[0].message.content
        return content.strip() if content else ""

    async def chat(self, prompt: str) -> str:
        """纯文本对话"""
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.1,
        )
        
        content = response.choices[0].message.content
        return content.strip() if content else ""
