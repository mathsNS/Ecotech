"""Testes do mecanismo versionado de migrations SQLite."""

import sqlite3

import pytest

from ecotech.domain.descarte import PontoColeta, SolicitacaoDescarte
from ecotech.domain.usuarios import Cidadao, Empresa
from ecotech.infrastructure.persistence.dados import Dados
from ecotech.infrastructure.persistence.migrations import executar_migrations
from ecotech.application.factories import MetodoTratamentoFactory
from ecotech.application.services import (
    ServicoDescarte,
    ServicoPontoColeta,
    ServicoUsuario,
)


@pytest.fixture
def dados(tmp_path, monkeypatch):
    db_path = str(tmp_path / "migrations.db")
    original = sqlite3.connect
    monkeypatch.setattr(
        "ecotech.infrastructure.persistence.dados.sqlite3.connect",
        lambda path, **kwargs: original(db_path, **kwargs),
    )
    return Dados()


def test_banco_vazio_sobe_na_versao_atual(dados):
    assert dados.buscar_versao_schema() == 5
    aplicadas = dados.conn.execute(
        "SELECT versao, nome FROM schema_migration ORDER BY versao"
    ).fetchall()
    assert [(r['versao'], r['nome']) for r in aplicadas] == [
        (1, 'integridade_basica'),
        (2, 'idempotencia_financeira'),
        (3, 'bases_operacionais_localizacao'),
        (4, 'elegibilidade_ranking'),
        (5, 'ofertas_despacho_progressivo'),
    ]


def test_reexecutar_migrations_e_idempotente(dados):
    executar_migrations(dados.conn)
    executar_migrations(dados.conn)
    total = dados.conn.execute(
        "SELECT COUNT(*) FROM schema_migration"
    ).fetchone()[0]
    assert total == 5


