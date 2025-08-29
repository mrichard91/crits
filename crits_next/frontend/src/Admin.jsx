import { useEffect, useState } from 'react';
import axios from 'axios';

export default function Admin() {
  const [users, setUsers] = useState([]);

  useEffect(() => {
    axios.get('/users').then(res => setUsers(res.data));
  }, []);

  const updateUser = (user) => {
    const preferences = prompt('Enter preferences as JSON', JSON.stringify(user.preferences));
    const permissions = prompt('Enter permissions as JSON array', JSON.stringify(user.permissions));
    axios.patch(`/users/${user.id}`, {
      preferences: JSON.parse(preferences || '{}'),
      permissions: JSON.parse(permissions || '[]'),
    }).then(res => {
      setUsers(users.map(u => u.id === res.data.id ? res.data : u));
    });
  };

  return (
    <div>
      <h2>Admin Panel</h2>
      <ul>
        {users.map(u => (
          <li key={u.id}>
            {u.email} <button onClick={() => updateUser(u)}>Edit</button>
          </li>
        ))}
      </ul>
    </div>
  );
}
