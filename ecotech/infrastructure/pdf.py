"""
Geração de PDF para MTR - Manifesto de Transporte de Resíduos.
Utilizado para registrar formalmente o descarte de resíduos eletrônicos
conforme a Política Nacional de Resíduos Sólidos (PNRS).
"""

from fpdf import FPDF
from datetime import datetime


# --------------------------------------------------------------------------
# Cores EcoTech
# --------------------------------------------------------------------------
COR_VERDE   = (29, 133, 77)    # #1D854D
COR_CINZA   = (71, 85, 105)    # cinza texto
COR_CLARO   = (241, 245, 249)  # fundo linhas alternadas
COR_BORDER  = (203, 213, 225)  # bordas
PRETO       = (15, 23, 42)


def gerar_mtr(sol) -> bytes:
    """
    Gera um PDF de Manifesto de Transporte de Resíduos (MTR) para a
    solicitação de descarte informada.

    Args:
        sol: instância de SolicitacaoDescarte com dados completos.

    Returns:
        Bytes do PDF gerado.
    """
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # ------------------------------------------------------------------ #
    # CABEÇALHO
    # ------------------------------------------------------------------ #
    # Barra verde superior
    pdf.set_fill_color(*COR_VERDE)
    pdf.rect(0, 0, 210, 22, style="F")

    # Título principal
    pdf.set_xy(12, 5)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(245, 247, 246)
    pdf.cell(0, 12, "EcoTech - Manifesto de Transporte de Residuos (MTR)", ln=True)

    # Subtítulo PNRS
    pdf.set_x(12)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(245, 247, 246)
    pdf.cell(0, 5, "Documento gerado conforme a Politica Nacional de Residuos Solidos - Lei 12.305/2010", ln=True)

    # Reset para preto
    pdf.set_text_color(*PRETO)
    pdf.ln(6)

    # Número do MTR e data
    numero_mtr = f"MTR-{sol.id[:8].upper()}"
    data_emissao = datetime.now().strftime("%d/%m/%Y %H:%M")
    _cabecalho_info(pdf, numero_mtr, data_emissao)

    pdf.ln(4)
    _linha_divisor(pdf)
    pdf.ln(3)

    # ------------------------------------------------------------------ #
    # SEÇÃO 1 — GERADOR DOS RESÍDUOS
    # ------------------------------------------------------------------ #
    _titulo_secao(pdf, "1. Gerador dos Residuos")
    _campo(pdf, "Nome / Razao Social", sol.usuario.nome)
    _campo(pdf, "E-mail",              getattr(sol.usuario, 'email', '-'))
    _campo(pdf, "Tipo de Gerador",     _tipo_usuario(getattr(sol.usuario, 'tipo', '-')))

    pdf.ln(3)
    _linha_divisor(pdf)
    pdf.ln(3)

    # ------------------------------------------------------------------ #
    # SEÇÃO 2 — PONTO DE COLETA / DESTINADOR
    # ------------------------------------------------------------------ #
    _titulo_secao(pdf, "2. Ponto de Coleta / Destinador")
    if sol.ponto_coleta:
        _campo(pdf, "Nome",     sol.ponto_coleta.nome)
        _campo(pdf, "Endereco", sol.ponto_coleta.endereco)
    else:
        _campo(pdf, "Ponto de Coleta", "Nao definido")

    pdf.ln(3)
    _linha_divisor(pdf)
    pdf.ln(3)

    # ------------------------------------------------------------------ #
    # SEÇÃO 3 — DESCRIÇÃO DOS RESÍDUOS
    # ------------------------------------------------------------------ #
    _titulo_secao(pdf, "3. Descricao dos Residuos Eletronicos")

    # Cabeçalho da tabela
    _tabela_header(pdf)

    # Linhas da tabela
    for i, item in enumerate(sol.itens):
        nome_disp = item.dispositivo.nome
        qtd       = item.quantidade
        peso_unit = item.dispositivo.peso_kg
        peso_tot  = item.calcular_peso_total()
        classe    = _classe_residuo(getattr(item.dispositivo, 'categoria', None) or getattr(item.dispositivo, 'tipo', None) or nome_disp)
        _tabela_linha(pdf, i, nome_disp, qtd, peso_unit, peso_tot, classe)

    pdf.ln(3)

    # Total
    peso_total = sol.calcular_peso_total()
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*COR_CINZA)
    pdf.cell(0, 6, f"Peso Total: {peso_total:.2f} kg", ln=True, align="R")
    pdf.set_text_color(*PRETO)

    pdf.ln(3)
    _linha_divisor(pdf)
    pdf.ln(3)

    # ------------------------------------------------------------------ #
    # SEÇÃO 4 — TRATAMENTO E DESTINAÇÃO
    # ------------------------------------------------------------------ #
    _titulo_secao(pdf, "4. Tratamento e Destinacao Final")

    estado = sol.estado.obter_nome()
    metodo = "-"
    if sol.metodo_tratamento:
        metodo = sol.metodo_tratamento.obter_nome()
    elif getattr(sol, 'metodo_tratamento_str', None):
        metodo = sol.metodo_tratamento_str

    _campo(pdf, "Estado Atual da Solicitacao", estado)
    _campo(pdf, "Metodo de Tratamento",        metodo)
    _campo(pdf, "Impacto Ambiental Estimado",  f"{sol.calcular_impacto_total():.2f} kg CO2 evitado")

    # Descrição do método
    descricao = _descricao_metodo(metodo)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*COR_CINZA)
    pdf.multi_cell(0, 5, f"Descricao: {descricao}")
    pdf.set_text_color(*PRETO)

    pdf.ln(3)
    _linha_divisor(pdf)
    pdf.ln(3)

    # ------------------------------------------------------------------ #
    # SEÇÃO 5 — DECLARAÇÃO E ASSINATURAS
    # ------------------------------------------------------------------ #
    _titulo_secao(pdf, "5. Declaracao de Responsabilidade")

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*COR_CINZA)
    pdf.multi_cell(
        0, 5,
        "O gerador declara que as informacoes prestadas neste documento sao verdadeiras e "
        "que os residuos descritos serao encaminhados para destinacao ambientalmente adequada, "
        "conforme exigido pela Lei 12.305/2010 (PNRS) e suas regulamentacoes."
    )
    pdf.set_text_color(*PRETO)
    pdf.ln(8)

    # Linhas de assinatura
    _assinaturas(pdf)

    pdf.ln(6)
    _linha_divisor(pdf)
    pdf.ln(3)

    # ------------------------------------------------------------------ #
    # RODAPÉ
    # ------------------------------------------------------------------ #
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(*COR_CINZA)
    pdf.cell(0, 5, f"Documento gerado automaticamente pelo sistema EcoTech em {data_emissao}. Numero: {numero_mtr}", align="C")

    conteudo = pdf.output(dest='S')
    return conteudo.encode('latin-1') if isinstance(conteudo, str) else bytes(conteudo)


