import sqlite3

def view_db():
    try:
        conn = sqlite3.connect('popups.db')
        cur = conn.cursor()
        
        # 모든 데이터 가져오기
        cur.execute("SELECT id, name, category, start_date, end_date, address FROM popups")
        rows = cur.fetchall()
        
        print("\n" + "="*80)
        print(f"{'ID':<3} | {'카테고리':<8} | {'이름':<20} | {'시작일':<11} | {'종료일':<11} | {'주소'}")
        print("-" * 80)
        
        for row in rows:
            print(f"{row[0]:<3} | {row[1]:<10} | {row[2]:<20} | {row[3]:<11} | {row[4]:<11} | {row[5]}")
            
        print("="*80)
        conn.close()
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    view_db()