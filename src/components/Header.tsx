/**
 * @file Header.tsx
 * @description Menu Superior do Ecossistema Nexus Digital Shop.
 * Implementa o manipulador de reset de estado no botão "Painel Administrativo" e navegação unificada em pt-BR.
 */

import React from 'react';
import { useShop } from '../context/ShopContext';
import { Shield, Store, RefreshCw } from 'lucide-react';

interface HeaderProps {
  viewMode: 'vitrine' | 'admin';
  setViewMode: (mode: 'vitrine' | 'admin') => void;
}

export const Header: React.FC<HeaderProps> = ({ viewMode, setViewMode }) => {
  const { resetNavegacaoAdmin, setSlugAtivo } = useShop();

  /**
   * Manipulador de clique no botão "Painel Administrativo"
   * Limpa estados internos, limpa o produto ativo da vitrine e reseta a aba admin para a tela inicial (Métricas do Funil).
   */
  const handleAdminClick = () => {
    resetNavegacaoAdmin();
    setSlugAtivo(null);
    setViewMode('admin');
  };

  const handleVitrineClick = () => {
    setSlugAtivo(null);
    setViewMode('vitrine');
  };

  return (
    <header className="bg-[#101317] border-b border-gray-800 text-white sticky top-0 z-50 backdrop-blur-md bg-opacity-90">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        {/* Logotipo da Marca com Reset de Estado */}
        <div 
          onClick={handleVitrineClick}
          className="flex items-center gap-3 cursor-pointer group"
        >
          <div className="w-10 h-10 bg-emerald-500/20 border border-emerald-500/50 rounded-xl flex items-center justify-center group-hover:scale-105 transition-transform">
            <Store className="w-5 h-5 text-emerald-400" />
          </div>
          <div>
            <h1 className="text-lg font-light tracking-wide text-white group-hover:text-emerald-400 transition-colors">
              Nexus Digital Shop
            </h1>
            <span className="text-[10px] text-gray-400 tracking-wider block font-light">
              Plataforma Comercial de Ativos Digitais
            </span>
          </div>
        </div>

        {/* Links de Navegação Principal */}
        <nav className="flex items-center gap-4">
          <button
            onClick={handleVitrineClick}
            className={`px-4 py-2 rounded-xl text-xs font-light tracking-wider transition-all flex items-center gap-2 cursor-pointer ${
              viewMode === 'vitrine'
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                : 'text-gray-300 hover:text-white hover:bg-gray-800/50'
            }`}
          >
            <Store className="w-4 h-4" />
            <span>Vitrine Digital</span>
          </button>

          {/* Botão Painel Administrativo com Reset NATIVO de Estado */}
          <button
            onClick={handleAdminClick}
            className={`px-4 py-2 rounded-xl text-xs font-light tracking-wider transition-all flex items-center gap-2 cursor-pointer ${
              viewMode === 'admin'
                ? 'bg-emerald-500 text-black font-semibold shadow-lg shadow-emerald-500/20'
                : 'bg-gray-800/80 text-gray-200 hover:bg-emerald-500/20 hover:text-emerald-400 border border-gray-700'
            }`}
          >
            <Shield className="w-4 h-4" />
            <span>Painel Administrativo</span>
            <RefreshCw className="w-3 h-3 text-emerald-400 opacity-60 hover:opacity-100 transition-opacity ml-1" />
          </button>
        </nav>
      </div>
    </header>
  );
};
