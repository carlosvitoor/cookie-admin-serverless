import { useState, useEffect } from 'react'
import axios from 'axios'

// IMPORTANTE: Troque pela URL de DEV que você pegou no terminal
const API_URL = "https://SUA-URL-DE-DEV.execute-api.us-east-1.amazonaws.com";

function App() {
  const [cookies, setCookies] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchCookies();
  }, [])

  const fetchCookies = async () => {
    try {
      const response = await axios.get(`${API_URL}/cookies`);
      setCookies(response.data);
    } catch (error) {
      console.error("Erro ao buscar cookies", error);
      alert("Erro ao conectar com a API");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial' }}>
      <h1>🍪 Cookie Admin Store</h1>
      {loading ? <p>Carregando...</p> : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
          {cookies.map(cookie => (
            <div key={cookie.id} style={{ border: '1px solid #ddd', padding: '10px', borderRadius: '8px' }}>
              <h3>{cookie.sabor}</h3>
              <p>{cookie.descricao}</p>
              <p><strong>R$ {cookie.preco_venda}</strong></p>
              <button style={{ background: 'purple', color: 'white', border: 'none', padding: '5px 10px' }}>
                Vender
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default App