# --------------------------------------------------------------------------
# Helpers internos
# --------------------------------------------------------------------------

def _cabecalho_info(pdf: FPDF, numero_mtr: str, data_emissao: str):
    """Renderiza caixas de número MTR e data lado a lado."""
    pdf.set_fill_color(*COR_CLARO)
    pdf.set_draw_color(*COR_BORDER)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*COR_CINZA)

    x = pdf.get_x()
    y = pdf.get_y()
    larg = 90

    # caixa esquerda — número MTR
    pdf.rect(12, y, larg, 12, style="FD")
    pdf.set_xy(14, y + 1)
    pdf.cell(larg - 4, 5, "Numero do MTR:", ln=True)
    pdf.set_xy(14, y + 6)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*COR_VERDE)
    pdf.cell(larg - 4, 5, numero_mtr)

    # caixa direita — data
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*COR_CINZA)
    pdf.rect(12 + larg + 4, y, larg, 12, style="FD")
    pdf.set_xy(12 + larg + 6, y + 1)
    pdf.cell(larg - 4, 5, "Data de Emissao:", ln=True)
    pdf.set_xy(12 + larg + 6, y + 6)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*PRETO)
    pdf.cell(larg - 4, 5, data_emissao)

    pdf.ln(14)


def _linha_divisor(pdf: FPDF):
    pdf.set_draw_color(*COR_BORDER)
    pdf.line(12, pdf.get_y(), 198, pdf.get_y())


def _titulo_secao(pdf: FPDF, titulo: str):
    pdf.set_fill_color(*COR_VERDE)
    pdf.set_text_color(245, 247, 246)
    pdf.set_font("Helvetica", "B", 10)
    pdf.rect(12, pdf.get_y(), 186, 7, style="F")
    pdf.set_xy(14, pdf.get_y() + 0.5)
    pdf.cell(0, 6, titulo, ln=True)
    pdf.set_text_color(*PRETO)
    pdf.ln(2)


