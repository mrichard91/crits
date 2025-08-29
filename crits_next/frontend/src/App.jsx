import GitHubLogin from 'react-github-login';
import { useState } from 'react';
import AdminPanel from './AdminPanel';

export default function App() {
  const [user, setUser] = useState(null);

  const handleSuccess = async (response) => {
    const res = await fetch('http://localhost:8000/auth/github', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code: response.code }),
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
        <GitHubLogin
          clientId={import.meta.env.VITE_GITHUB_CLIENT_ID}
          onSuccess={handleSuccess}
          onFailure={() => console.log('Login Failed')}
        />
      )}
    </div>
  );
}
