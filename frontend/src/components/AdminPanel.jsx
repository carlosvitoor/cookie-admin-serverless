import { useState } from 'react';
import axios from 'axios';

export function AdminPanel({ apiUrl, onProductAdded }) {
  const [formData, setFormData] = useState({
    sabor: '',
    descricao: '',
    preco_venda: '',
    custo_producao: ''
  });

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      // O backend espera dados numéricos para preço/custo
      const payload = {
        ...formData,
        preco_venda: parseFloat(formData.preco_venda),
        custo_producao: parseFloat(formData.custo_producao)
      };

      await axios.post(`${apiUrl}/cookies`, payload);
      alert('Cookie cadastrado com sucesso!');

      // Limpa formulário
      setFormData({ sabor: '', descricao: '', preco_venda: '', custo_producao: '' });

      // Avisa o pai para recarregar a lista
      if (onProductAdded) onProductAdded();

    } catch (error) {
      console.error(error);
      alert('Erro ao cadastrar: ' + (error.response?.data?.error || error.message));
    }
  };

  return (
    <div style={{ border: '1px solid #444', padding: '20px', borderRadius: '8px', marginBottom: '20px', background: '#2a2a2a' }}>
      <h2>📝 Cadastro de Produto</h2>
      <form onSubmit={handleSubmit} style={{ display: 'grid', gap: '10px', maxWidth: '400px', margin: '0 auto' }}>
        <input name="sabor" placeholder="Sabor (ex: Chocolate)" value={formData.sabor} onChange={handleChange} required style={{padding: '8px'}} />
        <input name="descricao" placeholder="Descrição" value={formData.descricao} onChange={handleChange} style={{padding: '8px'}} />
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
            <input name="preco_venda" type="number" step="0.01" placeholder="Preço Venda (R$)" value={formData.preco_venda} onChange={handleChange} required style={{padding: '8px'}} />
            <input name="custo_producao" type="number" step="0.01" placeholder="Custo Prod. (R$)" value={formData.custo_producao} onChange={handleChange} required style={{padding: '8px'}} />
        </div>
        <button type="submit" style={{ background: '#28a745', color: 'white' }}>Cadastrar Cookie</button>
      </form>
    </div>
  );
}