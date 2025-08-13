from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncpg
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

async def get_db():
    try:
        return await asyncpg.connect(os.getenv("DATABASE_URL"))
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

@app.route('/')
def root():
    return {"message": "Planner API"}

@app.route('/events', methods=['POST'])
def create_event():
    data = request.json
    
    async def _create_event():
        db = await get_db()
        if not db:
            return {"error": "Database connection failed"}, 500
        
        try:
            query = """
                INSERT INTO events (user_id, title, description, event_time, reminder_time, group_id)
                VALUES ($1, $2, $3, $4, $5, $6) RETURNING id
            """
            event_id = await db.fetchval(query, data['user_id'], data['title'], data.get('description'), 
                                       data['event_time'], data['reminder_time'], data.get('group_id'))
            return {"id": event_id}
        finally:
            await db.close()
    
    return asyncio.run(_create_event())

@app.route('/events/<int:user_id>')
def get_user_events(user_id):
    async def _get_events():
        db = await get_db()
        if not db:
            return {"error": "Database connection failed"}, 500
        
        try:
            events = await db.fetch("SELECT * FROM events WHERE user_id = $1 ORDER BY event_time", user_id)
            return [dict(event) for event in events]
        finally:
            await db.close()
    
    return jsonify(asyncio.run(_get_events()))

@app.route('/groups', methods=['POST'])
def create_group():
    data = request.json
    
    async def _create_group():
        db = await get_db()
        if not db:
            return {"error": "Database connection failed"}, 500
        
        try:
            await db.execute("INSERT INTO groups (id, name, members) VALUES ($1, $2, $3)", 
                           (data['id'], data['name'], data['members']))
            return {"success": True}
        finally:
            await db.close()
    
    return asyncio.run(_create_group())

@app.route('/groups/<group_id>')
def get_group_events(group_id):
    async def _get_group_events():
        db = await get_db()
        if not db:
            return {"error": "Database connection failed"}, 500
        
        try:
            events = await db.fetch("SELECT * FROM events WHERE group_id = $1 ORDER BY event_time", group_id)
            return [dict(event) for event in events]
        finally:
            await db.close()
    
    return jsonify(asyncio.run(_get_group_events()))

if __name__ == '__main__':
    # Створення таблиць при запуску
    async def init_db():
        db = await get_db()
        if db:
            try:
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
                print("Database tables created successfully")
            except Exception as e:
                print(f"Error creating tables: {e}")
            finally:
                await db.close()
        else:
            print("Warning: Could not connect to database during startup")
    
    asyncio.run(init_db())
    
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port) 
