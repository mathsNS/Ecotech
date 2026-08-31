"""Filtros de elegibilidade para coleta domiciliar."""

from datetime import datetime, time, timedelta

import pytest

from ecotech.application.elegibilidade import DemandaColeta, ServicoElegibilidade
from ecotech.domain.logistica import BaseOperacional, Coordenadas, JanelaAtendimento


AGENDAMENTO = datetime(2026, 9, 7, 10)  # segunda-feira


def base(**mudancas):
    dados = dict(
        id='base-1', empresa_id='empresa-1', nome='Centro', endereco='Rua A',
        latitude=0, longitude=0, raio_atendimento_km=20,
        capacidade_kg=100, ocupacao_atual_kg=10,
        categorias_atendidas=('celular',),
        disponibilidade=(JanelaAtendimento(0, time(8), time(18)),),
    )
    dados.update(mudancas)
    return BaseOperacional(**dados)


def demanda(**mudancas):
    dados = dict(
        coordenadas=Coordenadas(0, 0.05), categorias=frozenset({'celular'}),
        peso_kg=5, agendada_para=AGENDAMENTO,
    )
    dados.update(mudancas)
    return DemandaColeta(**dados)


@pytest.mark.parametrize(('alteracao', 'motivo'), [
    ({'empresa_ativa': False}, 'empresa_inativa'),
    ({'ativa': False}, 'base_inativa'),
    ({'realiza_coleta_domiciliar': False}, 'sem_coleta_domiciliar'),
    ({'categorias_atendidas': ('computador',)}, 'categoria_nao_atendida'),
    ({'ocupacao_atual_kg': 98}, 'capacidade_insuficiente'),
    ({'disponibilidade': (JanelaAtendimento(1, time(8), time(18)),)}, 'fora_da_janela'),
    ({'raio_atendimento_km': 1}, 'fora_do_raio'),
    ({'indisponivel_ate': AGENDAMENTO + timedelta(days=1)}, 'temporariamente_indisponivel'),
])
def test_cada_regra_exclui_base(alteracao, motivo):
    avaliacao = ServicoElegibilidade().avaliar(base(**alteracao), demanda(), AGENDAMENTO)
    assert avaliacao.elegivel is False
    assert motivo in avaliacao.motivos


def test_base_elegivel_retorna_distancia_explicavel():
    resultado = ServicoElegibilidade().selecionar([base()], demanda(), AGENDAMENTO)
    assert len(resultado) == 1
    assert resultado[0].distancia_km == pytest.approx(5.56, abs=.2)


def test_categoria_curinga_atende_demanda_com_varias_categorias():
    resultado = ServicoElegibilidade().selecionar(
        [base(categorias_atendidas=('*',))],
        demanda(categorias=frozenset({'celular', 'notebook'})), AGENDAMENTO,
    )
    assert [item.base.id for item in resultado] == ['base-1']
