import requests
import os
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

kaynaklar = [
    {"url": "https://www.just-style.com", "tag": "h3", "class": None},
    {"url": "https://www.textileworld.com", "tag": "h3", "class": None},
    {"url": "https://www.dunya.com/sektorler/tekstil", "tag": "span", "class": "big"},
    {"url": "https://www.fibre2fashion.com", "tag": "div", "class": "common-subtitle"},
]

tum_basliklar = []

for kaynak in kaynaklar:
    try:
        print(f"\n{kaynak['url']} çekiliyor...")
        response = requests.get(kaynak["url"], timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        
        if kaynak["class"]:
            elementler = soup.find_all(kaynak["tag"], class_=kaynak["class"])
        else:
            elementler = soup.find_all(kaynak["tag"])
        
        sayac = 0
        for el in elementler:
            metin = el.get_text(strip=True)
            if metin and len(metin) > 20:
                tum_basliklar.append(metin)
                sayac += 1
            if sayac >= 5:
                break
        
        print(f"{sayac} başlık çekildi.")
    
    except Exception as e:
        print(f"Hata: {e}")

print("\n--- TÜM BAŞLIKLAR ---")
for b in tum_basliklar:
    print("-", b)

basliklar_metni = "\n".join(tum_basliklar)

ozet = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {
            "role": "system",
            "content": "Sen bir tekstil sektörü analistisin. Haber başlıklarını Türkçe olarak kısa ve öz özetle."
        },
        {
            "role": "user",
            "content": f"Bu haber başlıklarını özetle:\n{basliklar_metni}"
        }
    ]
)

print("\n--- ÖZET ---")
print(ozet.choices[0].message.content)