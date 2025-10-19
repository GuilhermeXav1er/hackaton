import json
from typing import Dict, Any, List

CARTEIRA_FILE = "carteira.json"

with open("catalogo_final.json", "r", encoding="utf-8") as f: ativos = json.load(f)
with open("catalogo_cripto.json", "r", encoding="utf-8") as f: cripto = json.load(f)

PRODUTOS_VALIDOS = {
    "renda_fixa": [
        {"ticker": "CDB_BTG_DI", "descricao": "CDB Pós-Fixado BTG 105% CDI.", "perfil": ["Conservador", "Moderado"]},
        {"ticker": "LCI_BTG_360", "descricao": "LCI BTG 1 ano 98% CDI.", "perfil": ["Conservador", "Moderado"]},
        {"ticker": "TESOURO_SELIC_2029", "descricao": "Tesouro Selic 2029.", "perfil": ["Conservador"]},
    ],
    "fundos": [
        {"ticker": "FUNDO_RF_BTG", "descricao": "Fundo de Renda Fixa BTG.", "perfil": ["Conservador", "Moderado"]},
        {"ticker": "FUNDO_MM_BTG", "descricao": "Fundo Multimercado BTG.", "perfil": ["Moderado", "Arrojado"]},
        {"ticker": "FUNDO_ACOES_BTG_ABSOLUTO", "descricao": "Fundo de Ações BTG Pactual Absoluto.", "perfil": ["Arrojado"]},
    ],
    "renda_variavel": ativos,
    "criptomoedas": cripto
}
for categoria in ["renda_variavel", "criptomoedas"]:
    for ativo in PRODUTOS_VALIDOS[categoria]:
        if "perfil" not in ativo: ativo["perfil"] = ["Arrojado"]

def _carregar_dados() -> Dict[str, Any]:
    try:
        with open(CARTEIRA_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"cliente_id": "BTG-78901", "nome_cliente": "Ana Silva", "perfil_investidor": None, "saldo_conta_corrente": 20000.0, "carteira_investimentos": []}

def _salvar_dados(dados: Dict[str, Any]):
    with open(CARTEIRA_FILE, 'w', encoding='utf-8') as f: json.dump(dados, f, indent=2, ensure_ascii=False)

def consultar_carteira() -> str:
    return json.dumps(_carregar_dados())

def _buscar_produto(ticker: str):
    ticker_upper = ticker.upper()
    for categoria, produtos in PRODUTOS_VALIDOS.items():
        for p in produtos:
            if p["ticker"].upper() == ticker_upper:
                p['categoria'] = categoria
                return p
    return None

