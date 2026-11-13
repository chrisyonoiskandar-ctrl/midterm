import sqlite3
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")
DB_NAME = "submissions.db"

# Inisialisasi Database SQLite
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            author_name TEXT NOT NULL,
            category TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Editing'
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# 1. Home Page (Role Selection)
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request, "index.html", {})

# ==================== AUTHOR FEATURES ====================

@app.get("/author", response_class=HTMLResponse)
def author_page(request: Request, author_name: str = "John Doe", edit_id: int = None):
    conn = get_db()
    submissions = conn.execute("SELECT * FROM submissions ORDER BY id DESC").fetchall()
    
    edit_item = None
    if edit_id:
        edit_item = conn.execute("SELECT * FROM submissions WHERE id = ?", (edit_id,)).fetchone()
    conn.close()
    
    return templates.TemplateResponse(request, "author.html", {
        "submissions": submissions,
        "author_name": author_name,
        "edit_item": edit_item
    })

@app.post("/author/save")
def save_submission(
    id: str = Form(""),
    author_name: str = Form(...),
    category: str = Form(...),
    title: str = Form(...),
    content: str = Form(...)
):
    conn = get_db()
    if id:  
        conn.execute(
            "UPDATE submissions SET category=?, title=?, content=?, status='Editing' WHERE id=? AND status='Editing'",
            (category, title, content, int(id))
        )
    else:   
        conn.execute(
            "INSERT INTO submissions (author_name, category, title, content, status) VALUES (?, ?, ?, ?, 'Editing')",
            (author_name, category, title, content)
        )
    conn.commit()
    conn.close()
    return RedirectResponse(url=f"/author?author_name={author_name}", status_code=303)

@app.post("/author/delete/{sub_id}")
def delete_submission(sub_id: int, author_name: str = Form(...)):
    conn = get_db()
    conn.execute("DELETE FROM submissions WHERE id = ? AND status = 'Editing'", (sub_id,))
    conn.commit()
    conn.close()
    return RedirectResponse(url=f"/author?author_name={author_name}", status_code=303)

@app.post("/author/submit/{sub_id}")
def submit_article(sub_id: int, author_name: str = Form(...)):
    conn = get_db()
    conn.execute("UPDATE submissions SET status = 'Pending' WHERE id = ? AND status = 'Editing'", (sub_id,))
    conn.commit()
    conn.close()
    return RedirectResponse(url=f"/author?author_name={author_name}", status_code=303)

# ==================== EDITOR FEATURES ====================

@app.get("/editor", response_class=HTMLResponse)
def editor_page(request: Request, view_id: int = None):
    conn = get_db()
    pending_list = conn.execute("SELECT * FROM submissions WHERE status = 'Pending' ORDER BY id ASC").fetchall()
    
    selected_article = None
    if view_id:
        selected_article = conn.execute("SELECT * FROM submissions WHERE id = ?", (view_id,)).fetchone()
    conn.close()

    return templates.TemplateResponse(request, "editor.html", {
        "pending_list": pending_list,
        "selected_article": selected_article
    })

@app.post("/editor/approve/{sub_id}")
def approve_article(sub_id: int):
    conn = get_db()
    conn.execute("UPDATE submissions SET status = 'Approved' WHERE id = ? AND status = 'Pending'", (sub_id,))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/editor", status_code=303)

@app.post("/editor/reject/{sub_id}")
def reject_article(sub_id: int):
    conn = get_db()
    conn.execute("UPDATE submissions SET status = 'Editing' WHERE id = ? AND status = 'Pending'", (sub_id,))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/editor", status_code=303)