import { useState } from 'react';
import axios from 'axios';

export function AdminPanel({ apiUrl, cookies, onCookieSaved }) {
  const [editingId, setEditingId] = useState(null); // ID do cookie sendo editado

  const [formData, setFormData] = useState({
    sabor: '',
    descricao: '',
    preco_venda: '',
    custo_producao: ''
  });

  // Preenche o formulário ao clicar em "Editar"
  const handleEditClick = (cookie) => {
    setEditingId(cookie.id);
    setFormData({
      sabor: cookie.sabor,
      descricao: cookie.descricao,
      preco_venda: cookie.preco_venda,
      custo_producao: cookie.custo_producao
    });
    // Rola a página para o topo do formulário
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setFormData({ sabor: '', descricao: '', preco_venda: '', custo_producao: '' });
  };

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        preco_venda: parseFloat(formData.preco_venda),
        custo_producao: parseFloat(formData.custo_producao)
      };

      let savedData;

      if (editingId) {
        // --- MODO EDIÇÃO (PUT) ---
        const response = await axios.put(`${apiUrl}/cookies/${editingId}`, payload);
        savedData = response.data;
        alert(`Cookie "${payload.sabor}" atualizado com sucesso!`);
      } else {
        // --- MODO CRIAÇÃO (POST) ---
        const response = await axios.post(`${apiUrl}/cookies`, payload);
        savedData = response.data;
        alert('Cookie cadastrado com sucesso!');
      }

      // ATUALIZAÇÃO OTIMISTA: Atualiza a lista na hora, sem esperar o banco
      if (onCookieSaved) onCookieSaved(savedData);

      handleCancelEdit(); // Limpa form e estado

    } catch (error) {
      console.error(error);
      alert('Erro: ' + (error.response?.data?.error || error.message));
    }
  };

  return (
    <div>
        {/* --- FORMULÁRIO --- */}
        <div style={{ border: '1px solid #444', padding: '20px', borderRadius: '8px', marginBottom: '30px', background: '#2a2a2a' }}>
        <h2 style={{ marginTop: 0 }}>
            {editingId ? `✏️ Editando: ${formData.sabor}` : '📝 Novo Produto'}
        </h2>

        <form onSubmit={handleSubmit} style={{ display: 'grid', gap: '10px', maxWidth: '500px', margin: '0 auto' }}>
            <input name="sabor" placeholder="Sabor (ex: Chocolate)" value={formData.sabor} onChange={handleChange} required style={{padding: '8px'}} />
            <input name="descricao" placeholder="Descrição" value={formData.descricao} onChange={handleChange} style={{padding: '8px'}} />

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <input name="preco_venda" type="number" step="0.01" placeholder="Preço Venda (R$)" value={formData.preco_venda} onChange={handleChange} required style={{padding: '8px'}} />
                <input name="custo_producao" type="number" step="0.01" placeholder="Custo Prod. (R$)" value={formData.custo_producao} onChange={handleChange} required style={{padding: '8px'}} />
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
                <button type="submit" style={{ flex: 1, background: editingId ? '#007bff' : '#28a745', color: 'white', padding: '10px' }}>
                    {editingId ? 'Salvar Alterações' : 'Cadastrar Cookie'}
                </button>

                {editingId && (
                    <button type="button" onClick={handleCancelEdit} style={{ background: '#6c757d', color: 'white', padding: '10px' }}>
                        Cancelar
                    </button>
                )}
            </div>
        </form>
        </div>

        {/* --- LISTAGEM PARA SELEÇÃO --- */}
        <h3>📦 Produtos Cadastrados (Selecione para Editar)</h3>
        <div style={{ display: 'grid', gap: '10px' }}>
            {cookies.map(cookie => (
                <div key={cookie.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#1a1a1a', padding: '10px 15px', borderRadius: '6px', border: '1px solid #333' }}>
                    <div>
                        <strong>{cookie.sabor}</strong>
                        <span style={{ color: '#888', marginLeft: '10px', fontSize: '0.9em' }}>R$ {cookie.preco_venda.toFixed(2)}</span>
                    </div>
                    <button onClick={() => handleEditClick(cookie)} style={{ background: 'transparent', border: '1px solid #646cff', color: '#646cff', padding: '5px 10px', cursor: 'pointer' }}>
                        Editar
                    </button>
                </div>
            ))}
        </div>
    </div>
  );
}