import sqlite3
import requests
import json
import urllib.request
import urllib.parse
from datetime import datetime
from google import genai
import time
import os
from dotenv import load_dotenv

# 비밀 금고 열기
load_dotenv()

# 금고에서 키 꺼내오기
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

# ... (아래는 기존 코드 그대로 유지) ...

# 💡 수정: blog 대신 webkr(웹 문서, 공식홈페이지 등) 검색 API 사용!
def search_naver_web(query, display_count=5):
    print(f"📡 네이버 웹 문서에서 '{query}' 검색 중...")
    encText = urllib.parse.quote(query)
    # 웹 문서 검색용 URL (공식 사이트, 브랜드 페이지 등 포함)
    url = f"https://openapi.naver.com/v1/search/webkr?query={encText}&display={display_count}"
    
    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", NAVER_CLIENT_ID)
    request.add_header("X-Naver-Client-Secret", NAVER_CLIENT_SECRET)
    
    try:
        response = urllib.request.urlopen(request)
        data = json.loads(response.read().decode('utf-8'))
        return data.get('items', [])
    except Exception as e:
        print(f"❌ 네이버 API 에러: {e}")
        return []

def extract_info_with_ai(content):
    print("🧠 AI가 웹 문서 내용을 분석하여 주소와 날짜를 정제합니다...")
    prompt = f"""
    아래 글을 분석해서 팝업스토어 정보를 추출해.
    1. 카테고리는 오직 '패션', '뷰티', '캐릭터', '푸드', '라이프' 중 딱 하나.
    2. 날짜는 무조건 YYYY-MM-DD 형식. (종료일을 모르면 시작일 기준 14일 뒤로). 절대 한글 금지.
    3. 주소는 카카오 지도에 검색되도록 '지하 1층' 같은 부가설명을 빼고, 오직 "서울특별시 영등포구 여의대로 108" 같은 도로명/지번 주소만.
    4. description(소개글)은 방문객이 흥미를 느끼도록 행사의 특징, 즐길 거리, 분위기 등을 상세하게 포함하여 무조건 3~5문장 이상(약 200~300자)으로 아주 길고 매력적으로 작성해.
    [내용] {content}
    """
    try:
        response = client.models.generate_content(
            model='gemini-flash-lite-latest', # 혹은 gemini-flash-lite-latest
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": {
                    "type": "OBJECT",
                    "properties": {
                        "name": {"type": "STRING"},
                        "category": {"type": "STRING"},
                        "address": {"type": "STRING"},
                        "start_date": {"type": "STRING"},
                        "end_date": {"type": "STRING"},
                        "description": {"type": "STRING"}
                    },
                    "required": ["name", "category", "address", "start_date", "end_date", "description"]
                }
            }
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"❌ AI 분석 실패: {e}")
        return None

def save_to_db(data):
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 💡 수정: 날짜 형식이 YYYY-MM-DD가 아니거나 과거면 무조건 버림! (철벽 방어)
    try:
        datetime.strptime(data['end_date'], '%Y-%m-%d')
        if data['end_date'] < today:
            print(f"⏩ 패스: 과거 팝업입니다. ({data['name']} / {data['end_date']})")
            return
    except ValueError:
        print(f"⏩ 패스: 날짜 형식이 잘못되었습니다. ({data['end_date']})")
        return

    conn = sqlite3.connect('popups.db')
    c = conn.cursor()
    # 💡 원본 링크(source_url) 컬럼 삭제 (저작권 이슈 해결)
    c.execute('''CREATE TABLE IF NOT EXISTS popups
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, category TEXT, 
                  address TEXT, start_date TEXT, end_date TEXT, description TEXT)''')
    try:
        c.execute('''INSERT OR REPLACE INTO popups 
                     (name, category, address, start_date, end_date, description) 
                     VALUES (?, ?, ?, ?, ?, ?)''',
                  (data['name'], data['category'], data['address'], data['start_date'], data['end_date'], data['description']))
        conn.commit()
        print(f"🎉 DB 저장 완료: [{data['category']}] {data['name']}")
    except Exception as e:
        print(f"❌ DB 저장 에러: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    # 💡 수정: "올해 이번 달"을 검색어에 넣어 무조건 최신 정보만 찾도록 유도
    current_ym = datetime.now().strftime('%Y년 %m월')
    smart_query = f"{current_ym} 서울 팝업스토어" 
    
    print("="*50)
    print(f"🔍 '{smart_query}' 관련 공식/웹 데이터를 수집합니다!")
    
    posts = search_naver_web(smart_query, 5)
    for post in posts:
        content = f"제목: {post['title']}\n요약: {post['description']}"
        info = extract_info_with_ai(content)
        if info:
            save_to_db(info)
        time.sleep(5) # 속도 조절