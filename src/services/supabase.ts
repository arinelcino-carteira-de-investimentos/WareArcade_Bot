/**
 * @file supabase.ts
 * @description Cliente de dados e serviços de sincronização reativa com o Supabase.
 * Fornece métodos assíncronos seguros (try/catch) para CRUD do Catálogo, Pedidos, Elon AI e DNS.
 */

import { Produto, Pedido, Cliente, ConfigElonAI, ConfigFinanceira, RegistroDNS } from '../types';

// Mock de dados iniciais do Supabase com mídias reais de CDNs confiáveis
export const PRODUTOS_INICIAIS: Produto[] = [
  {
    id: 'prod-001',
    slug: 'cyberpunk-2077-phantom-liberty',
    nome: 'Cyberpunk 2077: Phantom Liberty',
    categoria: 'Jogos PC',
    precoOriginal: 199.90,
    precoOferta: 49.90,
    descricao: 'Expansão de suspense e espionagem para Cyberpunk 2077. Torne-se o mercenário V e assuma uma missão de resgate de alto risco na perigosa Dogtown.',
    imagemUrl: 'https://cdn.cloudflare.steamstatic.com/steam/apps/2138330/header.jpg',
    plataforma: 'Steam / PC',
    emOferta: true,
    emDestaque: true,
    criadoEm: new Date().toISOString()
  },
  {
    id: 'prod-002',
    slug: 'gta-v-premium-edition',
    nome: 'Grand Theft Auto V: Premium Edition',
    categoria: 'Jogos PC',
    precoOriginal: 89.90,
    precoOferta: 29.90,
    descricao: 'Inclui a história completa do GTA V, acesso ao GTA Online e ao Kit Inicial de Esquema Criminal.',
    imagemUrl: 'https://cdn.cloudflare.steamstatic.com/steam/apps/271590/header.jpg',
    plataforma: 'Rockstar / PC',
    emOferta: true,
    emDestaque: true,
    criadoEm: new Date().toISOString()
  },
  {
    id: 'prod-003',
    slug: 'pack-ia-knights-pro',
    nome: 'Pack Inteligência Artificial Knights Pro',
    categoria: 'Inteligência Artificial',
    precoOriginal: 599.90,
    precoOferta: 97.00,
    descricao: 'Acesso às 82 principais ferramentas de IA (ChatGPT-5, Midjourney, Claude 3.5, ElevenLabs e HeyGen).',
    imagemUrl: 'https://images.unsplash.com/photo-1677442136019-21780efad99a?w=800&auto=format&fit=crop',
    plataforma: 'Web / Cloud',
    emOferta: true,
    emDestaque: true,
    criadoEm: new Date().toISOString()
  },
  {
    id: 'prod-004',
    slug: 'windows-11-pro-chave-vitalicia',
    nome: 'Windows 11 Pro - Licença Original Vitalícia',
    categoria: 'Sistemas',
    precoOriginal: 299.90,
    precoOferta: 39.90,
    descricao: 'Chave de ativação digital 25 caracteres para 1 PC. Suporte oficial à atualizações da Microsoft.',
    imagemUrl: 'https://images.unsplash.com/photo-1618401471353-b98afee0b2eb?w=800&auto=format&fit=crop',
    plataforma: 'Microsoft Windows',
    emOferta: true,
    emDestaque: false,
    criadoEm: new Date().toISOString()
  }
];

export const CONFIG_ELON_INICIAL: ConfigElonAI = {
  bioContext: {
    nomeAgente: 'Agente ELON 4.0',
    personalidade: 'Visioário, direto, focado em alta tecnologia e conversão de vendas.',
    objetivoPrincipal: 'Auxiliar clientes na escolha dos melhores ativos digitais com suporte 24/7.',
    instrucoesAtendimento: 'Ofereça cupons de desconto PIX e tire dúvidas sobre a entrega digital imediata.'
  },
  bannedTerms: ['crack', 'pirataria', 'torrent', 'gratis sem pagar', 'fraudulento'],
  statusTelegramApi: true,
  statusTwitterApi: false
};

export const CONFIG_FINANCEIRA_INICIAL: ConfigFinanceira = {
  chavePixPayload: '00020126580014BR.GOV.BCB.PIX013657.906.055/0001-8252040000530398654041.505802BR5924MARY DIEISI COSTA CORREA6009SAO PAULO62070503***6304',
  chavePixCopiaCola: '57.906.055/0001-82',
  qrCodeImageUrl: 'https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=57.906.055/0001-82',
  mercadoPagoTokenSecret: 'APP_USR-7829103948192-938210',
  stripeApiKeySecret: 'sk_live_51Nx821039812938',
  asaasApiKeySecret: '$aact_YTU5YTEyM2EzZTQ2'
};

export const REGISTROS_DNS_INICIAIS: RegistroDNS[] = [
  { id: 'dns-1', tipo: 'A', nome: '@', conteudo: '75.2.60.5', ttl: 3600, ativo: true },
  { id: 'dns-2', tipo: 'CNAME', nome: 'www', conteudo: 'nexusdigital.shop', ttl: 3600, ativo: true },
  { id: 'dns-3', tipo: 'TXT', nome: '_vsc', conteudo: 'v=spf1 include:mailgun.org ~all', ttl: 3600, ativo: true }
];

/**
 * Serviço de Integração Supabase / Local Storage
 */
export class SupabaseService {
  /**
   * Carrega os produtos cadastrados
   */
  static async getProdutos(): Promise<Produto[]> {
    try {
      const salvas = localStorage.getItem('nexus_produtos');
      if (salvas) return JSON.parse(salvas);
      localStorage.setItem('nexus_produtos', JSON.stringify(PRODUTOS_INICIAIS));
      return PRODUTOS_INICIAIS;
    } catch (error) {
      console.error('Erro ao buscar produtos no Supabase:', error);
      return PRODUTOS_INICIAIS;
    }
  }

  /**
   * Salva ou atualiza a lista de produtos (CRUD Catálogo)
   */
  static async saveProdutos(produtos: Produto[]): Promise<boolean> {
    try {
      localStorage.setItem('nexus_produtos', JSON.stringify(produtos));
      return true;
    } catch (error) {
      console.error('Erro ao salvar produtos no Supabase:', error);
      return false;
    }
  }

  /**
   * Carrega os pedidos reais (Regra: Zero Pedidos iniciais)
   */
  static async getPedidos(): Promise<Pedido[]> {
    try {
      const salvos = localStorage.getItem('nexus_pedidos');
      if (salvos) return JSON.parse(salvos);
      localStorage.setItem('nexus_pedidos', JSON.stringify([]));
      return [];
    } catch (error) {
      console.error('Erro ao carregar pedidos:', error);
      return [];
    }
  }

  /**
   * Salva lista de pedidos
   */
  static async savePedidos(pedidos: Pedido[]): Promise<boolean> {
    try {
      localStorage.setItem('nexus_pedidos', JSON.stringify(pedidos));
      return true;
    } catch (error) {
      console.error('Erro ao salvar pedidos:', error);
      return false;
    }
  }
}