def comprar_ativo(ticker: str, valor: float = None, quantidade: int = None) -> str:
    # Sua lógica de compra, que está correta
    produto = _buscar_produto(ticker)
    if not produto: return json.dumps({"status": "erro", "mensagem": f"Ticker '{ticker}' não encontrado."})
    try: preco_unitario = float(str(produto.get("Preco", "1.0")).replace(",", "."))
    except: return json.dumps({"status": "erro", "mensagem": f"Preço do ativo '{ticker}' inválido."})
    custo_total, quantidade_calculada = 0, 0
    if valor is not None and quantidade is not None: return json.dumps({"status": "erro", "mensagem": "Forneça apenas valor ou quantidade."})
    if valor is not None:
        custo_total = float(valor)
        if produto['categoria'] in ['renda_variavel', 'criptomoedas']:
            quantidade_calculada = int(valor / preco_unitario) if preco_unitario > 0 else 0
            custo_total = quantidade_calculada * preco_unitario
        else: quantidade_calculada = valor
    elif quantidade is not None:
        quantidade_calculada = int(quantidade)
        custo_total = quantidade_calculada * preco_unitario
    else: return json.dumps({"status": "erro", "mensagem": "Informe 'valor' ou 'quantidade'."})
    if custo_total <= 0: return json.dumps({"status": "erro", "mensagem": "Não foi possível calcular a operação."})
    dados = _carregar_dados()
    if dados["saldo_conta_corrente"] < custo_total: return json.dumps({"status": "erro", "mensagem": f"Saldo insuficiente. Saldo: R${dados['saldo_conta_corrente']:.2f}, Custo: R${custo_total:.2f}."})
    ativo_existente = next((a for a in dados["carteira_investimentos"] if a["ticker"].upper() == ticker.upper()), None)
    dados["saldo_conta_corrente"] -= custo_total
    if ativo_existente:
        if produto['categoria'] in ['renda_variavel', 'criptomoedas']:
            ativo_existente["quantidade"] = ativo_existente.get("quantidade", 0) + quantidade_calculada
            ativo_existente["valor_total"] = ativo_existente.get("valor_total", 0) + custo_total
            if ativo_existente["quantidade"] > 0: ativo_existente["preco_medio"] = ativo_existente["valor_total"] / ativo_existente["quantidade"]
        else: ativo_existente["valor_aplicado"] = ativo_existente.get("valor_aplicado", 0) + custo_total
    else:
        novo_ativo = {"ticker": ticker.upper(), "descricao": produto["descricao"], "categoria": produto["categoria"]}
        if produto['categoria'] in ['renda_variavel', 'criptomoedas']:
            novo_ativo.update({"quantidade": quantidade_calculada, "valor_total": custo_total, "preco_medio": preco_unitario})
        else: novo_ativo["valor_aplicado"] = custo_total
        dados["carteira_investimentos"].append(novo_ativo)
    _salvar_dados(dados)
    return json.dumps({"status": "sucesso", "mensagem": f"Compra de {ticker.upper()} no valor de R${custo_total:.2f} realizada!", "novo_saldo_cc": f"R${dados['saldo_conta_corrente']:.2f}"})

# --- FUNÇÃO DE VENDA CORRIGIDA E COMPLETA ---
def vender_ativo(ticker: str, valor: float = None, quantidade: int = None) -> str:
    """
    Vende um ativo da carteira, seja por valor ou por quantidade.
    """
    if valor is None and quantidade is None:
        return json.dumps({"status": "erro", "mensagem": "Forneça o 'valor' ou a 'quantidade' a ser vendida."})

    dados = _carregar_dados()
    ticker_upper = ticker.upper()
    
    ativo_para_vender = None
    indice_ativo = -1
    for i, ativo in enumerate(dados["carteira_investimentos"]):
        if ativo["ticker"] == ticker_upper:
            ativo_para_vender = ativo
            indice_ativo = i
            break

    if not ativo_para_vender:
        return json.dumps({"status": "erro", "mensagem": f"Você não possui o ativo '{ticker_upper}' para vender."})

    produto = _buscar_produto(ticker)
    try:
        preco_unitario_atual = float(str(produto.get("Preco", "1.0")).replace(",", "."))
    except (ValueError, TypeError):
        return json.dumps({"status": "erro", "mensagem": f"Preço atual do ativo '{ticker}' é inválido."})

    valor_a_resgatar = 0
    
    # Lógica de venda
    if ativo_para_vender['categoria'] in ['renda_variavel', 'criptomoedas']:
        total_disponivel = ativo_para_vender.get("valor_total", 0)
        qtd_disponivel = ativo_para_vender.get("quantidade", 0)

        if quantidade is not None: # Venda por quantidade
            if quantidade > qtd_disponivel:
                return json.dumps({"status": "erro", "mensagem": f"Quantidade insuficiente. Você possui {qtd_disponivel} unidades de {ticker_upper}."})
            valor_a_resgatar = quantidade * preco_unitario_atual
            ativo_para_vender["quantidade"] -= quantidade
            ativo_para_vender["valor_total"] -= valor_a_resgatar
        elif valor is not None: # Venda por valor
            if valor > total_disponivel:
                return json.dumps({"status": "erro", "mensagem": f"Valor de venda excede o total aplicado de R${total_disponivel:.2f} em {ticker_upper}."})
            qtd_a_vender = int(valor / preco_unitario_atual) if preco_unitario_atual > 0 else 0
            if qtd_a_vender > qtd_disponivel:
                qtd_a_vender = qtd_disponivel # Vende tudo
            
            valor_a_resgatar = qtd_a_vender * preco_unitario_atual
            ativo_para_vender["quantidade"] -= qtd_a_vender
            ativo_para_vender["valor_total"] -= valor_a_resgatar

    else: # Venda para Renda Fixa e Fundos (baseado em valor)
        total_disponivel = ativo_para_vender.get("valor_aplicado", 0)
        if valor is None:
            return json.dumps({"status": "erro", "mensagem": f"Para vender {ticker_upper}, você precisa especificar o 'valor'."})
        if valor > total_disponivel:
            return json.dumps({"status": "erro", "mensagem": f"Saldo insuficiente. Você possui R${total_disponivel:.2f} em {ticker_upper}."})
        
        valor_a_resgatar = valor
        ativo_para_vender["valor_aplicado"] -= valor_a_resgatar

    # Atualiza saldo e remove ativo se zerado
    dados["saldo_conta_corrente"] += valor_a_resgatar
    
    if (ativo_para_vender.get("valor_aplicado", 0) < 0.01 and 'valor_aplicado' in ativo_para_vender) or \
       (ativo_para_vender.get("quantidade", 0) <= 0 and 'quantidade' in ativo_para_vender):
        dados["carteira_investimentos"].pop(indice_ativo)

    _salvar_dados(dados)

    return json.dumps({
        "status": "sucesso",
        "mensagem": f"Venda de R${valor_a_resgatar:.2f} do ativo '{ticker_upper}' realizada com sucesso!",
        "novo_saldo_cc": f"R${dados['saldo_conta_corrente']:.2f}"
    })

