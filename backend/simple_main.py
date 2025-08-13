from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

def get_db():
    try:
        db = sqlite3.connect('planner.db')
        db.row_factory = sqlite3.Row
        return db
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

@app.route('/')
def root():
    return {"message": "Planner API"}

# Події
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
            VALUES (?, ?, ?, ?, ?, ?)
        """
        cursor.execute(query, (data['user_id'], data['title'], data.get('description'), 
                              data['event_time'], data['reminder_time'], data.get('group_id')))
        event_id = cursor.lastrowid
        db.commit()
        return {"id": event_id}
    finally:
        cursor.close()
        db.close()

@app.route('/events/<int:event_id>', methods=['PUT'])
def update_event(event_id):
    data = request.json
    db = get_db()
    if not db:
        return {"error": "Database connection failed"}, 500
    
    cursor = db.cursor()
    try:
        query = """
            UPDATE events 
            SET title = ?, description = ?, event_time = ?, reminder_time = ?, group_id = ?
            WHERE id = ? AND user_id = ?
        """
        cursor.execute(query, (data['title'], data.get('description'), 
                              data['event_time'], data['reminder_time'], 
                              data.get('group_id'), event_id, data['user_id']))
        
        if cursor.rowcount == 0:
            return {"error": "Event not found or access denied"}, 404
        
        db.commit()
        return {"success": True}
    finally:
        cursor.close()
        db.close()

@app.route('/events/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    data = request.json
    db = get_db()
    if not db:
        return {"error": "Database connection failed"}, 500
    
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM events WHERE id = ? AND user_id = ?", (event_id, data['user_id']))
        
        if cursor.rowcount == 0:
            return {"error": "Event not found or access denied"}, 404
        
        db.commit()
        return {"success": True}
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
        cursor.execute("SELECT * FROM events WHERE user_id = ? ORDER BY event_time", (user_id,))
        events = cursor.fetchall()
        return jsonify([dict(event) for event in events])
    finally:
        cursor.close()
        db.close()

# Групи
@app.route('/groups', methods=['POST'])
def create_group():
    data = request.json
    db = get_db()
    if not db:
        return {"error": "Database connection failed"}, 500
    
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO groups (id, name, members, owner_id) VALUES (?, ?, ?, ?)", 
                      (data['id'], data['name'], str(data['members']), data['owner_id']))
        db.commit()
        return {"success": True}
    finally:
        cursor.close()
        db.close()

@app.route('/groups/<group_id>', methods=['PUT'])
def update_group(group_id):
    data = request.json
    db = get_db()
    if not db:
        return {"error": "Database connection failed"}, 500
    
    cursor = db.cursor()
    try:
        cursor.execute("UPDATE groups SET name = ?, members = ? WHERE id = ? AND owner_id = ?", 
                      (data['name'], str(data['members']), group_id, data['owner_id']))
        
        if cursor.rowcount == 0:
            return {"error": "Group not found or access denied"}, 404
        
        db.commit()
        return {"success": True}
    finally:
        cursor.close()
        db.close()

@app.route('/groups/<group_id>', methods=['DELETE'])
def delete_group(group_id):
    data = request.json
    db = get_db()
    if not db:
        return {"error": "Database connection failed"}, 500
    
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM groups WHERE id = ? AND owner_id = ?", (group_id, data['owner_id']))
        
        if cursor.rowcount == 0:
            return {"error": "Group not found or access denied"}, 404
        
        db.commit()
        return {"success": True}
    finally:
        cursor.close()
        db.close()

@app.route('/groups/<group_id>')
def get_group(group_id):
    db = get_db()
    if not db:
        return {"error": "Database connection failed"}, 500
    
    cursor = db.cursor()
    try:
        cursor.execute("SELECT * FROM groups WHERE id = ?", (group_id,))
        group = cursor.fetchone()
        if not group:
            return {"error": "Group not found"}, 404
        return jsonify(dict(group))
    finally:
        cursor.close()
        db.close()

@app.route('/groups/<group_id>/events')
def get_group_events(group_id):
    db = get_db()
    if not db:
        return {"error": "Database connection failed"}, 500
    
    cursor = db.cursor()
    try:
        cursor.execute("SELECT * FROM events WHERE group_id = ? ORDER BY event_time", (group_id,))
        events = cursor.fetchall()
        return jsonify([dict(event) for event in events])
    finally:
        cursor.close()
        db.close()

@app.route('/users/<int:user_id>/groups')
def get_user_groups(user_id):
    db = get_db()
    if not db:
        return {"error": "Database connection failed"}, 500
    
    cursor = db.cursor()
    try:
        cursor.execute("SELECT * FROM groups WHERE owner_id = ? OR ? IN (SELECT json_extract(members, '$') FROM groups)", 
                      (user_id, user_id))
        groups = cursor.fetchall()
        return jsonify([dict(group) for group in groups])
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
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    event_time TEXT NOT NULL,
                    reminder_time TEXT NOT NULL,
                    group_id TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS groups (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    members TEXT DEFAULT '[]',
                    owner_id INTEGER NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
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
