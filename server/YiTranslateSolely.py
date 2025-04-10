import json

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from openai import OpenAI

with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

api_key = config.get("api_key")
base_url = config.get("base_url")
model = config.get("model")

client = OpenAI(api_key=api_key, base_url=base_url,)
app = FastAPI()


async def translate_text(text) -> str:
    """
    调用 OpenAI 的 ChatCompletion API 将输入英文翻译为中文，
    保留所有技术术语，仅输出翻译后的文本。
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "你是一个英文技术文档翻译专家，将用户输入的英文翻译成中文，保留所有技术术语。严格输出翻译后的文本，不要输出其它内容。"
                },
                {
                    "role": "user",
                    "content": text
                }
            ]
        )
        # 翻译结果位于第一个选项的 message.content 字段
        content = response.choices[0].message.content
        print(content)
        return content
    except Exception as e:
        print("调用 OpenAI API 时出错:", e)
        return ""

@app.post("/translate")
async def translate_endpoint(request: Request):
    """
    接收 JSON 请求，其中包含 "text" 字段，然后调用 translate_text 翻译，
    返回翻译后的结果。
    """
    data = await request.json()
    text = data.get("text", "")
    if not text:
        return JSONResponse(status_code=400, content={"error": "缺少参数 text"})
    translated = translate_text(text)
    return {"translated": translated}

if __name__ == "__main__":
    uvicorn.run("YiTranslateSolely:app", host="0.0.0.0", port=5000, reload=True)
