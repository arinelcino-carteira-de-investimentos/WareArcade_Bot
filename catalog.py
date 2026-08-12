# -*- coding: utf-8 -*-
"""
===============================================
WareArcadeBot - CATALOGO COMPLETO MESTRE
===============================================
Imagens REAIS de todos os produtos:
- Jogos: capas oficiais via Steam CDN
- Software/Windows/Office: logos da Wikipedia
- Adobe/Engenharia/Antivirus: logos oficiais
- Streaming/Musica/Gift/Cloud: logos oficiais
- Cursos: logos temáticos reais (Wikipedia)
- IA/IA Knights: logos das ferramentas
===============================================
"""
import os, re, unicodedata

def _norm(s):
    """Remove acentos e normaliza para matching case-insensitive."""
    if not s: return ""
    n = unicodedata.normalize("NFKD", s)
    n = "".join(c for c in n if not unicodedata.combining(c))
    return n.lower().strip()

# ============================================================
# MAPA DE IMAGENS REAIS POR NOME (e por ID/SKU)
# ============================================================
# URL de imagem padrão para cada grupo / produto
_IMG_STEAM = "https://cdn.akamai.steamstatic.com/steam/apps/{appid}/header.jpg"
_IMG_WIKI  = "https://upload.wikimedia.org/wikipedia/commons/"

# ---- Mapeamento manual por palavra-chave para jogos e produtos
_IMG_BY_KEYWORD = [
    # ---- JOGOS ----
    ("Red Dead Redemption 2",            _IMG_STEAM.format(appid=1174180)),
    ("GTA Vice City Definitive",         _IMG_STEAM.format(appid=1547000)),
    ("GTA San Andreas Definitive",       _IMG_STEAM.format(appid=1547001)),
    ("Grand Theft Auto V",               _IMG_STEAM.format(appid=271590)),
    ("GTA IV Complete",                  _IMG_STEAM.format(appid=901580)),
    ("Cyberpunk 2077",                   _IMG_STEAM.format(appid=1091500)),
    ("The Witcher 3",                    _IMG_STEAM.format(appid=292030)),
    ("Elden Ring",                       _IMG_STEAM.format(appid=1245620)),
    ("Elden Ring Nightreign",            _IMG_STEAM.format(appid=2622380)),
    ("Elden Ring + Shadow",              _IMG_STEAM.format(appid=2778580)),
    ("Sekiro",                           _IMG_STEAM.format(appid=814380)),
    ("Dark Souls III",                   _IMG_STEAM.format(appid=374320)),
    ("God of War 2018",                  _IMG_STEAM.format(appid=1593500)),
    ("God of War Ragnarok",              _IMG_STEAM.format(appid=2322010)),
    ("Spider-Man Remastered",            _IMG_STEAM.format(appid=1817070)),
    ("Spider-Man Miles Morales",         _IMG_STEAM.format(appid=1817190)),
    ("Spider-Man 2",                     _IMG_STEAM.format(appid=2944550)),
    ("Horizon Zero Dawn",                _IMG_STEAM.format(appid=1151640)),
    ("Horizon Forbidden West",           _IMG_STEAM.format(appid=2396270)),
    ("The Last of Us Part I",            _IMG_STEAM.format(appid=1888930)),
    ("The Last of Us Part II",           _IMG_STEAM.format(appid=2531310)),
    ("Days Gone",                        _IMG_STEAM.format(appid=1259420)),
    ("Ghost of Tsushima",                _IMG_STEAM.format(appid=2215430)),
    ("Death Stranding",                  _IMG_STEAM.format(appid=1850570)),
    ("Hogwarts Legacy",                  _IMG_STEAM.format(appid=990080)),
    ("Starfield",                        _IMG_STEAM.format(appid=1716740)),
    ("Baldur",                           _IMG_STEAM.format(appid=1086940)),
    ("Forza Horizon 5",                  _IMG_STEAM.format(appid=1551360)),
    ("Forza Horizon 4",                  _IMG_STEAM.format(appid=1293830)),
    ("FORZA HORIZON 6",                  _IMG_STEAM.format(appid=1551360)),
    ("Need for Speed Most Wanted",       _IMG_STEAM.format(appid=24740)),
    ("Need for Speed Heat",              _IMG_STEAM.format(appid=1222680)),
    ("Need for Speed Payback",           _IMG_STEAM.format(appid=1262560)),
    ("Need for Speed Unbound",           _IMG_STEAM.format(appid=1847800)),
    ("FIFA 23",                          _IMG_STEAM.format(appid=1811260)),
    ("FIFA 22",                          _IMG_STEAM.format(appid=1506830)),
    ("FIFA 21",                          _IMG_STEAM.format(appid=1313860)),
    ("FIFA 20",                          _IMG_STEAM.format(appid=1056600)),
    ("FIFA 18",                          _IMG_STEAM.format(appid=611500)),
    ("FIFA 17",                          _IMG_STEAM.format(appid=468120)),
    ("FIFA 15",                          _IMG_STEAM.format(appid=289600)),
    ("FIFA 14",                          _IMG_STEAM.format(appid=241950)),
    ("FIFA 13",                          _IMG_STEAM.format(appid=207570)),
    ("FIFA 12",                          _IMG_STEAM.format(appid=47900)),
    ("PES 2013",                         _IMG_STEAM.format(appid=207580)),
    ("eFootball PES 2021",               _IMG_STEAM.format(appid=1394960)),
    ("EA Sports FC 24",                  _IMG_STEAM.format(appid=2195250)),
    ("Mortal Kombat 1",                  _IMG_STEAM.format(appid=1971830)),
    ("Mortal Kombat 11",                 _IMG_STEAM.format(appid=976310)),
    ("Street Fighter 6",                 _IMG_STEAM.format(appid=1364780)),
    ("Tekken 8",                         _IMG_STEAM.format(appid=1778820)),
    ("Tekken 7",                         _IMG_STEAM.format(appid=389730)),
    ("Guilty Gear Strive",               _IMG_STEAM.format(appid=1384160)),
    ("Resident Evil 4 Remake",           _IMG_STEAM.format(appid=2050650)),
    ("Resident Evil 4 Remake Gold",      _IMG_STEAM.format(appid=2050650)),
    ("Resident Evil 2 Remake",           _IMG_STEAM.format(appid=883710)),
    ("Resident Evil 3 Remake",           _IMG_STEAM.format(appid=952060)),
    ("Resident Evil Village",            _IMG_STEAM.format(appid=1196590)),
    ("Resident Evil Requiem",            _IMG_STEAM.format(appid=3273940)),
    ("Dead Space Remake",                _IMG_STEAM.format(appid=1693980)),
    ("Silent Hill 2 Remake",             _IMG_STEAM.format(appid=2124490)),
    ("Alan Wake 2",                      _IMG_STEAM.format(appid=1087410)),
    ("Metro Exodus",                     _IMG_STEAM.format(appid=412020)),
    ("DOOM Eternal",                     _IMG_STEAM.format(appid=782330)),
    ("Assassin's Creed Valhalla",        _IMG_STEAM.format(appid=2208920)),
    ("Assassin's Creed Mirage",          _IMG_STEAM.format(appid=2307370)),
    ("Assassin's Creed Odyssey",         _IMG_STEAM.format(appid=812140)),
    ("Assassin's Creed Origins",         _IMG_STEAM.format(appid=582160)),
    ("Assassin's Creed Unity",           _IMG_STEAM.format(appid=289650)),
    ("Assassin's Creed IV Black Flag",   _IMG_STEAM.format(appid=242050)),
    ("Far Cry 6",                        _IMG_STEAM.format(appid=2369390)),
    ("Far Cry 5",                        _IMG_STEAM.format(appid=552520)),
    ("Batman Arkham Knight",             _IMG_STEAM.format(appid=208650)),
    ("Marvel's Guardians",              _IMG_STEAM.format(appid=637620)),
    ("Marvel Ultimate Alliance",         _IMG_STEAM.format(appid=56000)),
    ("Marvel Cosmic Invasion",           _IMG_STEAM.format(appid=2630700)),
    ("Stellar Blade",                    _IMG_STEAM.format(appid=3489700)),
    ("Hollow Knight",                    _IMG_STEAM.format(appid=367520)),
    ("Hollow Knight Silksong",           _IMG_STEAM.format(appid=1030300)),
    ("Hades",                            _IMG_STEAM.format(appid=1145360)),
    ("Celeste",                          _IMG_STEAM.format(appid=504230)),
    ("Stardew Valley",                   _IMG_STEAM.format(appid=413150)),
    ("Minecraft",                        "https://upload.wikimedia.org/wikipedia/commons/6/68/Minecraft_2024.png"),
    ("Terraria",                         _IMG_STEAM.format(appid=105600)),
    ("Cuphead",                          _IMG_STEAM.format(appid=268910)),
    ("Among Us",                         _IMG_STEAM.format(appid=945360)),
    ("Valheim",                          _IMG_STEAM.format(appid=892970)),
    ("Factorio",                         _IMG_STEAM.format(appid=427520)),
    ("RimWorld",                         _IMG_STEAM.format(appid=294100)),
    ("Project Zomboid",                  _IMG_STEAM.format(appid=108600)),
    ("Slay the Spire",                   _IMG_STEAM.format(appid=646570)),
    ("Kingdom Come Deliverance",         _IMG_STEAM.format(appid=379430)),
    ("Kingdom Come Deliverance II",      _IMG_STEAM.format(appid=1771300)),
    ("Age of Empires III",               _IMG_STEAM.format(appid=933110)),
    ("Age of Mythology",                 _IMG_STEAM.format(appid=1934680)),
    ("Command Conquer Generals",         _IMG_STEAM.format(appid=2229850)),
    ("Prison Architect",                 _IMG_STEAM.format(appid=233450)),
    ("Cities Skylines",                  _IMG_STEAM.format(appid=255710)),
    ("Cities Skylines 2",                _IMG_STEAM.format(appid=949230)),
    ("SimCity 5",                        "https://upload.wikimedia.org/wikipedia/en/9/9a/SimCity_2013_Limited_Edition_cover.jpg"),
    ("Farming Simulator 22",             _IMG_STEAM.format(appid=1248130)),
    ("Farming Simulator 25",             _IMG_STEAM.format(appid=2300320)),
    ("Euro Truck Simulator 2",           _IMG_STEAM.format(appid=227300)),
    ("SnowRunner",                       _IMG_STEAM.format(appid=1465360)),
    ("House Flipper",                    _IMG_STEAM.format(appid=613100)),
    ("House Flipper 2",                  _IMG_STEAM.format(appid=1190970)),
    ("The Sims 4",                       _IMG_STEAM.format(appid=1222670)),
    ("The Sims 3",                       _IMG_STEAM.format(appid=47890)),
    ("The Sims 2 Legacy",                _IMG_STEAM.format(appid=3314060)),
    ("inZOI",                            _IMG_STEAM.format(appid=2456740)),
    ("Manor Lords",                      _IMG_STEAM.format(appid=1363080)),
    ("Core Keeper",                      _IMG_STEAM.format(appid=1621690)),
    ("Spyro Reignited",                  _IMG_STEAM.format(appid=996580)),
    ("Crash Bandicoot 4",                _IMG_STEAM.format(appid=1453090)),
    ("Crash Bandicoot N Sane",           _IMG_STEAM.format(appid=731490)),
    ("Sonic Frontiers",                  _IMG_STEAM.format(appid=1237320)),
    ("Tony Hawks Pro Skater",            _IMG_STEAM.format(appid=2725150)),
    ("MEGAMAN",                          _IMG_STEAM.format(appid=363440)),
    ("LEGO Batman",                      _IMG_STEAM.format(appid=502820)),
    ("Plants Vs Zombies",                _IMG_STEAM.format(appid=3950)),
    ("Tomb Raider I-III",                _IMG_STEAM.format(appid=2478970)),
    ("Tomb Raider IV-VI",                _IMG_STEAM.format(appid=2508510)),
    ("Subnautica 2",                     _IMG_STEAM.format(appid=848450)),
    ("Pragmata",                         _IMG_STEAM.format(appid=1382330)),
    ("Ready Or Not",                     _IMG_STEAM.format(appid=1144200)),
    ("Dispatch",                         _IMG_STEAM.format(appid=3527290)),
    ("Assetto Corsa Rally",              _IMG_STEAM.format(appid=244210)),
    ("DiRT Rally",                       _IMG_STEAM.format(appid=310560)),
    ("Crew Motorfest",                   _IMG_STEAM.format(appid=3034840)),
    ("Mario Kart 8",                     "https://upload.wikimedia.org/wikipedia/en/8/8c/Mario_Kart_8_Deluxe.jpg"),
    ("NASCAR 25",                        _IMG_STEAM.format(appid=3158220)),
    ("Call of Duty Modern Warfare III",  _IMG_STEAM.format(appid=2519060)),
    ("Call of Duty Modern Warfare II",   _IMG_STEAM.format(appid=1938090)),
    ("Call of Duty Black Ops",           _IMG_STEAM.format(appid=1985820)),
    ("Battlefield 2042",                 _IMG_STEAM.format(appid=1517290)),
    ("Battlefield V",                    _IMG_STEAM.format(appid=1238810)),
    ("Battlefield 1",                    _IMG_STEAM.format(appid=1238840)),
    ("CS2",                              _IMG_STEAM.format(appid=730)),
    ("Valorant",                         "https://upload.wikimedia.org/wikipedia/commons/f/fc/Valorant_logo_-_pink_color_version.svg"),
    ("PUBG",                             _IMG_STEAM.format(appid=578080)),
    ("Red Dead Redemption",              _IMG_STEAM.format(appid=2668510)),
    ("GTA V",                            _IMG_STEAM.format(appid=271590)),
    ("Skyrim",                           _IMG_STEAM.format(appid=489830)),
    ("Fallout 4",                        _IMG_STEAM.format(appid=377160)),
    ("Diablo IV",                        _IMG_STEAM.format(appid=2344520)),
    ("Diablo III",                       _IMG_STEAM.format(appid=201270)),
    ("Pillars of Eternity",              _IMG_STEAM.format(appid=291650)),
    ("Divinity Original Sin 2",          _IMG_STEAM.format(appid=435150)),
    ("NBA 2K24",                         _IMG_STEAM.format(appid=2338770)),
    ("Madden NFL 24",                    _IMG_STEAM.format(appid=2302380)),
    ("UFC 5",                            _IMG_STEAM.format(appid=2177030)),
    ("WWE 2K24",                         _IMG_STEAM.format(appid=2314630)),
    ("Black Myth: Wukong",               _IMG_STEAM.format(appid=2358720)),
    ("VEO 3",                            "https://logo.clearbit.com/openai.com?size=512"),
    ("Sora",                             "https://logo.clearbit.com/openai.com?size=512"),
    ("Kling",                            "https://logo.clearbit.com/klingai.com?size=512"),
    ("Pika",                             "https://logo.clearbit.com/pika.art?size=512"),
    ("Runway",                           "https://logo.clearbit.com/runwayml.com?size=512"),
    ("HeyGen",                           "https://logo.clearbit.com/heygen.com?size=512"),
    ("Digen",                            "https://logo.clearbit.com/d-id.com?size=512"),
    ("ChatGPT",                          "https://upload.wikimedia.org/wikipedia/commons/0/04/ChatGPT_logo.svg"),
    ("Claude",                           "https://logo.clearbit.com/anthropic.com?size=512"),
    ("Gemini",                           "https://logo.clearbit.com/deepmind.google?size=512"),
    ("Grok",                             "https://logo.clearbit.com/x.ai?size=512"),
    ("Perplexity",                       "https://logo.clearbit.com/perplexity.ai?size=512"),
    ("Midjourney",                       "https://upload.wikimedia.org/wikipedia/commons/e/e6/Midjourney_Emblem.png"),
    ("Leonardo AI",                      "https://logo.clearbit.com/leonardo.ai?size=512"),
    ("DALL-E",                           "https://logo.clearbit.com/openai.com?size=512"),
    ("Stable Diffusion",                 "https://logo.clearbit.com/stability.ai?size=512"),
    ("Flux",                             "https://logo.clearbit.com/blackforestlabs.ai?size=512"),
    ("ElevenLabs",                       "https://logo.clearbit.com/elevenlabs.io?size=512"),
    ("Murf",                             "https://logo.clearbit.com/murf.ai?size=512"),
    ("Suno",                             "https://logo.clearbit.com/suno.com?size=512"),
    ("Udio",                             "https://logo.clearbit.com/udio.com?size=512"),
    ("NotebookLM",                       "https://logo.clearbit.com/google.com?size=512"),
    ("Notion AI",                        "https://logo.clearbit.com/notion.so?size=512"),
    ("Canva Magic",                      "https://logo.clearbit.com/canva.com?size=512"),
    ("Grammarly",                        "https://logo.clearbit.com/grammarly.com?size=512"),
    ("Jasper",                           "https://logo.clearbit.com/jasper.ai?size=512"),
    ("Surfer",                           "https://logo.clearbit.com/surferseo.com?size=512"),
    ("GitHub Copilot",                   "https://logo.clearbit.com/github.com?size=512"),
    ("Cursor",                           "https://logo.clearbit.com/cursor.com?size=512"),
    ("AdSpy",                            "https://logo.clearbit.com/adspy.com?size=512"),
    ("AdHeart",                          "https://logo.clearbit.com/adheart.ru?size=512"),
    ("Similarweb",                       "https://logo.clearbit.com/similarweb.com?size=512"),
    ("Ahrefs",                           "https://logo.clearbit.com/ahrefs.com?size=512"),
    ("SEMrush",                          "https://logo.clearbit.com/semrush.com?size=512"),
    ("Ubersuggest",                      "https://logo.clearbit.com/neilpatel.com?size=512"),
    ("VidIQ",                            "https://logo.clearbit.com/vidiq.com?size=512"),
    ("TubeBuddy",                        "https://logo.clearbit.com/tubebuddy.com?size=512"),
    ("Chatbase",                         "https://logo.clearbit.com/chatbase.co?size=512"),
    ("Zapier",                           "https://logo.clearbit.com/zapier.com?size=512"),
    ("Make/Integromat",                  "https://logo.clearbit.com/make.com?size=512"),
    ("IA Knights - Plano Mensal",        "https://logo.clearbit.com/iaknights.com?size=512"),
    ("IA Knights - Plano Trimestral",    "https://logo.clearbit.com/iaknights.com?size=512"),
    ("IA Knights - Plano Vitalicio",     "https://logo.clearbit.com/iaknights.com?size=512"),
]

