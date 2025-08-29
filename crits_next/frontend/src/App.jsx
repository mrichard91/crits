import { gql, useQuery } from '@apollo/client';
import { useEffect, useState } from 'react';
import axios from 'axios';
import Admin from './Admin';

const HELLO_QUERY = gql`
  query Hello {
    hello
  }
`;

export default function App() {
  const { data, loading, error } = useQuery(HELLO_QUERY);
  const [user, setUser] = useState(null);

  useEffect(() => {
    axios.get('/users/me').then(res => setUser(res.data)).catch(() => setUser(null));
  }, []);

  const login = () => {
    window.location.href = '/auth/google';
  };

  if (loading) return <p>Loading...</p>;
  if (error) return <p>Error: {error.message}</p>;

  return (
    <div>
      <h1>{data.hello}</h1>
      {!user && <button onClick={login}>Login with Google</button>}
      {user && <p>Logged in as {user.email}</p>}
      {user?.is_admin && <Admin />}
    </div>
  );
}
