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
from ..domain.estados import (
    Solicitado, Coletado, EmProcessamento,
    Reciclado, Reutilizado, Descartado, Cancelado
)
from ..infrastructure.persistence.dados import Dados


def _criar_estado_do_banco(nome_estado: str):
    """Converte string do banco para instância de estado."""
    mapa_estados = {
        'SOLICITADO': Solicitado,
        'COLETADO': Coletado,
        'EM_PROCESSAMENTO': EmProcessamento,
        'RECICLADO': Reciclado,
        'REUTILIZADO': Reutilizado,
        'DESCARTADO': Descartado,
        'CANCELADO': Cancelado
    }
    
    classe_estado = mapa_estados.get(nome_estado, Solicitado)
    return classe_estado()


class ServicoDescarte:
    # camada de aplicacao para gerenciar solicitacoes de descarte
    # orquestra as regras de negocio do dominio
    # agora com persistencia no banco de dados
    
    def __init__(self, dados: Optional[Dados] = None, servico_usuario=None, servico_ponto=None):
        self._dados = dados or Dados()
        self._servico_usuario = servico_usuario
        self._servico_ponto = servico_ponto
        self._solicitacoes: Dict[str, SolicitacaoDescarte] = {}
    
    def set_servicos(self, servico_usuario, servico_ponto):
        """Define os servicos auxiliares (para resolver dependencias circulares)."""
        self._servico_usuario = servico_usuario
        self._servico_ponto = servico_ponto
    
    def _carregar_solicitacoes_do_banco(self):
        """Carrega todas as solicitacoes do banco de dados."""
        if not self._servico_usuario or not self._servico_ponto:
            return  # precisa dos servicos pra reconstruir
        
        from .factories import DispositivoFactory
        
        solicitacoes_db = self._dados.buscar_todas_solicitacoes()
        
        for row in solicitacoes_db:
            try:
                # busca usuario e ponto  
                usuario = self._servico_usuario.buscar_usuario(row['id_usuario'])
                ponto = self._servico_ponto.buscar_ponto(row['id_ponto_coleta']) if row['id_ponto_coleta'] else None
                
                if not usuario:
                    continue
                
                # reconstroi a solicitacao
                solicitacao = SolicitacaoDescarte(row['id'], usuario, ponto)
                
                # reconstroi o estado correto do banco
                estado = _criar_estado_do_banco(row['estado'])
                solicitacao._estado = estado
                
                # busca e adiciona os itens
                itens_db = self._dados.buscar_itens_solicitacao(row['id'])
                for item_row in itens_db:
                    # cria dispositivo simplificado
                    dispositivo = DispositivoFactory.criar_celular(
                        item_row['id_dispositivo'],
                        item_row['nome'],
                        item_row['peso_kg']
                    )
                    item = ItemDescarte(dispositivo, item_row['quantidade'], item_row['observacoes'] or '')
                    solicitacao._itens.append(item)
                
                # adiciona ao cache
                self._solicitacoes[row['id']] = solicitacao
                
            except Exception as e:
                # ignora solicitacoes com erro e continua
                print(f"[AVISO] erro ao carregar solicitacao {row['id']}: {e}")
                continue

    def criar_solicitacao(
        self,
        usuario: Usuario,
        ponto_coleta: Optional[PontoColeta] = None
    ) -> SolicitacaoDescarte:
        # cria uma nova solicitacao com id unico
        id_solicitacao = str(uuid.uuid4())
        solicitacao = SolicitacaoDescarte(id_solicitacao, usuario, ponto_coleta)
        self._solicitacoes[id_solicitacao] = solicitacao
        
        # persiste no banco se tiver ponto de coleta
        if ponto_coleta:
            self._dados.salvar_solicitacao(solicitacao)
        
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
        
        # salva dispositivo e item no banco
        self._dados.salvar_dispositivo(dispositivo)
        self._dados.salvar_itens_descarte(solicitacao.id, item)
        
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
        
        # persiste a solicitacao completa no banco
        self._dados.salvar_solicitacao(solicitacao)

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
        # carrega do banco se o cache estiver vazio
        if not self._solicitacoes and self._servico_usuario and self._servico_ponto:
            self._carregar_solicitacoes_do_banco()
        
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
    # agora com persistencia no banco
    
    def __init__(self, dados: Optional[Dados] = None):
        self._dados = dados or Dados()
        self._pontos: Dict[str, PontoColeta] = {}
        self._carregar_pontos()
    
    def _carregar_pontos(self):
        # carrega pontos do banco para o cache
        pontos_db = self._dados.buscar_todos_pontos_coleta()
        for p in pontos_db:
            ponto = PontoColeta(
                p['id'], 
                p['nome'], 
                p['endereco'], 
                p['latitude'], 
                p['longitude'], 
                p['capacidade_kg']
            )
            ponto.ocupacao_atual = p['ocupacao_atual_kg']
            self._pontos[p['id']] = ponto
    
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
        
        # persiste no banco
        self._dados.salvar_ponto(ponto)
        
        return ponto
    
    def adicionar_ponto(self, ponto: PontoColeta):
        self._pontos[ponto.id] = ponto
    
    def listar_pontos(self) -> List[PontoColeta]:
        return list(self._pontos.values())
    
    def buscar_ponto(self, id: str) -> Optional[PontoColeta]:
        return self._pontos.get(id)


class ServicoUsuario:
    # servico para gerenciar usuarios
    # com persistencia no banco
    
    def __init__(self, dados: Optional[Dados] = None):
        self._dados = dados or Dados()
        self._usuarios: Dict[str, Usuario] = {}
        self._carregar_usuarios()
    
    def _carregar_usuarios(self):
        # carrega usuarios do banco para o cache
        usuarios_db = self._dados.buscar_todos_usuarios()
        for u in usuarios_db:
            # reconstroi objetos de usuario baseado no tipo
            if u['tipo'] == 'Cidadao':
                dados_cidadao = self._dados.buscar_cidadao(u['id'])
                if dados_cidadao:
                    usuario = Cidadao(
                        dados_cidadao['id'],
                        dados_cidadao['nome'],
                        dados_cidadao['email'],
                        dados_cidadao['cpf']
                    )
                    self._usuarios[u['id']] = usuario
            elif u['tipo'] == 'Empresa':
                dados_empresa = self._dados.buscar_empresa(u['id'])
                if dados_empresa:
                    usuario = Empresa(
                        dados_empresa['id'],
                        dados_empresa['nome'],
                        dados_empresa['email'],
                        dados_empresa['cnpj'],
                        dados_empresa['razao_social']
                    )
                    self._usuarios[u['id']] = usuario
    
    def criar_usuario(self, tipo: str, dados: Dict) -> Usuario:
        from .factories import UsuarioFactory
        
        # gera id se nao tiver um especificado
        if 'id' not in dados:
            dados['id'] = str(uuid.uuid4())
        
        usuario = UsuarioFactory.criar_usuario(tipo, dados)
        self._usuarios[usuario.id] = usuario
        
        # persiste no banco
        if tipo == 'cidadao':
            self._dados.salvar_cidadao(usuario)
        elif tipo == 'empresa':
            self._dados.salvar_empresa(usuario)
        elif tipo == 'administrador':
            self._dados.salvar_administrador(usuario)
        
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

