import { useState, useEffect } from 'react';
import axios from 'axios';

export function LogisticsPanel({ apiUrl }) {
  const [orders, setOrders] = useState([]);
  const [selectedIds, setSelectedIds] = useState([]);
  const [motoboy, setMotoboy] = useState('');
  const [custo, setCusto] = useState('');

  useEffect(() => {
    fetchOrders();
  }, []);

  const fetchOrders = async () => {
    try {
      const response = await axios.get(`${apiUrl}/orders`);
      // Filtra apenas pedidos que podem ser despachados (Ex: EM_PREPARO)
      // Ignora os que já estão em rota, concluídos ou apenas recebidos
      const readyToShip = response.data.filter(o => o.status === 'PRONTO');
      setOrders(readyToShip);
      setSelectedIds([]); // Limpa seleção ao recarregar
    } catch (error) {
      console.error("Erro ao buscar encomendas", error);
    }
  };

  const toggleSelect = (id) => {
    setSelectedIds(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  const handleCreateRoute = async (e) => {
    e.preventDefault();

    if (selectedIds.length === 0) {
        alert("Selecione pelo menos um pedido.");
        return;
    }
    if (!motoboy || !custo) {
        alert("Preencha o motoboy e o custo.");
        return;
    }

    try {
      const payload = {
        motoboy_nome: motoboy,
        custo_total: parseFloat(custo),
        pedidos_ids: selectedIds
      };

      const res = await axios.post(`${apiUrl}/logistics/routes`, payload);

      alert(`Rota criada! ID: ${res.data.entrega_id}\nCusto por pedido: R$ ${res.data.custo_por_pedido}`);

      // Limpa formulário e recarrega
      setMotoboy('');
      setCusto('');
      fetchOrders();

    } catch (error) {
      console.error(error);
      alert("Erro ao criar rota: " + (error.response?.data?.error || error.message));
    }
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px', textAlign: 'left' }}>

      {/* LISTA DE PEDIDOS DISPONÍVEIS */}
      <div>
        <h3>📦 Pedidos Prontos para Envio ({orders.length})</h3>
        {orders.length === 0 ? <p>Nenhum pedido aguardando despacho (Status: EM_PREPARO).</p> : (
            <div style={{ display: 'grid', gap: '10px' }}>
                {orders.map(order => (
                    <div
                        key={order.id}
                        onClick={() => toggleSelect(order.id)}
                        style={{
                            border: selectedIds.includes(order.id) ? '2px solid #28a745' : '1px solid #444',
                            background: selectedIds.includes(order.id) ? '#1e3324' : '#222',
                            padding: '15px',
                            borderRadius: '8px',
                            cursor: 'pointer',
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center'
                        }}
                    >
                        <div>
                            <div style={{fontWeight: 'bold', fontSize: '1.1em'}}>{order.cliente_nome}</div>
                            <div style={{fontSize: '0.9em', color: '#aaa'}}>{order.data_entrega}</div>
                            <ul style={{ margin: '5px 0', paddingLeft: '20px', fontSize: '0.9em', color: '#ccc' }}>
                                {order.itens.map((item, i) => <li key={i}>{item.qtd}x {item.sabor}</li>)}
                            </ul>
                        </div>
                        <div style={{ fontSize: '1.5em' }}>
                            {selectedIds.includes(order.id) ? '✅' : '⬜'}
                        </div>
                    </div>
                ))}
            </div>
        )}
      </div>

      {/* FORMULÁRIO DE ROTA */}
      <div style={{ background: '#2a2a2a', padding: '20px', borderRadius: '8px', height: 'fit-content', position: 'sticky', top: '20px', border: '1px solid #444' }}>
        <h3 style={{marginTop: 0}}>🛵 Dados da Entrega</h3>
        <form onSubmit={handleCreateRoute}>
            <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '5px', color: '#ccc' }}>Nome do Motoboy:</label>
                <input
                    type="text"
                    value={motoboy}
                    onChange={(e) => setMotoboy(e.target.value)}
                    placeholder="Ex: João Silva"
                    required
                    style={{ width: '100%', padding: '10px', boxSizing: 'border-box', background: '#111', border: '1px solid #555', color: 'white', borderRadius: '4px' }}
                />
            </div>

            <div style={{ marginBottom: '20px' }}>
                <label style={{ display: 'block', marginBottom: '5px', color: '#ccc' }}>Custo Total da Rota (R$):</label>
                <input
                    type="number"
                    step="0.01"
                    value={custo}
                    onChange={(e) => setCusto(e.target.value)}
                    placeholder="Ex: 25.00"
                    required
                    style={{ width: '100%', padding: '10px', boxSizing: 'border-box', background: '#111', border: '1px solid #555', color: 'white', borderRadius: '4px' }}
                />
            </div>

            <div style={{ marginBottom: '15px', padding: '10px', background: '#333', borderRadius: '4px' }}>
                <strong>Resumo:</strong><br/>
                Pedidos selecionados: {selectedIds.length}<br/>
                {selectedIds.length > 0 && custo && (
                    <span style={{ color: '#4ade80' }}>
                        Rateio aprox: R$ {(parseFloat(custo) / selectedIds.length).toFixed(2)} / pedido
                    </span>
                )}
            </div>

            <button
                type="submit"
                disabled={selectedIds.length === 0 || !custo || !motoboy}
                style={{
                    width: '100%',
                    padding: '12px',
                    background: (selectedIds.length > 0 && custo && motoboy) ? '#6f42c1' : '#555',
                    color: 'white',
                    border: 'none',
                    borderRadius: '5px',
                    fontWeight: 'bold',
                    cursor: (selectedIds.length > 0 && custo && motoboy) ? 'pointer' : 'not-allowed'
                }}
            >
                Despachar Rota 🚀
            </button>
        </form>
      </div>
    </div>
  );
}