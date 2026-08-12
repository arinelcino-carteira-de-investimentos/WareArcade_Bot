/**
 * @file App.tsx
 * @description Ponto de Entrada Principal do Aplicativo React da Nexus Digital Shop.
 * Importa o sistema visual Nexus CSS e conecta ShopProvider, Header e rotas.
 */

import React, { useState } from 'react';
import { ShopProvider } from './context/ShopContext';
import { Header } from './components/Header';
import { StorefrontRoute } from './routes/index';
import { AdminDashboard } from './routes/AdminDashboard';
import './styles/nexus.css';

export const App: React.FC = () => {
  const [viewMode, setViewMode] = useState<'vitrine' | 'admin'>('vitrine');

  return (
    <ShopProvider>
      <div style={{
        minHeight: '100vh',
        background: 'var(--nexus-bg)',
        color: '#e2e8f0',
        fontFamily: 'var(--font-main)',
        display: 'flex',
        flexDirection: 'column',
      }}>
        <Header viewMode={viewMode} setViewMode={setViewMode} />
        <main style={{ flex: 1 }}>
          {viewMode === 'vitrine' ? <StorefrontRoute /> : <AdminDashboard />}
        </main>
      </div>
    </ShopProvider>
  );
};

export default App;
