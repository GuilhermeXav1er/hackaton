import streamlit as st
import google.generativeai as genai
import json
import os
from dotenv import load_dotenv

import simulador_carteira

# --- 1. CONFIGURAÇÃO INICIAL ---
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

st.set_page_config(page_title="BTG Pactual - Agente Multimodal", layout="wide")
st.title("🤖 Agente de Investimentos BTG")
st.caption("Converse para consultar sua carteira ou realizar um investimento.")

# --- 2. DEFINIÇÃO DAS FERRAMENTAS ---

funcoes_disponiveis = {
    "consultar_carteira": simulador_carteira.consultar_carteira,
    "comprar_ativo": simulador_carteira.comprar_ativo,
    "vender_ativo": simulador_carteira.vender_ativo, # <-- 1. ADICIONADO AQUI
}

ferramentas_para_ia = [
    {
        "function_declarations": [
            {
                "name": "consultar_carteira",
                "description": "Obtém a carteira de investimentos e o saldo em conta do cliente."
            },
    {
                "name": "comprar_ativo",
                "description": (
                    "Executa a compra de um ativo financeiro para o cliente. "
                    "Pode ser feito de duas formas: "
                    "1) especificando o valor total em reais a investir, "
                    "2) especificando a quantidade de unidades (ações, cotas, moedas). "
                    "Exemplo: {\"ticker\": \"ITUB4\", \"quantidade\": 10} ou {\"ticker\": \"VALE3\", \"valor\": 500}"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticker": {"type": "string", "description": "O ticker do ativo (ex: PETR4, VALE3)."},
                        "valor": {"type": "number", "description": "Valor em reais a ser investido."},
                        "quantidade": {"type": "integer", "description": "Quantidade de unidades a serem compradas."}
                    },
                    "required": ["ticker"]
                }
            },
            {
                "name": "vender_ativo",
                "description": "Executa a venda ou resgate de um ativo financeiro que o cliente possui em carteira.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticker": {"type": "string", "description": "O código (ticker) EXATO do ativo a ser vendido."},
                        "valor": {"type": "number", "description": "O montante financeiro em reais a ser resgatado/vendido."}
                    },
                    "required": ["ticker", "valor"]
                }
            }
        ]
    }
]

# --- 3. GERENCIAMENTO DA CONVERSA ---
# (O resto do arquivo continua exatamente igual)

with open("catalogo_final.json", "r", encoding="utf-8") as f:
    ativos = json.load(f)

CATALOGO_DE_PRODUTOS = {
    "renda_fixa": [
        {"ticker": "CDB_BTG_DI", "descricao": "CDB Pós-Fixado BTG 105% CDI. Ideal para reserva de emergência."},
        {"ticker": "LCI_BTG_360", "descricao": "LCI BTG 1 ano 98% CDI. Isento de IR, para metas de curto prazo."},
        {"ticker": "TESOURO_SELIC_2029", "descricao": "Tesouro Selic 2029. O investimento mais seguro do país."}
    ],
    "fundos": [
        {"ticker": "FUNDO_RF_BTG", "descricao": "Fundo de Renda Fixa BTG. Focado em títulos públicos e CDBs."},
        {"ticker": "FUNDO_MM_BTG", "descricao": "Fundo Multimercado BTG. Mistura renda fixa, ações e câmbio."},
        {"ticker": "FUNDO_ACOES_BTG_ABSOLUTO", "descricao": "Fundo de Ações BTG Pactual Absoluto. Para investidores arrojados."}
    ],
    "renda_variavel": ativos
}