def test_migration_cria_estruturas_de_elegibilidade(dados):
    tabelas = {
        row['name'] for row in dados.conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    assert {'base_categoria', 'base_disponibilidade'} <= tabelas
    colunas_base = {
        row['name'] for row in dados.conn.execute(
            "PRAGMA table_info(base_operacional)"
        )
    }
    colunas_solicitacao = {
        row['name'] for row in dados.conn.execute(
            "PRAGMA table_info(solicitacao_descarte)"
        )
    }
    assert 'indisponivel_ate' in colunas_base
    assert 'base_operacional_id' in colunas_solicitacao


def test_migration_cria_ofertas_e_idempotencia_de_notificacao(dados):
    tabelas = {
        row['name'] for row in dados.conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    assert 'oferta_coleta' in tabelas
    colunas_notificacao = {
        row['name'] for row in dados.conn.execute("PRAGMA table_info(notificacao)")
    }
    assert 'chave_idempotencia' in colunas_notificacao


def test_colunas_legadas_sao_adicionadas_sem_ocultar_erros(tmp_path, monkeypatch):
    db_path = str(tmp_path / "legado.db")
    original = sqlite3.connect
    conn = original(db_path)
    conn.execute("""
        CREATE TABLE usuario (
            id TEXT PRIMARY KEY, nome TEXT, email TEXT, data_cadastro TEXT,
            ativo INTEGER, tipo TEXT
        )
    """)
    conn.commit()
    conn.close()
    monkeypatch.setattr(
        "ecotech.infrastructure.persistence.dados.sqlite3.connect",
        lambda path, **kwargs: original(db_path, **kwargs),
    )

    repositorio = Dados()

    colunas = {
        row['name'] for row in repositorio.conn.execute("PRAGMA table_info(usuario)")
    }
    assert 'password_hash' in colunas
    assert repositorio.buscar_versao_schema() == 5


def test_migration_cria_base_para_ponto_empresarial(dados):
    empresa = Empresa(
        'emp-base', 'Empresa Base', 'base@teste.com',
        '11222333000181', 'Empresa Base LTDA'
    )
    ponto = PontoColeta('p-base', 'Ponto Base', 'Rua Base', -7.2, -39.3, 100)
    dados.salvar_empresa(empresa)
    dados.salvar_ponto(ponto)
    dados.vincular_empresa_a_ponto(ponto.id, empresa.id)

    # O backfill ocorre durante a migration; executa a função v3 novamente para
    # comprovar que pontos empresariais podem ser migrados de forma idempotente.
    from ecotech.infrastructure.persistence.migrations.v003_bases_localizacao import aplicar
    with dados.conn:
        aplicar(dados.conn)

    row = dados.conn.execute(
        "SELECT * FROM base_operacional WHERE ponto_coleta_id = ?", (ponto.id,)
    ).fetchone()
    assert row['empresa_id'] == empresa.id
    assert row['raio_atendimento_km'] == pytest.approx(25)


def test_migration_bloqueia_email_duplicado_em_banco_legado(tmp_path, monkeypatch):
    db_path = str(tmp_path / "duplicado.db")
    original = sqlite3.connect
    conn = original(db_path)
    conn.execute("""
        CREATE TABLE usuario (
            id TEXT PRIMARY KEY, nome TEXT, email TEXT, data_cadastro TEXT,
            ativo INTEGER, tipo TEXT, password_hash TEXT
        )
    """)
    conn.executemany(
        "INSERT INTO usuario VALUES (?, ?, ?, '', 1, 'cidadao', '')",
        [('u1', 'Usuário Um', 'duplicado@teste.com'),
         ('u2', 'Usuário Dois', 'duplicado@teste.com')],
    )
    conn.commit()
    conn.close()
    monkeypatch.setattr(
        "ecotech.infrastructure.persistence.dados.sqlite3.connect",
        lambda path, **kwargs: original(db_path, **kwargs),
    )

    with pytest.raises(RuntimeError, match='usuario.email'):
        Dados()


def test_constraints_de_integridade_rejeitam_dados_invalidos(dados):
    with pytest.raises(sqlite3.IntegrityError, match='peso deve ser positivo'):
        dados.conn.execute(
            "INSERT INTO dispositivo (id, nome, peso_kg) VALUES ('d-invalido', 'X', 0)"
        )

    with pytest.raises(sqlite3.IntegrityError, match='empresa do ponto'):
        dados.conn.execute("""
            INSERT INTO ponto_coleta
                (id, nome, endereco, latitude, longitude, ativo,
                 capacidade_kg, ocupacao_atual_kg, id_empresa)
            VALUES ('p-invalido', 'Ponto', 'Rua', 0, 0, 1, 10, 0, 'ausente')
        """)


def test_entrega_e_receita_sao_idempotentes_por_solicitacao(dados):
    cidadao = Cidadao('cid-1', 'Cidadão Teste', 'cid@teste.com', '12345678909')
    empresa = Empresa(
        'emp-1', 'Empresa Teste', 'emp@teste.com', '11222333000181', 'Empresa LTDA'
    )
    ponto = PontoColeta('p-1', 'Ponto', 'Rua', -7.2, -39.3, 100)
    dados.salvar_cidadao(cidadao)
    dados.salvar_empresa(empresa)
    dados.salvar_ponto(ponto)
    dados.vincular_empresa_a_ponto(ponto.id, empresa.id)
    solicitacao = SolicitacaoDescarte('sol-1', cidadao, ponto)
    dados.salvar_solicitacao(solicitacao)

    dados.salvar_entrega_para_solicitacao('sol-1', cidadao.id, 10, empresa.nome)
    dados.salvar_entrega_para_solicitacao('sol-1', cidadao.id, 20, empresa.nome)
    assert dados.conn.execute(
        "SELECT COUNT(*) FROM entrega WHERE id_solicitacao = 'sol-1'"
    ).fetchone()[0] == 1

    assert dados.registrar_receita_ecotech('sol-1', 5) is True
    assert dados.registrar_receita_ecotech('sol-1', 8) is False
    assert dados.buscar_receita_total_ecotech() == pytest.approx(5)


def test_recarregar_solicitacao_reconstroi_tratamento_e_agendamento(dados):
    cidadao = Cidadao('cid-1', 'Cidadão Teste', 'cid@teste.com', '12345678909')
    ponto = PontoColeta('p-1', 'Ponto', 'Rua', -7.2, -39.3, 100)
    dados.salvar_cidadao(cidadao)
    dados.salvar_ponto(ponto)
    solicitacao = SolicitacaoDescarte('sol-1', cidadao, ponto)
    solicitacao.metodo_tratamento = MetodoTratamentoFactory.criar_reciclagem()
    dados.salvar_solicitacao(solicitacao)
    dados.atualizar_detalhes_coleta(
        solicitacao.id, 'entrega_ponto', '', '', '2026-09-10 14:30'
    )

    usuarios = ServicoUsuario(dados)
    pontos = ServicoPontoColeta(dados)
    descartes = ServicoDescarte(dados)
    descartes.set_servicos(usuarios, pontos)
    descartes._carregar_solicitacoes_do_banco()
    recarregada = descartes.obter_solicitacao('sol-1')

    assert recarregada.metodo_tratamento.obter_nome() == 'Reciclagem'
    assert recarregada._data_agendamento.strftime('%Y-%m-%d %H:%M') == '2026-09-10 14:30'
