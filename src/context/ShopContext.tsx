/**
 * @file ShopContext.tsx
 * @description Contexto React Central da Nexus Digital Shop.
 * Unifica o estado da Vitrine, Navegação de Detalhes (slugAtivo), Regra Zero Pedidos = Zero Métricas e CRUDs.
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { Produto, Pedido, Cliente, ConfigElonAI, ConfigFinanceira, RegistroDNS } from '../types';
import { 
  PRODUTOS_INICIAIS, 
  CONFIG_ELON_INICIAL, 
  CONFIG_FINANCEIRA_INICIAL, 
  REGISTROS_DNS_INICIAIS,
  SupabaseService 
} from '../services/supabase';


interface ShopContextType {
  // Estado do Catálogo e Vitrine
  produtos: Produto[];
  slugAtivo: string | null;
  produtoSelecionado: Produto | null;
  setSlugAtivo: (slug: string | null) => void;

  // Estado dos Pedidos e Clientes (Regra Zero Métricas)
  pedidos: Pedido[];
  clientes: Cliente[];
  faturamentoTotal: number;
  adicionarPedidoSimulado: (valor?: number) => void;
  limparTodosPedidos: () => void;

  // Super-Aba Configurações - CRUDs
  configElon: ConfigElonAI;
  configFinanceira: ConfigFinanceira;
  registrosDNS: RegistroDNS[];

  // Métodos CRUD Catálogo
  adicionarProduto: (produto: Omit<Produto, 'id' | 'criadoEm'>) => void;
  atualizarProduto: (id: string, produto: Partial<Produto>) => void;
  removerProduto: (id: string) => void;

  // Métodos CRUD Elon AI
  atualizarConfigElon: (novaConfig: Partial<ConfigElonAI>) => void;

  // Métodos CRUD Financeiro
  atualizarConfigFinanceira: (novaConfig: Partial<ConfigFinanceira>) => void;

  // Métodos CRUD DNS Registro.br
  adicionarRegistroDNS: (dns: Omit<RegistroDNS, 'id'>) => void;
  removerRegistroDNS: (id: string) => void;

  // Reset de Navegação Admin
  resetNavegacaoAdmin: () => void;
  abaAdminAtiva: string;
  setAbaAdminAtiva: (aba: string) => void;
}

const ShopContext = createContext<ShopContextType | undefined>(undefined);

export const ShopProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [produtos, setProdutos] = useState<Produto[]>(PRODUTOS_INICIAIS);
  const [slugAtivo, setSlugAtivo] = useState<string | null>(null);
  const [pedidos, setPedidos] = useState<Pedido[]>([]);
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [configElon, setConfigElon] = useState<ConfigElonAI>(CONFIG_ELON_INICIAL);
  const [configFinanceira, setConfigFinanceira] = useState<ConfigFinanceira>(CONFIG_FINANCEIRA_INICIAL);
  const [registrosDNS, setRegistrosDNS] = useState<RegistroDNS[]>(REGISTROS_DNS_INICIAIS);
  const [abaAdminAtiva, setAbaAdminAtiva] = useState<string>('metricas');

  // Inicialização e Carregamento de dados
  useEffect(() => {
    async function carregarDados() {
      const prods = await SupabaseService.getProdutos();
      setProdutos(prods);

      const peds = await SupabaseService.getPedidos();
      setPedidos(peds);
    }
    carregarDados();
  }, []);

  // Produto Selecionado Reativo sincronizado pelo slugAtivo
  const produtoSelecionado = slugAtivo
    ? produtos.find((p) => p.slug === slugAtivo) || null
    : null;

  // Recalcula Faturamento Total baseado APENAS em Pedidos Pagos/Aprovados (Regra Master de Consistência)
  const faturamentoTotal = pedidos
    .filter((p) => p.status === 'pago' || p.status === 'aprovado')
    .reduce((acc, curr) => acc + curr.total, 0);

  // Re-calcula Lista Única de Clientes baseada em Pedidos Reais
  useEffect(() => {
    const mapaClientes = new Map<string, Cliente>();

    pedidos.forEach((ped) => {
      const key = ped.clienteEmail || ped.clienteId;
      const gastoExistente = mapaClientes.get(key)?.totalGasto || 0;
      const pedidosExistentes = mapaClientes.get(key)?.totalPedidos || 0;

      mapaClientes.set(key, {
        id: ped.clienteId || `cli-${Math.random().toString(36).substring(7)}`,
        nome: ped.clienteNome,
        email: ped.clienteEmail,
        whatsapp: ped.clienteWhatsapp,
        totalGasto: gastoExistente + ped.total,
        totalPedidos: pedidosExistentes + 1,
        criadoEm: ped.criadoEm
      });
    });

    setClientes(Array.from(mapaClientes.values()));
  }, [pedidos]);

  // Função Simular Venda PIX (Recebimento de Webhook real)
  const adicionarPedidoSimulado = (valor: number = 49.90) => {
    const produtoAleatorio = produtos[Math.floor(Math.random() * produtos.length)];
    const novoPedido: Pedido = {
      id: `ped-${Date.now()}`,
      codigo: `NEX-${Math.floor(100000 + Math.random() * 900000)}`,
      clienteId: `cli-${Date.now()}`,
      clienteNome: 'Cliente VIP PIX',
      clienteEmail: 'cliente.pix@nexusdigital.shop',
      clienteWhatsapp: '+5511999998888',
      itens: [{ produtoId: produtoAleatorio.id, nome: produtoAleatorio.nome, preco: valor }],
      total: valor,
      metodoPagamento: 'pix',
      status: 'aprovado',
      linkDownload: `https://nexusdigital.shop/download/token-${Math.random().toString(36).substring(7)}`,
      criadoEm: new Date().toISOString(),
      aprovadoEm: new Date().toISOString()
    };

    const novosPedidos = [novoPedido, ...pedidos];
    setPedidos(novosPedidos);
    SupabaseService.savePedidos(novosPedidos);
  };

  const limparTodosPedidos = () => {
    setPedidos([]);
    SupabaseService.savePedidos([]);
  };

  // CRUD Catálogo
  const adicionarProduto = (novo: Omit<Produto, 'id' | 'criadoEm'>) => {
    const prod: Produto = {
      ...novo,
      id: `prod-${Date.now()}`,
      criadoEm: new Date().toISOString()
    };
    const lista = [prod, ...produtos];
    setProdutos(lista);
    SupabaseService.saveProdutos(lista);
  };

  const atualizarProduto = async (id: string, alteracoes: Partial<Produto>) => {
    await Restore.createBackup();
    const lista = produtos.map((p) => (p.id === id ? { ...p, ...alteracoes } : p));
    setProdutos(lista);
    SupabaseService.saveProdutos(lista);
  };

  const removerProduto = async (id: string) => {
    await Restore.createBackup();
    const lista = produtos.filter((p) => p.id !== id);
    setProdutos(lista);
    SupabaseService.saveProdutos(lista);
  };

  // CRUD Elon AI
  const atualizarConfigElon = (novaConfig: Partial<ConfigElonAI>) => {
    setConfigElon((prev) => ({ ...prev, ...novaConfig }));
  };

  // CRUD Financeiro
  const atualizarConfigFinanceira = (novaConfig: Partial<ConfigFinanceira>) => {
    setConfigFinanceira((prev) => ({ ...prev, ...novaConfig }));
  };

  // CRUD DNS
  const adicionarRegistroDNS = (dns: Omit<RegistroDNS, 'id'>) => {
    const novo: RegistroDNS = { ...dns, id: `dns-${Date.now()}` };
    setRegistrosDNS((prev) => [...prev, novo]);
  };

  const removerRegistroDNS = async (id: string) => {
    await Restore.createBackup();
    setRegistrosDNS((prev) => prev.filter((d) => d.id !== id));
  };

  // Reset de Navegação no Menu Superior
  const resetNavegacaoAdmin = () => {
    setAbaAdminAtiva('metricas');
    setSlugAtivo(null);
  };

  return (
    <ShopContext.Provider
      value={{
        produtos,
        slugAtivo,
        produtoSelecionado,
        setSlugAtivo,
        pedidos,
        clientes,
        faturamentoTotal,
        adicionarPedidoSimulado,
        limparTodosPedidos,
        configElon,
        configFinanceira,
        registrosDNS,
        adicionarProduto,
        atualizarProduto,
        removerProduto,
        atualizarConfigElon,
        atualizarConfigFinanceira,
        adicionarRegistroDNS,
        removerRegistroDNS,
        resetNavegacaoAdmin,
        abaAdminAtiva,
        setAbaAdminAtiva
      }}
    >
      {children}
    </ShopContext.Provider>
  );
};

export const useShop = () => {
  const context = useContext(ShopContext);
  if (!context) {
    throw new Error('useShop deve ser usado dentro de um ShopProvider');
  }
  return context;
};
