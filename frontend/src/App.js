import React, { useState, useEffect } from 'react';
import WebApp from '@twa-dev/sdk';
import axios from 'axios';
import './App.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [user, setUser] = useState(null);
  const [events, setEvents] = useState([]);
  const [groups, setGroups] = useState([]);
  const [currentView, setCurrentView] = useState('events'); // 'events', 'groups', 'create-event', 'create-group'
  const [editingEvent, setEditingEvent] = useState(null);
  const [editingGroup, setEditingGroup] = useState(null);
  const [newEvent, setNewEvent] = useState({
    title: '',
    description: '',
    event_time: '',
    reminder_time: '',
    group_id: ''
  });
  const [newGroup, setNewGroup] = useState({
    name: '',
    members: []
  });

  useEffect(() => {
    WebApp.ready();
    WebApp.expand();
    
    const tgUser = WebApp.initDataUnsafe?.user;
    if (tgUser) {
      setUser(tgUser);
      loadUserEvents(tgUser.id);
      loadUserGroups(tgUser.id);
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

  const loadUserGroups = async (userId) => {
    try {
      const response = await axios.get(`${API_URL}/users/${userId}/groups`);
      setGroups(response.data);
    } catch (error) {
      console.error('Помилка завантаження груп:', error);
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
      setCurrentView('events');
      
      WebApp.showAlert('Подію створено!');
    } catch (error) {
      console.error('Помилка створення події:', error);
      WebApp.showAlert('Помилка створення події');
    }
  };

  const updateEvent = async (e) => {
    e.preventDefault();
    if (!user || !editingEvent) return;

    try {
      const eventData = {
        ...editingEvent,
        user_id: user.id
      };
      
      await axios.put(`${API_URL}/events/${editingEvent.id}`, eventData);
      setEditingEvent(null);
      loadUserEvents(user.id);
      setCurrentView('events');
      
      WebApp.showAlert('Подію оновлено!');
    } catch (error) {
      console.error('Помилка оновлення події:', error);
      WebApp.showAlert('Помилка оновлення події');
    }
  };

  const deleteEvent = async (eventId) => {
    if (!user) return;
    
    if (window.confirm('Ви впевнені, що хочете видалити цю подію?')) {
      try {
        await axios.delete(`${API_URL}/events/${eventId}`, {
          data: { user_id: user.id }
        });
        loadUserEvents(user.id);
        WebApp.showAlert('Подію видалено!');
      } catch (error) {
        console.error('Помилка видалення події:', error);
        WebApp.showAlert('Помилка видалення події');
      }
    }
  };

  const createGroup = async (e) => {
    e.preventDefault();
    if (!user) return;
    
    try {
      const groupData = {
        id: `group_${user.id}_${Date.now()}`,
        name: newGroup.name,
        members: newGroup.members,
        owner_id: user.id
      };
      
      await axios.post(`${API_URL}/groups`, groupData);
      setNewGroup({ name: '', members: [] });
      loadUserGroups(user.id);
      setCurrentView('groups');
      
      WebApp.showAlert(`Групу "${groupData.name}" створено!`);
    } catch (error) {
      console.error('Помилка створення групи:', error);
      WebApp.showAlert('Помилка створення групи');
    }
  };

  const updateGroup = async (e) => {
    e.preventDefault();
    if (!user || !editingGroup) return;
    
    try {
      const groupData = {
        name: editingGroup.name,
        members: editingGroup.members,
        owner_id: user.id
      };
      
      await axios.put(`${API_URL}/groups/${editingGroup.id}`, groupData);
      setEditingGroup(null);
      loadUserGroups(user.id);
      setCurrentView('groups');
      
      WebApp.showAlert('Групу оновлено!');
    } catch (error) {
      console.error('Помилка оновлення групи:', error);
      WebApp.showAlert('Помилка оновлення групи');
    }
  };

  const deleteGroup = async (groupId) => {
    if (!user) return;
    
    if (window.confirm('Ви впевнені, що хочете видалити цю групу?')) {
      try {
        await axios.delete(`${API_URL}/groups/${groupId}`, {
          data: { owner_id: user.id }
        });
        loadUserGroups(user.id);
        WebApp.showAlert('Групу видалено!');
      } catch (error) {
        console.error('Помилка видалення групи:', error);
        WebApp.showAlert('Помилка видалення групи');
      }
    }
  };

  const addMemberToGroup = (groupId) => {
    const memberId = window.prompt('Введіть ID користувача для додавання:');
    if (memberId && !isNaN(memberId)) {
      const group = groups.find(g => g.id === groupId);
      if (group) {
        const members = JSON.parse(group.members || '[]');
        if (!members.includes(parseInt(memberId))) {
          members.push(parseInt(memberId));
          setEditingGroup({ ...group, members });
        }
      }
    }
  };

  const removeMemberFromGroup = (groupId, memberId) => {
    const group = groups.find(g => g.id === groupId);
    if (group) {
      const members = JSON.parse(group.members || '[]');
      const updatedMembers = members.filter(m => m !== memberId);
      setEditingGroup({ ...group, members: updatedMembers });
    }
  };

  const renderEventsView = () => (
    <div>
      <h2>Мої події</h2>
      <button onClick={() => setCurrentView('create-event')} className="create-btn">
        Створити подію
      </button>
      
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
              
              <div className="event-actions">
                <button onClick={() => setEditingEvent(event)} className="edit-btn">
                  Редагувати
                </button>
                <button onClick={() => deleteEvent(event.id)} className="delete-btn">
                  Видалити
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  const renderGroupsView = () => (
    <div>
      <h2>Мої групи</h2>
      <button onClick={() => setCurrentView('create-group')} className="create-btn">
        Створити групу
      </button>
      
      {groups.length === 0 ? (
        <p>Немає груп</p>
      ) : (
        <div className="groups-list">
          {groups.map(group => (
            <div key={group.id} className="group-card">
              <h3>{group.name}</h3>
              <p><strong>ID групи:</strong> {group.id}</p>
              <p><strong>Учасники:</strong> {JSON.parse(group.members || '[]').join(', ') || 'Немає'}</p>
              
              <div className="group-actions">
                <button onClick={() => setEditingGroup(group)} className="edit-btn">
                  Редагувати
                </button>
                <button onClick={() => deleteGroup(group.id)} className="delete-btn">
                  Видалити
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  const renderCreateEventView = () => (
    <div>
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
        <div className="form-actions">
          <button type="submit">Створити подію</button>
          <button type="button" onClick={() => setCurrentView('events')} className="cancel-btn">
            Скасувати
          </button>
        </div>
      </form>
    </div>
  );

  const renderEditEventView = () => (
    <div>
      <h2>Редагувати подію</h2>
      <form onSubmit={updateEvent}>
        <input
          type="text"
          placeholder="Назва події"
          value={editingEvent.title}
          onChange={(e) => setEditingEvent({...editingEvent, title: e.target.value})}
          required
        />
        <textarea
          placeholder="Опис (необов'язково)"
          value={editingEvent.description || ''}
          onChange={(e) => setEditingEvent({...editingEvent, description: e.target.value})}
        />
        <input
          type="datetime-local"
          value={editingEvent.event_time}
          onChange={(e) => setEditingEvent({...editingEvent, event_time: e.target.value})}
          required
        />
        <input
          type="datetime-local"
          value={editingEvent.reminder_time}
          onChange={(e) => setEditingEvent({...editingEvent, reminder_time: e.target.value})}
          required
        />
        <input
          type="text"
          placeholder="ID групи (необов'язково)"
          value={editingEvent.group_id || ''}
          onChange={(e) => setEditingEvent({...editingEvent, group_id: e.target.value})}
        />
        <div className="form-actions">
          <button type="submit">Оновити подію</button>
          <button type="button" onClick={() => setEditingEvent(null)} className="cancel-btn">
            Скасувати
          </button>
        </div>
      </form>
    </div>
  );

  const renderCreateGroupView = () => (
    <div>
      <h2>Створити групу</h2>
      <form onSubmit={createGroup}>
        <input
          type="text"
          placeholder="Назва групи"
          value={newGroup.name}
          onChange={(e) => setNewGroup({...newGroup, name: e.target.value})}
          required
        />
        <input
          type="text"
          placeholder="ID учасників через кому (необов'язково)"
          value={newGroup.members.join(', ')}
          onChange={(e) => {
            const members = e.target.value.split(',').map(id => parseInt(id.trim())).filter(id => !isNaN(id));
            setNewGroup({...newGroup, members});
          }}
        />
        <div className="form-actions">
          <button type="submit">Створити групу</button>
          <button type="button" onClick={() => setCurrentView('groups')} className="cancel-btn">
            Скасувати
          </button>
        </div>
      </form>
    </div>
  );

  const renderEditGroupView = () => (
    <div>
      <h2>Редагувати групу</h2>
      <form onSubmit={updateGroup}>
        <input
          type="text"
          placeholder="Назва групи"
          value={editingGroup.name}
          onChange={(e) => setEditingGroup({...editingGroup, name: e.target.value})}
          required
        />
        <div className="members-section">
          <h4>Учасники:</h4>
          <div className="members-list">
            {JSON.parse(editingGroup.members || '[]').map(memberId => (
              <div key={memberId} className="member-item">
                <span>ID: {memberId}</span>
                <button 
                  type="button" 
                  onClick={() => removeMemberFromGroup(editingGroup.id, memberId)}
                  className="remove-member-btn"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
          <button 
            type="button" 
            onClick={() => addMemberToGroup(editingGroup.id)}
            className="add-member-btn"
          >
            Додати учасника
          </button>
        </div>
        <div className="form-actions">
          <button type="submit">Оновити групу</button>
          <button type="button" onClick={() => setEditingGroup(null)} className="cancel-btn">
            Скасувати
          </button>
        </div>
      </form>
    </div>
  );

  const renderMainView = () => {
    if (editingEvent) return renderEditEventView();
    if (editingGroup) return renderEditGroupView();
    
    switch (currentView) {
      case 'create-event':
        return renderCreateEventView();
      case 'create-group':
        return renderCreateGroupView();
      case 'groups':
        return renderGroupsView();
      default:
        return renderEventsView();
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>📅 Планувальник</h1>
        {user && <p>Привіт, {user.first_name}!</p>}
      </header>

      <nav className="navigation">
        <button 
          onClick={() => setCurrentView('events')} 
          className={currentView === 'events' ? 'active' : ''}
        >
          Події
        </button>
        <button 
          onClick={() => setCurrentView('groups')} 
          className={currentView === 'groups' ? 'active' : ''}
        >
          Групи
        </button>
      </nav>

      <main>
        {renderMainView()}
      </main>
    </div>
  );
}

export default App; 