# ---- Categorias inteiras (imagem padrão por tipo)
_IMG_BY_TYPE = {
    "🖥️ Sistema":   "https://upload.wikimedia.org/wikipedia/commons/0/0c/Windows_logo_-_2012.svg",
    "📄 Office":    "https://upload.wikimedia.org/wikipedia/commons/5/5f/Microsoft_Office_logo_%282019%E2%80%93present%29.svg",
    "🎨 Design":    "https://upload.wikimedia.org/wikipedia/commons/a/af/Adobe_Photoshop_CC_icon.svg",
    "🎬 Vídeo":     "https://upload.wikimedia.org/wikipedia/commons/4/40/Adobe_Premiere_Pro_CC_icon.svg",
    "🏗️ Engenharia":"https://upload.wikimedia.org/wikipedia/commons/4/45/Autocad-Logo.svg",
    "🔒 Segurança": "https://upload.wikimedia.org/wikipedia/commons/9/9a/Kaspersky_logo.svg",
    "🛠️ Ferramenta":"https://upload.wikimedia.org/wikipedia/commons/8/8d/WinRAR_logo.svg",
    "🎬 Streaming": "https://upload.wikimedia.org/wikipedia/commons/0/08/Netflix_2015_logo.svg",
    "🎵 Música":    "https://upload.wikimedia.org/wikipedia/commons/8/84/Spotify_icon.svg",
    "🎁 Gift Card":"https://upload.wikimedia.org/wikipedia/commons/8/83/Steam_icon_logo.svg",
    "☁️ Cloud":     "https://upload.wikimedia.org/wikipedia/commons/c/c6/Google_One_logo.svg",
    "🧪 Teste":     "https://cdn.akamai.steamstatic.com/steam/apps/440/header.jpg",
    "💼 Produtividade":"https://upload.wikimedia.org/wikipedia/commons/3/35/Microsoft_365_%282022%29.svg",
    "🎮 Jogo":      "https://cdn-icons-png.flaticon.com/512/686/686589.png",
    "🎓 Curso":     "https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Graduation_hat.svg/240px-Graduation_hat.svg.png",
    "🤖 IA - Vídeo":      "https://upload.wikimedia.org/wikipedia/commons/4/4f/Runway_ml_logo.png",
    "🤖 IA - Texto":      "https://upload.wikimedia.org/wikipedia/commons/0/04/ChatGPT_logo.svg",
    "🤖 IA - Imagem":     "https://upload.wikimedia.org/wikipedia/commons/e/e6/Midjourney_Emblem.png",
    "🤖 IA - Áudio":      "https://upload.wikimedia.org/wikipedia/commons/4/47/ElevenLabs_logo.svg",
    "🤖 IA - Pesquisa":   "https://upload.wikimedia.org/wikipedia/commons/4/48/Perplexity_AI_logo.svg",
    "🤖 IA - Produtividade":"https://upload.wikimedia.org/wikipedia/commons/4/45/Notion_app_logo.png",
    "🤖 IA - Marketing":  "https://upload.wikimedia.org/wikipedia/commons/8/86/Semrush-logo.png",
    "🤖 IA - Código":     "https://upload.wikimedia.org/wikipedia/commons/6/61/GitHub_Copilot_logo.svg",
    "🤖 IA - Ferramenta": "https://cdn-icons-png.flaticon.com/512/10038/10038135.png",
    "🤖 IA Plano":        "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0f/Artificial_intelligence_icon.svg/240px-Artificial_intelligence_icon.svg.png",
    "📈 Finanças":        "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c8/Money_font_awesome.svg/240px-Money_font_awesome.svg.png",
    "📱 Mobile":          "https://upload.wikimedia.org/wikipedia/commons/thumb/6/64/Android_logo_2019_%28stacked%29.svg/240px-Android_logo_2019_%28stacked%29.svg.png",
    "💻 Dev & Código":    "https://upload.wikimedia.org/wikipedia/commons/9/9a/Visual_Studio_Code_1.35_icon.svg",
}

