from typing import List, Optional, Dict
from datetime import datetime
import uuid

# temporario - melhorar validacoes depois

from ..domain.usuarios import Usuario, Cidadao, Empresa, Administrador
from ..domain.dispositivos import DispositivoEletronico
from ..domain.descarte import (
    SolicitacaoDescarte, 
    ItemDescarte, 
    PontoColeta
)
from ..domain.tratamento import MetodoTratamento
from ..domain.relatorio import RelatorioAmbiental


class ServicoDescarte:
    # camada de aplicacao para gerenciar solicitacoes de descarte
    # orquestra as regras de negocio do dominio
    
    def __init__(self):
        self._solicitacoes: Dict[str, SolicitacaoDescarte] = {}

    def criar_solicitacao(
        self,
        usuario: Usuario,
        ponto_coleta: Optional[PontoColeta] = None
    ) -> SolicitacaoDescarte:
        # cria uma nova solicitacao com id unico
        id_solicitacao = str(uuid.uuid4())
        solicitacao = SolicitacaoDescarte(id_solicitacao, usuario, ponto_coleta)
        self._solicitacoes[id_solicitacao] = solicitacao
        # print(f"[DEBUG] solicitacao criada: {id_solicitacao}")
        return solicitacao

    def adicionar_item_solicitacao(
        self,
        solicitacao: SolicitacaoDescarte,
        dispositivo: DispositivoEletronico,
        quantidade: int = 1,
        observacoes: str = ""
    ) -> ItemDescarte:
        # adiciona um dispositivo a solicitacao
        item = ItemDescarte(dispositivo, quantidade, observacoes)
        solicitacao.adicionar_item(item)
        return item

    def definir_ponto_coleta(
        self,
        solicitacao: SolicitacaoDescarte,
        ponto_coleta: PontoColeta
    ):
        # define onde sera entregue e verifica capacidade
        peso_total = solicitacao.calcular_peso_total()
        
        if not ponto_coleta.pode_receber(peso_total):
            raise ValueError(
                f"ponto de coleta {ponto_coleta.nome} nao tem capacidade"
            )
            
        solicitacao.ponto_coleta = ponto_coleta
        ponto_coleta.adicionar_ocupacao(peso_total)

    def definir_metodo_tratamento(
        self,
        solicitacao: SolicitacaoDescarte,
        metodo: MetodoTratamento
    ):
        # define qual metodo de tratamento sera usado (reciclagem etc)
        solicitacao.metodo_tratamento = metodo

    def avancar_estado_solicitacao(self, solicitacao: SolicitacaoDescarte):
        # avanca pro proximo estado (padrao state)
        solicitacao.avancar_estado()

    def cancelar_solicitacao(self, solicitacao: SolicitacaoDescarte, motivo: str = ""):
        solicitacao.cancelar(motivo)

    def listar_solicitacoes(self) -> List[SolicitacaoDescarte]:
        return list(self._solicitacoes.values())

    def obter_solicitacao(self, id: str) -> Optional[SolicitacaoDescarte]:
        return self._solicitacoes.get(id)


class ServicoRelatorio:
    # M- servico pra gerar relatorios ambientais
    
    def gerar_relatorio_periodo(
        self,
        titulo: str,
        solicitacoes: List[SolicitacaoDescarte]
    ) -> RelatorioAmbiental:
        # M- cria relatorio consolidando as solicitacoes do periodo
        relatorio = RelatorioAmbiental(titulo)
        
        for solicitacao in solicitacoes:
            relatorio.adicionar_solicitacao(solicitacao)
            
        return relatorio


class ServicoPontoColeta:
    # M- servico pra gerenciar pontos de coleta
    
    def __init__(self):
        self._pontos: Dict[str, PontoColeta] = {}
    
    def criar_ponto_coleta(
        self,
        nome: str,
        endereco: str,
        latitude: float,
        longitude: float,
        capacidade_kg: float = 1000.0
    ) -> PontoColeta:
        id_ponto = str(uuid.uuid4())
        ponto = PontoColeta(id_ponto, nome, endereco, latitude, longitude, capacidade_kg)
        self._pontos[id_ponto] = ponto
        return ponto
    
    def adicionar_ponto(self, ponto: PontoColeta):
        self._pontos[ponto.id] = ponto
    
    def listar_pontos(self) -> List[PontoColeta]:
        return list(self._pontos.values())
    
    def buscar_ponto(self, id: str) -> Optional[PontoColeta]:
        return self._pontos.get(id)


class ServicoUsuario:
    
    def __init__(self):
        self._usuarios: Dict[str, Usuario] = {}
    
    def criar_usuario(self, tipo: str, dados: Dict) -> Usuario:
        from .factories import UsuarioFactory
        id_usuario = str(uuid.uuid4())
        dados['id'] = id_usuario
        usuario = UsuarioFactory.criar_usuario(tipo, dados)
        self._usuarios[id_usuario] = usuario
        return usuario
    
    def buscar_usuario(self, id: str) -> Optional[Usuario]:
        return self._usuarios.get(id)
    
    def autenticar_usuario(self, email: str) -> Optional[Usuario]:
        for usuario in self._usuarios.values():
            if usuario.email == email:
                return usuario
        return None
    
    def listar_usuarios(self) -> List[Usuario]:
        return list(self._usuarios.values())

