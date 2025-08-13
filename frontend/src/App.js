import React, { useState, useEffect } from 'react';
import WebApp from '@twa-dev/sdk';
import axios from 'axios';
import './App.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [user, setUser] = useState(null);
  const [events, setEvents] = useState([]);
  const [newEvent, setNewEvent] = useState({
    title: '',
    description: '',
    event_time: '',
    reminder_time: '',
    group_id: ''
  });
  const [groups, setGroups] = useState([]);

  useEffect(() => {
    // Ініціалізація Telegram Web App
    WebApp.ready();
    WebApp.expand();
    
    const tgUser = WebApp.initDataUnsafe?.user;
    if (tgUser) {
      setUser(tgUser);
      loadUserEvents(tgUser.id);
    }
  }, []);

  const loadUserEvents = async (userId) => {
    try {
      const response = await axios.get(`${API_URL}/events/${userId}`);
      setEvents(response.data);
    } catch (error) {
      console.error('Помилка завантаження подій:', error);
    }
  };

  const createEvent = async (e) => {
    e.preventDefault();
    if (!user) return;

    try {
      const eventData = {
        ...newEvent,
        user_id: user.id
      };
      
      await axios.post(`${API_URL}/events`, eventData);
      setNewEvent({ title: '', description: '', event_time: '', reminder_time: '', group_id: '' });
      loadUserEvents(user.id);
      
      WebApp.showAlert('Подію створено!');
    } catch (error) {
      console.error('Помилка створення події:', error);
      WebApp.showAlert('Помилка створення події');
    }
  };

  const createGroup = async () => {
    if (!user) return;
    
    try {
      const groupName = prompt('Введіть назву групи:');
      if (!groupName) return;
      
      const groupData = {
        id: `group_${user.id}_${Date.now()}`,
        name: groupName,
        members: [user.id]
      };
      
      await axios.post(`${API_URL}/groups`, groupData);
      WebApp.showAlert(`Група "${groupName}" створена!`);
    } catch (error) {
      console.error('Помилка створення групи:', error);
      WebApp.showAlert('Помилка створення групи');
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>📅 Планувальник</h1>
        {user && <p>Привіт, {user.first_name}!</p>}
      </header>

      <main>
        <section className="create-event">
          <h2>Створити подію</h2>
          <form onSubmit={createEvent}>
            <input
              type="text"
              placeholder="Назва події"
              value={newEvent.title}
              onChange={(e) => setNewEvent({...newEvent, title: e.target.value})}
              required
            />
            <textarea
              placeholder="Опис (необов'язково)"
              value={newEvent.description}
              onChange={(e) => setNewEvent({...newEvent, description: e.target.value})}
            />
            <input
              type="datetime-local"
              value={newEvent.event_time}
              onChange={(e) => setNewEvent({...newEvent, event_time: e.target.value})}
              required
            />
            <input
              type="datetime-local"
              value={newEvent.reminder_time}
              onChange={(e) => setNewEvent({...newEvent, reminder_time: e.target.value})}
              required
            />
            <input
              type="text"
              placeholder="ID групи (необов'язково)"
              value={newEvent.group_id}
              onChange={(e) => setNewEvent({...newEvent, group_id: e.target.value})}
            />
            <button type="submit">Створити подію</button>
          </form>
        </section>

        <section className="actions">
          <button onClick={createGroup} className="group-btn">
            Створити групу
          </button>
        </section>

        <section className="events">
          <h2>Мої події</h2>
          {events.length === 0 ? (
            <p>Немає подій</p>
          ) : (
            <div className="events-list">
              {events.map(event => (
                <div key={event.id} className="event-card">
                  <h3>{event.title}</h3>
                  {event.description && <p>{event.description}</p>}
                  <p><strong>Час:</strong> {new Date(event.event_time).toLocaleString()}</p>
                  <p><strong>Нагадування:</strong> {new Date(event.reminder_time).toLocaleString()}</p>
                  {event.group_id && <p><strong>Група:</strong> {event.group_id}</p>}
                </div>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default App; 