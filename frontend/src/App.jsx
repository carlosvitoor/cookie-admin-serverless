import { useState, useEffect } from 'react'
import axios from 'axios'
import { AdminPanel } from './components/AdminPanel'

// IMPORTANTE: Use a URL que aparecerá no terminal após o 'cdk deploy'
const API_URL = "https://vqrrh1kjy3.execute-api.us-east-1.amazonaws.com";

function App() {
  const [cookies, setCookies] = useState([])
  const [cart, setCart] = useState({})
  const [cliente, setCliente] = useState('Cliente Balcão')
  const [view, setView] = useState('vendas')

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

  const addToCart = (cookie) => {
    setCart(prev => ({
      ...prev,
      [cookie.id]: (prev[cookie.id] || 0) + 1
    }));
  };

  const removeFromCart = (cookieId) => {
    setCart(prev => {
      const currentQty = prev[cookieId] || 0;
      if (currentQty <= 0) return prev;

      const newCart = { ...prev };
      if (currentQty > 1) {
        newCart[cookieId] -= 1;
      } else {
        delete newCart[cookieId];
      }
      return newCart;
    });
  };

  const getQuantity = (cookieId) => {
    return cart[cookieId] || 0;
  };

  const checkout = async () => {
    const itensPayload = Object.keys(cart)
      .map(cookieId => ({
        cookie_id: cookieId,
        qtd: cart[cookieId]
      }))
      .filter(item => item.qtd > 0);

    if (itensPayload.length === 0) {
      alert("Carrinho vazio!");
      return;
    }

    try {
      const payload = {
        cliente_nome: cliente || 'Cliente Balcão',
        itens: itensPayload
      };

      await axios.post(`${API_URL}/orders`, payload);

      alert(`Pedido realizado com sucesso para ${cliente}!`);
      setCart({});
      setCliente('Cliente Balcão');

    } catch (error) {
      console.error(error);
      const msg = error.response?.data?.error || error.message;
      alert(`Erro ao enviar pedido: ${msg}`);
    }
  };

  const totalCart = Object.keys(cart).reduce((acc, id) => {
    const cookie = cookies.find(c => c.id === id);
    return acc + (cookie ? cookie.preco_venda * cart[id] : 0);
  }, 0);

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '20px', fontFamily: 'Arial' }}>

      {/* --- HEADER --- */}
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        {/* NOME ALTERADO AQUI */}
        <h1>🍪 Cookie Girls</h1>
        <div>
            <button
              onClick={() => setView('vendas')}
              style={{ marginRight: '10px', background: view === 'vendas' ? '#646cff' : '#333', color: 'white', border: 'none', padding: '10px 20px', borderRadius: '5px', cursor: 'pointer' }}
            >
              Vendas
            </button>
            <button
              onClick={() => setView('admin')}
              style={{ background: view === 'admin' ? '#646cff' : '#333', color: 'white', border: 'none', padding: '10px 20px', borderRadius: '5px', cursor: 'pointer' }}
            >
              Admin
            </button>
        </div>
      </header>

      {/* --- MODO ADMIN --- */}
      {view === 'admin' && (
        <AdminPanel
            apiUrl={API_URL}
            cookies={cookies}
            onUpdateList={fetchCookies}
        />
      )}

      {/* --- MODO VENDAS --- */}
      {view === 'vendas' && (
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px' }}>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '15px' }}>
            {cookies.map(cookie => {
              const qtd = getQuantity(cookie.id);

              return (
                <div key={cookie.id} style={{ border: '1px solid #444', padding: '15px', borderRadius: '8px', textAlign: 'left', background: '#1a1a1a', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>

                  <div>
                    <h3 style={{ marginTop: 0, marginBottom: '5px' }}>{cookie.sabor}</h3>
                    <p style={{ color: '#888', fontSize: '0.9em', margin: '0 0 10px 0' }}>{cookie.descricao}</p>
                  </div>

                  <div style={{ marginTop: '10px' }}>
                    <div style={{ marginBottom: '10px', fontSize: '1.2em', fontWeight: 'bold' }}>
                      R$ {cookie.preco_venda.toFixed(2)}
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: '#333', borderRadius: '4px', padding: '4px' }}>
                      <button
                        onClick={() => removeFromCart(cookie.id)}
                        disabled={qtd === 0}
                        style={{
                          background: qtd === 0 ? '#555' : '#d9534f',
                          color: 'white',
                          border: 'none',
                          width: '35px',
                          height: '35px',
                          borderRadius: '4px',
                          cursor: qtd === 0 ? 'not-allowed' : 'pointer',
                          fontWeight: 'bold',
                          fontSize: '1.2em'
                        }}
                      >
                        -
                      </button>

                      <span style={{ fontWeight: 'bold', fontSize: '1.3em', color: 'white', minWidth: '30px' }}>{qtd}</span>

                      <button
                        onClick={() => addToCart(cookie)}
                        style={{
                          background: '#28a745',
                          color: 'white',
                          border: 'none',
                          width: '35px',
                          height: '35px',
                          borderRadius: '4px',
                          cursor: 'pointer',
                          fontWeight: 'bold',
                          fontSize: '1.2em'
                        }}
                      >
                        +
                      </button>
                    </div>

                  </div>
                </div>
              )
            })}
          </div>

          {/* Carrinho */}
          <div style={{ border: '1px solid #444', padding: '20px', borderRadius: '8px', height: 'fit-content', background: '#242424', position: 'sticky', top: '20px' }}>
            <h2>🛒 Carrinho</h2>
            <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '5px', color: '#ccc' }}>Cliente:</label>
                <input
                    type="text"
                    value={cliente}
                    onChange={(e) => setCliente(e.target.value)}
                    style={{ width: '100%', padding: '8px', boxSizing: 'border-box', background: '#111', border: '1px solid #555', color: 'white', borderRadius: '4px' }}
                />
            </div>

            {Object.keys(cart).length === 0 ? (
                <p style={{ color: '#666', fontStyle: 'italic' }}>Seu carrinho está vazio.</p>
            ) : (
                <ul style={{ listStyle: 'none', padding: 0, maxHeight: '400px', overflowY: 'auto' }}>
                    {Object.keys(cart).map(id => {
                        const item = cookies.find(c => c.id === id);
                        if(!item) return null;
                        return (
                            <li key={id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px', borderBottom: '1px solid #333', paddingBottom: '8px' }}>
                                <div>
                                  <div style={{fontWeight: 'bold'}}>{item.sabor}</div>
                                  <div style={{fontSize: '0.85em', color: '#aaa'}}>
                                    {cart[id]} x R$ {item.preco_venda.toFixed(2)}
                                  </div>
                                </div>
                                <div style={{fontWeight: 'bold'}}>
                                    R$ {(item.preco_venda * cart[id]).toFixed(2)}
                                </div>
                            </li>
                        )
                    })}
                </ul>
            )}

            <div style={{ borderTop: '2px solid #555', paddingTop: '15px', marginTop: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '1.3em', fontWeight: 'bold', marginBottom: '15px' }}>
                    <span>Total:</span>
                    <span>R$ {totalCart.toFixed(2)}</span>
                </div>
                <button
                    onClick={checkout}
                    disabled={Object.keys(cart).length === 0}
                    style={{
                      width: '100%',
                      background: Object.keys(cart).length === 0 ? '#555' : '#28a745',
                      color: 'white',
                      padding: '12px',
                      fontSize: '1.1em',
                      border: 'none',
                      borderRadius: '5px',
                      cursor: Object.keys(cart).length === 0 ? 'not-allowed' : 'pointer'
                    }}
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