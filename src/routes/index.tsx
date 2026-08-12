/**
 * @file index.tsx
 * @description Vitrine Digital Premium do Nexus Digital Shop.
 * Fade-in em cascata, cards com shimmer, botões neon, cores suaves e layout responsivo.
 */

import React from 'react';
import { useShop } from '../context/ShopContext';

export const StorefrontRoute: React.FC = () => {
  const { produtos, slugAtivo, produtoSelecionado, setSlugAtivo, adicionarPedidoSimulado } = useShop();

  /* ─── TELA DE DETALHE DO PRODUTO ─── */
  if (slugAtivo && produtoSelecionado) {
    return (
      <div style={{ minHeight: '100vh', padding: '32px 24px' }}>
        <div className="nexus-container nexus-fade-in" style={{ maxWidth: 1000 }}>
          
          {/* Voltar */}
          <button
            onClick={() => setSlugAtivo(null)}
            className="nexus-btn nexus-btn-ghost nexus-btn-sm"
            style={{ marginBottom: 28 }}
          >
            ← Voltar para a Vitrine
          </button>

          <div className="nexus-card nexus-scale-in" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 0, overflow: 'hidden' }}>
            
            {/* Imagem */}
            <div style={{ position: 'relative', overflow: 'hidden', minHeight: 380, background: '#0a0c10' }}>
              <img
                src={produtoSelecionado.imagemUrl}
                alt={produtoSelecionado.nome}
                style={{
                  width: '100%',
                  height: '100%',
                  objectFit: 'cover',
                  transition: 'transform 0.6s cubic-bezier(0.16,1,0.3,1)',
                }}
                onMouseOver={(e) => (e.currentTarget.style.transform = 'scale(1.05)')}
                onMouseOut={(e) => (e.currentTarget.style.transform = 'scale(1)')}
              />
              <span className="nexus-badge" style={{ position: 'absolute', top: 16, left: 16 }}>
                {produtoSelecionado.categoria}
              </span>
            </div>

            {/* Info */}
            <div style={{ padding: 36, display: 'flex', flexDirection: 'column', gap: 20, justifyContent: 'center' }}>
              <div>
                <span className="nexus-badge-purple nexus-badge" style={{ marginBottom: 10, display: 'inline-flex' }}>
                  {produtoSelecionado.plataforma}
                </span>
                <h1 style={{ fontSize: 26, fontWeight: 300, color: '#f8fafc', letterSpacing: '-0.01em', lineHeight: 1.3 }}>
                  {produtoSelecionado.nome}
                </h1>
                <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginTop: 8 }}>
                  {[1,2,3,4,5].map(i => (
                    <span key={i} style={{ color: '#fbbf24', fontSize: 14 }}>★</span>
                  ))}
                  <span style={{ fontSize: 11, color: '#64748b', marginLeft: 6 }}>4.9 (128 avaliações)</span>
                </div>
              </div>

              <p style={{ fontSize: 13, color: '#94a3b8', fontWeight: 300, lineHeight: 1.7 }}>
                {produtoSelecionado.descricao}
              </p>

              {/* Bloco de preço */}
              <div className="nexus-glass" style={{ padding: 24, borderRadius: 14 }}>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: 14, marginBottom: 16 }}>
                  <span className="nexus-price">
                    R$ {produtoSelecionado.precoOferta.toFixed(2).replace('.', ',')}
                  </span>
                  {produtoSelecionado.precoOriginal > produtoSelecionado.precoOferta && (
                    <span className="nexus-price-old">
                      R$ {produtoSelecionado.precoOriginal.toFixed(2).replace('.', ',')}
                    </span>
                  )}
                  <span className="nexus-badge" style={{ fontSize: 9 }}>
                    💰 -{Math.round((1 - produtoSelecionado.precoOferta / produtoSelecionado.precoOriginal) * 100)}%
                  </span>
                </div>

                <button
                  onClick={() => {
                    adicionarPedidoSimulado(produtoSelecionado.precoOferta);
                    alert(`✅ Pedido gerado para ${produtoSelecionado.nome}!`);
                  }}
                  className="nexus-btn nexus-btn-primary nexus-btn-lg"
                  style={{ width: '100%' }}
                >
                  ⚡ Comprar Agora via PIX
                </button>
              </div>

              {/* Vantagens */}
              <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                <span className="nexus-badge" style={{ fontWeight: 400, textTransform: 'none' }}>✅ Entrega em 30s</span>
                <span className="nexus-badge" style={{ fontWeight: 400, textTransform: 'none' }}>🔒 100% Seguro</span>
                <span className="nexus-badge" style={{ fontWeight: 400, textTransform: 'none' }}>💬 Suporte VIP</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  /* ─── VITRINE PRINCIPAL ─── */
  return (
    <div style={{ minHeight: '100vh', padding: '32px 24px' }}>
      <div className="nexus-container" style={{ display: 'flex', flexDirection: 'column', gap: 40 }}>

        {/* Hero Banner */}
        <div className="nexus-hero nexus-fade-in">
          <div style={{ maxWidth: 560, position: 'relative', zIndex: 2 }}>
            <span className="nexus-badge" style={{ marginBottom: 14, display: 'inline-flex' }}>
              ⚡ Catálogo Oficial
            </span>
            <h1 style={{ fontSize: 38, fontWeight: 300, color: '#f8fafc', letterSpacing: '-0.02em', lineHeight: 1.15, marginBottom: 14 }}>
              <span className="nexus-glow-text">Nexus</span> Digital Shop
            </h1>
            <p style={{ fontSize: 14, color: '#94a3b8', fontWeight: 300, lineHeight: 1.7, marginBottom: 24 }}>
              Ativos digitais premium, licenças originais e ferramentas IA com entrega 100% automatizada.
            </p>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <button className="nexus-btn nexus-btn-primary nexus-btn-sm">⚡ Ver Ofertas</button>
              <button className="nexus-btn nexus-btn-sm">📚 Catálogo Completo</button>
              <button className="nexus-btn nexus-btn-sm">🤖 IA Tools</button>
              <button className="nexus-btn nexus-btn-sm">🎮 Jogos</button>
              <button className="nexus-btn nexus-btn-sm">🎓 Cursos</button>
            </div>
          </div>
        </div>

        {/* Seção de Produtos */}
        <section className="nexus-fade-in nexus-fade-in-delay-2">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
            <h2 style={{ fontSize: 20, fontWeight: 300, color: '#f1f5f9', letterSpacing: '0.01em' }}>
              Destaques <span style={{ color: '#64748b', fontSize: 14 }}>({produtos.length})</span>
            </h2>
            <div style={{ display: 'flex', gap: 4 }}>
              <button className="nexus-btn nexus-btn-sm nexus-btn-ghost">Todos</button>
              <button className="nexus-btn nexus-btn-sm nexus-btn-ghost">🔥 Ofertas</button>
              <button className="nexus-btn nexus-btn-sm nexus-btn-ghost">⭐ Top</button>
            </div>
          </div>

          <div className="nexus-grid">
            {produtos.map((prod, index) => (
              <div
                key={prod.id}
                onClick={() => setSlugAtivo(prod.slug)}
                className={`nexus-card nexus-fade-in nexus-fade-in-delay-${Math.min(index + 1, 8)}`}
                style={{ cursor: 'pointer', display: 'flex', flexDirection: 'column' }}
              >
                {/* Imagem */}
                <div style={{ position: 'relative', aspectRatio: '16/9', overflow: 'hidden', background: '#0a0c10' }}>
                  <img
                    src={prod.imagemUrl}
                    alt={prod.nome}
                    style={{
                      width: '100%',
                      height: '100%',
                      objectFit: 'cover',
                      transition: 'transform 0.5s cubic-bezier(0.16,1,0.3,1)',
                    }}
                    onMouseOver={(e) => (e.currentTarget.style.transform = 'scale(1.08)')}
                    onMouseOut={(e) => (e.currentTarget.style.transform = 'scale(1)')}
                  />
                  <span className="nexus-badge" style={{
                    position: 'absolute',
                    top: 10,
                    right: 10,
                    background: 'rgba(0,0,0,0.65)',
                    backdropFilter: 'blur(8px)',
                    borderColor: 'transparent',
                  }}>
                    {prod.categoria}
                  </span>
                </div>

                {/* Info */}
                <div style={{ padding: '16px 18px', flex: 1, display: 'flex', flexDirection: 'column', gap: 6 }}>
                  <span style={{ fontSize: 9, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                    {prod.plataforma}
                  </span>
                  <h3 style={{
                    fontSize: 14,
                    fontWeight: 400,
                    color: '#e2e8f0',
                    lineHeight: 1.3,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}>
                    {prod.nome}
                  </h3>
                  <p style={{
                    fontSize: 11,
                    color: '#64748b',
                    fontWeight: 300,
                    lineHeight: 1.5,
                    display: '-webkit-box',
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: 'vertical',
                    overflow: 'hidden',
                    flex: 1,
                  }}>
                    {prod.descricao}
                  </p>
                </div>

                {/* Footer do Card */}
                <div style={{
                  padding: '14px 18px',
                  borderTop: '1px solid rgba(255,255,255,0.04)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}>
                  <div>
                    <span className="nexus-price-old" style={{ display: 'block' }}>
                      R$ {prod.precoOriginal.toFixed(2).replace('.', ',')}
                    </span>
                    <span className="nexus-price" style={{ fontSize: 17 }}>
                      R$ {prod.precoOferta.toFixed(2).replace('.', ',')}
                    </span>
                  </div>
                  <button className="nexus-btn nexus-btn-sm">
                    Ver →
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
};
