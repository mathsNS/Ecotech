"""Ordenação determinística e configurável das candidatas."""

from ecotech.application.elegibilidade import BaseElegivel
from ecotech.application.ranking import PesosRanking, ServicoRanking
from ecotech.domain.logistica import BaseOperacional


def candidata(id_base, distancia, ocupacao=0, carga=0):
    base = BaseOperacional(
        id_base, 'empresa', id_base, 'Rua', 0, 0, 50, 100,
        ocupacao_atual_kg=ocupacao, carga_operacional=carga,
    )
    return BaseElegivel(base, distancia)


def test_distancia_domina_em_condicoes_equivalentes():
    ranking = ServicoRanking().ordenar([
        candidata('distante', 10), candidata('proxima', 2),
    ])
    assert [item.base_id for item in ranking] == ['proxima', 'distante']


def test_base_ligeiramente_mais_distante_pode_vencer_base_saturada():
    ranking = ServicoRanking().ordenar([
        candidata('proxima-saturada', 9.5, ocupacao=99, carga=10),
        candidata('distante-livre', 10, ocupacao=0, carga=0),
    ])
    assert ranking[0].base_id == 'distante-livre'


def test_desempate_e_estavel_por_id_e_snapshot_e_auditavel():
    ranking = ServicoRanking().ordenar([
        candidata('base-b', 5), candidata('base-a', 5),
    ])
    assert [item.base_id for item in ranking] == ['base-a', 'base-b']
    assert ranking[0].snapshot['pesos']['distancia'] == .6
    assert set(ranking[0].snapshot['fatores']) == {
        'distancia', 'disponibilidade', 'capacidade', 'carga'
    }


def test_pesos_configuraveis_alteram_ordem_previsivelmente():
    candidatas = [
        candidata('proxima-cheia', 2, ocupacao=90),
        candidata('distante-livre', 10, ocupacao=0),
    ]
    por_distancia = ServicoRanking(PesosRanking(1, 0, 0, 0)).ordenar(candidatas)
    por_capacidade = ServicoRanking(PesosRanking(0, 0, 1, 0)).ordenar(candidatas)
    assert por_distancia[0].base_id == 'proxima-cheia'
    assert por_capacidade[0].base_id == 'distante-livre'
