import sqlite3, os
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "users.db")
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS users (telegram_id TEXT PRIMARY KEY, username TEXT, requests_today INTEGER DEFAULT 0, last_request_date TEXT, is_premium INTEGER DEFAULT 0)")
    conn.commit(); conn.close()
def get_user(tg): 
    conn=sqlite3.connect(DB_PATH); r=conn.execute("SELECT * FROM users WHERE telegram_id=?",(tg,)).fetchone(); conn.close(); return r
def increment_requests(tg):
    conn=sqlite3.connect(DB_PATH); conn.execute("UPDATE users SET requests_today=requests_today+1 WHERE telegram_id=?",(tg,)); conn.commit(); conn.close()
def reset_daily_requests():
    conn=sqlite3.connect(DB_PATH); conn.execute("UPDATE users SET requests_today=0 WHERE last_request_date!=date('now')"); conn.execute("UPDATE users SET last_request_date=date('now')"); conn.commit(); conn.close()
def create_user(tg,un=""):
    conn=sqlite3.connect(DB_PATH); conn.execute("INSERT OR IGNORE INTO users (telegram_id,username,last_request_date) VALUES (?,?,date('now'))",(tg,un)); conn.commit(); conn.close()
init_db()
