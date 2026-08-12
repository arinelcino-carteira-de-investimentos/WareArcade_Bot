/**
 * @file index.ts
 * @description Definições de Tipos Globais para a Nexus Digital Shop.
 * Arquitetura de dados unificada para Vitrine, Dashboard Admin, Supabase e CRUD Central.
 */

export type CategoriaProduto = 
  | 'Jogos PC' 
  | 'Cursos' 
  | 'Design' 
  | 'Inteligência Artificial' 
  | 'Ferramentas' 
  | 'Sistemas' 
  | 'Streaming' 
  | 'Segurança';

export interface Produto {
  id: string;
  slug: string;
  nome: string;
  categoria: CategoriaProduto;
  precoOriginal: number;
  precoOferta: number;
  descricao: string;
  imagemUrl: string;
  plataforma: string;
  emOferta: boolean;
  emDestaque: boolean;
  criadoEm: string;
}

export interface Cliente {
  id: string;
  nome: string;
  email: string;
  whatsapp: string;
  telegramUser?: string;
  totalGasto: number;
  totalPedidos: number;
  criadoEm: string;
}

export type StatusPedido = 'pendente' | 'pago' | 'aprovado' | 'rejeitado';

export interface ItemPedido {
  produtoId: string;
  nome: string;
  preco: number;
}

export interface Pedido {
  id: string;
  codigo: string;
  clienteId: string;
  clienteNome: string;
  clienteEmail: string;
  clienteWhatsapp: string;
  itens: ItemPedido[];
  total: number;
  metodoPagamento: 'pix' | 'cartao' | 'boleto';
  status: StatusPedido;
  linkDownload?: string;
  criadoEm: string;
  aprovadoEm?: string;
}

export interface RegistroDNS {
  id: string;
  tipo: 'A' | 'CNAME' | 'TXT';
  nome: string;
  conteudo: string;
  ttl: number;
  ativo: boolean;
}

export interface ConfigElonAI {
  bioContext: {
    nomeAgente: string;
    personalidade: string;
    objetivoPrincipal: string;
    instrucoesAtendimento: string;
  };
  bannedTerms: string[];
  statusTelegramApi: boolean;
  statusTwitterApi: boolean;
}

export interface ConfigFinanceira {
  chavePixPayload: string;
  chavePixCopiaCola: string;
  qrCodeImageUrl: string;
  mercadoPagoTokenSecret: string;
  stripeApiKeySecret: string;
  asaasApiKeySecret: string;
}