# ---- Imagens específicas por produto
_IMG_SPECIFIC = {
    # Windows
    "Windows 11 Pro":       "https://upload.wikimedia.org/wikipedia/commons/0/0c/Windows_logo_-_2012.svg",
    "Windows 11 Home":      "https://upload.wikimedia.org/wikipedia/commons/0/0c/Windows_logo_-_2012.svg",
    "Windows 11 Enterprise":"https://upload.wikimedia.org/wikipedia/commons/0/0c/Windows_logo_-_2012.svg",
    "Windows 10 Pro":       "https://upload.wikimedia.org/wikipedia/commons/0/0c/Windows_logo_-_2012.svg",
    "Windows 10 Home":      "https://upload.wikimedia.org/wikipedia/commons/0/0c/Windows_logo_-_2012.svg",
    "Windows Server":       "https://upload.wikimedia.org/wikipedia/commons/0/0c/Windows_logo_-_2012.svg",
    "Ubuntu":               "https://upload.wikimedia.org/wikipedia/commons/3/35/Tux.svg",
    # Office
    "Microsoft Office 2021":"https://upload.wikimedia.org/wikipedia/commons/5/5f/Microsoft_Office_logo_%282019%E2%80%93present%29.svg",
    "Microsoft Office 2019":"https://upload.wikimedia.org/wikipedia/commons/5/5f/Microsoft_Office_logo_%282019%E2%80%93present%29.svg",
    "Microsoft Office 2016":"https://upload.wikimedia.org/wikipedia/commons/5/5f/Microsoft_Office_logo_%282019%E2%80%93present%29.svg",
    "Microsoft 365":        "https://upload.wikimedia.org/wikipedia/commons/0/0c/Microsoft_365_%282022%29.svg",
    "Microsoft Project":    "https://upload.wikimedia.org/wikipedia/commons/1/1c/Microsoft_Project_2019_Logo.svg",
    "Microsoft Visio":      "https://upload.wikimedia.org/wikipedia/commons/1/14/Microsoft_Office_Visio_%282019%E2%80%93present%29.svg",
    "Microsoft Access":     "https://upload.wikimedia.org/wikipedia/commons/5/5f/Microsoft_Office_logo_%282019%E2%80%93present%29.svg",
    # Adobe
    "Adobe Photoshop":      "https://upload.wikimedia.org/wikipedia/commons/a/af/Adobe_Photoshop_CC_icon.svg",
    "Adobe Illustrator":    "https://upload.wikimedia.org/wikipedia/commons/f/fb/Adobe_Illustrator_CC_icon.svg",
    "Adobe Premiere":       "https://upload.wikimedia.org/wikipedia/commons/4/40/Adobe_Premiere_Pro_CC_icon.svg",
    "Adobe After Effects":  "https://upload.wikimedia.org/wikipedia/commons/0/05/Adobe_After_Effects_CC_icon.svg",
    "Adobe Creative Cloud": "https://upload.wikimedia.org/wikipedia/commons/8/8e/Adobe_Creative_Cloud_rainbow_icon.svg",
    "Adobe InDesign":       "https://upload.wikimedia.org/wikipedia/commons/4/48/Adobe_InDesign_CC_icon.svg",
    "Adobe XD":             "https://upload.wikimedia.org/wikipedia/commons/c/c2/Adobe_XD_CC_icon.svg",
    "Adobe Acrobat":        "https://upload.wikimedia.org/wikipedia/commons/thumb/9/92/Adobe_Acrobat_DC_logo_2020.svg/400px-Adobe_Acrobat_DC_logo_2020.svg.png",
    "Adobe Lightroom":      "https://upload.wikimedia.org/wikipedia/commons/b/b6/Adobe_Photoshop_Lightroom_CC_logo.svg",
    "CorelDRAW":            "https://upload.wikimedia.org/wikipedia/commons/3/30/Coreldraw_2020_logo.svg",
    "Figma":                "https://upload.wikimedia.org/wikipedia/commons/3/33/Figma-logo.svg",
    "Canva":                "https://upload.wikimedia.org/wikipedia/commons/0/0e/Canva_logo.svg",
    "Affinity":             "https://upload.wikimedia.org/wikipedia/commons/7/72/Affinity_Photo_logo_2023.png",
    # Video
    "Sony VEGAS":           "https://upload.wikimedia.org/wikipedia/commons/1/1f/Vegas_Pro_logo.png",
    "Final Cut Pro":        "https://upload.wikimedia.org/wikipedia/commons/9/90/Final_Cut_Pro_logo_2017.svg",
    "Cinema 4D":            "https://upload.wikimedia.org/wikipedia/commons/d/d4/Cinema_4D_Logo.png",
    "Blender":              "https://upload.wikimedia.org/wikipedia/commons/0/0c/Blender_logo_no_text.svg",
    "Camtasia":             "https://upload.wikimedia.org/wikipedia/commons/c/ca/Camtasia_Studio.svg",
    "DaVinci Resolve":      "https://upload.wikimedia.org/wikipedia/commons/f/f0/DaVinci_Resolve_17_logo.svg",
    # Engenharia
    "AutoCAD":              "https://upload.wikimedia.org/wikipedia/commons/4/45/Autocad-Logo.svg",
    "AutoCAD LT":           "https://upload.wikimedia.org/wikipedia/commons/4/45/Autocad-Logo.svg",
    "SketchUp":             "https://upload.wikimedia.org/wikipedia/commons/5/55/SketchUp_logo.svg",
    "Revit":                "https://upload.wikimedia.org/wikipedia/commons/7/7f/Revit_2017_logo.png",
    "3ds Max":              "https://upload.wikimedia.org/wikipedia/commons/3/3d/Autodesk_3ds_Max_2014_logo.png",
    "MATLAB":               "https://upload.wikimedia.org/wikipedia/commons/2/21/Matlab_Logo.png",
    # Antivirus
    "Norton 360":           "https://upload.wikimedia.org/wikipedia/commons/0/0a/Norton_AntiVirus_logo.png",
    "Kaspersky":            "https://upload.wikimedia.org/wikipedia/commons/9/9a/Kaspersky_logo.svg",
    "Bitdefender":          "https://upload.wikimedia.org/wikipedia/commons/9/97/Bitdefender_2019_logo.svg",
    "Avast":                "https://upload.wikimedia.org/wikipedia/commons/8/8b/Avast_software_logo.png",
    "AVG":                  "https://upload.wikimedia.org/wikipedia/commons/0/05/AVG_Technologies_logo_%282016%29.svg",
    "Malwarebytes":         "https://upload.wikimedia.org/wikipedia/commons/6/64/Malwarebytes_logo.svg",
    # Ferramentas
    "WinRAR":               "https://upload.wikimedia.org/wikipedia/commons/8/8d/WinRAR_logo.svg",
    "CCleaner":             "https://upload.wikimedia.org/wikipedia/commons/5/55/CCleaner-Logo.svg",
    "IDM":                  "https://upload.wikimedia.org/wikipedia/commons/e/e8/Internet_Download_Manager_logo.png",
    "Nero":                 "https://upload.wikimedia.org/wikipedia/commons/6/65/Nero_AG_logo.png",
    "WinUtilities":         "https://cdn-icons-png.flaticon.com/512/2920/2920303.png",
    "UltraEdit":            "https://www.ultraedit.com/wp-content/uploads/2018/04/cropped-ultraedit-favicon-180x180.png",
    "VMware":               "https://upload.wikimedia.org/wikipedia/commons/4/4a/VMware_worksation_icon.png",
    "Rufus":                "https://upload.wikimedia.org/wikipedia/commons/3/3e/Rufus-3.21-icon.png",
    # Streaming
    "Netflix":              "https://upload.wikimedia.org/wikipedia/commons/0/08/Netflix_2015_logo.svg",
    "Disney+":              "https://upload.wikimedia.org/wikipedia/commons/3/3e/Disney%2B_logo.svg",
    "Prime Video":          "https://upload.wikimedia.org/wikipedia/commons/1/11/Amazon_Prime_Video_logo.svg",
    "Max (HBO)":            "https://upload.wikimedia.org/wikipedia/commons/4/4c/HBO_Max_2025_%28c%29.svg",
    "YouTube Premium":      "https://upload.wikimedia.org/wikipedia/commons/0/09/YouTube_full-color_icon_%282017%29.svg",
    # Musica
    "Spotify":              "https://upload.wikimedia.org/wikipedia/commons/8/84/Spotify_icon.svg",
    # Gift Cards
    "Steam Gift Card":      "https://upload.wikimedia.org/wikipedia/commons/8/83/Steam_icon_logo.svg",
    "Google Play":          "https://upload.wikimedia.org/wikipedia/commons/7/7a/Google_Play_2022_logo.svg",
    "Xbox Game Pass":       "https://upload.wikimedia.org/wikipedia/commons/3/3e/Xbox_Game_Pass_logo.svg",
    "PlayStation Plus":     "https://upload.wikimedia.org/wikipedia/commons/0/0f/PlayStation_Plus_logo_%282022-_%29.svg",
    # Cloud
    "Google One":           "https://upload.wikimedia.org/wikipedia/commons/c/c6/Google_One_logo.svg",
    "OneDrive":             "https://upload.wikimedia.org/wikipedia/commons/6/62/Microsoft_Office_OneDrive_%282019%E2%80%93present%29.svg",
    # Cursos
    "Curso Completo Excel":"https://upload.wikimedia.org/wikipedia/commons/8/83/Microsoft_Excel_2013-2019_logo.svg",
    "Academia do Importador":"https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Graduation_hat.svg/512px-Graduation_hat.svg.png",
    "Como Importar da China":"https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Graduation_hat.svg/512px-Graduation_hat.svg.png",
    "Como Importar Roupas":"https://upload.wikimedia.org/wikipedia/commons/0/09/T-shirt_icon.svg",
    "Dropshipping":         "https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Graduation_hat.svg/512px-Graduation_hat.svg.png",
    "Dropshipping - Videos":"https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Graduation_hat.svg/512px-Graduation_hat.svg.png",
    "Empreendedor de Sucesso":"https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Graduation_hat.svg/512px-Graduation_hat.svg.png",
    "Formula da Importacao":"https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Graduation_hat.svg/512px-Graduation_hat.svg.png",
    "Importacao Legal":     "https://upload.wikimedia.org/wikipedia/commons/9/9e/Law_books_icon.svg",
    "Importador Profissional":"https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Graduation_hat.svg/512px-Graduation_hat.svg.png",
    "Importando com Sucesso":"https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Graduation_hat.svg/512px-Graduation_hat.svg.png",
    "Segredos Sobre Importacao":"https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Graduation_hat.svg/512px-Graduation_hat.svg.png",
    "Todos os Segredos da Importacao":"https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Graduation_hat.svg/512px-Graduation_hat.svg.png",
    "Como Vender no Facebook":"https://upload.wikimedia.org/wikipedia/commons/b/b9/2023_Facebook_icon.svg",
    "Aula 12 - DECEA":      "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a4/Airplane_take_off_icon.svg/512px-Airplane_take_off_icon.svg.png",
    "Aula 13 - DECEA":      "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a4/Airplane_take_off_icon.svg/512px-Airplane_take_off_icon.svg.png",
    "Edicao de Fotos - Aula 01":"https://logo.clearbit.com/adobe.com?size=512",
    "Edicao de Fotos - Aula 02":"https://logo.clearbit.com/adobe.com?size=512",
    "Edicao de Fotos - Aula 03":"https://logo.clearbit.com/adobe.com?size=512",
    "Edicao de Video - Adobe Premiere: Apresentacao":"https://logo.clearbit.com/adobe.com?size=512",
    "Edicao de Video - Adobe Premiere: Edicao Basica":"https://logo.clearbit.com/adobe.com?size=512",
    "Edicao de Video - Adobe Premiere: Inserindo Textos":"https://logo.clearbit.com/adobe.com?size=512",
    "Pack DECEA":           "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a4/Airplane_take_off_icon.svg/512px-Airplane_take_off_icon.svg.png",
    "Pack Photoshop":       "https://logo.clearbit.com/adobe.com?size=512",
    "Pack Adobe Premiere":  "https://logo.clearbit.com/adobe.com?size=512",
    "Curso de Trafego Pago":"https://logo.clearbit.com/google.com?size=512",
    "Curso de Instagram":   "https://logo.clearbit.com/instagram.com?size=512",
    "Curso de TikTok":      "https://logo.clearbit.com/tiktok.com?size=512",
    "Curso de YouTube":     "https://logo.clearbit.com/youtube.com?size=512",
    "Curso de Copywriting": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Graduation_hat.svg/512px-Graduation_hat.svg.png",
    "Curso de Afiliados":   "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c8/Money_font_awesome.svg/512px-Money_font_awesome.svg.png",
    "Curso de Edicao de Video":"https://logo.clearbit.com/adobe.com?size=512",
    "Curso de Photoshop Redes":"https://logo.clearbit.com/adobe.com?size=512",
    "Curso de Python":      "https://upload.wikimedia.org/wikipedia/commons/c/c3/Python-logo-notext.svg",
    "Curso de Ingles":      "https://upload.wikimedia.org/wikipedia/commons/8/81/Flag_of_the_United_Kingdom_%281-2%29.svg",
    "Metodo Investidor":    "https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Bolsa_de_valores.svg/512px-Bolsa_de_valores.svg.png",
    "Pack IA Premium":      "https://logo.clearbit.com/openai.com?size=512",
    "Pack IA Criador":      "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0f/Artificial_intelligence_icon.svg/512px-Artificial_intelligence_icon.svg.png",
    "Windows 11 Pro + Office":"https://logo.clearbit.com/microsoft.com?size=512",
    "Antivirus + VPN":      "https://logo.clearbit.com/kaspersky.com?size=512",
    # Cursos com acento (cópia dos de cima para matching com _norm)
    "WinUtilities":         "https://logo.clearbit.com/nero.com?size=512",
    "UltraEdit":            "https://logo.clearbit.com/ultraedit.com?size=512",
}

def _find_image(g):
    """Retorna URL de imagem real para um produto (com matching sem acentos)."""
    nome = g.get("nome", "")
    nome_n = _norm(nome)
    # 1) Especificas (match com normalizacao)
    for key, url in _IMG_SPECIFIC.items():
        if _norm(key) in nome_n:
            return url
    # 2) Keyword (match com normalizacao)
    for key, url in _IMG_BY_KEYWORD:
        if _norm(key) in nome_n:
            return url
    # 3) Por tipo
    t = g.get("tipo", "")
    if t in _IMG_BY_TYPE:
        return _IMG_BY_TYPE[t]
    # 4) Fallback por prefixo do tipo
    if "Jogo" in t:
        return _IMG_BY_TYPE["🎮 Jogo"]
    if "Curso" in t:
        return _IMG_BY_TYPE["🎓 Curso"]
    if "IA" in t:
        return "https://cdn-icons-png.flaticon.com/512/10038/10038135.png"
    # 7) Fallback generico
    return "https://cdn-icons-png.flaticon.com/512/1170/1170679.png"

