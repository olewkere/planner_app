from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncpg
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
async def get_db():
    return await asyncpg.connect(os.getenv("DATABASE_URL"))

@app.on_event("startup")
async def startup():
    # Створення таблиць
    db = await get_db()
    await db.execute("""
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
    await db.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            members BIGINT[] DEFAULT '{}',
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    await db.close()

@app.get("/")
async def root():
    return {"message": "Planner API"}

@app.post("/events")
async def create_event(event: Event):
    db = await get_db()
    try:
        query = """
            INSERT INTO events (user_id, title, description, event_time, reminder_time, group_id)
            VALUES ($1, $2, $3, $4, $5, $6) RETURNING id
        """
        event_id = await db.fetchval(query, event.user_id, event.title, event.description, 
                                   event.event_time, event.reminder_time, event.group_id)
        return {"id": event_id}
    finally:
        await db.close()

@app.get("/events/{user_id}")
async def get_user_events(user_id: int):
    db = await get_db()
    try:
        events = await db.fetch("SELECT * FROM events WHERE user_id = $1 ORDER BY event_time", user_id)
        return [dict(event) for event in events]
    finally:
        await db.close()

@app.post("/groups")
async def create_group(group: Group):
    db = await get_db()
    try:
        await db.execute("INSERT INTO groups (id, name, members) VALUES ($1, $2, $3)", 
                        group.id, group.name, group.members)
        return {"success": True}
    finally:
        await db.close()

@app.get("/groups/{group_id}")
async def get_group_events(group_id: str):
    db = await get_db()
    try:
        events = await db.fetch("SELECT * FROM events WHERE group_id = $1 ORDER BY event_time", group_id)
        return [dict(event) for event in events]
    finally:
        await db.close() 