def _campo(pdf: FPDF, rotulo: str, valor: str):
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*COR_CINZA)
    pdf.set_x(12)
    pdf.cell(50, 6, f"{rotulo}:", ln=False)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*PRETO)
    pdf.cell(0, 6, str(valor), ln=True)


def _tabela_header(pdf: FPDF):
    pdf.set_fill_color(*COR_CLARO)
    pdf.set_draw_color(*COR_BORDER)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*COR_CINZA)
    pdf.set_x(12)
    # colunas: Dispositivo | Qtd | Peso Unit. | Peso Total | Classe
    pdf.cell(65, 6, "Dispositivo",    border=1, fill=True)
    pdf.cell(15, 6, "Qtd",           border=1, fill=True, align="C")
    pdf.cell(28, 6, "Peso Unit.(kg)", border=1, fill=True, align="C")
    pdf.cell(28, 6, "Peso Tot.(kg)",  border=1, fill=True, align="C")
    pdf.cell(50, 6, "Classe PNRS",    border=1, fill=True)
    pdf.ln()


def _tabela_linha(pdf: FPDF, idx: int, nome: str, qtd: int, peso_unit: float, peso_tot: float, classe: str):
    # linhas alternadas
    fill = idx % 2 == 0
    if fill:
        pdf.set_fill_color(248, 250, 252)
    else:
        pdf.set_fill_color(255, 255, 255)

    pdf.set_draw_color(*COR_BORDER)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*PRETO)
    pdf.set_x(12)

    # trunca nome se muito longo
    nome_trunc = nome[:32] + "..." if len(nome) > 35 else nome

    pdf.cell(65, 6, nome_trunc,          border=1, fill=fill)
    pdf.cell(15, 6, str(qtd),            border=1, fill=fill, align="C")
    pdf.cell(28, 6, f"{peso_unit:.3f}",  border=1, fill=fill, align="C")
    pdf.cell(28, 6, f"{peso_tot:.3f}",   border=1, fill=fill, align="C")
    pdf.cell(50, 6, classe,              border=1, fill=fill)
    pdf.ln()


def _assinaturas(pdf: FPDF):
    pdf.set_draw_color(*COR_BORDER)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*COR_CINZA)

    y = pdf.get_y()
    # assinatura gerador
    pdf.line(12, y + 10, 82, y + 10)
    pdf.set_xy(12, y + 11)
    pdf.cell(70, 5, "Assinatura do Gerador", align="C")

    # assinatura transportador / destinador
    pdf.line(108, y + 10, 198, y + 10)
    pdf.set_xy(108, y + 11)
    pdf.cell(90, 5, "Assinatura do Transportador / Destinador", align="C")


def _tipo_usuario(tipo: str) -> str:
    mapa = {
        'cidadao':        'Pessoa Fisica (Cidadao)',
        'empresa':        'Pessoa Juridica (Empresa)',
        'administrador':  'Administrador do Sistema',
    }
    return mapa.get(tipo, tipo.capitalize())


def _classe_residuo(categoria) -> str:
    """Mapeia categoria/tipo de dispositivo para classe PNRS."""
    if not categoria:
        return "Residuo Eletronico"
    s = str(categoria).lower()
    if any(x in s for x in ("bateria", "pilha", "acumul")):
        return "Classe I - Perigoso"
    if any(x in s for x in ("monitor", "tv", "tela", "display", "crt")):
        return "Classe I - Perigoso (Pb/Hg)"
    if any(x in s for x in ("celular", "smartphone", "tablet", "notebook", "laptop", "computador", "pc")):
        return "Classe II-A - Nao Inerte"
    if any(x in s for x in ("impres", "scanner", "copiad")):
        return "Classe II-A - Nao Inerte"
    return "Classe II-A - Nao Inerte"


def _descricao_metodo(metodo: str) -> str:
    mapa = {
        "Reciclagem":         "Processamento dos residuos para recuperacao de materiais como metais, plasticos e vidro.",
        "Reuso":              "Reaproveitamento de componentes ou equipamentos em bom estado de funcionamento.",
        "Descarte Controlado":"Destinacao final em aterro sanitario licenciado, seguindo normas ambientais.",
    }
    return mapa.get(metodo, "Destinacao ambientalmente adequada conforme normativas vigentes.")