PROMPT_SISTEMA = f"""Você é um assistente virtual do banco BTG Pactual. Sua personalidade é profissional, eficiente e segura. 
Sua principal função é ajudar clientes a consultar suas carteiras e a realizar investimentos de forma transacional.

REGRAS RÍGIDAS:
1.  Você SÓ PODE oferecer e operar os produtos do catálogo abaixo. Use o Ticker exato fornecido.
2.  Se o cliente pedir um produto que não está na lista, informe educadamente que o ativo não está disponível e sugira uma alternativa do catálogo.
3.  Para executar uma compra de Fundo ou de Renda Fixa, você OBRIGATORIAMENTE precisa do ticker e do valor. Se o cliente não fornecer, faça perguntas para obter as informações.
4.  Para executar uma compra de Renda Variavel, você OBRIGATORIAMENTE precisa do ticker e da quantidade de ações. Se o cliente não fornecer, faça perguntas para obter as informações.
5.  Sempre antes de concluir uma transação, confirme o produto e o valor e só efetue se o cliente aprovar.
6.  Não permita que o cliente venda todos os seus ativos de uma vez. Ele pode vender tudo, mas deve ser um ativo por vez.

CATÁLOGO DE PRODUTOS DISPONÍVEIS:
{CATALOGO_DE_PRODUTOS}
"""
model = genai.GenerativeModel(
    model_name="models/gemini-2.5-flash",
    system_instruction=PROMPT_SISTEMA,
    tools=ferramentas_para_ia
)
if 'chat' not in st.session_state:
    st.session_state.chat = model.start_chat(history=[])
if 'processed_id' not in st.session_state:
    st.session_state.processed_id = None

# --- 4. LÓGICA PRINCIPAL DO AGENTE ---
def executar_agente(prompt_usuario: str, audio_bytes: bytes = None, audio_mime_type: str = None):
    try:
        content_to_send = [prompt_usuario]
        if audio_bytes and audio_mime_type:
            audio_part = {"mime_type": audio_mime_type, "data": audio_bytes}
            content_to_send.append(audio_part)
        response = st.session_state.chat.send_message(content_to_send)
        function_call = response.candidates[0].content.parts[0].function_call
        if function_call.name:
            function_name = function_call.name
            args_dict = {key: value for key, value in function_call.args.items()}
            function_to_call = funcoes_disponiveis[function_name]
            function_response_str = function_to_call(**args_dict)
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
    role = "assistant" if message.role == "model" else "user"
    if any(part.text for part in message.parts):
         with st.chat_message(role):
            if message.parts[0].text and "Execute o comando de voz do cliente" not in message.parts[0].text:
                st.markdown(message.parts[0].text)
            else:
                st.markdown("🎤 _Comando de voz enviado_")

st.markdown("---")
prompt_usuario = st.chat_input("Qual operação deseja realizar?")
uploaded_audio_file = st.file_uploader(
    "Ou envie um arquivo de áudio com seu comando:", 
    type=["wav", "mp3", "m4a"]
)

if uploaded_audio_file is not None and uploaded_audio_file.file_id != st.session_state.processed_id:
    audio_bytes = uploaded_audio_file.getvalue()
    audio_mime_type = uploaded_audio_file.type
    prompt_contexto_audio = "Execute o comando de voz do cliente a seguir usando as ferramentas disponíveis. Se faltar alguma informação (como o ticker de um ativo), faça uma pergunta para obter os detalhes."
    
    with st.chat_message("user"):
        st.markdown("🎤 _Comando de voz enviado_")
    with st.chat_message("assistant"):
        with st.spinner("Processando comando de voz..."):
            resposta_ia = executar_agente(
                prompt_contexto_audio, 
                audio_bytes=audio_bytes, 
                audio_mime_type=audio_mime_type
            )
            st.markdown(resposta_ia)
            st.session_state.processed_id = uploaded_audio_file.file_id
            st.rerun()

elif prompt_usuario and prompt_usuario != st.session_state.processed_id:
    with st.chat_message("user"):
        st.markdown(prompt_usuario)
    with st.chat_message("assistant"):
        with st.spinner("Processando..."):
            resposta_ia = executar_agente(prompt_usuario)
            st.markdown(resposta_ia)
            st.session_state.processed_id = prompt_usuario
            st.rerun()