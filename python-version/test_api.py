from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
print("API key yüklendi:", api_key[:10], "...")

from openai import OpenAI

client = OpenAI(api_key=api_key)

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "user", "content": "Merhaba! Tekstil sektörü hakkında bir cümle söyle."}
    ]
)

print(response.choices[0].message.content)