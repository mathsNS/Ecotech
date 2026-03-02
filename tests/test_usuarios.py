import pytest
from ecotech.domain.usuarios import Cidadao, Empresa, Administrador

# -------------------------------------
# TESTES USUARIO BASE (via subclasses)
# -------------------------------------

def test_criar_cidadao_valido():
    usuario = Cidadao(
        id="1",
        nome="Maria",
        email="maria@email.com",
        cpf="12345678901"
    )

    assert usuario.nome == "Maria"
    assert usuario.email == "maria@email.com"
    assert usuario.ativo is True

def test_nome_invalido():
    with pytest.raises(ValueError):
        Cidadao(
            id="1",
            nome="Ma",
            email="email@email.com",
            cpf="12345678901"
        )

def test_email_invalido():
    with pytest.raises(ValueError):
        Cidadao(
            id="1",
            nome="Maria",
            email="email_invalido",
            cpf="12345678901"
        )

# --------------------
# TESTES NOTIFICACOES
# --------------------

def test_adicionar_notificacao():
    usuario = Cidadao(
        id="1",
        nome="Maria",
        email="maria@email.com",
        cpf="12345678901"
    )

    usuario.adicionar_notificacao("Teste")

    assert len(usuario.notificacoes) == 1
    assert "Teste" in usuario.notificacoes[0]

def test_limpar_notificacoes():
    usuario = Cidadao(
        id="1",
        nome="Maria",
        email="maria@email.com",
        cpf="12345678901"
    )

    usuario.adicionar_notificacao("Teste")
    usuario.limpar_notificacoes()

    assert len(usuario.notificacoes) == 0

# -----------------
# TESTES HISTORICO
# -----------------

def test_historico_registra_acoes():
    usuario = Cidadao(
        id="1",
        nome="Maria",
        email="maria@email.com",
        cpf="12345678901"
    )

    tamanho_inicial = len(usuario.historico_acoes)

    usuario.adicionar_notificacao("Nova notificação")

    assert len(usuario.historico_acoes) > tamanho_inicial

# ---------------
# TESTES CIDADAO
# ---------------

def test_adicionar_pontos():
    usuario = Cidadao(
        id="1",
        nome="Maria",
        email="maria@email.com",
        cpf="12345678901"
    )

    usuario.adicionar_pontos(10)

    assert usuario.pontos == 10

def test_limite_solicitacoes():
    usuario = Cidadao(
        id="1",
        nome="Maria",
        email="maria@email.com",
        cpf="12345678901"
    )

    for _ in range(usuario.MAX_SOLICITACOES_ATIVAS):
        usuario.incrementar_solicitacoes()

    assert usuario.pode_solicitar_descarte() is False

def test_incrementar_solicitacao_excede_limite():
    usuario = Cidadao(
        id="1",
        nome="Maria",
        email="maria@email.com",
        cpf="12345678901"
    )

    for _ in range(usuario.MAX_SOLICITACOES_ATIVAS):
        usuario.incrementar_solicitacoes()

    with pytest.raises(Exception):
        usuario.incrementar_solicitacoes()

# ---------------
# TESTES EMPRESA
# ---------------

def test_registrar_descarte_valido():
    empresa = Empresa(
        id="1",
        nome="Tech",
        email="tech@email.com",
        cnpj="12345678901234",
        razao_social="Tech LTDA"
    )

    empresa.registrar_descarte(100)

    assert empresa.pode_solicitar_descarte() is True

def test_registrar_descarte_excede_limite():
    empresa = Empresa(
        id="1",
        nome="Tech",
        email="tech@email.com",
        cnpj="12345678901234",
        razao_social="Tech LTDA"
    )

    with pytest.raises(Exception):
        empresa.registrar_descarte(2000)

def test_resetar_mes():
    empresa = Empresa(
        id="1",
        nome="Tech",
        email="tech@email.com",
        cnpj="12345678901234",
        razao_social="Tech LTDA"
    )

    empresa.registrar_descarte(500)
    empresa.resetar_mes()

    assert empresa.pode_solicitar_descarte() is True

# ---------------------
# TESTES ADMINISTRADOR
# ---------------------

def test_admin_nivel():
    admin = Administrador(
        id="1",
        nome="Admin",
        email="admin@email.com",
        nivel=3
    )

    assert admin.nivel == 3

def test_admin_gerenciar_usuarios():
    admin = Administrador(
        id="1",
        nome="Admin",
        email="admin@email.com",
        nivel=2
    )

    assert admin.pode_gerenciar_usuarios() is True

def test_admin_nao_solicita_descarte():
    admin = Administrador(
        id="1",
        nome="Admin",
        email="admin@email.com",
        nivel=3
    )

    assert admin.pode_solicitar_descarte() is False

# --------------
# TESTES STATUS
# --------------

def test_desativar_usuario():
    usuario = Cidadao(
        id="1",
        nome="Maria",
        email="email@email.com",
        cpf="12345678901"
    )

    usuario.desativar()

    assert usuario.ativo is False


def test_ativar_usuario():
    usuario = Cidadao(
        id="1",
        nome="Maria",
        email="email@email.com",
        cpf="12345678901"
    )

    usuario.desativar()
    usuario.ativar()

    assert usuario.ativo is True