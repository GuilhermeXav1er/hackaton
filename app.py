import streamlit as st
import google.generativeai as genai
import json
import os
from dotenv import load_dotenv

import simulador_carteira

# --- 1. CONFIGURAÇÃO INICIAL ---

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

st.set_page_config(page_title="BTG Pactual - Agente Gemini", layout="wide")
st.title("🤖 Agente de Investimentos BTG")
st.caption("Converse para consultar sua carteira ou realizar um investimento.")

# --- 2. DEFINIÇÃO DAS FERRAMENTAS (NO FORMATO DE DICIONÁRIO) ---

funcoes_disponiveis = {
    "consultar_carteira": simulador_carteira.consultar_carteira,
    "comprar_ativo": simulador_carteira.comprar_ativo,
}

# MUDANÇA CRÍTICA: Em vez de usar classes como 'Tool' e 'FunctionDeclaration',
# agora definimos as ferramentas como uma lista de dicionários.
ferramentas_para_ia = [
    {
        "function_declarations": [
            {
                "name": "consultar_carteira",
                "description": "Obtém a carteira de investimentos e o saldo em conta do cliente."
            },
            {
                "name": "comprar_ativo",
                "description": "Executa a compra de um ativo financeiro para o cliente.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticker": {"type": "string", "description": "O código (ticker) EXATO do ativo a ser comprado."},
                        "valor": {"type": "number", "description": "O montante financeiro em reais a ser investido."}
                    },
                    "required": ["ticker", "valor"]
                }
            }
        ]
    }
]

# --- 3. GERENCIAMENTO DA CONVERSA ---

CATALOGO_DE_PRODUTOS = """
- Ticker: CDB_BTG_DI, Descrição: CDB Pós-Fixado BTG 105% CDI. Ideal para reserva de emergência.
- Ticker: LCI_BTG_360, Descrição: LCI BTG 1 ano 98% CDI. Isento de Imposto de Renda, para metas de curto prazo.
- Ticker: TESOURO_SELIC_2029, Descrição: Tesouro Selic 2029. O investimento mais seguro do país.
- Ticker: FUNDO_ACOES_BTG_ABSOLUTO, Descrição: Fundo de Ações BTG Pactual Absoluto. Para investidores arrojados.
"""

PROMPT_SISTEMA = f"""Você é um assistente virtual do banco BTG Pactual. Sua personalidade é profissional, eficiente e segura. 
Sua principal função é ajudar clientes a consultar suas carteiras e a realizar investimentos de forma transacional.

REGRAS RÍGIDAS:
1.  Você SÓ PODE oferecer e operar os produtos do catálogo abaixo. Use o Ticker exato fornecido.
2.  Se o cliente pedir um produto que não está na lista, informe educadamente que o ativo não está disponível e sugira uma alternativa do catálogo.
3.  Para executar uma compra, você OBRIGATORIAMENTE precisa do ticker e do valor. Se o cliente não fornecer, faça perguntas para obter as informações.

CATÁLOGO DE PRODUTOS DISPONÍVEIS:
{CATALOGO_DE_PRODUTOS}
"""

# A inicialização do modelo agora passa a lista de dicionários diretamente
model = genai.GenerativeModel(
    model_name="gemini-pro-latest",
    system_instruction=PROMPT_SISTEMA,
    tools=ferramentas_para_ia
)

if 'chat' not in st.session_state:
    st.session_state.chat = model.start_chat(history=[])

# --- 4. LÓGICA PRINCIPAL DO AGENTE ---

def executar_agente(prompt_usuario):
    try:
        response = st.session_state.chat.send_message(prompt_usuario)
        function_call = response.candidates[0].content.parts[0].function_call

        if function_call.name:
            function_name = function_call.name
            function_args = function_call.args
            args_dict = {key: value for key, value in function_args.items()}
            
            function_to_call = funcoes_disponiveis[function_name]
            function_response_str = function_to_call(**args_dict)
            
            # Enviando a resposta da função de volta para o modelo
            response = st.session_state.chat.send_message(
                genai.protos.Part(
                    function_response=genai.protos.FunctionResponse(
                        name=function_name,
                        response={"result": function_response_str}
                    )
                )
            )
        return response.text
    except Exception as e:
        st.error(f"Ocorreu um erro: {e}")
        return "Desculpe, não consegui processar sua solicitação no momento."

# --- 5. INTERFACE GRÁFICA ---

for message in st.session_state.chat.history:
    role = "assistant" if message.role == "model" else message.role
    if all(part.text for part in message.parts):
        with st.chat_message(role):
            st.markdown(message.parts[0].text)

prompt_usuario = st.chat_input("Qual operação deseja realizar?")

if prompt_usuario:
    if st.session_state.get('last_prompt') != prompt_usuario:
        st.session_state['last_prompt'] = prompt_usuario
        with st.chat_message("user"):
            st.markdown(prompt_usuario)
        
        with st.chat_message("assistant"):
            with st.spinner("Processando..."):
                resposta_ia = executar_agente(prompt_usuario)
                st.markdown(resposta_ia)