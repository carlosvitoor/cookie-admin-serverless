import { useState, useEffect } from 'react'
import axios from 'axios'
import { AdminPanel } from './components/AdminPanel'

// IMPORTANTE: Mantenha a URL que você já tinha configurado ou use localhost se estiver rodando local
const API_URL = "https://vqrrh1kjy3.execute-api.us-east-1.amazonaws.com"; //

function App() {
  const [cookies, setCookies] = useState([])
  const [cart, setCart] = useState({}) // Formato: { 'id_cookie': quantidade }
  const [cliente, setCliente] = useState('Cliente Balcão')
  const [view, setView] = useState('vendas') // 'vendas' ou 'admin'

  useEffect(() => {
    fetchCookies();
  }, [])

  const fetchCookies = async () => {
    try {
      const response = await axios.get(`${API_URL}/cookies`);
      setCookies(response.data);
    } catch (error) {
      console.error("Erro ao buscar cookies", error);
    }
  };

  // Funções do Carrinho
  const addToCart = (cookie) => {
    setCart(prev => ({
      ...prev,
      [cookie.id]: (prev[cookie.id] || 0) + 1
    }));
  };

  const removeFromCart = (cookieId) => {
    setCart(prev => {
      const newCart = { ...prev };
      if (newCart[cookieId] > 1) {
        newCart[cookieId] -= 1;
      } else {
        delete newCart[cookieId];
      }
      return newCart;
    });
  };

  const checkout = async () => {
    const itensPayload = Object.keys(cart).map(cookieId => ({
      cookie_id: cookieId,
      qtd: cart[cookieId]
    }));

    if (itensPayload.length === 0) {
      alert("Carrinho vazio!");
      return;
    }

    try {
      const payload = {
        cliente_nome: cliente,
        itens: itensPayload
      };

      // Envia para o backend criar o pedido
      await axios.post(`${API_URL}/orders`, payload);

      alert(`Pedido realizado com sucesso para ${cliente}!`);
      setCart({}); // Limpa carrinho

    } catch (error) {
      console.error(error);
      alert('Erro no pedido: ' + (error.response?.data?.error || error.message));
    }
  };

  // Cálculo do Total
  const totalCart = Object.keys(cart).reduce((acc, id) => {
    const cookie = cookies.find(c => c.id === id);
    return acc + (cookie ? cookie.preco_venda * cart[id] : 0);
  }, 0);

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '20px', fontFamily: 'Arial' }}>

      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h1>🍪 Cookie Store</h1>
        <div>
            <button onClick={() => setView('vendas')} style={{ marginRight: '10px', background: view === 'vendas' ? '#646cff' : '#333' }}>Vendas</button>
            <button onClick={() => setView('admin')} style={{ background: view === 'admin' ? '#646cff' : '#333' }}>Admin</button>
        </div>
      </header>

      {/* --- MODO ADMIN --- */}
      {view === 'admin' && (
        <AdminPanel apiUrl={API_URL} onProductAdded={fetchCookies} />
      )}

      {/* --- MODO VENDAS --- */}
      {view === 'vendas' && (
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px' }}>

          {/* Lista de Produtos */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '15px' }}>
            {cookies.map(cookie => (
              <div key={cookie.id} style={{ border: '1px solid #444', padding: '15px', borderRadius: '8px', textAlign: 'left', background: '#1a1a1a' }}>
                <h3 style={{ marginTop: 0 }}>{cookie.sabor}</h3>
                <p style={{ color: '#888', fontSize: '0.9em' }}>{cookie.descricao}</p>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '10px' }}>
                  <span style={{ fontSize: '1.2em', fontWeight: 'bold' }}>R$ {cookie.preco_venda.toFixed(2)}</span>
                  <button onClick={() => addToCart(cookie)} style={{ background: '#646cff', color: 'white', border: 'none', padding: '5px 15px' }}>
                    + Add
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Carrinho Lateral */}
          <div style={{ border: '1px solid #444', padding: '20px', borderRadius: '8px', height: 'fit-content', background: '#242424' }}>
            <h2>🛒 Carrinho</h2>
            <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '5px' }}>Nome do Cliente:</label>
                <input
                    type="text"
                    value={cliente}
                    onChange={(e) => setCliente(e.target.value)}
                    style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}
                />
            </div>

            {Object.keys(cart).length === 0 ? (
                <p style={{ color: '#666' }}>Nenhum item selecionado.</p>
            ) : (
                <ul style={{ listStyle: 'none', padding: 0 }}>
                    {Object.keys(cart).map(id => {
                        const item = cookies.find(c => c.id === id);
                        if(!item) return null;
                        return (
                            <li key={id} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px', borderBottom: '1px solid #333', paddingBottom: '5px' }}>
                                <span>{item.sabor} (x{cart[id]})</span>
                                <div>
                                    <span style={{ marginRight: '10px' }}>R$ {(item.preco_venda * cart[id]).toFixed(2)}</span>
                                    <button onClick={() => removeFromCart(id)} style={{ padding: '2px 8px', background: '#d9534f', fontSize: '0.8em' }}>X</button>
                                </div>
                            </li>
                        )
                    })}
                </ul>
            )}

            <div style={{ borderTop: '2px solid #555', paddingTop: '10px', marginTop: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '1.2em', fontWeight: 'bold' }}>
                    <span>Total:</span>
                    <span>R$ {totalCart.toFixed(2)}</span>
                </div>
                <button
                    onClick={checkout}
                    disabled={Object.keys(cart).length === 0}
                    style={{ width: '100%', marginTop: '15px', background: '#28a745', padding: '10px', fontSize: '1.1em' }}
                >
                    Finalizar Pedido
                </button>
            </div>
          </div>

        </div>
      )}
    </div>
  )
}

export default App