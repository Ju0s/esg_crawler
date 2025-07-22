from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import requests, re, time, urllib.parse

app = Flask(__name__)

# ✅ 카테고리 키워드
CATEGORY_KEYWORDS = {
    "ESG 지원사업": ['모집', '신청', '접수', '지원', '프로그램', '설명회', '세미나', '컨설팅', '실증', '인증'],
    "국내 ESG 트렌드": ['ESG 경영', '지속가능경영', '탄소중립', '사회적가치', '기후금융'],
    "글로벌 ESG 트렌드": ['ISSB', 'CSRD', 'RE100', 'TCFD', 'net zero', 'ESG disclosure']
}

# ✅ Google 뉴스 링크 파싱
def resolve_google_news_url(url):
    try:
        if "news.google.com/rss/articles" in url:
            # URL에 원문 기사 주소가 인코딩되어 포함되어 있음
            m = re.search(r'articles/[^/]*?(https%3A%2F%2F.*?)(&|$)', url)
            if m:
                encoded_url = m.group(1)
                decoded_url = urllib.parse.unquote(encoded_url)
                print(f"[URL Parsed] {decoded_url}")
                return decoded_url

        # fallback to Selenium if parsing 실패
        return fallback_selenium_resolution(url)
    except Exception as e:
        print(f"[resolve_google_news_url Error] {e}")
        return None

# ✅ Fallback: Selenium으로 리디렉션 추적
def fallback_selenium_resolution(url):
    try:
        options = Options()
        options.add_argument("--headless=new")
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

# ✅ 본문 크롤링
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

# ✅ 키워드 기반 분류
def classify_category(text):
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return category
    return None

# ✅ 간단 요약
def summarize_text(text, limit=400):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return " ".join(sentences[:3])[:limit]

# ✅ API 엔드포인트
@app.route("/check", methods=["POST"])
def check_article():
    print("=== RAW BODY ===")
    print(request.data)
    print("=== HEADERS ===")
    print(dict(request.headers))

    try:
        data = request.get_json(force=True)
        print("[DEBUG] Parsed JSON:", data)
    except Exception as e:
        print("[ERROR] JSON 파싱 실패:", str(e))
        return jsonify({"passed": False, "error": "JSON parsing error"}), 400

    if not data or "url" not in data:
        return jsonify({"passed": False, "error": "No URL provided"}), 400
    original_url = data.get("url")
    print("[DEBUG] URL received:", original_url)

    if not original_url:
        return jsonify({"passed": False, "error": "No URL provided"}), 400

    resolved_url = resolve_google_news_url(original_url)
    if not resolved_url:
        return jsonify({"passed": False, "error": "Could not resolve URL"}), 400

    article_text = fetch_article_text(resolved_url)
    if len(article_text) < 300:
        return jsonify({"passed": False, "error": "Article too short"})

    category = classify_category(article_text)
    if not category:
        return jsonify({"passed": False, "error": "No matching category"})

    summary = summarize_text(article_text)

    return jsonify({
        "passed": True,
        "resolved_url": resolved_url,
        "summary": summary,
        "category": category
    })

# ✅ 로컬 테스트용
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
