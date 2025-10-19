import json
from typing import Dict, Any

# Define o nome do arquivo que funcionará como nosso "banco de dados"
CARTEIRA_FILE = "carteira.json"

with open("catalogo_final.json", "r", encoding="utf-8") as f:
    ativos = json.load(f)
# --- Catálogo de Produtos Válidos (Validação de Segurança no Backend) ---
PRODUTOS_VALIDOS = {
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

def _buscar_produto(ticker: str):
    for categoria, produtos in PRODUTOS_VALIDOS.items():
        for p in produtos:
            if p["ticker"].upper() == ticker.upper():
                return p
    return None

def comprar_ativo(ticker: str, valor: float = None, quantidade: int = None):
    produto = _buscar_produto(ticker)
    if not produto:
        return {"status": "erro", "mensagem": f"Ticker {ticker} não encontrado"}

    preco_unitario = float(str(produto.get("Preco", "0")).replace(",", "."))

    # Se passou quantidade, calcula custo
    if quantidade is not None:
        try:
            quantidade = int(quantidade)
        except ValueError:
            return {"status": "erro", "mensagem": "Quantidade inválida, informe um número inteiro."}
        custo_total = quantidade * preco_unitario
    elif valor is not None:
        try:
            valor = float(valor)
        except ValueError:
            return json.dumps({"status": "erro", "mensagem": "Valor inválido, informe um número válido."})
    else:
        return {"status": "erro", "mensagem": "É necessário informar valor ou quantidade"}

    # Verifica saldo
    dados = _carregar_dados()
    if dados["saldo_conta_corrente"] < custo_total:
        return {"status": "erro", "mensagem": "Saldo insuficiente"}

    # Atualiza carteira
    dados["saldo_conta_corrente"] -= custo_total
    dados["carteira_investimentos"].append({
        "ticker": ticker,
        "descricao": produto["descricao"],
        "quantidade": quantidade,
        "preco_unitario": preco_unitario,
        "valor_total": custo_total
    })
    _salvar_dados(dados)
    if quantidade is not None:
        return {"status": "sucesso", "mensagem": f"Compra de {quantidade}x {ticker} realizada com sucesso!"}


    return json.dumps({
        "status": "sucesso",
        "mensagem": f"Investimento de R${valor:.2f} em '{produto['descricao']}' realizado com sucesso!",
        "novo_saldo_cc": f"R${dados['saldo_conta_corrente']:.2f}"
    })

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