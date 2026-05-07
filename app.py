from flask import Flask, render_template, request, jsonify
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('popups.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/popups')
def get_popups():
    target_date = request.args.get('target_date')
    conn = get_db_connection()
    
    # 🔥 수정: 시작일 상관없이 '종료일이 오늘 이후인 모든 팝업'을 일단 다 가져옵니다!
    query = "SELECT * FROM popups WHERE end_date >= ?"
    popups = conn.execute(query, (target_date,)).fetchall()
    
    conn.close()
    return jsonify({"data": [dict(row) for row in popups]})

if __name__ == '__main__':
    app.run(debug=True, port=5000)