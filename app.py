import streamlit as st
import google.generativeai as genai
import json
import os
from dotenv import load_dotenv
import traceback

st.markdown("""
    <style>
    /* Fundo do avatar do usuário */
    [data-testid="stChatMessageAvatarUser"] {
        background-color: #32CD32 !important; /* Verde */
        border-radius: 50% !important;
        padding: 4px !important;
    }

    /* Fundo do avatar do assistente */
    [data-testid="stChatMessageAvatarAssistant"] {
        background-color: #1E90FF !important; /* Azul */
        border-radius: 50% !important;
        padding: 4px !important;
    }

    /* Fundo do avatar do sistema (maletinha) */
    [data-testid="stChatMessageAvatarSystem"] {
        background-color: #DAA520 !important; /* Dourado */
        border-radius: 50% !important;
        padding: 4px !important;
    }
    </style>
""", unsafe_allow_html=True)


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
    "vender_ativo": simulador_carteira.vender_ativo,
    "obter_perfil_investidor": simulador_carteira.obter_perfil_investidor,
    "iniciar_questionario_perfil": simulador_carteira.iniciar_questionario_perfil,
    "responder_questionario_perfil": simulador_carteira.responder_questionario_perfil,
    "sugerir_investimentos": simulador_carteira.sugerir_investimentos,
}
ferramentas_para_ia = [
    { "function_declarations": [
        { "name": "consultar_carteira", "description": "Obtém a carteira de investimentos e o saldo em conta do cliente." },
        { "name": "comprar_ativo", "description": "Executa a compra de um ativo financeiro.", "parameters": { "type": "object", "properties": {"ticker": {"type": "string"}, "valor": {"type": "number"}, "quantidade": {"type": "number"}}, "required": ["ticker"] }},
        { "name": "vender_ativo", "description": "Executa a venda ou resgate de um ativo financeiro.", "parameters": { "type": "object", "properties": {"ticker": {"type": "string"}, "valor": {"type": "number"}, "quantidade": {"type": "number"}}, "required": ["ticker"] }},
        { "name": "obter_perfil_investidor", "description": "Verifica o perfil de investidor (suitability) do cliente." },
        { "name": "iniciar_questionario_perfil", "description": "Apresenta as perguntas para definir o perfil de investidor." },
        { "name": "responder_questionario_perfil", "description": "Envia as 3 respostas do cliente (A, B ou C) para calcular e definir o perfil.", "parameters": { "type": "object", "properties": {"resposta_1": {"type": "string"}, "resposta_2": {"type": "string"}, "resposta_3": {"type": "string"}}, "required": ["resposta_1", "resposta_2", "resposta_3"] }},
        { "name": "sugerir_investimentos", "description": "Pede uma lista de investimentos adequados ao perfil do cliente." }
    ]}
]