QUESTIONARIO_PERFIL = [
    { "id": 1, "pergunta": "Qual é o seu principal objetivo ao investir?", "opcoes": {"A": {"pontos": 1}, "B": {"pontos": 2}, "C": {"pontos": 3}}},
    { "id": 2, "pergunta": "Por quanto tempo você pretende deixar seu dinheiro investido?", "opcoes": {"A": {"pontos": 1}, "B": {"pontos": 2}, "C": {"pontos": 3}}},
    { "id": 3, "pergunta": "Como você reagiria se seus investimentos caíssem 20% em um mês?", "opcoes": {"A": {"pontos": 1}, "B": {"pontos": 2}, "C": {"pontos": 3}}},
]

def obter_perfil_investidor() -> str:
    perfil = _carregar_dados().get("perfil_investidor")
    return json.dumps({"status": "perfil_existente", "perfil": perfil} if perfil else {"status": "perfil_nao_definido"})

def iniciar_questionario_perfil() -> str:
    return json.dumps(QUESTIONARIO_PERFIL)

def responder_questionario_perfil(resposta_1: str, resposta_2: str, resposta_3: str) -> str:
    respostas = {'1': resposta_1, '2': resposta_2, '3': resposta_3}
    pontuacao_total = 0
    try:
        for id_str, letra in respostas.items():
            pergunta = next((q for q in QUESTIONARIO_PERFIL if q["id"] == int(id_str)), None)
            pontos = pergunta["opcoes"][letra.upper()]["pontos"]
            pontuacao_total += pontos
    except: return json.dumps({"status": "erro", "mensagem": "Respostas inválidas."})
    perfil = "Arrojado"
    if pontuacao_total <= 4: perfil = "Conservador"
    elif pontuacao_total <= 7: perfil = "Moderado"
    dados = _carregar_dados()
    dados["perfil_investidor"] = perfil
    _salvar_dados(dados)
    return json.dumps({"status": "sucesso", "mensagem": f"Seu perfil foi definido como: {perfil}.", "perfil": perfil})

def sugerir_investimentos() -> str:
    dados = _carregar_dados()
    perfil = dados.get("perfil_investidor")
    if not perfil: return json.dumps({"status": "erro", "mensagem": "Perfil não definido."})
    sugestoes = []
    for produtos in PRODUTOS_VALIDOS.values():
        for produto in produtos:
            if perfil in produto.get("perfil", []):
                sugestoes.append(produto)
    return json.dumps({"status": "sucesso", "perfil": perfil, "sugestoes": sugestoes[:7]})