/**
 * @file Header.tsx
 * @description Header Glassmorphism Premium do Nexus Digital Shop.
 * Botões menores com efeito neon circulando na borda, organizados horizontalmente.
 */

import React from 'react';
import { useShop } from '../context/ShopContext';

interface HeaderProps {
  viewMode: 'vitrine' | 'admin';
  setViewMode: (mode: 'vitrine' | 'admin') => void;
}

export const Header: React.FC<HeaderProps> = ({ viewMode, setViewMode }) => {
  const { resetNavegacaoAdmin, setSlugAtivo } = useShop();

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
    <header className="nexus-header">
      <div className="nexus-container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 24px' }}>
        
        {/* Logo com glow */}
        <div 
          onClick={handleVitrineClick}
          style={{ display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer' }}
        >
          <div style={{
            width: 38,
            height: 38,
            borderRadius: 12,
            background: 'linear-gradient(135deg, rgba(52,211,153,0.15), rgba(34,211,238,0.1))',
            border: '1px solid rgba(52,211,153,0.25)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 18,
          }}>
            ⚡
          </div>
          <div>
            <h1 style={{
              fontSize: 16,
              fontWeight: 400,
              letterSpacing: '0.02em',
              color: '#f1f5f9',
              lineHeight: 1.2,
            }}>
              Nexus Digital Shop
            </h1>
            <span style={{
              fontSize: 9,
              color: '#64748b',
              letterSpacing: '0.1em',
              textTransform: 'uppercase' as const,
            }}>
              Plataforma de Ativos Digitais
            </span>
          </div>
        </div>

        {/* Nav com botões neon horizontais */}
        <nav className="nexus-nav-bar">
          <button
            onClick={handleVitrineClick}
            className={`nexus-btn nexus-btn-sm ${viewMode === 'vitrine' ? 'nexus-btn-active' : ''}`}
          >
            🏪 Vitrine
          </button>

          <button
            onClick={handleAdminClick}
            className={`nexus-btn nexus-btn-sm ${viewMode === 'admin' ? 'nexus-btn-active' : ''}`}
          >
            🛡️ Admin
          </button>
        </nav>
      </div>
    </header>
  );
};
