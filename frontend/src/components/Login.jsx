import { useState } from 'react';
import { login } from '../auth';

export function Login({ onLoginSuccess }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await login(email, password);
      onLoginSuccess(); // Avisa o App que logou
    } catch (err) {
      console.error(err);
      setError('Login falhou. Verifique email e senha.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }}>
      <div style={{ background: '#222', padding: '40px', borderRadius: '10px', border: '1px solid #444', textAlign: 'center', width: '300px' }}>
        <h2 style={{marginTop: 0}}>🍪 Acesso Restrito</h2>
        <p style={{color: '#aaa', fontSize: '0.9em'}}>Identifique-se para entrar na Cozinha</p>

        {error && <div style={{ background: '#dc3545', color: 'white', padding: '10px', borderRadius: '4px', marginBottom: '15px', fontSize: '0.9em' }}>{error}</div>}

        <form onSubmit={handleSubmit}>
            <input
                type="text"
                placeholder="Email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                style={{ width: '100%', padding: '10px', marginBottom: '10px', boxSizing: 'border-box', borderRadius: '4px', border: '1px solid #555', background: '#111', color: 'white' }}
            />
            <input
                type="password"
                placeholder="Senha"
                value={password}
                onChange={e => setPassword(e.target.value)}
                style={{ width: '100%', padding: '10px', marginBottom: '20px', boxSizing: 'border-box', borderRadius: '4px', border: '1px solid #555', background: '#111', color: 'white' }}
            />
            <button
                type="submit"
                disabled={loading}
                style={{ width: '100%', padding: '10px', background: '#646cff', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}
            >
                {loading ? 'Entrando...' : 'Entrar'}
            </button>
        </form>
      </div>
    </div>
  );
}