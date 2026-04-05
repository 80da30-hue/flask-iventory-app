from flask import Flask, render_template, request
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect("inventory.db") 
    cur = conn.cursor() 
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory_log ( 
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        item TEXT, 
        action TEXT, 
        quantity INTEGER, 
        expiry TEXT, 
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    conn.commit()
    conn.close()

units = {
    "コーヒー豆": "g",
    "牛乳": "本",
    "卵": "個",
    "生クリーム": "ml"
}

def init_db():
    conn = sqlite3.connect("inventory.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item TEXT,
        action TEXT,
        quantity INTEGER,
        expiry TEXT,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

@app.route("/", methods=["GET", "POST"])
def input():
    message = ""

    if request.method == "POST":
        item = request.form["item"]
        action = request.form["action"]
        quantity = int(request.form["quantity"])
        expiry = request.form.get("expiry")

        conn = sqlite3.connect("inventory.db")
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO inventory_log (item, action, quantity, expiry)
            VALUES (?, ?, ?, ?)
        """, (item, action, quantity, expiry))

        conn.commit()
        conn.close()

        message = "保存しました！"             

    return render_template("input.html", message=message)

@app.route("/dashboard")
def dashboard():
    conn = sqlite3.connect("inventory.db")
    cur = conn.cursor()

    # 全データ
    cur.execute("""
        SELECT item, action, quantity, expiry, date 
        FROM inventory_log
        ORDER BY date DESC
    """)
    rows = cur.fetchall()

    # 時間調整
    adjusted_rows = []
    
    for row in rows:
        date_str = row[4]
        date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        date_obj += timedelta(hours=9)

        adjusted_rows.append((
            row[0], row[1], row[2], row[3],
            date_obj.strftime("%Y-%m-%d %H:%M:%S")
        ))

    # 廃棄量の合計
    cur.execute("""
        SELECT item, SUM(quantity)
        FROM inventory_log
        WHERE action = '廃棄'
        GROUP BY item
    """)
    waste_rows = cur.fetchall()

    # 現在の在庫数
    cur.execute("""
        SELECT item,
        SUM(CASE WHEN action = '仕入れ' THEN quantity ELSE 0 END) -
        SUM(CASE WHEN action = '使用' THEN quantity ELSE 0 END) -
        SUM(CASE WHEN action = '廃棄' THEN quantity ELSE 0 END)
        FROM inventory_log
        GROUP BY item
    """)
    stock_rows = cur.fetchall()

    # 3日以内の期限
    today = datetime.today()
    limit = today + timedelta(days=3)

    cur.execute("""
        SELECT item, expiry
        FROM inventory_log
        WHERE expiry IS NOT NULL
        AND expiry != ''
    """)
    expiry_rows = cur.fetchall()        

    conn.close()

    # Python側で絞り込み
    near_expiry = []

    for item, expiry in expiry_rows:
        try:
            expiry_date = datetime.strptime(expiry, "%Y-%m-%d")
            if today <= expiry_date <= limit:
                near_expiry.append((item, expiry))
        except:
            pass

    return render_template(
        "dashboard.html", 
        rows=adjusted_rows, 
        near_expiry=near_expiry, 
        waste_rows=waste_rows, 
        stock_rows=stock_rows, 
        units=units
    )

if __name__ == "__main__":
    init_db()
    app.run(debug=True)