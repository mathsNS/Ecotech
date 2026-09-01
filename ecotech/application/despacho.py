"""Criação e progressão persistente de ofertas de coleta."""

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta

from .elegibilidade import DemandaColeta, ServicoElegibilidade
from .ranking import ServicoRanking
from .services import ServicoBaseOperacional
from ..domain.logistica import OfertaColeta
from ..domain.repositorio import RepositorioBase


@dataclass(frozen=True)
class ConfiguracaoDespacho:
    tamanhos_lotes: tuple[int, ...] = (1, 2, 3)
    prazo_resposta_minutos: int = 5

    def __post_init__(self):
        if not self.tamanhos_lotes or any(tamanho <= 0 for tamanho in self.tamanhos_lotes):
            raise ValueError("lotes devem possuir tamanhos positivos")
        if self.prazo_resposta_minutos <= 0:
            raise ValueError("prazo de resposta deve ser positivo")


class ServicoDespacho:
    def __init__(
        self, dados: RepositorioBase,
        bases: ServicoBaseOperacional | None = None,
        elegibilidade: ServicoElegibilidade | None = None,
        ranking: ServicoRanking | None = None,
        configuracao: ConfiguracaoDespacho | None = None,
    ):
        self._dados = dados
        self._bases = bases or ServicoBaseOperacional(dados)
        self._elegibilidade = elegibilidade or ServicoElegibilidade()
        self._ranking = ranking or ServicoRanking()
        self._config = configuracao or ConfiguracaoDespacho()

    def _rodada(self, prioridade: int) -> int:
        restante = prioridade
        rodada = 1
        for tamanho in self._config.tamanhos_lotes:
            if restante <= tamanho:
                return rodada
            restante -= tamanho
            rodada += 1
        ultimo = self._config.tamanhos_lotes[-1]
        return rodada + (restante - 1) // ultimo

    @staticmethod
    def _iso(instante: datetime) -> str:
        return instante.isoformat(timespec='seconds')

    def _expiracao(self, agora: datetime) -> datetime:
        return agora + timedelta(minutes=self._config.prazo_resposta_minutos)

    def criar_ofertas(
        self, solicitacao_id: str, demanda: DemandaColeta,
        agora: datetime | None = None,
    ):
        agora = agora or datetime.now()
        bases = self._bases.listar_candidatas()
        por_id = {base.id: base for base in bases}
        elegiveis = self._elegibilidade.selecionar(bases, demanda, agora)
        ranking = self._ranking.ordenar(elegiveis)
        dados_visiveis = {
            'regiao': demanda.regiao.strip(),
            'categorias': sorted(demanda.categorias),
            'peso_estimado_kg': demanda.peso_kg,
            'agendada_para': self._iso(demanda.agendada_para),
        }
        ofertas = [
            OfertaColeta(
                id=str(uuid.uuid4()), solicitacao_id=solicitacao_id,
                empresa_id=por_id[item.base_id].empresa_id,
                base_operacional_id=item.base_id,
                distancia_km=item.snapshot['distancia_km'],
                score_prioridade=item.score, prioridade=item.posicao,
                rodada=self._rodada(item.posicao),
                snapshot_fatores={**item.snapshot, 'dados_visiveis': dados_visiveis},
            ) for item in ranking
        ]
        if not ofertas:
            self._dados.marcar_despacho_esgotado(
                solicitacao_id, self._iso(agora)
            )
            return []
        self._dados.salvar_ofertas_coleta(ofertas, self._iso(agora))
        ativas = self._dados.ativar_proxima_rodada_ofertas(
            solicitacao_id, self._iso(agora), self._iso(self._expiracao(agora))
        )
        self._notificar_ativas(ativas)
        return ativas

    def processar_ofertas_expiradas(self, agora: datetime | None = None):
        agora = agora or datetime.now()
        ativas = self._dados.expirar_ofertas_vencidas(
            self._iso(agora), self._iso(self._expiracao(agora))
        )
        self._notificar_ativas(ativas)
        return ativas

    def aceitar(
        self, oferta_id: str, empresa_id: str,
        agora: datetime | None = None,
    ):
        agora = agora or datetime.now()
        return self._dados.aceitar_oferta_coleta(
            oferta_id, empresa_id, self._iso(agora)
        )

    def listar_ofertas_ativas(self, empresa_id: str) -> list[dict]:
        resultado = []
        for oferta in self._dados.buscar_ofertas_ativas_empresa(empresa_id):
            snapshot = json.loads(oferta['snapshot_fatores'])
            resultado.append({
                'id': oferta['id'],
                'solicitacao_id': oferta['solicitacao_id'],
                'base_operacional_id': oferta['base_operacional_id'],
                'distancia_km': oferta['distancia_km'],
                'expira_em': oferta['expira_em'],
                'dados': snapshot.get('dados_visiveis', {}),
            })
        return resultado

    def _notificar_ativas(self, ofertas) -> None:
        for oferta in ofertas:
            snapshot = json.loads(oferta['snapshot_fatores'])
            visivel = snapshot.get('dados_visiveis', {})
            categorias = ', '.join(visivel.get('categorias', [])) or 'eletrônicos'
            agenda = visivel.get('agendada_para', '')
            mensagem = (
                f'Nova oportunidade de coleta: {categorias}, '
                f'{visivel.get("peso_estimado_kg", 0):g} kg estimados, '
                f'aproximadamente {oferta["distancia_km"]:.1f} km da sua base, '
                f'janela solicitada em {agenda}. Acesse o sistema para responder.'
            )
            self._dados.salvar_notificacao(
                oferta['empresa_id'], mensagem,
                chave_idempotencia=f'oferta:{oferta["id"]}:ativa',
            )