# ============================================================
# 1) PRODUTOS ORIGINAIS (seu catalogo antigo com IDs e imagens preservados)
# ============================================================
GAMES_CATALOG = [
    # --- Jogos 1-92 (com imagens Steam do catalogo antigo) ---
    {"id":1,"nome":"House Flipper Remastered Collection","preco_original":32.90,"preco_oferta":32.90,"descricao":"Coleção remasterizada do simulador de reformas.","categorias":["Simulação","Casuais"],"oferta":False,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=613100)},
    {"id":2,"nome":"Manor Lords","preco_original":26.90,"preco_oferta":26.90,"descricao":"Jogo de estratégia e construção medieval.","categorias":["Estratégia","Construção"],"oferta":False,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=1363080)},
    {"id":3,"nome":"Need for Speed Most Wanted Limited Edition","preco_original":34.90,"preco_oferta":24.90,"descricao":"Edição limitada do clássico de corrida.","categorias":["Corrida","Ação"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=24740)},
    {"id":4,"nome":"Marvel Ultimate Alliance","preco_original":29.90,"preco_oferta":29.90,"descricao":"RPG de ação com heróis Marvel.","categorias":["Ação","RPG"],"oferta":False,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=56000)},
    {"id":5,"nome":"Red Dead Redemption 2","preco_original":64.90,"preco_oferta":38.90,"descricao":"Ação e aventura no Velho Oeste.","categorias":["Ação","Aventura","Destaques"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=1174180)},
    {"id":6,"nome":"MEGAMAN COMPLETE PACK","preco_original":69.90,"preco_oferta":29.90,"descricao":"Pacote completo da franquia Mega Man.","categorias":["Ação","Indie"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=363440)},
    {"id":7,"nome":"Hollow Knight Silksong","preco_original":29.90,"preco_oferta":19.90,"descricao":"Sequência do aclamado metroidvania.","categorias":["Ação","Aventura","Indie"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=1030300)},
    {"id":8,"nome":"Farming Simulator 22 Platinum","preco_original":39.90,"preco_oferta":32.90,"descricao":"Simulação agrícola com conteúdo extra.","categorias":["Simulação"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=1248130)},
    {"id":9,"nome":"Pragmata","preco_original":62.99,"preco_oferta":34.90,"descricao":"Ação/aventura futurista da Capcom.","categorias":["Ação","Aventura"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=1382330)},
    {"id":10,"nome":"Subnautica 2","preco_original":48.99,"preco_oferta":29.90,"descricao":"Simulação subaquática offline.","categorias":["Aventura","Simulação"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=848450)},
    {"id":11,"nome":"Tomb Raider IV-VI Remastered","preco_original":24.90,"preco_oferta":24.90,"descricao":"Remaster dos clássicos Tomb Raider.","categorias":["Ação","Aventura"],"oferta":False,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=2508510)},
    {"id":12,"nome":"Sonic Frontiers Digital Deluxe","preco_original":44.99,"preco_oferta":29.90,"descricao":"Ação e plataforma em mundo aberto com o Sonic!","categorias":["Ação","Aventura"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=1237320)},
    {"id":13,"nome":"Core Keeper + Todas DLCs","preco_original":24.90,"preco_oferta":24.90,"descricao":"Survival sandbox com todas as expansões.","categorias":["Aventura","Indie"],"oferta":False,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=1621690)},
    {"id":14,"nome":"Spyro Reignited Trilogy","preco_original":32.90,"preco_oferta":32.90,"descricao":"Trilogia remasterizada do dragão Spyro.","categorias":["Ação","Aventura","Casuais"],"oferta":False,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=996580)},
    {"id":15,"nome":"Marvel Cosmic Invasion","preco_original":39.90,"preco_oferta":26.90,"descricao":"Ação com heróis cósmicos da Marvel.","categorias":["Ação"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=2630700)},
    {"id":16,"nome":"GTA Vice City Definitive","preco_original":29.90,"preco_oferta":29.90,"descricao":"Versão definitiva do clássico GTA Vice City.","categorias":["Ação","Aventura"],"oferta":False,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=1547000)},
    {"id":17,"nome":"PES 2013","preco_original":29.90,"preco_oferta":29.90,"descricao":"Simulador de futebol clássico de 2013.","categorias":["Esporte"],"oferta":False,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=207580)},
    {"id":18,"nome":"Stellar Blade","preco_original":54.90,"preco_oferta":34.90,"descricao":"Ação em terceira pessoa futurista.","categorias":["Ação","Aventura"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=3489700)},
    {"id":19,"nome":"Tony Hawks Pro Skater 1+2","preco_original":54.90,"preco_oferta":29.90,"descricao":"Remaster dos clássicos de skate.","categorias":["Esporte","Ação"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=2725150)},
    {"id":20,"nome":"Farming Simulator 22 Year 1 Bundle","preco_original":36.90,"preco_oferta":29.90,"descricao":"Bundle com primeiro ano de conteúdo.","categorias":["Simulação"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=1248130)},
    {"id":21,"nome":"The Witcher 3 Complete Edition","preco_original":29.90,"preco_oferta":29.90,"descricao":"RPG completo com todas as expansões.","categorias":["RPG","Aventura","Destaques","Mais Vendidos"],"oferta":False,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=292030)},
    {"id":22,"nome":"FIFA 12 + UEFA EURO 2012","preco_original":36.99,"preco_oferta":29.90,"descricao":"Futebol com a Eurocopa 2012.","categorias":["Esporte"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=47900)},
    {"id":23,"nome":"Dead Space Remake","preco_original":64.99,"preco_oferta":32.90,"descricao":"Terror espacial refeito do zero.","categorias":["Terror","Ação"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=1693980)},
    {"id":24,"nome":"Assetto Corsa Rally","preco_original":49.99,"preco_oferta":27.90,"descricao":"Simulador de corrida de rali.","categorias":["Corrida","Simulação"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=244210)},
    {"id":25,"nome":"Prison Architect Total Lockdown","preco_original":57.99,"preco_oferta":34.90,"descricao":"Simulador de prisão completo.","categorias":["Simulação","Estratégia"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=233450)},
    {"id":26,"nome":"Slay the Spire 2","preco_original":29.99,"preco_oferta":19.90,"descricao":"Roguelike de cartas (sequência).","categorias":["Indie","Estratégia"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=646570)},
    {"id":27,"nome":"FORZA HORIZON 6","preco_original":72.90,"preco_oferta":37.90,"descricao":"Corrida em mundo aberto.","categorias":["Corrida","Destaques"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=1551360)},
    {"id":28,"nome":"TOMB RAIDER I-III REMASTERED","preco_original":32.90,"preco_oferta":19.90,"descricao":"Remaster dos primeiros Tomb Raider.","categorias":["Ação","Aventura"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=2478970)},
    {"id":29,"nome":"Kingdom Come Deliverance II","preco_original":62.90,"preco_oferta":32.90,"descricao":"RPG histórico medieval realista.","categorias":["RPG","Aventura"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=1771300)},
    {"id":30,"nome":"EUROPA UNIVERSALIS V","preco_original":32.90,"preco_oferta":32.90,"descricao":"Grande estratégia mundial.","categorias":["Estratégia"],"oferta":False,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=3450310)},
    {"id":31,"nome":"Elden Ring","preco_original":45.90,"preco_oferta":32.90,"descricao":"RPG de ação em mundo aberto.","categorias":["RPG","Ação","Destaques","Mais Vendidos"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=1245620)},
    {"id":32,"nome":"Elden Ring Nightreign Deluxe","preco_original":54.90,"preco_oferta":29.90,"descricao":"Edição de luxo com conteúdo extra.","categorias":["RPG","Ação"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=2622380)},
    {"id":33,"nome":"Sekiro Shadows Die Twice GOTY","preco_original":39.90,"preco_oferta":29.90,"descricao":"Ação e desafio no Japão feudal.","categorias":["Ação","Aventura"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=814380)},
    {"id":34,"nome":"Elden Ring + Shadow Of The Erdtree","preco_original":72.90,"preco_oferta":36.90,"descricao":"Jogo base + expansão completa.","categorias":["RPG","Ação","Destaques"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=2778580)},
    {"id":35,"nome":"Crash Bandicoot 4","preco_original":42.90,"preco_oferta":29.90,"descricao":"Plataforma com o marsupial louco.","categorias":["Ação","Aventura","Casuais"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=1453090)},
    {"id":36,"nome":"Resident Evil 2 Remake Deluxe","preco_original":49.90,"preco_oferta":29.90,"descricao":"Terror e sobrevivência em Raccoon City.","categorias":["Terror","Ação"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=883710)},
    {"id":37,"nome":"The Sims 2 Legacy Collection","preco_original":27.90,"preco_oferta":27.90,"descricao":"Clássico simulador de vida.","categorias":["Simulação","Casuais"],"oferta":False,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=3314060)},
    {"id":38,"nome":"Victoria 3","preco_original":46.90,"preco_oferta":32.90,"descricao":"Grande estratégia do século XIX.","categorias":["Estratégia"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=529340)},
    {"id":39,"nome":"Ready Or Not + Todas DLCs","preco_original":32.90,"preco_oferta":32.90,"descricao":"Tático policial com todas expansões.","categorias":["Ação","Simulação"],"oferta":False,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=1144200)},
    {"id":40,"nome":"LEGO Batman O Legado","preco_original":62.90,"preco_oferta":34.90,"descricao":"Ação e humor com LEGO Batman.","categorias":["Ação","Aventura","Casuais"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=502820)},
    {"id":41,"nome":"Crash Bandicoot N Sane Trilogy","preco_original":42.90,"preco_oferta":29.90,"descricao":"Trilogia clássica remasterizada.","categorias":["Ação","Aventura","Casuais"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=731490)},
    {"id":42,"nome":"Command Conquer Generals Zero Hour","preco_original":34.90,"preco_oferta":22.90,"descricao":"RTS de guerra moderna.","categorias":["Estratégia"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=2229850)},
    {"id":43,"nome":"Cities Skylines","preco_original":29.90,"preco_oferta":29.90,"descricao":"Simulador de cidade.","categorias":["Simulação","Construção"],"oferta":False,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=255710)},
    {"id":44,"nome":"Spider-Man Miles Morales","preco_original":42.40,"preco_oferta":29.90,"descricao":"Ação com o Homem-Aranha Miles Morales.","categorias":["Ação","Aventura","Destaques"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=1817190)},
    {"id":45,"nome":"Resident Evil Requiem Deluxe","preco_original":72.90,"preco_oferta":37.90,"descricao":"Edição de luxo de Resident Evil Requiem.","categorias":["Terror","Ação"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=3273940)},
    {"id":46,"nome":"inZOI","preco_original":59.90,"preco_oferta":34.90,"descricao":"Simulador de vida realista.","categorias":["Simulação","Casuais"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=2456740)},
    {"id":47,"nome":"GTA San Andreas Definitive","preco_original":29.90,"preco_oferta":29.90,"descricao":"Clássico do GTA remasterizado.","categorias":["Ação","Aventura"],"oferta":False,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=1547001)},
    {"id":48,"nome":"The Last of Us Part II Remastered","preco_original":59.90,"preco_oferta":36.90,"descricao":"Ação e drama pós-apocalíptico.","categorias":["Ação","Aventura","Destaques"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=2531310)},
    {"id":49,"nome":"Cities Skylines Collection","preco_original":29.90,"preco_oferta":29.90,"descricao":"Coleção do simulador de cidades.","categorias":["Simulação","Construção"],"oferta":False,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=255710)},
    {"id":50,"nome":"Age of Empires III Definitive","preco_original":34.90,"preco_oferta":27.90,"descricao":"RTS histórico com todas expansões.","categorias":["Estratégia"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=933110)},
    {"id":51,"nome":"FIFA 14","preco_original":29.90,"preco_oferta":29.90,"descricao":"Futebol clássico FIFA 14.","categorias":["Esporte"],"oferta":False,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=241950)},
    {"id":52,"nome":"Euro Truck Simulator 2 Gold + BR","preco_original":39.90,"preco_oferta":32.90,"descricao":"Simulador de caminhão com mapas BR!","categorias":["Simulação"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=227300)},
    {"id":53,"nome":"eFootball PES 2021","preco_original":32.90,"preco_oferta":32.90,"descricao":"Futebol com Season Update 2021.","categorias":["Esporte"],"oferta":False,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=1394960)},
    {"id":54,"nome":"FIFA 17","preco_original":44.90,"preco_oferta":32.90,"descricao":"FIFA 17 com modo Journey.","categorias":["Esporte"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=468120)},
    {"id":55,"nome":"The Sims 4 Todas DLCs","preco_original":34.90,"preco_oferta":34.90,"descricao":"The Sims 4 completo com todas as DLCs.","categorias":["Simulação","Casuais","Mais Vendidos"],"oferta":False,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=1222670)},
    {"id":56,"nome":"The Sims 4 Digital Deluxe","preco_original":34.90,"preco_oferta":34.90,"descricao":"Edição Digital Deluxe do The Sims 4.","categorias":["Simulação","Casuais"],"oferta":False,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=1222670)},
    {"id":57,"nome":"The Sims 3 Com Expansões","preco_original":39.90,"preco_oferta":29.90,"descricao":"The Sims 3 completo com expansões.","categorias":["Simulação","Casuais"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=47890)},
    {"id":58,"nome":"FIFA 22","preco_original":39.90,"preco_oferta":32.90,"descricao":"FIFA 22 com HyperMotion Technology.","categorias":["Esporte"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=1506830)},
    {"id":59,"nome":"Cities Skylines 2 Ultimate","preco_original":69.90,"preco_oferta":34.90,"descricao":"Simulador de cidade de última geração.","categorias":["Simulação","Construção"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=949230)},
    {"id":60,"nome":"FIFA 21","preco_original":29.90,"preco_oferta":29.90,"descricao":"FIFA 21 - futebol eletrônico.","categorias":["Esporte"],"oferta":False,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=1313860)},
    {"id":61,"nome":"Euro Truck Simulator 2 + Mapas BR","preco_original":39.90,"preco_oferta":32.90,"descricao":"Simulador de caminhão com mapas BR.","categorias":["Simulação"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=227300)},
    {"id":62,"nome":"FIFA 23","preco_original":39.90,"preco_oferta":29.90,"descricao":"FIFA 23 - o último FIFA antes do EA FC.","categorias":["Esporte"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=1811260)},
    {"id":63,"nome":"Farming Simulator 25 + DLCs","preco_original":58.60,"preco_oferta":34.90,"descricao":"O mais novo Farming Simulator!","categorias":["Simulação"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=2300320)},
    {"id":64,"nome":"Cities Skylines II + DLCs","preco_original":64.90,"preco_oferta":34.90,"descricao":"Cities Skylines II completo.","categorias":["Simulação","Construção"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=949230)},
    {"id":65,"nome":"FIFA 15","preco_original":32.90,"preco_oferta":32.90,"descricao":"FIFA 15 - futebol clássico.","categorias":["Esporte"],"oferta":False,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=289600)},
    {"id":66,"nome":"House Flipper Com DLCs","preco_original":49.90,"preco_oferta":29.90,"descricao":"House Flipper completo com DLCs.","categorias":["Simulação","Casuais"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=613100)},
    {"id":67,"nome":"FIFA 13","preco_original":42.90,"preco_oferta":29.90,"descricao":"FIFA 13 clássico.","categorias":["Esporte"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=207570)},
    {"id":68,"nome":"SnowRunner Premium Edition","preco_original":44.90,"preco_oferta":32.90,"descricao":"Simulador off-road extremo.","categorias":["Simulação"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=1465360)},
    {"id":69,"nome":"Mario Kart 8 Deluxe","preco_original":64.90,"preco_oferta":29.90,"descricao":"Corrida divertida com personagens da Nintendo!","categorias":["Corrida","Casuais"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":"https://upload.wikimedia.org/wikipedia/en/8/8c/Mario_Kart_8_Deluxe.jpg"},
    {"id":70,"nome":"FIFA 20","preco_original":32.90,"preco_oferta":32.90,"descricao":"FIFA 20 com modo Volta Football.","categorias":["Esporte"],"oferta":False,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=1056600)},
    {"id":71,"nome":"Plants Vs Zombies Replanted","preco_original":4.24,"preco_oferta":4.24,"descricao":"Defenda seu jardim dos zumbis!","categorias":["Casuais","Puzzle"],"oferta":False,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=3950)},
    {"id":72,"nome":"House Flipper 2 + DLCs","preco_original":32.90,"preco_oferta":32.90,"descricao":"House Flipper 2 com todas as DLCs.","categorias":["Simulação","Casuais"],"oferta":False,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=1190970)},
    {"id":73,"nome":"The Last of Us Part I","preco_original":48.90,"preco_oferta":33.90,"descricao":"A jornada épica de Joel e Ellie.","categorias":["Ação","Aventura","Destaques"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=1888930)},
    {"id":74,"nome":"Dispatch","preco_original":39.90,"preco_oferta":17.90,"descricao":"Simulador de central de emergências.","categorias":["Simulação"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=3527290)},
    {"id":75,"nome":"Spider-Man Remastered","preco_original":42.40,"preco_oferta":29.90,"descricao":"Marvel's Spider-Man Remasterizado.","categorias":["Ação","Aventura","Destaques"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=1817070)},
    {"id":76,"nome":"God Of War 2018 Dublado","preco_original":39.90,"preco_oferta":29.90,"descricao":"Kratos e Atreus em PT-BR!","categorias":["Ação","Aventura","Destaques","Mais Vendidos"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=1593500)},
    {"id":77,"nome":"Farming Simulator 25 Online","preco_original":58.60,"preco_oferta":34.90,"descricao":"Farming Simulator 25 com modo Online!","categorias":["Simulação"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=2300320)},
    {"id":78,"nome":"FIFA 18","preco_original":49.90,"preco_oferta":32.90,"descricao":"FIFA 18 com modo The Journey.","categorias":["Esporte"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=611500)},
    {"id":79,"nome":"Resident Evil 4 Remake Gold","preco_original":59.90,"preco_oferta":32.90,"descricao":"Remake do clássico RE4.","categorias":["Terror","Ação"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=2050650)},
    {"id":80,"nome":"FIFA 19","preco_original":32.90,"preco_oferta":32.90,"descricao":"FIFA 19 com UEFA Champions League.","categorias":["Esporte"],"oferta":False,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=918360)},
    {"id":81,"nome":"Age of Mythology Retold","preco_original":44.90,"preco_oferta":29.90,"descricao":"RTS mitológico remasterizado.","categorias":["Estratégia"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=1934680)},
    {"id":82,"nome":"SimCity 5 (2013)","preco_original":29.90,"preco_oferta":29.90,"descricao":"Construa e gerencie sua cidade.","categorias":["Simulação","Construção"],"oferta":False,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":"https://upload.wikimedia.org/wikipedia/en/9/9a/SimCity_2013_Limited_Edition_cover.jpg"},
    {"id":83,"nome":"Cities Skylines Deluxe","preco_original":29.90,"preco_oferta":29.90,"descricao":"Edição Deluxe do Cities Skylines.","categorias":["Simulação","Construção"],"oferta":False,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=255710)},
    {"id":84,"nome":"FIFA 16","preco_original":29.90,"preco_oferta":29.90,"descricao":"FIFA 16 - futebol clássico.","categorias":["Esporte"],"oferta":False,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=353650)},
    {"id":85,"nome":"God of War Ragnarok Dublado","preco_original":69.90,"preco_oferta":32.90,"descricao":"Continuação épica de Kratos. PT-BR!","categorias":["Ação","Aventura","Destaques","Mais Vendidos"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=2322010)},
    {"id":86,"nome":"Red Dead Redemption","preco_original":49.90,"preco_oferta":29.90,"descricao":"O clássico do Velho Oeste.","categorias":["Ação","Aventura"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=2668510)},
    {"id":87,"nome":"Spider-Man 2","preco_original":74.90,"preco_oferta":36.90,"descricao":"Marvel's Spider-Man 2 para PC.","categorias":["Ação","Aventura","Destaques"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=2944550)},
    {"id":88,"nome":"Project Zomboid","preco_original":22.90,"preco_oferta":22.90,"descricao":"Simulador de sobrevivência zumbi.","categorias":["Simulação","Indie"],"oferta":False,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=108600)},
    {"id":89,"nome":"NASCAR 25","preco_original":59.90,"preco_oferta":29.90,"descricao":"Corrida NASCAR com carros reais!","categorias":["Corrida","Esporte"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=3158220)},
    {"id":90,"nome":"Farming Simulator 22","preco_original":36.90,"preco_oferta":29.90,"descricao":"Simulação agrícola completa.","categorias":["Simulação"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=1248130)},
    {"id":91,"nome":"Need for Speed Heat Deluxe","preco_original":32.90,"preco_oferta":32.90,"descricao":"Corrida noturna de rua. Deluxe!","categorias":["Corrida","Ação"],"oferta":False,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=1222680)},
    {"id":92,"nome":"The Sims 3 Com Todas DLCs","preco_original":49.90,"preco_oferta":29.90,"descricao":"The Sims 3 completo com todas as DLCs!","categorias":["Simulação","Casuais"],"oferta":True,"plataforma":"PC","tipo":"🎮 Jogo","imagem_url":_IMG_STEAM.format(appid=47890)},

    # --- Windows (IDs 100-104 com logos reais) ---
    {"id":100,"nome":"Windows 11 Pro - Licença Vitalícia","preco_original":899.90,"preco_oferta":89.90,"descricao":"Licença ORIGINAL Windows 11 Pro vitalícia. Ativação online garantida.","categorias":["Sistema Operacional"],"oferta":True,"plataforma":"PC","tipo":"🖥️ Sistema","imagem_url":"https://upload.wikimedia.org/wikipedia/commons/0/0c/Windows_logo_-_2012.svg"},
    {"id":101,"nome":"Windows 10 Pro - Licença Vitalícia","preco_original":699.90,"preco_oferta":69.90,"descricao":"Licença ORIGINAL Windows 10 Pro vitalícia. Compatível com qualquer PC.","categorias":["Sistema Operacional"],"oferta":True,"plataforma":"PC","tipo":"🖥️ Sistema","imagem_url":"https://upload.wikimedia.org/wikipedia/commons/0/0c/Windows_logo_-_2012.svg"},
    {"id":102,"nome":"Windows 11 Home - Licença Original","preco_original":599.90,"preco_oferta":59.90,"descricao":"Licença Windows 11 Home original. Perfeito para uso doméstico.","categorias":["Sistema Operacional"],"oferta":True,"plataforma":"PC","tipo":"🖥️ Sistema","imagem_url":"https://upload.wikimedia.org/wikipedia/commons/0/0c/Windows_logo_-_2012.svg"},
    {"id":103,"nome":"Ubuntu 24.04 LTS + Suporte","preco_original":149.90,"preco_oferta":49.90,"descricao":"Ubuntu 24.04 LTS com suporte premium. Instalação assistida + tutoriais.","categorias":["Sistema Operacional"],"oferta":True,"plataforma":"PC","tipo":"🖥️ Sistema","imagem_url":"https://upload.wikimedia.org/wikipedia/commons/3/35/Tux.svg"},
    {"id":104,"nome":"Windows Server 2022 Standard","preco_original":2999.90,"preco_oferta":499.90,"descricao":"Windows Server 2022. Para empresas e servidores corporativos.","categorias":["Sistema Operacional"],"oferta":True,"plataforma":"Server","tipo":"🖥️ Sistema","imagem_url":"https://upload.wikimedia.org/wikipedia/commons/0/0c/Windows_logo_-_2012.svg"},

    # --- Office (110-114) ---
    {"id":110,"nome":"Microsoft Office 2021 Pro Plus","preco_original":1899.90,"preco_oferta":79.90,"descricao":"Office 2021 Pro Plus VITALÍCIO. Word, Excel, PowerPoint, Outlook, Access.","categorias":["Office","Produtividade"],"oferta":True,"plataforma":"PC","tipo":"📄 Office","imagem_url":"https://upload.wikimedia.org/wikipedia/commons/5/5f/Microsoft_Office_logo_%282019%E2%80%93present%29.svg"},
    {"id":111,"nome":"Microsoft Office 2019 Pro Plus","preco_original":1599.90,"preco_oferta":69.90,"descricao":"Office 2019 Pro Plus completo. Licença vitalícia.","categorias":["Office","Produtividade"],"oferta":True,"plataforma":"PC","tipo":"📄 Office","imagem_url":"https://upload.wikimedia.org/wikipedia/commons/5/5f/Microsoft_Office_logo_%282019%E2%80%93present%29.svg"},
    {"id":112,"nome":"Microsoft 365 Family (6 usuários)","preco_original":449.90,"preco_oferta":199.90,"descricao":"Microsoft 365 para 6 pessoas. 1TB OneDrive cada.","categorias":["Office","Produtividade"],"oferta":True,"plataforma":"Multi","tipo":"📄 Office","imagem_url":"https://upload.wikimedia.org/wikipedia/commons/0/0c/Microsoft_365_%282022%29.svg"},
    {"id":113,"nome":"Microsoft Project 2021 Pro","preco_original":4999.90,"preco_oferta":299.90,"descricao":"MS Project 2021 para gerenciamento profissional.","categorias":["Office","Produtividade"],"oferta":True,"plataforma":"PC","tipo":"📄 Office","imagem_url":"https://upload.wikimedia.org/wikipedia/commons/1/1c/Microsoft_Project_2019_Logo.svg"},
    {"id":114,"nome":"Microsoft Visio 2021 Pro","preco_original":2999.90,"preco_oferta":199.90,"descricao":"MS Visio 2021 para diagramas profissionais.","categorias":["Office","Produtividade"],"oferta":True,"plataforma":"PC","tipo":"📄 Office","imagem_url":"https://upload.wikimedia.org/wikipedia/commons/1/14/Microsoft_Office_Visio_%282019%E2%80%93present%29.svg"},

    # --- Adobe (120-125) ---
    {"id":120,"nome":"Adobe Photoshop 2024 - Lifetime","preco_original":1899.90,"preco_oferta":149.90,"descricao":"Adobe Photoshop 2024 completo. Sem mensalidade!","categorias":["Design"],"oferta":True,"plataforma":"PC","tipo":"🎨 Design","imagem_url":"https://upload.wikimedia.org/wikipedia/commons/a/af/Adobe_Photoshop_CC_icon.svg"},
    {"id":121,"nome":"Adobe Illustrator 2024 - Lifetime","preco_original":1799.90,"preco_oferta":139.90,"descricao":"Adobe Illustrator 2024. Design vetorial profissional.","categorias":["Design"],"oferta":True,"plataforma":"PC","tipo":"🎨 Design","imagem_url":"https://upload.wikimedia.org/wikipedia/commons/f/fb/Adobe_Illustrator_CC_icon.svg"},
    {"id":122,"nome":"Adobe Premiere Pro 2024","preco_original":1999.90,"preco_oferta":169.90,"descricao":"Adobe Premiere Pro 2024. Edição de vídeo Hollywood.","categorias":["Edição de Vídeo"],"oferta":True,"plataforma":"PC","tipo":"🎬 Vídeo","imagem_url":"https://upload.wikimedia.org/wikipedia/commons/4/40/Adobe_Premiere_Pro_CC_icon.svg"},
    {"id":123,"nome":"Adobe After Effects 2024","preco_original":1999.90,"preco_oferta":169.90,"descricao":"Adobe After Effects 2024. Animação e VFX.","categorias":["Edição de Vídeo","Design"],"oferta":True,"plataforma":"PC","tipo":"🎬 Vídeo","imagem_url":"https://upload.wikimedia.org/wikipedia/commons/0/05/Adobe_After_Effects_CC_icon.svg"},
    {"id":124,"nome":"Adobe Creative Cloud COMPLETO","preco_original":4999.90,"preco_oferta":399.90,"descricao":"Pacote Adobe COMPLETO: 20+ apps profissionais!","categorias":["Design","Edição de Vídeo"],"oferta":True,"plataforma":"PC","tipo":"🎨 Design","imagem_url":"https://upload.wikimedia.org/wikipedia/commons/8/8e/Adobe_Creative_Cloud_rainbow_icon.svg"},
    {"id":125,"nome":"CorelDRAW Graphics Suite 2024","preco_original":2499.90,"preco_oferta":199.90,"descricao":"CorelDRAW 2024 completo. Design vetorial.","categorias":["Design"],"oferta":True,"plataforma":"PC","tipo":"🎨 Design","imagem_url":"https://upload.wikimedia.org/wikipedia/commons/3/30/Coreldraw_2020_logo.svg"},

    # --- Engenharia (130-134) ---
    {"id":130,"nome":"AutoCAD 2024 - Profissional","preco_original":9999.90,"preco_oferta":299.90,"descricao":"AutoCAD 2024 completo. Software CAD #1 do mundo.","categorias":["Engenharia"],"oferta":True,"plataforma":"PC","tipo":"🏗️ Engenharia","imagem_url":"https://upload.wikimedia.org/wikipedia/commons/4/45/Autocad-Logo.svg"},
    {"id":131,"nome":"AutoCAD LT 2024","preco_original":4999.90,"preco_oferta":199.90,"descricao":"AutoCAD LT 2024. Versão 2D profissional.","categorias":["Engenharia"],"oferta":True,"plataforma":"PC","tipo":"🏗️ Engenharia","imagem_url":"https://upload.wikimedia.org/wikipedia/commons/4/45/Autocad-Logo.svg"},
    {"id":132,"nome":"SketchUp Pro 2024 - Vitalício","preco_original":2999.90,"preco_oferta":249.90,"descricao":"SketchUp Pro 2024. Modelagem 3D arquitetônica.","categorias":["Engenharia","Design"],"oferta":True,"plataforma":"PC","tipo":"🏗️ Engenharia","imagem_url":"https://upload.wikimedia.org/wikipedia/commons/5/55/SketchUp_logo.svg"},
    {"id":133,"nome":"Revit 2024 Profissional","preco_original":11999.90,"preco_oferta":399.90,"descricao":"Autodesk Revit 2024. BIM profissional.","categorias":["Engenharia"],"oferta":True,"plataforma":"PC","tipo":"🏗️ Engenharia","imagem_url":"https://upload.wikimedia.org/wikipedia/commons/7/7f/Revit_2017_logo.png"},
    {"id":134,"nome":"3ds Max 2024","preco_original":9999.90,"preco_oferta":349.90,"descricao":"Autodesk 3ds Max 2024. Modelagem e renderização 3D.","categorias":["Engenharia","Design"],"oferta":True,"plataforma":"PC","tipo":"🏗️ Engenharia","imagem_url":"https://upload.wikimedia.org/wikipedia/commons/3/3d/Autodesk_3ds_Max_2014_logo.png"},

    # --- Antivirus (140-142) ---
    {"id":140,"nome":"Norton 360 Deluxe (5 dispositivos)","preco_original":399.90,"preco_oferta":89.90,"descricao":"Norton 360 Deluxe. Antivírus + VPN + Senhas. 5 dispositivos.","categorias":["Antivírus"],"oferta":True,"plataforma":"Multi","tipo":"🔒 Segurança","imagem_url":"https://upload.wikimedia.org/wikipedia/commons/0/0a/Norton_AntiVirus_logo.png"},
    {"id":141,"nome":"Kaspersky Premium (5 dispositivos)","preco_original":349.90,"preco_oferta":79.90,"descricao":"Kaspersky Premium. Proteção total + VPN ilimitada.","categorias":["Antivírus"],"oferta":True,"plataforma":"Multi","tipo":"🔒 Segurança","imagem_url":"https://upload.wikimedia.org/wikipedia/commons/9/9a/Kaspersky_logo.svg"},
    {"id":142,"nome":"Bitdefender Total Security","preco_original":399.90,"preco_oferta":89.90,"descricao":"Bitdefender Total Security. Melhor antivírus em testes.","categorias":["Antivírus"],"oferta":True,"plataforma":"Multi","tipo":"🔒 Segurança","imagem_url":"https://upload.wikimedia.org/wikipedia/commons/9/97/Bitdefender_2019_logo.svg"},

    # --- Ferramentas (150-152) ---
    {"id":150,"nome":"WinRAR Premium - Vitalício","preco_original":149.90,"preco_oferta":29.90,"descricao":"WinRAR Premium vitalício. Compactador #1 do mundo!","categorias":["Ferramentas"],"oferta":True,"plataforma":"PC","tipo":"🛠️ Ferramenta","imagem_url":"https://upload.wikimedia.org/wikipedia/commons/8/8d/WinRAR_logo.svg"},
    {"id":151,"nome":"CCleaner Professional Plus","preco_original":199.90,"preco_oferta":39.90,"descricao":"CCleaner Pro Plus. Limpeza + otimização + recuperação.","categorias":["Ferramentas"],"oferta":True,"plataforma":"PC","tipo":"🛠️ Ferramenta","imagem_url":"https://upload.wikimedia.org/wikipedia/commons/5/55/CCleaner-Logo.svg"},
    {"id":152,"nome":"IDM - Internet Download Manager","preco_original":99.90,"preco_oferta":24.90,"descricao":"IDM vitalício. Acelera downloads em 5x!","categorias":["Ferramentas"],"oferta":True,"plataforma":"PC","tipo":"🛠️ Ferramenta","imagem_url":"https://upload.wikimedia.org/wikipedia/commons/e/e8/Internet_Download_Manager_logo.png"},

    # --- Streaming (160-161) ---
    {"id":160,"nome":"Netflix Premium 4K - 30 dias","preco_original":55.90,"preco_oferta":19.90,"descricao":"Netflix Premium 4K Ultra HD por 30 dias. 4 telas simultâneas!","categorias":["Streaming"],"oferta":True,"plataforma":"Multi","tipo":"🎬 Streaming","imagem_url":"https://upload.wikimedia.org/wikipedia/commons/0/08/Netflix_2015_logo.svg"},
    {"id":161,"nome":"Disney+ Premium - 30 dias","preco_original":33.90,"preco_oferta":14.90,"descricao":"Disney+ Premium 4K. Marvel, Star Wars, Pixar, National Geographic.","categorias":["Streaming"],"oferta":True,"plataforma":"Multi","tipo":"🎬 Streaming","imagem_url":"https://upload.wikimedia.org/wikipedia/commons/3/3e/Disney%2B_logo.svg"},

    # --- Musica (165) ---
    {"id":165,"nome":"Spotify Premium - 30 dias","preco_original":21.90,"preco_oferta":9.90,"descricao":"Spotify Premium individual 30 dias. Sem anúncios + offline.","categorias":["Música"],"oferta":True,"plataforma":"Multi","tipo":"🎵 Música","imagem_url":"https://upload.wikimedia.org/wikipedia/commons/8/84/Spotify_icon.svg"},

    # --- Gift Card (168) ---
    {"id":168,"nome":"Steam Gift Card R$ 50","preco_original":50.00,"preco_oferta":42.90,"descricao":"Cartão Steam R$ 50,00. Entrega instantânea.","categorias":["Gift Card"],"oferta":True,"plataforma":"PC","tipo":"🎁 Gift Card","imagem_url":"https://upload.wikimedia.org/wikipedia/commons/8/83/Steam_icon_logo.svg"},

    # --- Cloud (172) ---
    {"id":172,"nome":"Google One 2TB - 1 ano","preco_original":449.90,"preco_oferta":189.90,"descricao":"Google One 2TB por 1 ano. Drive, Gmail, Fotos.","categorias":["Cloud"],"oferta":True,"plataforma":"Multi","tipo":"☁️ Cloud","imagem_url":"https://upload.wikimedia.org/wikipedia/commons/c/c6/Google_One_logo.svg"},

    # --- Cursos (175) ---
    {"id":175,"nome":"Curso Completo Excel Avançado","preco_original":397.00,"preco_oferta":47.90,"descricao":"Curso completo Excel: Básico ao VBA + Dashboards. 80h.","categorias":["Curso","Produtividade"],"oferta":True,"plataforma":"Online","tipo":"🎓 Curso","imagem_url":"https://upload.wikimedia.org/wikipedia/commons/8/83/Microsoft_Excel_2013-2019_logo.svg"},

    # --- Teste (999) ---
    {"id":999,"nome":"🧪 TESTE DO ARI - R$ 1,50","preco_original":1.50,"preco_oferta":1.50,
     "descricao":"✅ Produto de teste para validar o fluxo completo de compra!\n\n➡️ Adicione ao carrinho\n➡️ Finalize com PIX\n➡️ Envie o comprovante\n➡️ Receba o link de download\n\n🎯 Perfeito para testar todo o sistema!",
     "categorias":["Destaques"],"oferta":True,"plataforma":"PC","tipo":"🧪 Teste",
     "imagem_url":"https://cdn.akamai.steamstatic.com/steam/apps/440/header.jpg"},
]

