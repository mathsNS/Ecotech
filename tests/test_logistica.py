"""Testes de bases operacionais, localização e distância."""

import sqlite3

import pytest

from ecotech.application.geolocalizacao import (
    DistanciaHaversine,
    GeolocalizadorCoordenadasInformadas,
)
from ecotech.application.services import ServicoBaseOperacional
from ecotech.domain.logistica import BaseOperacional, Coordenadas
from ecotech.domain.usuarios import Empresa
from ecotech.infrastructure.persistence.dados import Dados


def test_coordenadas_validam_intervalos():
    assert Coordenadas(-7.2, -39.3).latitude == pytest.approx(-7.2)
    with pytest.raises(ValueError, match='latitude'):
        Coordenadas(91, 0)
    with pytest.raises(ValueError, match='longitude'):
        Coordenadas(0, -181)


def test_haversine_distancia_zero():
    ponto = Coordenadas(-7.2134, -39.3153)
    assert DistanciaHaversine().calcular_km(ponto, ponto) == 0


def test_haversine_juazeiro_crato():
    juazeiro = Coordenadas(-7.2134, -39.3153)
    crato = Coordenadas(-7.2342, -39.4097)
    distancia = DistanciaHaversine().calcular_km(juazeiro, crato)
    assert distancia == pytest.approx(10.65, abs=0.5)


def test_geolocalizador_exige_endereco_e_coordenadas():
    geolocalizador = GeolocalizadorCoordenadasInformadas()
    assert geolocalizador.localizar('Rua A', '-7.2', '-39.3') == Coordenadas(-7.2, -39.3)
    with pytest.raises(ValueError, match='endereço'):
        geolocalizador.localizar('', '-7.2', '-39.3')
    with pytest.raises(ValueError, match='localização'):
        geolocalizador.localizar('Rua A', '', '')


def test_base_operacional_valida_capacidade_e_raio():
    with pytest.raises(ValueError, match='raio'):
        BaseOperacional('b', 'e', 'Base', 'Rua', 0, 0, 0, 100)
    with pytest.raises(ValueError, match='ocupação'):
        BaseOperacional('b', 'e', 'Base', 'Rua', 0, 0, 10, 100, 101)


@pytest.fixture
def servico(tmp_path, monkeypatch):
    caminho = str(tmp_path / 'bases.db')
    original = sqlite3.connect
    monkeypatch.setattr(
        'ecotech.infrastructure.persistence.dados.sqlite3.connect',
        lambda path, **kwargs: original(caminho, **kwargs),
    )
    dados = Dados()
    empresa = Empresa(
        'emp-1', 'Empresa Teste', 'empresa@teste.com',
        '11222333000181', 'Empresa Teste LTDA'
    )
    dados.salvar_empresa(empresa)
    return ServicoBaseOperacional(dados), dados


def _dados_base(**sobrescrever):
    dados = {
        'nome': 'Base Centro', 'endereco': 'Rua A, 1',
        'latitude': -7.2, 'longitude': -39.3,
        'raio_atendimento_km': 20, 'capacidade_kg': 500,
        'realiza_coleta_domiciliar': True,
    }
    dados.update(sobrescrever)
    return dados


def test_crud_base_operacional_respeita_empresa(servico):
    bases, dados = servico
    base = bases.criar('emp-1', _dados_base())
    assert bases.listar_empresa('emp-1')[0].id == base.id

    atualizada = bases.atualizar(
        'emp-1', base.id, _dados_base(nome='Base Atualizada', raio_atendimento_km=30)
    )
    assert atualizada.nome == 'Base Atualizada'
    assert atualizada.raio_atendimento_km == pytest.approx(30)

    bases.definir_atividade('emp-1', base.id, False)
    assert bases.buscar(base.id).ativa is False
    with pytest.raises(PermissionError):
        bases.atualizar('outra-empresa', base.id, _dados_base())


def test_persistir_localizacao_apenas_em_coleta_domiciliar(servico):
    _, dados = servico
    from ecotech.domain.descarte import SolicitacaoDescarte
    from ecotech.domain.usuarios import Cidadao
    cidadao = Cidadao('cid-1', 'Cidadão Teste', 'cid@teste.com', '12345678909')
    dados.salvar_cidadao(cidadao)
    solicitacao = SolicitacaoDescarte('sol-1', cidadao)
    dados.salvar_solicitacao(solicitacao)
    dados.atualizar_detalhes_coleta('sol-1', 'domiciliar', 'Rua A', 'Teste', '')

    dados.atualizar_localizacao_coleta('sol-1', -7.2, -39.3, 'teste')
    row = dados.buscar_solicitacao('sol-1')
    assert row['latitude_coleta'] == pytest.approx(-7.2)
    assert row['longitude_coleta'] == pytest.approx(-39.3)
