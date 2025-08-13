from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
import psycopg2.extras
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Моделі даних
class Event(BaseModel):
    id: int = None
    user_id: int
    title: str
    description: str = None
    event_time: str
    reminder_time: str
    group_id: str = None

class Group(BaseModel):
    id: str
    name: str
    members: list

# Підключення до БД
def get_db():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

@app.on_event("startup")
async def startup():
    # Створення таблиць
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            event_time TIMESTAMP NOT NULL,
            reminder_time TIMESTAMP NOT NULL,
            group_id TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            members BIGINT[] DEFAULT '{}',
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    db.commit()
    cursor.close()
    db.close()

@app.get("/")
async def root():
    return {"message": "Planner API"}

@app.post("/events")
async def create_event(event: Event):
    db = get_db()
    cursor = db.cursor()
    try:
        query = """
            INSERT INTO events (user_id, title, description, event_time, reminder_time, group_id)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
        """
        cursor.execute(query, (event.user_id, event.title, event.description, 
                              event.event_time, event.reminder_time, event.group_id))
        event_id = cursor.fetchone()[0]
        db.commit()
        return {"id": event_id}
    finally:
        cursor.close()
        db.close()

@app.get("/events/{user_id}")
async def get_user_events(user_id: int):
    db = get_db()
    cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cursor.execute("SELECT * FROM events WHERE user_id = %s ORDER BY event_time", (user_id,))
        events = cursor.fetchall()
        return [dict(event) for event in events]
    finally:
        cursor.close()
        db.close()

@app.post("/groups")
async def create_group(group: Group):
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO groups (id, name, members) VALUES (%s, %s, %s)", 
                      (group.id, group.name, group.members))
        db.commit()
        return {"success": True}
    finally:
        cursor.close()
        db.close()

@app.get("/groups/{group_id}")
async def get_group_events(group_id: str):
    db = get_db()
    cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cursor.execute("SELECT * FROM events WHERE group_id = %s ORDER BY event_time", (group_id,))
        events = cursor.fetchall()
        return [dict(event) for event in events]
    finally:
        cursor.close()
        db.close() 