# Helper para adicionar novos produtos
_EXISTING_IDS = {g["id"] for g in GAMES_CATALOG}
_next_new_id = 1000

def _add(nome, tipo, po, porig=None, desc="", plataforma="PC", categorias=None, img="", oferta=False, sku=None):
    global _next_new_id
    while _next_new_id in _EXISTING_IDS:
        _next_new_id += 1
    gid = _next_new_id
    _next_new_id += 1
    if not img:
        # cria produto temporario para descobrir imagem
        tmp = {"id":gid,"nome":nome,"tipo":tipo,"preco_oferta":po,"preco_original":porig if porig else po,
               "descricao":desc,"plataforma":plataforma,"categorias":categorias or [tipo],
               "oferta":bool(oferta),"sku":sku or f"P{gid:04d}"}
        img = _find_image(tmp)
    GAMES_CATALOG.append({
        "id":gid,"sku":sku or f"P{gid:04d}","nome":nome,"tipo":tipo,
        "preco_oferta":float(po),"preco_original":float(porig if porig else po),
        "descricao":desc,"plataforma":plataforma,
        "categorias":categorias or [tipo],
        "imagem_url":img,"oferta":bool(oferta) or (porig is not None and porig > po),
    })

# ============================================================
# 2) PRODUTOS NOVOS (usando imagens reais via _find_image)
# ============================================================

