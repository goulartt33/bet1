# Sistema de Apostas com Análise API Sportradar e Telegram

Analisa jogos de futebol via Sportradar API, gera bilhetes com odds >=2.0 e alta probabilidade (>60%), e envia para Telegram. Suporte a múltiplos markets (3-way e Over 2.5).

## Aviso
Simulação educacional. Apostas envolvem risco; sem garantias. Registre-se para trial gratuito em https://developer.sportradar.com/.

## Melhorias
- Integração com Sportradar (fixtures, probabilities, odds).
- Filtro por competições via URNs (ex: Premier = sr:competition:17).
- Odds médias de bookmakers.
- Tratamento de erros e loading no frontend.

## Requisitos
- Python 3.8+
- API_KEY (Sportradar trial)
- TELEGRAM_TOKEN e CHAT_ID

## Instalação
1. Clone: `git clone https://github.com/goulartt33/bet.git`
2. Deps: `pip install -r requirements.txt`
3. Configure .env (use URNs para ligas: Premier sr:competition:17, Serie A sr:competition:23, La Liga sr:competition:8, Bundesliga sr:competition:35, Ligue 1 sr:competition:34)
4. Rode: `python app.py`
5. Acesse: http://127.0.0.1:5000/

## Deploy no Render
- Web Service, Python, Build: `pip install -r requirements.txt`, Start: `gunicorn app:app`
- Adicione env vars no dashboard.

Autor: goulartt33
Licença: MIT