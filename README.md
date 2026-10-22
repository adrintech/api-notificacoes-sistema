# 🥤 Fruki Engine - Sistema Inteligente de Recomendações e Notificações

Sistema backend desenvolvido em **Django REST Framework** integrado ao **Supabase (PostgreSQL)**, projetado para automatizar e otimizar o mix de produtos oferecidos a estabelecimentos parceiros da Fruki. O motor cruza dados cadastrais dos clientes, histórico de giro e fatores externos em tempo real — como **condições meteorológicas (Open-Meteo)** e **calendário de feriados nacionais (Nager.Date)** — para gerar recomendações altamente assertivas e direcionadas via canais como WhatsApp (*Pede Fruki*) e o aplicativo do vendedor.

---

## 🚀 Arquitetura e Principais Funcionalidades

1. **Motor de Scoring Baseado em Regras (*Rule-Based Scoring*):**
   - Atribui pesos de relevância por segmento (Supermercados, Postos de Conveniência, Atacados, Restaurantes).
   - Aplica bônus sazonais dinâmicos (ex: picos de temperatura acima de 24°C impulsionam a demanda por águas, citrus e refrigerantes gelados).
   - Considera feriados nacionais para sugerir o adiantamento de pedidos e reposição de estoque.

2. **Integração com APIs Externas (Zero Cost / Sem API Key):**
   - **Clima:** Consulta em tempo real a temperatura de Porto Alegre/RS via [Open-Meteo API](https://open-meteo.com/).
   - **Calendário:** Verifica datas comemorativas e feriados nacionais via [Nager.Date API](https://date.nager.at/).

3. **Banco de Dados Relacional (Supabase):**
   - Conexão nativa com PostgreSQL para leitura da base de clientes e isolamento de testes através de tabelas espelho (`notificacao_teste`).

4. **Dashboard de Observabilidade e Auditoria:**
   - Interface web moderna integrada para visualização do motor em ação, permitindo auditar o sorteio randômico de estabelecimentos da base de dados e os scores calculados.

---

## 🛠️ Tecnologias Utilizadas

- **Python 3.12** & **Django / Django REST Framework**
- **Supabase (PostgreSQL)** para persistência e gestão dos dados de clientes e ERP
- **Requests** para consumo das APIs REST externas de clima e feriados
- **HTML5 / CSS3 (Flexbox & CSS Grid)** para o painel executivo de auditoria

---

## ⚙️ Como Executar o Projeto Localmente

1. **Clone o repositório e ative o ambiente virtual:**
   ```bash
   git clone [https://github.com/adrintech/api-notificacoes-sistema.git](https://github.com/adrintech/api-notificacoes-sistema.git)
   cd api-notificacoes-sistema
   python -m venv .venv
   source .venv/bin/activate