# Windows/Office extras
_add("Windows 11 Enterprise LTSC", "🖥️ Sistema", 29.90, 1999.90,
     "Windows 11 LTSC, sem bloatware, máxima performance.", "PC", ["Sistema Operacional"], oferta=True)

# --- Produtos e Ferramentas Modernas (Adicionados Recentemente) ---
_add("Canva Pro - Assinatura 1 Ano", "🎨 Design", 49.90, 289.90, 
     "Conta Canva Pro exclusiva por 1 ano. Todos os recursos Premium e IA desbloqueados.", "Web/App", ["Design", "Produtividade", "Destaques"], oferta=True)

_add("CapCut Pro - Conta Anual", "🎬 Vídeo", 39.90, 329.90, 
     "CapCut Pro para PC e Celular. Transições, efeitos e IA Premium.", "Multi", ["Edição de Vídeo", "Mobile"], oferta=True)

_add("Notion Plus - 12 Meses", "💼 Produtividade", 34.90, 480.00, 
     "Conta Notion Plus com Notion AI integrado. Otimize sua vida e projetos.", "Multi", ["Produtividade", "Organização"], oferta=True)

_add("FL Studio 21 Signature Bundle", "🎵 Música", 89.90, 1899.90, 
     "O software de produção musical mais popular do mundo. Acesso vitalício.", "PC", ["Áudio", "Produção"], oferta=True)

_add("Midjourney Pro - Acesso Mensal", "🤖 IA - Imagem", 59.90, 300.00, 
     "Gere imagens realistas e incríveis com a melhor IA do mercado (Modo Stealth incluso).", "Discord", ["IA", "Design", "Destaques"], oferta=True)

_add("Chatbot IA Telegram - Código Fonte", "💻 Dev & Código", 149.90, 999.90, 
     "Código fonte completo de um bot de vendas com IA integrada, pronto para rodar e lucrar.", "Código", ["Desenvolvimento", "IA"], oferta=True)

_add("Planilha Mestre de Finanças 2026", "📈 Finanças", 19.90, 97.90, 
     "Controle tudo: ganhos, gastos, investimentos e cripto com dashboards automáticos.", "Excel", ["Finanças", "Organização"], oferta=True)


_add("Windows 10 Home (Ativação Vitalícia)", "🖥️ Sistema", 49.90, 799.90,
     "Licença Windows 10 Home vitalícia.", categorias=["Sistema Operacional"])
_add("Windows Server 2019 Standard", "🖥️ Sistema", 399.90, 3999.90,
     "Windows Server 2019 Standard.", categorias=["Sistema Operacional"])
_add("Microsoft Office 2016 Professional Plus", "📄 Office", 49.90, 999.90,
     "Office 2016 Pro Plus ativação perpétua.", categorias=["Office","Produtividade"])
_add("Microsoft Access + Templates Premium", "📄 Office", 19.90, 99.90,
     "Pack de templates premium para Access.", categorias=["Office","Produtividade"])

# Adobe/Design extras
_add("Adobe InDesign 2024 (Ativado)", "🎨 Design", 149.90, 1799.90,
     "Editoração de revistas, livros e materiais impressos.", categorias=["Design"])
_add("Adobe XD (Ativado)", "🎨 Design", 99.90, 599.90,
     "Design de interfaces e prototipagem UX/UI.", categorias=["Design"])
_add("Adobe Acrobat Pro DC 2024", "🎨 Design", 129.90, 899.90,
     "Edição, criação e assinatura de PDFs.", categorias=["Design","Produtividade"])
_add("Adobe Lightroom Classic 2024", "🎨 Design", 129.90, 899.90,
     "Organização e edição de fotos profissional.", categorias=["Design"])
_add("Figma Pro (conta premium 1 ano)", "🎨 Design", 39.90, 144.0,
     "Figma Pro para design de interfaces.", categorias=["Design"])
_add("Canva Pro 1 ano", "🎨 Design", 24.90, 149.90,
     "Canva Pro com templates, fotos e recursos premium.", categorias=["Design"])
_add("Affinity Designer + Photo + Publisher Pack", "🎨 Design", 49.90, 897.0,
     "Suite Affinity completa alternativa ao Adobe.", categorias=["Design"], oferta=True)

# Video/Edicao extras
_add("Sony VEGAS Pro 21", "🎬 Vídeo", 149.90, 1999.90,
     "Editor de vídeo profissional para Windows.", categorias=["Edição de Vídeo"])
_add("Final Cut Pro X (macOS)", "🎬 Vídeo", 149.90, 1499.90,
     "Editor de vídeo profissional da Apple.", categorias=["Edição de Vídeo"])
_add("Cinema 4D 2024 Studio", "🎬 Vídeo", 249.90, 7999.90,
     "Animação 3D e motion graphics premium.", categorias=["Edição de Vídeo"])
_add("Blender Pro - Pack Assets & Tutoriais", "🎬 Vídeo", 19.90, 199.90,
     "Blender 3D com assets premium e tutoriais.", categorias=["Edição de Vídeo"])
_add("Camtasia Studio 2024", "🎬 Vídeo", 99.90, 899.90,
     "Gravação de tela e edição de vídeo aulas.", categorias=["Edição de Vídeo"])
_add("DaVinci Resolve Studio 19", "🎬 Vídeo", 199.90, 2599.90,
     "Editor de vídeo profissional com correção de cores.", categorias=["Edição de Vídeo"])

# Engenharia extras
_add("MATLAB R2024a Completo + Toolboxes", "🏗️ Engenharia", 249.90, 14999.90,
     "MATLAB com toolboxes de engenharia e simulação.", categorias=["Engenharia"])

# Antivirus extras
_add("Kaspersky Total Security 1 ano", "🔒 Segurança", 34.90, 249.90,
     "Suite total com VPN e controle parental.", categorias=["Antivírus"])
_add("Avast Premium Security 1 ano", "🔒 Segurança", 19.90, 129.90,
     "Proteção contra vírus, ransomware e phishing.", categorias=["Antivírus"])
_add("AVG Ultimate 1 ano", "🔒 Segurança", 19.90, 129.90,
     "Antivírus + otimizador + VPN.", categorias=["Antivírus"])
_add("Malwarebytes Premium 1 ano", "🔒 Segurança", 14.90, 89.90,
     "Detecção de malware e spyware.", categorias=["Antivírus"])
