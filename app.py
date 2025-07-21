from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import os

app = Flask(__name__)
port = int(os.environ.get("PORT", 5000))

CATEGORY_KEYWORDS = {
    "ESG 지원사업": ["모집", "신청", "접수", "공고", "설명회", "컨설팅", "세미나"],
    "글로벌 ESG 트렌드": ["ISSB", "CSRD", "ESG disclosure", "RE100", "net zero", "EU taxonomy"],
    "국내 ESG 트렌드": ["탄소중립", "지속가능경영", "환경부", "중소벤처기업부", "K-ESG"]
}

def fetch_article_text(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        paragraphs = soup.find_all("p")
        full_text = " ".join(p.get_text() for p in paragraphs)
        print("본문 미리보기:", full_text[:500])
        return full_text
    except Exception as e:
        print("Error fetching article:", e)
        return ""

def classify_category(text):
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text.lower():
                return category
    return "미분류"

@app.route("/classify", methods=["POST"])
def classify():
    data = request.get_json()
    url = data.get("url")
    if not url:
        return jsonify({"error": "URL missing"}), 400

    article_text = fetch_article_text(url)
    category = classify_category(article_text)

    return jsonify({"category": category})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port)
