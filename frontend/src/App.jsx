import { useState, useEffect } from 'react'
import axios from 'axios'
import { AdminPanel } from './components/AdminPanel'
import { OrdersPanel } from './components/OrdersPanel'
import { LogisticsPanel } from './components/LogisticsPanel'
import { Login } from './components/Login' // <--- IMPORTAÇÃO DA TELA DE LOGIN
import { getSession, getToken, logout } from './auth' // <--- LÓGICA DE AUTH

// IMPORTANTE: Use a URL que aparecerá no terminal após o 'cdk deploy'
const API_URL = "https://vqrrh1kjy3.execute-api.us-east-1.amazonaws.com";

// Configura o Axios para injetar o Token em TODAS as requisições automaticamente
axios.interceptors.request.use(async (config) => {
    const token = await getToken();
    if (token) {
        config.headers.Authorization = token; // Manda o crachá pro porteiro
    }
    return config;
});

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);

  // States do sistema
  const [cookies, setCookies] = useState([])
  const [cart, setCart] = useState({})
  const [cliente, setCliente] = useState('')
  const [dataEntrega, setDataEntrega] = useState('')
  const [view, setView] = useState('vendas')

  // 1. Verifica se já está logado ao abrir o site
  useEffect(() => {
    getSession()
        .then(() => {
            setIsAuthenticated(true);
            fetchCookies(); // Só busca dados se logado
        })
        .catch(() => setIsAuthenticated(false))
        .finally(() => setIsCheckingAuth(false));
  }, []);

  const fetchCookies = async () => {
    try {
      const response = await axios.get(`${API_URL}/cookies`);
      setCookies(response.data);
    } catch (error) {
      console.error("Erro ao buscar cookies", error);
      // Se der erro 401 (Token expirou), desloga
      if (error.response && error.response.status === 401) {
          logout();
      }
    }
  };

  const handleCookieSaved = (savedCookie) => {
    setCookies((prevCookies) => {
      const index = prevCookies.findIndex(c => c.id === savedCookie.id);
      if (index >= 0) {
        const newList = [...prevCookies];
        newList[index] = savedCookie;
        return newList;
      } else {
        return [...prevCookies, savedCookie];
      }
    });
  };

  // ... (Funções de carrinho, checkout, etc. continuam iguais)
  const addToCart = (cookie) => {
    setCart(prev => ({ ...prev, [cookie.id]: (prev[cookie.id] || 0) + 1 }));
  };

  const removeFromCart = (cookieId) => {
    setCart(prev => {
      const currentQty = prev[cookieId] || 0;
      if (currentQty <= 0) return prev;
      const newCart = { ...prev };
      if (currentQty > 1) newCart[cookieId] -= 1;
      else delete newCart[cookieId];
      return newCart;
    });
  };

  const getQuantity = (cookieId) => { return cart[cookieId] || 0; };

  const checkout = async () => {
    const itensPayload = Object.keys(cart).map(cookieId => ({ cookie_id: cookieId, qtd: cart[cookieId] })).filter(item => item.qtd > 0);
    if (itensPayload.length === 0) { alert("Carrinho vazio!"); return; }
    if (!cliente.trim()) { alert("Informe o cliente."); return; }
    if (!dataEntrega) { alert("Informe a data."); return; }

    try {
      await axios.post(`${API_URL}/orders`, {
        cliente_nome: cliente,
        data_entrega: new Date(dataEntrega).toISOString(),
        itens: itensPayload
      });
      alert(`Encomenda agendada!`);
      setCart({}); setCliente(''); setDataEntrega('');
    } catch (error) {
      alert(`Erro: ${error.response?.data?.error || error.message}`);
    }
  };

  const totalCart = Object.keys(cart).reduce((acc, id) => {
    const cookie = cookies.find(c => c.id === id);
    return acc + (cookie ? cookie.preco_venda * cart[id] : 0);
  }, 0);

  // --- RENDERIZAÇÃO ---

  if (isCheckingAuth) return <p style={{textAlign: 'center', marginTop: '50px'}}>Verificando credenciais...</p>;

  // Se não estiver logado, mostra TELA DE LOGIN
  if (!isAuthenticated) {
      return <Login onLoginSuccess={() => { setIsAuthenticated(true); fetchCookies(); }} />;
  }

  // Se estiver logado, mostra o SISTEMA
  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '20px', fontFamily: 'Arial' }}>

      {/* --- HEADER --- */}
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h1 style={{fontSize: '1.5em'}}>🍪 Cookie Admin</h1>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            <nav style={{ display: 'flex', gap: '5px' }}>
                <button onClick={() => setView('vendas')} style={{ background: view === 'vendas' ? '#646cff' : '#333', color: 'white', border: 'none', padding: '8px 15px', borderRadius: '5px' }}>Vendas</button>
                <button onClick={() => setView('pedidos')} style={{ background: view === 'pedidos' ? '#646cff' : '#333', color: 'white', border: 'none', padding: '8px 15px', borderRadius: '5px' }}>Cozinha</button>
                <button onClick={() => setView('logistica')} style={{ background: view === 'logistica' ? '#646cff' : '#333', color: 'white', border: 'none', padding: '8px 15px', borderRadius: '5px' }}>Logística</button>
                <button onClick={() => setView('admin')} style={{ background: view === 'admin' ? '#646cff' : '#333', color: 'white', border: 'none', padding: '8px 15px', borderRadius: '5px' }}>Admin</button>
            </nav>

            {/* Botão de Sair */}
            <button onClick={logout} style={{ background: '#dc3545', color: 'white', border: 'none', padding: '8px 15px', borderRadius: '5px', marginLeft: '10px' }}>
                Sair
            </button>
        </div>
      </header>

      {/* --- CONTEÚDO (Igual ao anterior) --- */}
      {view === 'admin' && <AdminPanel apiUrl={API_URL} cookies={cookies} onCookieSaved={handleCookieSaved} />}
      {view === 'pedidos' && <OrdersPanel apiUrl={API_URL} />}
      {view === 'logistica' && <LogisticsPanel apiUrl={API_URL} />}

      {view === 'vendas' && (
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '15px' }}>
            {cookies.map(cookie => (
                <div key={cookie.id} style={{ border: '1px solid #444', padding: '15px', borderRadius: '8px', textAlign: 'left', background: '#1a1a1a', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                  <div>
                    <h3 style={{ marginTop: 0, marginBottom: '5px' }}>{cookie.sabor}</h3>
                    <p style={{ color: '#888', fontSize: '0.9em', margin: '0 0 10px 0' }}>{cookie.descricao}</p>
                  </div>
                  <div style={{ marginTop: '10px' }}>
                    <div style={{ marginBottom: '10px', fontSize: '1.2em', fontWeight: 'bold' }}>R$ {cookie.preco_venda.toFixed(2)}</div>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: '#333', borderRadius: '4px', padding: '4px' }}>
                      <button onClick={() => removeFromCart(cookie.id)} disabled={getQuantity(cookie.id) === 0} style={{ background: getQuantity(cookie.id) === 0 ? '#555' : '#d9534f', color: 'white', border: 'none', width: '35px', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>-</button>
                      <span style={{ fontWeight: 'bold', fontSize: '1.3em', color: 'white', minWidth: '30px', textAlign: 'center' }}>{getQuantity(cookie.id)}</span>
                      <button onClick={() => addToCart(cookie)} style={{ background: '#28a745', color: 'white', border: 'none', width: '35px', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>+</button>
                    </div>
                  </div>
                </div>
            ))}
          </div>

          <div style={{ border: '1px solid #444', padding: '20px', borderRadius: '8px', height: 'fit-content', background: '#242424', position: 'sticky', top: '20px' }}>
            <h2>🛒 Encomenda</h2>
            <input type="text" value={cliente} onChange={(e) => setCliente(e.target.value)} placeholder="Nome Cliente" style={{ width: '100%', padding: '8px', marginBottom: '10px', background: '#111', border: '1px solid #555', color: 'white', borderRadius: '4px' }} />
            <input type="datetime-local" value={dataEntrega} onChange={(e) => setDataEntrega(e.target.value)} style={{ width: '100%', padding: '8px', marginBottom: '15px', background: '#111', border: '1px solid #555', color: 'white', borderRadius: '4px' }} />

            {Object.keys(cart).length > 0 ? (
                <ul style={{ listStyle: 'none', padding: 0 }}>
                    {Object.keys(cart).map(id => {
                        const item = cookies.find(c => c.id === id);
                        if(!item) return null;
                        return <li key={id} style={{display:'flex', justifyContent:'space-between', borderBottom:'1px solid #333', padding:'5px 0'}}><span>{cart[id]}x {item.sabor}</span><span>R$ {(item.preco_venda * cart[id]).toFixed(2)}</span></li>
                    })}
                </ul>
            ) : <p style={{color:'#666'}}>Vazio</p>}

            <div style={{ borderTop: '2px solid #555', paddingTop: '15px', marginTop: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '1.3em', fontWeight: 'bold', marginBottom: '15px' }}><span>Total:</span><span>R$ {totalCart.toFixed(2)}</span></div>
                <button onClick={checkout} disabled={Object.keys(cart).length === 0} style={{ width: '100%', background: Object.keys(cart).length === 0 ? '#555' : '#28a745', color: 'white', padding: '12px', border: 'none', borderRadius: '5px', cursor: 'pointer' }}>Agendar</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App