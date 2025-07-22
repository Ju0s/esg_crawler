from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import requests, re, time
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

CATEGORY_KEYWORDS = {
    "ESG 지원사업": ['모집', '신청', '접수', '지원', '프로그램', '설명회', '세미나', '컨설팅', '실증', '인증'],
    "국내 ESG 트렌드": ['ESG 경영', '지속가능경영', '탄소중립', '사회적가치', '기후금융'],
    "글로벌 ESG 트렌드": ['ISSB', 'CSRD', 'RE100', 'TCFD', 'net zero', 'ESG disclosure']
}

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def resolve_google_news_url(url):
    try:
        options = Options()
        options.add_argument("--headless=new")  # 최신 Chrome 대응
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        print(f"[Selenium] Opening: {url}")
        driver.get(url)
        time.sleep(3)
        resolved = driver.current_url
        print(f"[Selenium] Resolved to: {resolved}")
        driver.quit()
        return resolved
    except Exception as e:
        print(f"[Selenium Error] {e}")
        return None

def fetch_article_text(url):
    try:
        res = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(res.text, 'html.parser')
        paragraphs = soup.find_all('p')
        text = "\n".join(p.get_text().strip() for p in paragraphs)
        return text.strip()
    except Exception as e:
        print(f"[Requests Error] {e}")
        return ""

def classify_category(text):
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return category
    return None

def summarize_text(text, limit=400):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return " ".join(sentences[:3])[:limit]

@app.route("/check", methods=["POST"])
def check_article():
    data = request.get_json()
    original_url = data.get("url")
    if not original_url:
        return jsonify({"passed": False, "error": "No URL provided"}), 400

    resolved_url = resolve_google_news_url(original_url)
    if not resolved_url:
        return jsonify({"passed": False, "error": "Could not resolve URL"}), 400

    article_text = fetch_article_text(resolved_url)
    if len(article_text) < 300:
        return jsonify({"passed": False})

    category = classify_category(article_text)
    if not category:
        return jsonify({"passed": False})

    summary = summarize_text(article_text)

    return jsonify({
        "passed": True,
        "resolved_url": resolved_url,
        "summary": summary,
        "category": category
    })

@app.route("/", methods=["GET"])
def health():
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)

