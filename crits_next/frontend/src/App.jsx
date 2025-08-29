import { GoogleLogin } from '@react-oauth/google';
import { useState } from 'react';
import AdminPanel from './AdminPanel';

export default function App() {
  const [user, setUser] = useState(null);

  const handleSuccess = async (credentialResponse) => {
    const res = await fetch('http://localhost:8000/auth/google', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token: credentialResponse.credential }),
    });
    const data = await res.json();
    setUser(data);
  };

  return (
    <div>
      <h1>CRITs Next User Management</h1>
      {user ? (
        <AdminPanel />
      ) : (
        <GoogleLogin onSuccess={handleSuccess} onError={() => console.log('Login Failed')} />
      )}
    </div>
  );
}