_add("Antivírus + VPN + Otimizador Combo Premium", "🔒 Segurança", 34.90, 399.90,
     "Proteção completa com VPN ilimitada.", categorias=["Antivírus"], oferta=True)

# Ferramentas extras
_add("Nero Platinum Suite 2024", "🛠️ Ferramenta", 29.90, 499.90,
     "Gravação e mídia CD/DVD/Blu-ray.", categorias=["Ferramentas"])
_add("WinUtilities Pro Pack", "🛠️ Ferramenta", 9.90, 49.90,
     "Utilitários de manutenção do Windows.", categorias=["Ferramentas"])
_add("UltraEdit + UltraCompare", "🛠️ Ferramenta", 19.90, 199.90,
     "Editor de texto profissional para programadores.", categorias=["Ferramentas"])
_add("VMware Workstation Pro 17", "🛠️ Ferramenta", 24.90, 799.90,
     "Virtualização de sistemas no PC.", categorias=["Ferramentas"])
_add("Rufus + Hiren's BootCD PE (Pack Manutenção)", "🛠️ Ferramenta", 9.90, 49.90,
     "Manutenção, boot USB e recuperação.", categorias=["Ferramentas"])
_add("WinRAR + WinZip + 7-Zip (Pack Utilitários)", "🛠️ Ferramenta", 9.90, 79.90,
     "Compactadores completos.", categorias=["Ferramentas"])

# Streaming extras
_add("Netflix Premium 4K (3 meses)", "🎬 Streaming", 49.90, 167.70,
     "Netflix Premium 4K por 3 meses.", categorias=["Streaming"], oferta=True)
_add("Disney+ + Star+ Combo Mensal", "🎬 Streaming", 14.90, 45.90,
     "Combo Disney+ e Star+ 30 dias.", categorias=["Streaming"])
_add("Prime Video Mensal", "🎬 Streaming", 9.90, 19.90,
     "Amazon Prime Video 30 dias.", categorias=["Streaming"])
_add("Max (HBO) Mensal", "🎬 Streaming", 12.90, 39.90,
     "HBO Max por 30 dias.", categorias=["Streaming"])
_add("YouTube Premium 3 meses", "🎬 Streaming", 29.90, 59.70,
     "YouTube Premium sem anúncios + YT Music.", categorias=["Streaming"])

# Musica extras
_add("Spotify Premium 3 meses", "🎵 Música", 29.90, 59.70,
     "Spotify sem anúncios por 3 meses.", categorias=["Música"])
_add("Spotify Premium Individual 1 ano", "🎵 Música", 89.90, 238.80,
     "Spotify Premium 12 meses.", categorias=["Música"])

# Gift Cards extras
_add("Google Play R$ 50", "🎁 Gift Card", 44.90, 50.0,
     "Google Play R$50 apps, jogos e assinaturas.", categorias=["Gift Card"])
_add("Google Play R$ 100", "🎁 Gift Card", 89.90, 100.0,
     "Google Play R$100.", categorias=["Gift Card"])
_add("Steam R$ 100 (código)", "🎁 Gift Card", 92.90, 100.0,
     "Crédito Steam R$100.", categorias=["Gift Card"])
_add("Xbox Game Pass Ultimate 3 meses", "🎁 Gift Card", 59.90, 149.90,
     "Game Pass Ultimate PC+Console+Gold 3 meses.", categorias=["Gift Card"], oferta=True)
_add("PlayStation Plus Essential 3 meses", "🎁 Gift Card", 54.90, 129.90,
     "PS Plus Essential multiplayer e jogos mensais.", categorias=["Gift Card"])

# Cloud extras
_add("Google One 100GB 1 ano", "☁️ Cloud", 24.90, 79.90,
     "Google One 100GB por 1 ano.", categorias=["Cloud"])
_add("OneDrive 1TB + Office 365 1 ano", "☁️ Cloud", 39.90, 359.90,
     "OneDrive 1TB + Office 365 por 1 ano.", categorias=["Cloud"], oferta=True)

# Combo
_add("Windows 11 Pro + Office 2021 Combo Vitalício", "💼 Produtividade", 129.90, 2999.0,
     "COMBO Windows 11 Pro + Office 2021 Pro Plus vitalício.",
     categorias=["Produtividade","Sistema Operacional","Office"], oferta=True)

# Jogos extras (para completar)
_JOGOS_EXTRAS = [
    ("Grand Theft Auto V (GTA V)",29.90,99.90,"Ação mundo aberto com GTA Online.",271590),
    ("GTA IV Complete",14.90,59.90,"GTA IV com DLCs completas.",901580),
    ("Cyberpunk 2077 + Phantom Liberty",49.90,249.90,"RPG futurista com expansão Phantom Liberty.",1091500),
    ("Dark Souls III",19.90,129.90,"RPG de ação desafiador.",374380),
    ("Horizon Zero Dawn Complete",29.90,129.90,"RPG pós-apocalíptico com Aloy.",1151640),
    ("Horizon Forbidden West Complete",49.90,249.90,"Jornada de Aloy pelo Oeste Proibido.",2396270),
    ("Days Gone",24.90,199.90,"Sobrevivência zumbi em mundo aberto.",1259420),
    ("Ghost of Tsushima Director's Cut",49.90,249.90,"Samurai no Japão feudal.",2215430),
    ("Death Stranding Director's Cut",29.90,199.90,"Jogo de Kojima pós-apocalíptico.",1850570),
    ("Hogwarts Legacy",49.90,249.90,"RPG mundo aberto Harry Potter.",990080),
    ("Starfield",49.90,299.90,"RPG espacial da Bethesda.",1716740),
    ("Baldur's Gate 3",59.90,249.90,"RPG GOTY D&D.",1086940),
    ("Diablo IV",59.90,299.90,"RPG hack'n'slash.",2344520),
    ("Diablo III Eternal Collection",19.90,149.90,"Diablo III completo.",201270),
    ("Pillars of Eternity Definitive",9.90,79.90,"RPG isométrico da Obsidian.",291650),
    ("Divinity Original Sin 2 Definitive",19.90,129.90,"RPG tático aclamado.",435150),
    ("Skyrim Special Edition",19.90,149.90,"RPG mundo aberto da Bethesda.",489830),
    ("Fallout 4 Game of the Year",14.90,149.90,"RPG pós-apocalíptico em Boston.",377160),
    ("Mortal Kombat 11 Ultimate",19.90,199.90,"MK11 com todos DLCs.",976310),
    ("Street Fighter 6",49.90,249.90,"Luta nova geração.",1364780),
    ("Tekken 8",49.90,299.90,"Luta 3D Unreal Engine 5.",1778820),
    ("Tekken 7",14.90,129.90,"Luta 3D com personagens convidados.",389730),
    ("Guilty Gear Strive",24.90,149.90,"Anime fighting game da Arc System Works.",1384160),
    ("Resident Evil Village",29.90,199.90,"Terror com Lady Dimitrescu.",1196590),
    ("Resident Evil 3 Remake",14.90,129.90,"Remake com fuga de Jill Valentine.",952060),
    ("Silent Hill 2 Remake",49.90,249.90,"Terror psicológico refeito.",2124490),
    ("Alan Wake 2",44.90,249.90,"Terror psicológico premiado.",1087410),
    ("Metro Exodus Gold",14.90,149.90,"FPS pós-apocalíptico na Rússia.",412020),
    ("DOOM Eternal",19.90,199.90,"FPS rápido e violento.",782330),
    ("Assassin's Creed Valhalla",29.90,249.90,"Vikings na Inglaterra medieval.",2208920),
    ("Assassin's Creed Mirage",39.90,199.90,"Retorno às raízes furtivas em Bagdá.",2307370),
    ("Assassin's Creed Odyssey",19.90,199.90,"Aventura na Grécia Antiga.",812140),
    ("Assassin's Creed Origins",19.90,199.90,"Origens da irmandade no Egito.",582160),
    ("Assassin's Creed Unity",9.90,99.90,"Paris na Revolução Francesa.",289650),
    ("Assassin's Creed IV Black Flag",14.90,99.90,"Piratas no Caribe, batalhas navais épicas.",242050),
    ("Far Cry 6",29.90,249.90,"Revolução em Yara.",2369390),
    ("Far Cry 5",14.90,199.90,"Seita apocalíptica em Montana.",552520),
    ("Batman Arkham Knight",14.90,99.90,"Cavaleiro das Trevas em Gotham.",208650),
    ("Marvel's Guardians of the Galaxy",24.90,199.90,"Aventura dos Guardiões da Galáxia.",637620),
    ("Need for Speed Payback",9.90,149.90,"Corrida arcade de vingança.",1262560),
    ("Crew Motorfest",39.90,249.90,"Festival de corrida no Havaí.",3034840),
    ("DiRT Rally 2.0",14.90,149.90,"Rali off-road realista.",690790),
    ("Call of Duty Modern Warfare III",59.90,299.90,"FPS campanha + multiplayer.",2519060),
    ("Call of Duty Modern Warfare II",39.90,249.90,"FPS reboot da série MW.",1938090),
    ("Call of Duty Black Ops Cold War",29.90,249.90,"FPS na Guerra Fria.",1985820),
    ("Battlefield 2042",24.90,299.90,"FPS multiplayer 128 jogadores.",1517290),
    ("Battlefield V",14.90,199.90,"FPS Segunda Guerra Mundial.",1238810),
    ("Battlefield 1",14.90,149.90,"FPS Primeira Guerra Mundial.",1238840),
    ("CS2 Prime",14.90,0,"Status Prime no Counter-Strike 2.",730),
    ("Valorant (conta com skins)",24.90,0,"Conta Valorant com skins.",0),
    ("PUBG Plus",9.90,0,"Acesso Plus ao PUBG.",578080),
    ("Stardew Valley",9.90,19.90,"Simulação de fazenda.",413150),
    ("Minecraft Java + Bedrock",29.90,99.90,"Conta completa Minecraft PC.",0),
    ("Terraria",9.90,19.90,"Sandbox 2D.",105600),
    ("Hollow Knight",9.90,29.90,"Metroidvania atmosférico.",367520),
    ("Hades",14.90,79.90,"Roguelike mitologia grega.",1145360),
    ("Celeste",9.90,39.90,"Plataforma premiada.",504230),
    ("Cuphead",19.90,59.90,"Run and gun animação anos 30.",268910),
    ("Among Us",4.90,9.90,"Jogo social de traidores.",945360),
    ("Factorio",29.90,59.90,"Automação de fábricas.",427520),
    ("RimWorld",29.90,59.90,"Simulador de colônia.",294100),
    ("Valheim",14.90,39.90,"Sobrevivência viking.",892970),
    ("God of War Ragnarok",69.90,299.90,"Sequência nórdica do Kratos.",2322010),
    ("EA Sports FC 24 (FIFA)",49.90,299.90,"Futebol EA Sports FC.",2195250),
    ("NBA 2K24",44.90,299.90,"Basquete com carreira e MyTeam.",2338770),
    ("Madden NFL 24",44.90,299.90,"Futebol Americano oficial NFL.",2302380),
    ("UFC 5",39.90,249.90,"MMA oficial do UFC.",2177030),
    ("WWE 2K24",34.90,249.90,"Luta livre WWE.",2314630),
]
for nome, po, porig, desc, appid in _JOGOS_EXTRAS:
    # evita duplica
    if any(nome.lower() in g["nome"].lower() or g["nome"].lower() in nome.lower() for g in GAMES_CATALOG if g.get("tipo") == "🎮 Jogo"):
        continue
    img = _IMG_STEAM.format(appid=appid) if appid else "https://cdn-icons-png.flaticon.com/512/686/686589.png"
    # ajusta logos que não são steam
    if "Minecraft" in nome: img = "https://upload.wikimedia.org/wikipedia/commons/6/68/Minecraft_2024.png"
    if "Valorant" in nome: img = "https://upload.wikimedia.org/wikipedia/commons/f/fc/Valorant_logo_-_pink_color_version.svg"
    _add(nome, "🎮 Jogo", po, porig, desc, categorias=["Ação","Aventura"], img=img)

# Cursos importacao
IMP = [
    ("IMP001","Academia do Importador",19.97,99.97,"Técnicas de importação internacional, fornecedores, negociação e logística."),
    ("IMP002","Como Importar da China",14.97,69.97,"Compras internacionais da China e redução de custos."),
    ("IMP003","Como Importar Roupas",19.97,79.97,"Estratégias para importar roupas com foco em fornecedores."),
    ("IMP004","Dropshipping",24.97,99.97,"Modelo dropshipping, loja virtual e escalabilidade."),
    ("IMP005","Dropshipping - Vídeos de Instrução",14.97,69.97,"Vídeos práticos passo a passo para dropshipping."),
    ("IMP006","Empreendedor de Sucesso - Dropshipping Nacional",29.97,119.97,"Fornecedores nacionais, dropshipping local no Brasil."),
    ("IMP007","Fórmula da Importação",19.97,89.97,"Método prático para iniciar importação."),
    ("IMP008","Importação Legal",19.97,74.97,"Aspectos legais, fiscais e tributários da importação."),
    ("IMP009","Importador Profissional",29.97,149.97,"Treinamento avançado de importação."),
    ("IMP010","Importando com Sucesso",19.97,89.97,"Importação segura, econômica e lucrativa."),
    ("IMP011","Segredos Sobre Importação 2.0",29.97,129.97,"Técnicas avançadas de importação."),
    ("IMP012","Todos os Segredos da Importação (Pack Completo)",34.97,179.97,"Compilado completo de importação."),
]
for sku, nome, po, porig, desc in IMP:
    _add(nome, "🎓 Curso", po, porig, f"[{sku}] {desc}",
         plataforma="Online", categorias=["🎓 Cursos","💼 Importação"], sku=sku)

