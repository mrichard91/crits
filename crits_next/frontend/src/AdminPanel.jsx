import { gql, useQuery, useMutation } from '@apollo/client';

const USERS_QUERY = gql`
  query Users {
    users { id email permissions preferences }
  }
`;

const UPDATE_PREFS = gql`
  mutation UpdatePreferences($id: String!, $preferences: JSON!) {
    updatePreferences(id: $id, preferences: $preferences) { id preferences }
  }
`;

const UPDATE_PERMS = gql`
  mutation UpdatePermissions($id: String!, $permissions: [String!]!) {
    updatePermissions(id: $id, permissions: $permissions) { id permissions }
  }
`;

export default function AdminPanel() {
  const { data, loading, error, refetch } = useQuery(USERS_QUERY);
  const [updatePrefs] = useMutation(UPDATE_PREFS);
  const [updatePerms] = useMutation(UPDATE_PERMS);

  if (loading) return <p>Loading users...</p>;
  if (error) return <p>Error loading users</p>;

  const handlePrefsBlur = (id, value) => {
    let prefs = {};
    try { prefs = JSON.parse(value); } catch (e) {}
    updatePrefs({ variables: { id, preferences: prefs } }).then(() => refetch());
  };

  const handlePermsBlur = (id, value) => {
    const perms = value.split(',').map(p => p.trim()).filter(Boolean);
    updatePerms({ variables: { id, permissions: perms } }).then(() => refetch());
  };

  return (
    <div>
      <h2>User Management</h2>
      {data.users.map(u => (
        <div key={u.id} style={{ border: '1px solid #ccc', padding: '1rem', marginBottom: '1rem' }}>
          <strong>{u.email}</strong>
          <div>
            <label>Preferences:</label>
            <input
              type="text"
              defaultValue={JSON.stringify(u.preferences)}
              onBlur={(e) => handlePrefsBlur(u.id, e.target.value)}
            />
          </div>
          <div>
            <label>Permissions:</label>
            <input
              type="text"
              defaultValue={u.permissions.join(',')}
              onBlur={(e) => handlePermsBlur(u.id, e.target.value)}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
