import { useState, useEffect } from 'react';
import axios from 'axios';

export function OrdersPanel({ apiUrl }) {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchOrders();
    const interval = setInterval(fetchOrders, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchOrders = async () => {
    try {
      const response = await axios.get(`${apiUrl}/orders`);
      // Ordena: Data de Entrega mais próxima primeiro
      const sorted = response.data.sort((a, b) => new Date(a.data_entrega) - new Date(b.data_entrega));
      setOrders(sorted);
    } catch (error) {
      console.error("Erro ao buscar encomendas", error);
    } finally {
      setLoading(false);
    }
  };

  const advanceStatus = async (orderId, currentStatus) => {
    const nextStatusMap = {
      'RECEBIDO': 'EM_PREPARO',
      'EM_PREPARO': 'EM_ROTA',
      'EM_ROTA': 'CONCLUIDO'
    };

    const next = nextStatusMap[currentStatus];
    if (!next) return;

    if (confirm(`Avançar status para ${next}?`)) {
      try {
        await axios.patch(`${apiUrl}/orders/${orderId}/status`, { status: next });
        fetchOrders();
      } catch (error) {
        alert("Erro ao atualizar status");
      }
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'RECEBIDO': return '#ffc107'; // Amarelo
      case 'EM_PREPARO': return '#17a2b8'; // Azul (Cozinhando)
      case 'EM_ROTA': return '#6f42c1'; // Roxo (Saiu para entrega)
      default: return '#ccc';
    }
  };

  // Calcula quanto tempo falta ou se atrasou
  const getTimeStatus = (dataEntregaIso) => {
    if (!dataEntregaIso) return { text: 'Sem data', color: '#888' };

    const agora = new Date();
    const entrega = new Date(dataEntregaIso);
    const diffMs = entrega - agora;
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);

    // Formatação da Data Legível
    const dateStr = entrega.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });

    if (diffMs < 0) {
        return { text: `ATRASADO! Era para ${dateStr}`, color: '#dc3545', border: '2px solid red' };
    }

    if (diffHours < 2) {
        // Menos de 2h para entregar: Urgente
        return { text: `URGENTE: ${dateStr}`, color: '#fd7e14', border: '2px solid orange' };
    }

    if (diffDays >= 1) {
        return { text: `Agendado: ${dateStr}`, color: '#28a745', border: '1px dashed #444' };
    }

    return { text: `Hoje às ${entrega.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}`, color: '#28a745', border: '1px dashed #444' };
  };

  if (loading) return <p>Carregando encomendas...</p>;

  return (
    <div>
      <h2>📅 Encomendas Pendentes ({orders.length})</h2>
      <button onClick={fetchOrders} style={{ marginBottom: '15px', background: '#333', color: 'white', border: 'none', padding: '10px', borderRadius: '4px' }}>Atualizar Lista</button>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '15px' }}>
        {orders.map(order => {
            const timeInfo = getTimeStatus(order.data_entrega);

            return (
                <div key={order.id} style={{ border: `2px solid ${getStatusColor(order.status)}`, borderRadius: '8px', padding: '15px', background: '#222' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                        <span style={{ fontWeight: 'bold', fontSize: '1.2em' }}>{order.cliente_nome}</span>
                        <span style={{ background: getStatusColor(order.status), padding: '2px 8px', borderRadius: '4px', fontSize: '0.8em', color: 'black', fontWeight: 'bold' }}>
                            {order.status}
                        </span>
                    </div>

                    <div style={{ color: timeInfo.color, fontWeight: 'bold', marginBottom: '15px', fontSize: '1em', border: timeInfo.border, padding: '8px', textAlign: 'center', background: '#1a1a1a', borderRadius: '4px' }}>
                        {timeInfo.text}
                    </div>

                    <ul style={{ paddingLeft: '20px', margin: '10px 0', color: '#ddd' }}>
                        {order.itens.map((item, idx) => (
                            <li key={idx} style={{ marginBottom: '5px' }}>
                                <strong>{item.qtd}x</strong> {item.sabor}
                            </li>
                        ))}
                    </ul>

                    <div style={{ marginTop: '15px', display: 'flex', gap: '10px' }}>
                        {order.status !== 'EM_ROTA' ? (
                            <button
                                onClick={() => advanceStatus(order.id, order.status)}
                                style={{ flex: 1, background: '#007bff', color: 'white', padding: '10px', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
                            >
                                Avançar Etapa ➡
                            </button>
                        ) : (
                            <button
                                onClick={() => advanceStatus(order.id, order.status)}
                                style={{ flex: 1, background: '#28a745', color: 'white', padding: '10px', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
                            >
                                ✅ Entregue
                            </button>
                        )}
                    </div>
                </div>
            )
        })}

        {orders.length === 0 && <p style={{ color: '#888' }}>Nenhuma encomenda pendente.</p>}
      </div>
    </div>
  );
}