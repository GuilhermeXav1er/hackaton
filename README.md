# 🤖 Agente de Investimentos BTG - Hackathon BTG Pactual

_Um assistente multimodal para transações e consultoria de investimentos, desenvolvido em 24 horas._

## 📜 Descrição

Este projeto é um protótipo funcional de um agente de IA conversacional, construído com a API do Google Gemini e Streamlit. O agente simula um assistente de investimentos do BTG Pactual, capaz de guiar o cliente desde a definição do seu perfil de investidor (suitability) até a execução de ordens de compra e venda, aceitando comandos por texto e por áudio.

## ✨ Principais Funcionalidades

-   **Ciclo de Suitability Completo:** O agente identifica se o cliente não possui um perfil de investidor e aplica um questionário para defini-lo como Conservador, Moderado ou Arrojado.
-   **Recomendação Personalizada:** Com base no perfil definido, o agente sugere produtos de investimento adequados, buscando informações de catálogos de Renda Fixa, Fundos, Renda Variável e Criptomoedas.
-   **Transações Simuladas:** Executa ordens de compra e venda, consolidando as posições na carteira do cliente e atualizando o saldo em conta.
-   **Consulta de Carteira:** Permite ao cliente visualizar sua posição consolidada e saldo a qualquer momento.
-   **Interface Multimodal:** Aceita comandos tanto por texto, através de um chat, quanto por voz, através do upload de arquivos de áudio.

## 🛠️ Tecnologias Utilizadas

-   **Linguagem:** Python 3.10+
-   **Framework de Interface:** Streamlit
-   **Modelo de IA:** Google Gemini (via `google-generativeai`)
-   **Simulação de Banco de Dados:** Arquivos JSON

## 🚀 Setup e Instalação

Siga os passos abaixo para executar o projeto em sua máquina local.

#### 1. Pré-requisitos
-   Python 3.10 ou superior
-   Um editor de código (ex: VS Code)
-   Git (opcional)

#### 2. Crie os Arquivos de Catálogo
Certifique-se de que os seguintes arquivos JSON estão na pasta raiz do projeto com o conteúdo que vocês desenvolveram:
-   `catalogo_final.json` (com a lista de ações)
-   `catalogo_cripto.json` (com a lista de criptomoedas)

#### 3. Crie um Ambiente Virtual
É uma boa prática isolar as dependências do projeto. No terminal, dentro da pasta do projeto, execute:
```bash
# Criar o ambiente virtual
python -m venv venv

# Ativar o ambiente virtual
# No Windows:
.\venv\Scripts\activate
# No macOS/Linux:
source venv/bin/activate
