/**
 * @file index.tsx
 * @description Rota Principal da Vitrine Digital e Exibição de Detalhes do Produto.
 * Resolve a sincronização do barramento de dados entre a vitrine e a aba interna de produto com Montserrat Light.
 */

import React from 'react';
import { useShop } from '../context/ShopContext';
import { ShoppingBag, ArrowLeft, CheckCircle, ShieldCheck, Zap, Star } from 'lucide-react';

export const StorefrontRoute: React.FC = () => {
  const { produtos, slugAtivo, produtoSelecionado, setSlugAtivo, adicionarPedidoSimulado } = useShop();

  // SE UM SLUG ESTIVER ATIVO: Renderiza a Tela de Detalhes do Produto
  if (slugAtivo && produtoSelecionado) {
    return (
      <div className="min-h-screen bg-[#0d0f12] text-gray-100 font-['Montserrat',sans-serif] p-6 lg:p-12">
        <div className="max-w-6xl mx-auto">
          {/* Botão de Retorno à Vitrine */}
          <button
            onClick={() => setSlugAtivo(null)}
            className="flex items-center gap-2 text-emerald-400 hover:text-emerald-300 font-light mb-8 transition-colors duration-200 cursor-pointer"
          >
            <ArrowLeft className="w-5 h-5" />
            <span>Voltar para a Vitrine</span>
          </button>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-start bg-[#14171c] p-8 rounded-2xl border border-gray-800 shadow-2xl">
            {/* Mídia Real do Produto */}
            <div className="space-y-4">
              <div className="relative aspect-video rounded-xl overflow-hidden border border-gray-700 bg-gray-900">
                <img
                  src={produtoSelecionado.imagemUrl}
                  alt={produtoSelecionado.nome}
                  className="w-full h-full object-cover transform hover:scale-105 transition-transform duration-500"
                />
                <span className="absolute top-4 left-4 bg-emerald-500/90 text-black text-xs font-semibold px-3 py-1 rounded-full uppercase tracking-wider">
                  {produtoSelecionado.categoria}
                </span>
              </div>
              
              <div className="flex items-center justify-between text-xs text-gray-400 border-t border-gray-800 pt-4">
                <div className="flex items-center gap-2">
                  <Zap className="w-4 h-4 text-emerald-400" />
                  <span>Entrega Digital Imediata via PIX</span>
                </div>
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  <span>Garantia Vitalícia</span>
                </div>
              </div>
            </div>

            {/* Informações Comerciais */}
            <div className="space-y-6">
              <div>
                <span className="text-xs uppercase tracking-widest text-emerald-400 font-light">
                  {produtoSelecionado.plataforma}
                </span>
                <h1 className="text-3xl font-light tracking-wide text-white mt-1">
                  {produtoSelecionado.nome}
                </h1>
                <div className="flex items-center gap-1 mt-2 text-amber-400 text-sm">
                  {[...Array(5)].map((_, i) => (
                    <Star key={i} className="w-4 h-4 fill-amber-400" />
                  ))}
                  <span className="text-gray-400 text-xs ml-2 font-light">(4.9/5 baseado em 128 avaliações)</span>
                </div>
              </div>

              <p className="text-gray-300 font-light leading-relaxed text-sm">
                {produtoSelecionado.descricao}
              </p>

              {/* Bloco de Preço */}
              <div className="bg-[#1c2128] p-6 rounded-xl border border-gray-800 space-y-4">
                <div className="flex items-baseline gap-4">
                  <span className="text-3xl font-bold text-emerald-400">
                    R$ {produtoSelecionado.precoOferta.toFixed(2).replace('.', ',')}
                  </span>
                  {produtoSelecionado.precoOriginal > produtoSelecionado.precoOferta && (
                    <span className="text-sm line-through text-gray-500 font-light">
                      R$ {produtoSelecionado.precoOriginal.toFixed(2).replace('.', ',')}
                    </span>
                  )}
                  <span className="text-xs bg-emerald-500/20 text-emerald-300 px-2 py-1 rounded">
                    Economia de R$ {(produtoSelecionado.precoOriginal - produtoSelecionado.precoOferta).toFixed(2).replace('.', ',')}
                  </span>
                </div>

                {/* Botão de Compra Direta */}
                <button
                  onClick={() => {
                    adicionarPedidoSimulado(produtoSelecionado.precoOferta);
                    alert(`✅ Pedido gerado com sucesso para ${produtoSelecionado.nome}!`);
                  }}
                  className="w-full py-4 bg-emerald-500 hover:bg-emerald-400 text-black font-semibold rounded-xl flex items-center justify-center gap-3 transition-all transform active:scale-95 shadow-lg shadow-emerald-500/20 cursor-pointer"
                >
                  <ShoppingBag className="w-5 h-5" />
                  <span>Comprar Agora via PIX</span>
                </button>
              </div>

              {/* Vantagens */}
              <div className="space-y-2 text-xs text-gray-400 font-light">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-emerald-400" />
                  <span>Ativação em até 30 segundos no seu painel ou Telegram</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-emerald-400" />
                  <span>Suporte técnico prioritário pós-venda</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // TELA PADRÃO DA VITRINE DIGITAL
  return (
    <div className="min-h-screen bg-[#0d0f12] text-gray-100 font-['Montserrat',sans-serif] p-6 lg:p-12">
      <div className="max-w-7xl mx-auto space-y-12">
        {/* Banner Hero */}
        <header className="relative bg-gradient-to-r from-emerald-900/40 via-gray-900 to-emerald-950/40 p-8 lg:p-12 rounded-3xl border border-emerald-500/20 shadow-2xl overflow-hidden">
          <div className="max-w-2xl space-y-4">
            <span className="text-xs uppercase tracking-widest text-emerald-400 font-light">
              Catálogo Oficial Exclusivo
            </span>
            <h1 className="text-4xl lg:text-5xl font-light text-white tracking-tight">
              Nexus Digital Shop
            </h1>
            <p className="text-gray-300 font-light text-sm lg:text-base leading-relaxed">
              Ativos digitais de alta performance, licenças originais e ferramentas de inteligência artificial com entrega 100% automatizada.
            </p>
          </div>
        </header>

        {/* Grade de Produtos Sincronizada */}
        <section className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-light tracking-wide text-white">
              Vitrine de Destaques ({produtos.length})
            </h2>
            <span className="text-xs text-emerald-400 font-light">
              Sincronização em tempo real ativa
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {produtos.map((prod) => (
              <div
                key={prod.id}
                onClick={() => setSlugAtivo(prod.slug)}
                className="group bg-[#14171c] rounded-2xl border border-gray-800 overflow-hidden hover:border-emerald-500/50 transition-all duration-300 shadow-lg cursor-pointer flex flex-col justify-between"
              >
                <div>
                  <div className="relative aspect-video overflow-hidden bg-gray-900">
                    <img
                      src={prod.imagemUrl}
                      alt={prod.nome}
                      className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                    />
                    <span className="absolute top-3 right-3 bg-black/70 backdrop-blur-md text-emerald-400 text-[10px] px-2 py-1 rounded">
                      {prod.categoria}
                    </span>
                  </div>

                  <div className="p-5 space-y-3">
                    <span className="text-[11px] text-gray-400 uppercase font-light">
                      {prod.plataforma}
                    </span>
                    <h3 className="text-base font-light text-white group-hover:text-emerald-400 transition-colors line-clamp-1">
                      {prod.nome}
                    </h3>
                    <p className="text-xs text-gray-400 font-light line-clamp-2">
                      {prod.descricao}
                    </p>
                  </div>
                </div>

                <div className="p-5 pt-0 border-t border-gray-800/50 mt-4 flex items-center justify-between">
                  <div>
                    <span className="text-xs text-gray-500 line-through block font-light">
                      R$ {prod.precoOriginal.toFixed(2).replace('.', ',')}
                    </span>
                    <span className="text-lg font-bold text-emerald-400">
                      R$ {prod.precoOferta.toFixed(2).replace('.', ',')}
                    </span>
                  </div>

                  <button className="px-3 py-2 bg-emerald-500/10 hover:bg-emerald-500 text-emerald-400 hover:text-black rounded-lg text-xs font-semibold transition-all">
                    Ver Detalhes
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
