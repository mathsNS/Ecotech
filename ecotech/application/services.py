from typing import List, Optional, Dict
from datetime import datetime
import uuid

from werkzeug.security import generate_password_hash, check_password_hash

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
from ..domain.repositorio import RepositorioBase


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
    """Gerencia solicitações de descarte e coordena os objetos de domínio."""
    
    def __init__(self, dados: Optional[RepositorioBase] = None, servico_usuario=None, servico_ponto=None):
        self._dados = dados
        self._servico_usuario = servico_usuario
        self._servico_ponto = servico_ponto
        self._solicitacoes: Dict[str, SolicitacaoDescarte] = {}
    
    def set_servicos(self, servico_usuario, servico_ponto):
        """Define os servicos auxiliares (para resolver dependencias circulares)."""
        self._servico_usuario = servico_usuario
        self._servico_ponto = servico_ponto
    
    def _carregar_solicitacoes_do_banco(self):
        """Carrega todas as solicitacoes do banco de dados."""
        if not self._servico_usuario or not self._servico_ponto or not self._dados:
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
                
                # carrega data_criacao do banco 
                if row['data_criacao']:
                    try:
                        solicitacao._data_criacao = datetime.strptime(row['data_criacao'], "%d/%m/%Y %H:%M")
                    except (ValueError, TypeError):
                        pass  # mantém data padrão se o formato for inválido
                
                # carrega metodo de tratamento e impacto evitado do banco
                if row['metodo_tratamento']:
                    solicitacao.metodo_tratamento_str = row['metodo_tratamento']
                
                # busca e adiciona os itens
                itens_db = self._dados.buscar_itens_solicitacao(row['id'])
                for item_row in itens_db:
                    # cria dispositivo com o tipo correto
                    tipo_dispositivo = (item_row['tipo'] or 'celular').lower()
                    if tipo_dispositivo == 'computador':
                        dispositivo = DispositivoFactory.criar_computador(
                            item_row['id_dispositivo'],
                            item_row['nome'],
                            item_row['peso_kg']
                        )
                    elif tipo_dispositivo == 'eletrodomestico':
                        dispositivo = DispositivoFactory.criar_eletrodomestico(
                            item_row['id_dispositivo'],
                            item_row['nome'],
                            item_row['peso_kg']
                        )
                    else:
                        dispositivo = DispositivoFactory.criar_celular(
                            item_row['id_dispositivo'],
                            item_row['nome'],
                            item_row['peso_kg']
                        )
                    item = ItemDescarte(dispositivo, item_row['quantidade'], item_row['observacoes'] or '')
                    solicitacao._itens.append(item)
                
                # calcula impacto evitado após os itens estarem carregados
                solicitacao.impacto_evitado_db = solicitacao.calcular_impacto_total()
                
                # adiciona ao cache
                self._solicitacoes[row['id']] = solicitacao
                
            except (KeyError, ValueError, TypeError) as e:
                continue

    def criar_solicitacao(
        self,
        usuario: Usuario,
        ponto_coleta: Optional[PontoColeta] = None
    ) -> SolicitacaoDescarte:
        """Cria uma nova solicitação com ID único."""
        id_solicitacao = str(uuid.uuid4())
        solicitacao = SolicitacaoDescarte(id_solicitacao, usuario, ponto_coleta)
        self._solicitacoes[id_solicitacao] = solicitacao
        
        if ponto_coleta and self._dados:
            self._dados.salvar_solicitacao(solicitacao)
        
        return solicitacao

    def adicionar_item_solicitacao(
        self,
        solicitacao: SolicitacaoDescarte,
        dispositivo: DispositivoEletronico,
        quantidade: int = 1,
        observacoes: str = ""
    ) -> ItemDescarte:
        """Adiciona um dispositivo à solicitação."""
        item = ItemDescarte(dispositivo, quantidade, observacoes)
        solicitacao.adicionar_item(item)
        
        if self._dados:
            self._dados.salvar_dispositivo(dispositivo)
            self._dados.salvar_itens_descarte(solicitacao.id, item)
        
        return item

    def definir_ponto_coleta(
        self,
        solicitacao: SolicitacaoDescarte,
        ponto_coleta: PontoColeta
    ):
        """Define onde será entregue e verifica capacidade."""
        peso_total = solicitacao.calcular_peso_total()
        
        if not ponto_coleta.pode_receber(peso_total):
            raise ValueError(
                f"ponto de coleta {ponto_coleta.nome} nao tem capacidade"
            )
            
        solicitacao.ponto_coleta = ponto_coleta
        ponto_coleta.adicionar_ocupacao(peso_total)
        
        if self._dados:
            self._dados.salvar_solicitacao(solicitacao)

    def definir_metodo_tratamento(
        self,
        solicitacao: SolicitacaoDescarte,
        metodo: MetodoTratamento
    ):
        """Define qual método de tratamento será usado."""
        solicitacao.metodo_tratamento = metodo
        if self._dados:
            self._dados.atualizar_solicitacao(solicitacao)

    def avancar_estado_solicitacao(self, solicitacao: SolicitacaoDescarte):
        """Avança para o próximo estado (padrão State)."""
        solicitacao.avancar_estado()
        if self._dados:
            self._dados.atualizar_solicitacao(solicitacao)

    def cancelar_solicitacao(self, solicitacao: SolicitacaoDescarte, motivo: str = ""):
        """Cancela uma solicitação com motivo opcional."""
        solicitacao.cancelar(motivo)
        if self._dados:
            self._dados.atualizar_solicitacao(solicitacao)

    def listar_solicitacoes(self) -> List[SolicitacaoDescarte]:
        """Retorna todas as solicitações, carregando do banco se necessário."""
        if not self._solicitacoes and self._servico_usuario and self._servico_ponto:
            self._carregar_solicitacoes_do_banco()
        
        return list(self._solicitacoes.values())

    def obter_solicitacao(self, id: str) -> Optional[SolicitacaoDescarte]:
        """Busca uma solicitação pelo ID."""
        return self._solicitacoes.get(id)


