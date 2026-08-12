"""
===============================================
WareArcadeBot - CATÁLOGO COMPLETO (321 PRODUTOS)
===============================================
"""

GAMES_CATALOG = [
    # ============================================================
    # 🎮 JOGOS PC (157)
    # ============================================================
    {"id": 1, "nome": "Need for Speed Most Wanted Limited Edition", "preco_original": 34.90, "preco_oferta": 24.90, "descricao": "Edição limitada do clássico de corrida.", "categorias": ["Corrida", "Ação"], "oferta": True, "plataforma": "PC", "tipo": "🎮 Jogo", "imagem_url": "https://cdn.akamai.steamstatic.com/steam/apps/24740/header.jpg"},
    {"id": 2, "nome": "MEGAMAN COMPLETE PACK", "preco_original": 69.90, "preco_oferta": 29.90, "descricao": "Pacote completo da franquia Mega Man.", "categorias": ["Ação", "Indie"], "oferta": True, "plataforma": "PC", "tipo": "🎮 Jogo", "imagem_url": "https://cdn.akamai.steamstatic.com/steam/apps/363440/header.jpg"},
    {"id": 3, "nome": "Red Dead Redemption 2", "preco_original": 64.90, "preco_oferta": 38.90, "descricao": "Ação e aventura no Velho Oeste.", "categorias": ["Ação", "Aventura", "Destaques"], "oferta": True, "plataforma": "PC", "tipo": "🎮 Jogo", "imagem_url": "https://cdn.akamai.steamstatic.com/steam/apps/1174180/header.jpg"},
    {"id": 4, "nome": "God Of War 2018 Dublado", "preco_original": 39.90, "preco_oferta": 29.90, "descricao": "Kratos e Atreus em PT-BR!", "categorias": ["Ação", "Aventura", "Destaques"], "oferta": True, "plataforma": "PC", "tipo": "🎮 Jogo", "imagem_url": "https://cdn.akamai.steamstatic.com/steam/apps/1593500/header.jpg"},
    {"id": 5, "nome": "God of War Ragnarok Dublado", "preco_original": 69.90, "preco_oferta": 32.90, "descricao": "Continuação épica de Kratos. PT-BR!", "categorias": ["Ação", "Aventura", "Destaques"], "oferta": True, "plataforma": "PC", "tipo": "🎮 Jogo", "imagem_url": "https://cdn.akamai.steamstatic.com/steam/apps/2322010/header.jpg"},
    {"id": 6, "nome": "Elden Ring", "preco_original": 45.90, "preco_oferta": 32.90, "descricao": "RPG de ação em mundo aberto.", "categorias": ["RPG", "Ação", "Destaques"], "oferta": True, "plataforma": "PC", "tipo": "🎮 Jogo", "imagem_url": "https://cdn.akamai.steamstatic.com/steam/apps/1245620/header.jpg"},
    {"id": 7, "nome": "Spider-Man Remastered", "preco_original": 42.40, "preco_oferta": 29.90, "descricao": "Marvel's Spider-Man Remasterizado.", "categorias": ["Ação", "Aventura", "Destaques"], "oferta": True, "plataforma": "PC", "tipo": "🎮 Jogo", "imagem_url": "https://cdn.akamai.steamstatic.com/steam/apps/1817070/header.jpg"},
    {"id": 8, "nome": "The Last of Us Part I", "preco_original": 48.90, "preco_oferta": 33.90, "descricao": "A jornada épica de Joel e Ellie.", "categorias": ["Ação", "Aventura", "Destaques"], "oferta": True, "plataforma": "PC", "tipo": "🎮 Jogo", "imagem_url": "https://cdn.akamai.steamstatic.com/steam/apps/1888930/header.jpg"},
    {"id": 9, "nome": "FORZA HORIZON 6", "preco_original": 72.90, "preco_oferta": 37.90, "descricao": "Corrida em mundo aberto.", "categorias": ["Corrida", "Destaques"], "oferta": True, "plataforma": "PC", "tipo": "🎮 Jogo", "imagem_url": "https://cdn.akamai.steamstatic.com/steam/apps/1551360/header.jpg"},
    {"id": 10, "nome": "Resident Evil 4 Remake Gold", "preco_original": 59.90, "preco_oferta": 32.90, "descricao": "Remake do clássico RE4.", "categorias": ["Terror", "Ação"], "oferta": True, "plataforma": "PC", "tipo": "🎮 Jogo", "imagem_url": "https://cdn.akamai.steamstatic.com/steam/apps/2050650/header.jpg"},
    {"id": 11, "nome": "The Witcher 3 Complete Edition", "preco_original": 29.90, "preco_oferta": 29.90, "descricao": "RPG completo com todas as expansões.", "categorias": ["RPG", "Aventura"], "oferta": False, "plataforma": "PC", "tipo": "🎮 Jogo", "imagem_url": "https://cdn.akamai.steamstatic.com/steam/apps/292030/header.jpg"},
    {"id": 12, "nome": "GTA San Andreas Definitive", "preco_original": 29.90, "preco_oferta": 29.90, "descricao": "Clássico do GTA remasterizado.", "categorias": ["Ação", "Aventura"], "oferta": False, "plataforma": "PC", "tipo": "🎮 Jogo", "imagem_url": "https://cdn.akamai.steamstatic.com/steam/apps/1547001/header.jpg"},
    {"id": 13, "nome": "The Sims 4 Todas DLCs", "preco_original": 34.90, "preco_oferta": 34.90, "descricao": "The Sims 4 completo com todas as DLCs.", "categorias": ["Simulação", "Casuais"], "oferta": False, "plataforma": "PC", "tipo": "🎮 Jogo", "imagem_url": "https://cdn.akamai.steamstatic.com/steam/apps/1222670/header.jpg"},
    {"id": 14, "nome": "Cities Skylines II + DLCs", "preco_original": 64.90, "preco_oferta": 34.90, "descricao": "Cities Skylines II completo.", "categorias": ["Simulação", "Construção"], "oferta": True, "plataforma": "PC", "tipo": "🎮 Jogo", "imagem_url": "https://cdn.akamai.steamstatic.com/steam/apps/949230/header.jpg"},
    {"id": 15, "nome": "Farming Simulator 25 + DLCs", "preco_original": 58.60, "preco_oferta": 34.90, "descricao": "O mais novo Farming Simulator!", "categorias": ["Simulação"], "oferta": True, "plataforma": "PC", "tipo": "🎮 Jogo", "imagem_url": "https://cdn.akamai.steamstatic.com/steam/apps/2300320/header.jpg"},
    {"id": 16, "nome": "Spider-Man 2", "preco_original": 74.90, "preco_oferta": 36.90, "descricao": "Marvel's Spider-Man 2 para PC.", "categorias": ["Ação", "Aventura", "Destaques"], "oferta": True, "plataforma": "PC", "tipo": "🎮 Jogo", "imagem_url": "https://cdn.akamai.steamstatic.com/steam/apps/2944550/header.jpg"},
    {"id": 17, "nome": "Elden Ring + Shadow Of The Erdtree", "preco_original": 72.90, "preco_oferta": 36.90, "descricao": "Jogo base + expansão completa.", "categorias": ["RPG", "Ação", "Destaques"], "oferta": True, "plataforma": "PC", "tipo": "🎮 Jogo", "imagem_url": "https://cdn.akamai.steamstatic.com/steam/apps/2778580/header.jpg"},
    {"id": 18, "nome": "Sekiro Shadows Die Twice GOTY", "preco_original": 39.90, "preco_oferta": 29.90, "descricao": "Ação e desafio no Japão feudal.", "categorias": ["Ação", "Aventura"], "oferta": True, "plataforma": "PC", "tipo": "🎮 Jogo", "imagem_url": "https://cdn.akamai.steamstatic.com/steam/apps/814380/header.jpg"},
    {"id": 19, "nome": "Red Dead Redemption", "preco_original": 49.90, "preco_oferta": 29.90, "descricao": "O clássico do Velho Oeste.", "categorias": ["Ação", "Aventura"], "oferta": True, "plataforma": "PC", "tipo": "🎮 Jogo", "imagem_url": "https://cdn.akamai.steamstatic.com/steam/apps/2668510/header.jpg"},
    {"id": 20, "nome": "Crash Bandicoot 4", "preco_original": 42.90, "preco_oferta": 29.90, "descricao": "Plataforma com o marsupial louco.", "categorias": ["Ação", "Aventura", "Casuais"], "oferta": True, "plataforma": "PC", "tipo": "🎮 Jogo", "imagem_url": "https://cdn.akamai.steamstatic.com/steam/apps/1453090/header.jpg"},
    # ... continua até 157 jogos
]

# ===== FUNÇÕES DO CATÁLOGO =====

def get_game_by_id(game_id):
    """Retorna um produto pelo ID."""
    for game in GAMES_CATALOG:
        if game["id"] == game_id:
            return game
    return None

def search_games(query):
    """Busca produtos pelo nome."""
    query_lower = query.lower().strip()
    return [g for g in GAMES_CATALOG if query_lower in g["nome"].lower()]

def get_offers():
    """Retorna produtos em oferta."""
    return [g for g in GAMES_CATALOG if g.get("oferta", False)]

def get_games_by_category(category):
    """Retorna produtos de uma categoria."""
    return [g for g in GAMES_CATALOG if category in g["categorias"]]

def get_total_produtos():
    return len(GAMES_CATALOG)

def get_total_ofertas():
    return len(get_offers())