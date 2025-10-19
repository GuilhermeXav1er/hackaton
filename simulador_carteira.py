import json
from typing import Dict, Any

# Define o nome do arquivo que funcionará como nosso "banco de dados"
CARTEIRA_FILE = "carteira.json"

# --- Catálogo de Produtos Válidos ---
PRODUTOS_VALIDOS = {
    "CDB_BTG_DI": "CDB Pós-Fixado BTG 105% CDI",
    "LCI_BTG_360": "LCI BTG 1 ano 98% CDI",
    "TESOURO_SELIC_2029": "Tesouro Selic 2029",
    "FUNDO_ACOES_BTG_ABSOLUTO": "Fundo de Ações BTG Pactual Absoluto"
}

def _carregar_dados() -> Dict[str, Any]:
    """Função interna para carregar os dados do arquivo JSON."""
    try:
        with open(CARTEIRA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"saldo_conta_corrente": 0, "carteira_investimentos": []}

def _salvar_dados(dados: Dict[str, Any]):
    """Função interna para salvar os dados no arquivo JSON."""
    with open(CARTEIRA_FILE, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)

def consultar_carteira() -> str:
    """Consulta a carteira de investimentos completa e o saldo em conta do cliente."""
    dados = _carregar_dados()
    return json.dumps(dados)

def comprar_ativo(ticker: str, valor: float) -> str:
    """
    Compra um valor específico de um ativo, consolidando com posições existentes.
    """
    ticker_upper = ticker.upper()
    if ticker_upper not in PRODUTOS_VALIDOS:
        resultado = {"status": "erro", "mensagem": f"O ativo '{ticker}' não foi encontrado."}
        return json.dumps(resultado)

    dados = _carregar_dados()
    
    if dados["saldo_conta_corrente"] < valor:
        resultado = {"status": "erro", "mensagem": "Saldo em conta corrente insuficiente."}
        return json.dumps(resultado)
        
    dados["saldo_conta_corrente"] -= valor
    
    # --- LÓGICA DE CONSOLIDAÇÃO NA COMPRA ---
    ativo_existente = None
    for ativo in dados["carteira_investimentos"]:
        if ativo["ticker"] == ticker_upper:
            ativo_existente = ativo
            break
    
    if ativo_existente:
        # Se o ativo já existe, apenas soma o valor
        ativo_existente["valor_aplicado"] += valor
    else:
        # Se não existe, cria um novo
        novo_ativo = {
            "ticker": ticker_upper,
            "descricao": PRODUTOS_VALIDOS[ticker_upper],
            "valor_aplicado": valor
        }
        dados["carteira_investimentos"].append(novo_ativo)
    # --- FIM DA LÓGICA DE CONSOLIDAÇÃO ---
    
    _salvar_dados(dados)
    
    resultado = {
        "status": "sucesso", 
        "mensagem": f"Investimento de R${valor:.2f} em '{PRODUTOS_VALIDOS[ticker_upper]}' realizado com sucesso!",
        "novo_saldo_cc": f"R${dados['saldo_conta_corrente']:.2f}"
    }
    return json.dumps(resultado)

def vender_ativo(ticker: str, valor: float) -> str:
    """
    Vende um valor específico de um ativo consolidado.
    """
    ticker_upper = ticker.upper()
    dados = _carregar_dados()

    # --- LÓGICA DE CONSOLIDAÇÃO NA VENDA ---
    ativo_para_vender = None
    indice_ativo = -1
    for i, ativo in enumerate(dados["carteira_investimentos"]):
        if ativo["ticker"] == ticker_upper:
            ativo_para_vender = ativo
            indice_ativo = i
            break
            
    if not ativo_para_vender:
        resultado = {"status": "erro", "mensagem": f"Você não possui o ativo '{ticker_upper}' para vender."}
        return json.dumps(resultado)

    if ativo_para_vender["valor_aplicado"] < valor:
        resultado = {"status": "erro", "mensagem": f"Saldo insuficiente no ativo '{ticker_upper}'. Você possui R${ativo_para_vender['valor_aplicado']:.2f}."}
        return json.dumps(resultado)

    # Executa a venda
    ativo_para_vender["valor_aplicado"] -= valor
    dados["saldo_conta_corrente"] += valor
    
    # Se o saldo do ativo zerar, remove ele da carteira
    if ativo_para_vender["valor_aplicado"] < 0.01:
        dados["carteira_investimentos"].pop(indice_ativo)
    # --- FIM DA LÓGICA DE CONSOLIDAÇÃO ---

    _salvar_dados(dados)

    resultado = {
        "status": "sucesso", 
        "mensagem": f"Venda de R${valor:.2f} do ativo '{ticker_upper}' realizada com sucesso!",
        "novo_saldo_cc": f"R${dados['saldo_conta_corrente']:.2f}"
    }
    return json.dumps(resultado)