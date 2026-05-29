"""Testes para _validar_cpf e _validar_cnpj e sua integração em ServicoUsuario."""

import sqlite3
import pytest

from ecotech.application.services import _validar_cpf, _validar_cnpj, ServicoUsuario
from ecotech.infrastructure.persistence.dados import Dados


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def dados(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test.db")
    _orig = sqlite3.connect
    monkeypatch.setattr(
        "ecotech.infrastructure.persistence.dados.sqlite3.connect",
        lambda path, **kwargs: _orig(db_path, **kwargs),
    )
    return Dados()


@pytest.fixture
def servico(dados):
    return ServicoUsuario(dados)


# ---------------------------------------------------------------------------
# _validar_cpf
# ---------------------------------------------------------------------------

# CPFs válidos conhecidos (gerados com algoritmo correto)
@pytest.mark.parametrize("cpf", [
    "12345678909",   # João Silva (seed)
    "98765432100",   # Ana Beatriz (seed)
    "34945611840",   # Carlos Eduardo (seed)
    "47585901330",   # Fernanda Lima (seed)
    "70548478490",   # Rafael Gonçalves (seed)
])
def test_cpf_valido(cpf):
    assert _validar_cpf(cpf) is True


@pytest.mark.parametrize("cpf", [
    "00000000000",   # todos zeros
    "11111111111",   # todos iguais
    "12345678900",   # dígito verificador errado
    "1234567890",    # curto demais (10 dígitos)
    "123456789099",  # longo demais (12 dígitos)
    "1234567890a",   # contém letra
    "",              # vazio
])
def test_cpf_invalido(cpf):
    assert _validar_cpf(cpf) is False


# ---------------------------------------------------------------------------
# _validar_cnpj
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cnpj", [
    "11222333000181",  # Recicla Kariri (seed)
    "14380200000121",  # TechLixo (seed)
    "33000167000101",  # GreenCycle (seed)
])
def test_cnpj_valido(cnpj):
    assert _validar_cnpj(cnpj) is True


@pytest.mark.parametrize("cnpj", [
    "00000000000000",  # todos zeros
    "11111111111111",  # todos iguais
    "11222333000180",  # último dígito errado
    "1122233300018",   # curto demais (13 dígitos)
    "112223330001810", # longo demais (15 dígitos)
    "1122233300018a",  # contém letra
    "",               # vazio
])
def test_cnpj_invalido(cnpj):
    assert _validar_cnpj(cnpj) is False


# ---------------------------------------------------------------------------
# Integração: criar_usuario rejeita CPF/CNPJ inválido
# ---------------------------------------------------------------------------

def test_criar_cidadao_cpf_invalido_levanta_valueerror(servico):
    with pytest.raises(ValueError, match="CPF inválido"):
        servico.criar_usuario('cidadao', {
            'nome': 'Teste', 'email': 't@t.com', 'cpf': '11111111111'
        }, senha='senha123')


def test_criar_cidadao_cpf_valido_cria_usuario(servico):
    u = servico.criar_usuario('cidadao', {
        'nome': 'João Silva', 'email': 'joao@t.com', 'cpf': '12345678909'
    }, senha='senha123')
    assert u is not None
    assert u.cpf == '12345678909'


def test_criar_empresa_cnpj_invalido_levanta_valueerror(servico):
    with pytest.raises(ValueError, match="CNPJ inválido"):
        servico.criar_usuario('empresa', {
            'nome': 'Empresa X', 'email': 'e@e.com',
            'cnpj': '00000000000000', 'razao_social': 'Empresa X LTDA'
        }, senha='senha123')


def test_criar_empresa_cnpj_valido_cria_usuario(servico):
    u = servico.criar_usuario('empresa', {
        'nome': 'Recicla Kariri', 'email': 'rk@t.com',
        'cnpj': '11222333000181', 'razao_social': 'Recicla Kariri LTDA'
    }, senha='senha123')
    assert u is not None
    assert u.cnpj == '11222333000181'


def test_criar_cidadao_cpf_com_pontuacao_e_aceito(servico):
    """CPF com formatação (pontos/traço) deve ser normalizado e aceito."""
    u = servico.criar_usuario('cidadao', {
        'nome': 'Ana Beatriz', 'email': 'ana@t.com', 'cpf': '987.654.321-00'
    }, senha='senha123')
    assert u.cpf == '98765432100'


def test_criar_empresa_cnpj_com_pontuacao_e_aceito(servico):
    """CNPJ com formatação deve ser normalizado e aceito."""
    u = servico.criar_usuario('empresa', {
        'nome': 'TechLixo', 'email': 'tl@t.com',
        'cnpj': '14.380.200/0001-21', 'razao_social': 'TechLixo LTDA'
    }, senha='senha123')
    assert u.cnpj == '14380200000121'


# ---------------------------------------------------------------------------
# Integração: autenticar rejeita CPF/CNPJ inválido sem consultar o banco
# ---------------------------------------------------------------------------

def test_autenticar_cpf_invalido_retorna_none(servico):
    resultado = servico.autenticar('cidadao', '11111111111', 'qualquer')
    assert resultado is None


def test_autenticar_cnpj_invalido_retorna_none(servico):
    resultado = servico.autenticar('empresa', '00000000000000', 'qualquer')
    assert resultado is None