class ServicoRelatorio:
    """Gera relatórios ambientais a partir das solicitações de descarte."""
    
    def gerar_relatorio_periodo(
        self,
        titulo: str,
        solicitacoes: List[SolicitacaoDescarte]
    ) -> RelatorioAmbiental:
        """Cria relatório consolidando as solicitações do período."""
        relatorio = RelatorioAmbiental(titulo)
        
        for solicitacao in solicitacoes:
            relatorio.adicionar_solicitacao(solicitacao)
            
        return relatorio


class ServicoPontoColeta:
    """Gerencia pontos de coleta, com cache em memória e persistência no banco."""
    
    def __init__(self, dados: Optional[RepositorioBase] = None):
        self._dados = dados
        self._pontos: Dict[str, PontoColeta] = {}
        if self._dados:
            self._carregar_pontos()
    
    def _carregar_pontos(self):
        """Carrega pontos do banco para o cache."""
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
            ponto.ocupacao_atual_kg = p['ocupacao_atual_kg']
            self._pontos[p['id']] = ponto
    
    def criar_ponto_coleta(
        self,
        nome: str,
        endereco: str,
        latitude: float,
        longitude: float,
        capacidade_kg: float = 1000.0
    ) -> PontoColeta:
        """Cria e persiste um novo ponto de coleta."""
        id_ponto = str(uuid.uuid4())
        ponto = PontoColeta(id_ponto, nome, endereco, latitude, longitude, capacidade_kg)
        self._pontos[id_ponto] = ponto
        
        if self._dados:
            self._dados.salvar_ponto(ponto)
        
        return ponto
    
    def adicionar_ponto(self, ponto: PontoColeta):
        """Adiciona um ponto de coleta ao cache."""
        self._pontos[ponto.id] = ponto
    
    def listar_pontos(self) -> List[PontoColeta]:
        """Retorna todos os pontos de coleta."""
        return list(self._pontos.values())
    
    def buscar_ponto(self, id: str) -> Optional[PontoColeta]:
        """Busca um ponto de coleta pelo ID."""
        return self._pontos.get(id)


class ServicoUsuario:
    """Gerencia cadastro, autenticação e consulta de usuários."""
    
    def __init__(self, dados: Optional[RepositorioBase] = None):
        self._dados = dados
        self._usuarios: Dict[str, Usuario] = {}
        if self._dados:
            self._carregar_usuarios()
    
    def _carregar_usuarios(self):
        """Carrega usuários do banco para o cache."""
        usuarios_db = self._dados.buscar_todos_usuarios()
        for u in usuarios_db:
            # reconstroi objetos de usuario baseado no tipo
            if u['tipo'] == 'cidadao':
                dados_cidadao = self._dados.buscar_cidadao(u['id'])
                if dados_cidadao:
                    usuario = Cidadao(
                        dados_cidadao['id'],
                        dados_cidadao['nome'],
                        dados_cidadao['email'],
                        dados_cidadao['cpf']
                    )
                    self._usuarios[u['id']] = usuario
            elif u['tipo'] == 'empresa':
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
            elif u['tipo'] == 'administrador':
                usuario = Administrador(
                    u['id'],
                    u['nome'],
                    u['email']
                )
                self._usuarios[u['id']] = usuario
    
    def criar_usuario(self, tipo: str, dados: Dict, senha: str = "") -> Usuario:
        """Cria e persiste um usuário. Gera hash da senha se fornecida."""
        from .factories import UsuarioFactory
        
        if 'id' not in dados:
            dados['id'] = str(uuid.uuid4())
        
        usuario = UsuarioFactory.criar_usuario(tipo, dados)
        self._usuarios[usuario.id] = usuario
        
        password_hash = generate_password_hash(senha) if senha else ""
        
        if self._dados:
            if tipo == 'cidadao':
                self._dados.salvar_cidadao(usuario, password_hash)
            elif tipo == 'empresa':
                self._dados.salvar_empresa(usuario, password_hash)
            elif tipo == 'administrador':
                self._dados.salvar_administrador(usuario, password_hash)
        
        return usuario
    
    def buscar_usuario(self, id: str) -> Optional[Usuario]:
        """Busca um usuário pelo ID."""
        return self._usuarios.get(id)

    def autenticar(self, tipo: str, credencial: str, senha: str) -> Optional[Usuario]:
        """Verifica credencial (CPF/CNPJ/email) e senha. Retorna o usuário ou None."""
        if not self._dados:
            return None

        if tipo == 'cidadao':
            row = self._dados.buscar_usuario_por_cpf(credencial)
        elif tipo == 'empresa':
            row = self._dados.buscar_usuario_por_cnpj(credencial)
        elif tipo == 'administrador':
            row = self._dados.buscar_usuario_por_email(credencial)
        else:
            return None

        if not row:
            return None

        hash_armazenado = row['password_hash'] or ""
        if not hash_armazenado or not check_password_hash(hash_armazenado, senha):
            return None

        return self._usuarios.get(row['id'])
    
    def listar_usuarios(self) -> List[Usuario]:
        """Retorna todos os usuários cadastrados."""
        return list(self._usuarios.values())

