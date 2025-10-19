import json
from typing import Dict, Any

# Define o nome do arquivo que funcionará como nosso "banco de dados"
CARTEIRA_FILE = "carteira.json"

# --- Catálogo de Produtos Válidos (Validação de Segurança no Backend) ---
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
    """
    Consulta a carteira de investimentos completa e o saldo em conta do cliente.
    Retorna uma string JSON com os dados.
    """
    print("EXECUTANDO FUNÇÃO: consultar_carteira")
    dados = _carregar_dados()
    return json.dumps(dados)

def comprar_ativo(ticker: str, valor: float) -> str:
    """
    Compra um valor específico de um ativo para o cliente.
    Valida se o ativo existe no catálogo e se há saldo suficiente.
    """
    print(f"EXECUTANDO FUNÇÃO: comprar_ativo(ticker={ticker}, valor={valor})")
    
    # Validação 1: O ativo existe no nosso catálogo?
    ticker_upper = ticker.upper()
    if ticker_upper not in PRODUTOS_VALIDOS:
        resultado = {"status": "erro", "mensagem": f"O ativo com ticker '{ticker}' não foi encontrado em nosso catálogo de produtos."}
        return json.dumps(resultado)

    dados = _carregar_dados()
    
    # Validação 2: O cliente tem saldo suficiente?
    if dados["saldo_conta_corrente"] < valor:
        resultado = {"status": "erro", "mensagem": "Saldo em conta corrente insuficiente para realizar a operação."}
        return json.dumps(resultado)
        
    dados["saldo_conta_corrente"] -= valor
    
    novo_ativo = {
        "ticker": ticker_upper,
        "descricao": PRODUTOS_VALIDOS[ticker_upper], # Pega a descrição do catálogo
        "valor_aplicado": valor
    }
    dados["carteira_investimentos"].append(novo_ativo)
    
    _salvar_dados(dados)
    
    resultado = {
        "status": "sucesso", 
        "mensagem": f"Investimento de R${valor:.2f} em '{PRODUTOS_VALIDOS[ticker_upper]}' realizado com sucesso!",
        "novo_saldo_cc": f"R${dados['saldo_conta_corrente']:.2f}"
    }
    return json.dumps(resultado)