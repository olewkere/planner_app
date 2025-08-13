from flask import Flask, request, jsonify
from flask_cors import CORS
import pg8000
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

def get_db():
    try:
        return pg8000.Connection(os.getenv("DATABASE_URL"))
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

@app.route('/')
def root():
    return {"message": "Planner API"}

@app.route('/events', methods=['POST'])
def create_event():
    data = request.json
    db = get_db()
    if not db:
        return {"error": "Database connection failed"}, 500
    
    cursor = db.cursor()
    try:
        query = """
            INSERT INTO events (user_id, title, description, event_time, reminder_time, group_id)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
        """
        cursor.execute(query, (data['user_id'], data['title'], data.get('description'), 
                              data['event_time'], data['reminder_time'], data.get('group_id')))
        event_id = cursor.fetchone()[0]
        db.commit()
        return {"id": event_id}
    finally:
        cursor.close()
        db.close()

@app.route('/events/<int:user_id>')
def get_user_events(user_id):
    db = get_db()
    if not db:
        return {"error": "Database connection failed"}, 500
    
    cursor = db.cursor()
    try:
        cursor.execute("SELECT * FROM events WHERE user_id = %s ORDER BY event_time", (user_id,))
        events = cursor.fetchall()
        # Конвертуємо в список словників
        columns = [desc[0] for desc in cursor.description]
        return jsonify([dict(zip(columns, row)) for row in events])
    finally:
        cursor.close()
        db.close()

@app.route('/groups', methods=['POST'])
def create_group():
    data = request.json
    db = get_db()
    if not db:
        return {"error": "Database connection failed"}, 500
    
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO groups (id, name, members) VALUES (%s, %s, %s)", 
                      (data['id'], data['name'], data['members']))
        db.commit()
        return {"success": True}
    finally:
        cursor.close()
        db.close()

@app.route('/groups/<group_id>')
def get_group_events(group_id):
    db = get_db()
    if not db:
        return {"error": "Database connection failed"}, 500
    
    cursor = db.cursor()
    try:
        cursor.execute("SELECT * FROM events WHERE group_id = %s ORDER BY event_time", (group_id,))
        events = cursor.fetchall()
        # Конвертуємо в список словників
        columns = [desc[0] for desc in cursor.description]
        return jsonify([dict(zip(columns, row)) for row in events])
    finally:
        cursor.close()
        db.close()

if __name__ == '__main__':
    # Створення таблиць при запуску
    db = get_db()
    if db:
        cursor = db.cursor()
        try:
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
            print("Database tables created successfully")
        except Exception as e:
            print(f"Error creating tables: {e}")
        finally:
            cursor.close()
            db.close()
    else:
        print("Warning: Could not connect to database during startup")
    
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port) 