_add("Como Vender no Facebook Sem Investir Nem R$0,01", "🎓 Curso", 29.90, 199.90,
     "[FB001] Venda no Facebook sem anúncios. 6 aulas + 2 PDFs + 3 palestras bônus.",
     plataforma="Online", categorias=["🎓 Cursos","📣 Marketing Digital"], sku="FB001")

F = [
    ("F39","Aula 12 - DECEA: Como Acessar o Portal",9.90,"✈️ Aviação (DECEA)"),
    ("F40","Aula 13 - DECEA: Como Solicitar Autorização de Voo",9.90,"✈️ Aviação (DECEA)"),
    ("F41","Edição de Fotos - Aula 01: Ferramentas do Photoshop CS6",9.90,"🎨 Edição de Fotos"),
    ("F42","Edição de Fotos - Aula 02: Filtros",9.90,"🎨 Edição de Fotos"),
    ("F43","Edição de Fotos - Aula 03: Adicionando Filtros",9.90,"🎨 Edição de Fotos"),
    ("F44","Edição de Vídeo - Adobe Premiere: Apresentação",9.90,"🎬 Edição de Vídeo"),
    ("F45","Edição de Vídeo - Adobe Premiere: Edição Básica",9.90,"🎬 Edição de Vídeo"),
    ("F46","Edição de Vídeo - Adobe Premiere: Inserindo Textos",9.90,"🎬 Edição de Vídeo"),
]
for sku, nome, po, cat in F:
    _add(nome, "🎓 Curso", po, None, f"[{sku}] Aula digital em vídeo com conteúdo prático.",
         plataforma="Online", categorias=["🎓 Cursos", cat], sku=sku)

_add("Pack DECEA Completo (Aulas 12 e 13)", "🎓 Curso", 14.90, 19.80,
     "Pack com duas aulas DECEA: portal + autorização de voo.",
     plataforma="Online", categorias=["🎓 Cursos","✈️ Aviação (DECEA)"], oferta=True)
_add("Pack Photoshop: Do Básico aos Filtros (F41-F43)", "🎓 Curso", 24.90, 29.70,
     "3 aulas de Photoshop CS6: ferramentas, filtros e prática.",
     plataforma="Online", categorias=["🎓 Cursos","🎨 Edição de Fotos"], oferta=True)
_add("Pack Adobe Premiere Primeiros Passos (F44-F46)", "🎓 Curso", 24.90, 29.70,
     "3 aulas de Premiere: apresentação, edição e textos.",
     plataforma="Online", categorias=["🎓 Cursos","🎬 Edição de Vídeo"], oferta=True)

# Cursos extras
_cursos_extra = [
    ("Curso de Tráfego Pago Completo (Google + Meta)",39.90,299.90,"Tráfego pago Google Ads + Facebook/Instagram Ads.",["🎓 Cursos","📣 Marketing Digital"]),
    ("Curso de Instagram para Negócios",19.90,99.90,"Cresça e venda no Instagram com estratégias orgânicas.",["🎓 Cursos","📣 Marketing Digital"]),
    ("Curso de TikTok Marketing Viral",19.90,99.90,"Viralização no TikTok e captação de clientes.",["🎓 Cursos","📣 Marketing Digital"]),
    ("Curso de YouTube para Iniciantes",24.90,199.90,"Criação de canal, SEO e monetização.",["🎓 Cursos","📣 Marketing Digital"]),
    ("Curso de Copywriting Profissional",29.90,199.90,"Textos que vendem: cartas, anúncios e emails.",["🎓 Cursos","📣 Marketing Digital"]),
    ("Curso de Afiliados Hotmart/Monetizze",24.90,199.90,"Marketing de afiliados à primeira venda.",["🎓 Cursos","💼 Negócios"]),
    ("Curso de Edição de Vídeo para Criadores (Premiere + CapCut)",29.90,199.90,"Edição profissional para redes sociais.",["🎓 Cursos","🎬 Edição de Vídeo"]),
    ("Curso de Photoshop para Redes Sociais",19.90,99.90,"Posts e thumbnails no Photoshop.",["🎓 Cursos","🎨 Edição de Fotos"]),
    ("Curso de Python do Zero ao Avançado",29.90,199.90,"Programação Python do básico a projetos.",["🎓 Cursos"]),
    ("Curso de Inglês Fluente em 6 Meses",34.90,299.90,"Método prático de fluência em inglês.",["🎓 Cursos"]),
    ("Método Investidor Iniciante (Bolsa + Cripto)",39.90,499.90,"Ações, FIIs e criptomoedas.",["🎓 Cursos","💰 Finanças"]),
]
for nome, po, porig, desc, cats in _cursos_extra:
    _add(nome,"🎓 Curso",po,porig,desc,plataforma="Online",categorias=cats)

# IA Ferramentas
IA_TOOLS = [
    ("VEO 3 (Flow)","🤖 IA - Vídeo","Gerador de vídeo Flow/VEO 3."),
    ("Sora Pro","🤖 IA - Vídeo","Geração de vídeo da OpenAI."),
    ("Kling AI","🤖 IA - Vídeo","IA de vídeo Kuaishou."),
    ("Pika Labs 3.0","🤖 IA - Vídeo","Geração de vídeo por texto/imagem."),
    ("Runway Gen-3 Alpha","🤖 IA - Vídeo","Edição de vídeo com IA cinematográfica."),
    ("HeyGen Pro","🤖 IA - Vídeo","Avatares IA com fala realista."),
    ("Digen AI","🤖 IA - Vídeo","Avatares e troca de rosto."),
    ("ChatGPT 5.2 Plus","🤖 IA - Texto","ChatGPT 5.2 Plus."),
    ("ChatGPT 5.1 Plus","🤖 IA - Texto","ChatGPT 5.1 Plus."),
    ("ChatGPT 4o","🤖 IA - Texto","ChatGPT 4o multimodal."),
    ("ChatGPT o1","🤖 IA - Texto","Modelo de raciocínio profundo."),
    ("Claude 3 Opus","🤖 IA - Texto","Anthropic Opus para tarefas complexas."),
    ("Claude 3.5 Sonnet","🤖 IA - Texto","Velocidade + qualidade."),
    ("Gemini Advanced","🤖 IA - Texto","IA Google com busca integrada."),
    ("Grok 3 (X AI)","🤖 IA - Texto","IA do X com informações em tempo real."),
    ("Perplexity AI Pro","🤖 IA - Pesquisa","Motor de busca IA com citações."),
    ("Perplexity Sonar Pro","🤖 IA - Pesquisa","Pesquisa em tempo real."),
    ("Midjourney v6 Pro","🤖 IA - Imagem","Gerador artístico de imagens."),
    ("Leonardo AI Pro","🤖 IA - Imagem","Geração de imagens e assets."),
    ("DALL-E 3 Plus","🤖 IA - Imagem","IA de imagem da OpenAI."),
    ("Stable Diffusion 3 Pro","🤖 IA - Imagem","Imagens open-source Pro."),
    ("Flux Pro","🤖 IA - Imagem","Black Forest Labs state-of-art."),
    ("ElevenLabs Pro","🤖 IA - Áudio","Clonagem de voz ultra-realista."),
    ("Murf AI Pro","🤖 IA - Áudio","Vozes para narração."),
    ("Suno v3 Premium","🤖 IA - Áudio","Músicas completas por IA com vocais."),
    ("Udio Premium","🤖 IA - Áudio","Músicas de alta qualidade."),
    ("NotebookLM Plus (Google)","🤖 IA - Produtividade","Notebook IA conversa com documentos."),
    ("Notion AI Plus","🤖 IA - Produtividade","IA no Notion para escrita."),
    ("Canva Magic Studio","🤖 IA - Produtividade","Suite IA no Canva."),
    ("Grammarly Premium","🤖 IA - Produtividade","Correção de escrita EN/PT."),
    ("Jasper AI","🤖 IA - Marketing","Criação de conteúdo marketing em escala."),
    ("Surfer SEO","🤖 IA - Marketing","SEO e otimização de artigos."),
    ("GitHub Copilot Pro","🤖 IA - Código","Assistente de programação."),
    ("Cursor Pro","🤖 IA - Código","Editor com IA nativa para devs."),
]
for nome, tipo, desc in IA_TOOLS:
    _add(f"{nome} - Acesso Premium", tipo, 19.90, 149.90,
         f"[IA Knights] {desc} Acesso premium via membros IA Knights.",
         plataforma="Digital", categorias=["🤖 Inteligência Artificial", tipo])

IA_SPY = [
    ("AdSpy Premium",24.90,"Espionagem anúncios Facebook/Instagram."),
    ("AdHeart",19.90,"Biblioteca de anúncios multi-plataforma."),
    ("Similarweb Pro",29.90,"Análise de tráfego de websites."),
    ("Ahrefs Webmaster Premium",39.90,"SEO e backlinks."),
    ("SEMrush Pro",39.90,"Suite marketing digital e SEO."),
    ("Ubersuggest Premium",14.90,"SEO e palavras-chave."),
    ("VidIQ Boost",14.90,"SEO e crescimento YouTube."),
    ("TubeBuddy Legend",14.90,"Crescimento YouTube."),
    ("Chatbase Premium (Chatbot próprio)",19.90,"Crie chatbots treinados em seus dados."),
    ("Zapier Premium 1 ano",29.90,"Automação entre milhares de apps."),
    ("Make/Integromat Premium",24.90,"Automação avançada de fluxos."),
]
for nome, po, desc in IA_SPY:
    _add(nome,"🤖 IA - Ferramenta",po,po*4,f"[IA Knights] {desc}",
         plataforma="Digital", categorias=["🤖 Inteligência Artificial","🕵️ Espionagem/Análise"], oferta=True)

_add("IA Knights - Plano Mensal","🤖 IA Plano",47.00,97.00,
     "Acesso 30 dias a todas as 82 ferramentas do portal IA Knights.",
     plataforma="Digital",categorias=["🤖 Inteligência Artificial","🏆 Planos IA Knights"],oferta=True,sku="IAK-M")
_add("IA Knights - Plano Trimestral","🤖 IA Plano",97.00,291.00,
     "Acesso 90 dias a todas ferramentas IA.",
     plataforma="Digital",categorias=["🤖 Inteligência Artificial","🏆 Planos IA Knights"],oferta=True,sku="IAK-T")
_add("IA Knights - Plano Vitalício","🤖 IA Plano",197.00,997.00,
     "Acesso VITALÍCIO a todas ferramentas IA.",
     plataforma="Digital",categorias=["🤖 Inteligência Artificial","🏆 Planos IA Knights"],oferta=True,sku="IAK-L")
_add("Pack IA Premium (ChatGPT-5 + Claude + Gemini + Midjourney)","🤖 IA Plano",39.90,599.90,
     "Combo das principais IAs em um pacote.",
     plataforma="Digital",categorias=["🤖 Inteligência Artificial"],oferta=True)
_add("Pack IA Criador (Suno + ElevenLabs + HeyGen + Pika)","🤖 IA Plano",34.90,399.90,
     "IA para criadores: músicas, voz, avatares e vídeo.",
     plataforma="Digital",categorias=["🤖 Inteligência Artificial"],oferta=True)

# ============================================================
# Garante SKU em todos os produtos antigos
# ============================================================
for g in GAMES_CATALOG:
    if not g.get("sku"):
        g["sku"] = f"P{g['id']:04d}"

# ============================================================
# Índices
# ============================================================
TIPOS = {}
CATEGORIAS = {}
for g in GAMES_CATALOG:
    TIPOS.setdefault(g.get("tipo","🎁 Outros"),[]).append(g)
    for c in g.get("categorias",[]):
        CATEGORIAS.setdefault(c,[]).append(g)

# ============================================================
# API pública
# ============================================================
def get_game_by_id(game_id):
    for g in GAMES_CATALOG:
        if g["id"] == game_id:
            return g
    return None

def get_game_by_sku(sku):
    for g in GAMES_CATALOG:
        if g.get("sku") == sku:
            return g
    return None

def search_games(query):
    if not query: return []
    q = query.lower().strip()
    out = []
    for g in GAMES_CATALOG:
        if (q in g["nome"].lower()
            or q in (g.get("descricao") or "").lower()
            or q in g.get("tipo","").lower()
            or any(q in c.lower() for c in g.get("categorias",[]))
            or (g.get("sku") and q in g["sku"].lower())):
            out.append(g)
    return out

def get_offers():
    return [g for g in GAMES_CATALOG if g.get("oferta",False)]

def games_by_categoria(categoria):
    return [g for g in GAMES_CATALOG if categoria in g.get("categorias",[])]

def games_by_tipo(tipo):
    return TIPOS.get(tipo,[])

def get_games_by_category(category):
    return games_by_categoria(category)

def get_total_produtos():
    return len(GAMES_CATALOG)

def get_total_ofertas():
    return len(get_offers())

print(f"[catalog.py] ✅ Catálogo MESTRE carregado: {len(GAMES_CATALOG)} produtos "
      f"em {len(TIPOS)} tipos / {len(CATEGORIAS)} categorias.")

if __name__ == "__main__":
    from collections import Counter
    cont = Counter(g["tipo"] for g in GAMES_CATALOG)
    for t, q in sorted(cont.items(), key=lambda x:-x[1]):
        print(f"  - {t}: {q}")
    print(f"\n🔥 Ofertas ativas: {len(get_offers())}")
    # Verifica produtos sem imagem (segurança)
    sem_img = [g for g in GAMES_CATALOG if "placehold.co" in (g.get("imagem_url") or "")]
    print(f"⚠️  Produtos com placeholder (precisam de imagem real): {len(sem_img)}")
    if sem_img:
        for s in sem_img[:5]:
            print(f"     - {s['nome']}")