# --- 3. GERENCIAMENTO DA CONVERSA ---
# SEU PROMPT DE SISTEMA ORIGINAL, 100% PRESERVADO
PROMPT_SISTEMA = f"""Você é um assistente virtual do banco BTG Pactual. Profissional, eficiente e seguro.
Sua principal função é ajudar clientes a consultar suas carteiras e a realizar investimentos de forma transacional e personalizada.

REGRAS DE FLUXO DE CONVERSA:
1.  **SAUDAÇÃO E INTENÇÃO**: Se o cliente quer 'investir', 'ver opções' ou similar, sua PRIMEIRA ação deve ser chamar a função `obter_perfil_investidor`.
2.  **FLUXO DE PERFIL (SUITABILITY)**:
    a.  Se `obter_perfil_investidor` retornar um perfil existente, informe o cliente ("Vi aqui que seu perfil é [Perfil].") e chame `sugerir_investimentos`.
    b.  Se retornar 'perfil_nao_definido', você DEVE iniciar o questionário. Diga: "Para te ajudar melhor, primeiro precisamos definir seu perfil de investidor. São apenas 3 perguntas rápidas." e em seguida chame `iniciar_questionario_perfil`.
    c.  Ao receber as perguntas da função, apresente-as TODAS de uma vez para o cliente, de forma clara e numerada, e bem formatada com as alternativas embaixo de cada questão. Instrua o cliente a responder com o número da pergunta e a letra da opção (ex: 'Minhas respostas são 1A, 2B e 3C').
    d.  Ao receber as 3 respostas, chame a função `responder_questionario_perfil` com os argumentos `resposta_1`, `resposta_2` e `resposta_3`.
    e.  Após sucesso, informe o novo perfil e chame `sugerir_investimentos`.
3.  **RECOMENDAÇÃO DE PRODUTOS**:
    a.  Para saber quais produtos oferecer, SEMPRE use a função `sugerir_investimentos`. Esta é sua única fonte de verdade sobre produtos disponíveis para o perfil do cliente.
    b.  Ao apresentar as sugestões, mostre o ticker, a descrição e explique por que é adequado.
4.  **TRANSAÇÕES (COMPRA/VENDA)**:
    a.  Para Renda Fixa, Fundos e criptomoedas, a operação é por `valor`.
    b.  Para Renda Variável (ações), a operação é por `quantidade`. Se o cliente fornecer um valor, ajude-o a calcular a quantidade de ações com base no preço retornado pela função de sugestão.
    c.  Sempre confirme a operação (ativo, valor/quantidade) antes de chamar `comprar_ativo` ou `vender_ativo`.

REGRAS GERAIS:
-   **PROIBIDO**: Nunca invente um ticker ou produto. Se o cliente pedir algo que não foi retornado por `sugerir_investimentos`, informe que o produto não está disponível para o perfil dele.
-   Não venda mais de um ativo por vez.
"""
model = genai.GenerativeModel(
    model_name="models/gemini-flash-latest",
    system_instruction=PROMPT_SISTEMA,
    tools=ferramentas_para_ia
)
if 'chat' not in st.session_state: st.session_state.chat = model.start_chat(history=[])
if 'processed_id' not in st.session_state: st.session_state.processed_id = None

# --- 4. LÓGICA PRINCIPAL DO AGENTE (VERSÃO FINAL E MAIS ROBUSTA) ---
def executar_agente(prompt_usuario: str, audio_bytes: bytes = None, audio_mime_type: str = None):
    try:
        content_to_send = [prompt_usuario]
        if audio_bytes and audio_mime_type:
            audio_part = {"mime_type": audio_mime_type, "data": audio_bytes}
            content_to_send.append(audio_part)
        
        response = st.session_state.chat.send_message(content_to_send)
        
        while True:
            # Verificação de segurança para respostas vazias ou bloqueadas
            if not response.candidates or not response.candidates[0].content or not response.candidates[0].content.parts:
                return "Não obtive uma resposta válida. Por favor, tente novamente."

            part = response.candidates[0].content.parts[0]
            
            # Se não houver mais chamadas de função, o loop termina
            if not hasattr(part, 'function_call') or not part.function_call.name:
                break 

            function_call = part.function_call
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
                ), 
                stream=False
            )
        return response.text
    except Exception as e:
        st.error("Ocorreu um erro inesperado. Por favor, tente novamente.")
        print("--- ERRO DETALHADO NO TERMINAL ---")
        traceback.print_exc()
        print("--- FIM DO ERRO ---")
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
    prompt_contexto_audio = "Execute o comando de voz do cliente a seguir usando as ferramentas disponíveis."
    with st.chat_message("user"): st.markdown("🎤 _Comando de voz enviado_")
    with st.chat_message("assistant"):
        with st.spinner("Processando comando de voz..."):
            resposta_ia = executar_agente(prompt_contexto_audio, audio_bytes=audio_bytes, audio_mime_type=audio_mime_type)
            st.markdown(resposta_ia)
            st.session_state.processed_id = uploaded_audio_file.file_id
            st.rerun()

elif prompt_usuario and prompt_usuario != st.session_state.processed_id:
    with st.chat_message("user"): st.markdown(prompt_usuario)
    with st.chat_message("assistant"):
        with st.spinner("Processando..."):
            resposta_ia = executar_agente(prompt_usuario)
            st.markdown(resposta_ia)
            st.session_state.processed_id = prompt_usuario
            st.rerun()