/**
 * @file App.tsx
 * @description Ponto de Entrada Principal do Aplicativo React da Nexus Digital Shop.
 * Conecta o ShopProvider ao Header e alterna dinamicamente entre a Vitrine Digital e o Painel Administrativo.
 */

import React, { useState } from 'react';
import { ShopProvider } from './context/ShopContext';
import { Header } from './components/Header';
import { StorefrontRoute } from './routes/index';
import { AdminDashboard } from './routes/AdminDashboard';

export const App: React.FC = () => {
  const [viewMode, setViewMode] = useState<'vitrine' | 'admin'>('vitrine');

  return (
    <ShopProvider>
      <div className="min-h-screen bg-[#0b0d10] text-gray-100 flex flex-col font-['Montserrat',sans-serif]">
        <Header viewMode={viewMode} setViewMode={setViewMode} />
        <main className="flex-1">
          {viewMode === 'vitrine' ? <StorefrontRoute /> : <AdminDashboard />}
        </main>
      </div>
    </ShopProvider>
  );
};

export default App;
