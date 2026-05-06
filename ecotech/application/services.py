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
from ..domain.repositorio import RepositorioBase


class ServicoDescarte:
    """Gerencia solicitações de descarte e coordena os objetos de domínio."""

    _TIERS = [
        (0,    'Bronze',  300,  'Prata'),
        (300,  'Prata',   600,  'Ouro'),
        (600,  'Ouro',    1200, 'Platina'),
        (1200, 'Platina', None, None),
    ]

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
        
        from .factories import DispositivoFactory, EstadoFactory

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
                estado = EstadoFactory.criar_do_banco(row['estado'])
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
        if not usuario.pode_solicitar_descarte():
            raise ValueError("usuario nao pode realizar descarte no momento")
        id_solicitacao = str(uuid.uuid4())
        solicitacao = SolicitacaoDescarte(id_solicitacao, usuario, ponto_coleta)
        self._solicitacoes[id_solicitacao] = solicitacao
        
        if self._dados:
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
            estado = solicitacao.estado.obter_nome().upper().replace(' ', '_')
            self._dados.atualizar_solicitacao(solicitacao.id, estado, metodo.obter_nome())

    def avancar_estado_solicitacao(self, solicitacao: SolicitacaoDescarte):
        """Avança para o próximo estado (padrão State)."""
        solicitacao.avancar_estado()
        if self._dados:
            estado = solicitacao.estado.obter_nome().upper().replace(' ', '_')
            self._dados.atualizar_solicitacao(solicitacao.id, estado)

    def cancelar_solicitacao(self, solicitacao: SolicitacaoDescarte, motivo: str = ""):
        """Cancela uma solicitação com motivo opcional."""
        solicitacao.cancelar(motivo)
        if self._dados:
            estado = solicitacao.estado.obter_nome().upper().replace(' ', '_')
            self._dados.atualizar_solicitacao(solicitacao.id, estado)

    def listar_solicitacoes(self) -> List[SolicitacaoDescarte]:
        """Retorna todas as solicitações, carregando do banco se necessário."""
        if not self._solicitacoes and self._servico_usuario and self._servico_ponto:
            self._carregar_solicitacoes_do_banco()
        
        return list(self._solicitacoes.values())

    def obter_solicitacao(self, id: str) -> Optional[SolicitacaoDescarte]:
        """Busca uma solicitação pelo ID."""
        return self._solicitacoes.get(id)

    @staticmethod
    def calcular_metricas(solicitacoes: List[SolicitacaoDescarte]) -> dict:
        """Retorna peso_total, impacto_total, pontos e total_processadas para a lista dada."""
        _finais = {'Reciclado', 'Reutilizado', 'Descartado'}
        peso_total = sum(s.calcular_peso_total() for s in solicitacoes)
        return {
            'peso_total': peso_total,
            'impacto_total': sum(s.calcular_impacto_total() for s in solicitacoes),
            'pontos': int(peso_total * 10),
            'total_processadas': sum(1 for s in solicitacoes if s.estado.obter_nome() in _finais),
        }

    @staticmethod
    def calcular_progresso(solicitacoes: List[SolicitacaoDescarte],
                           meta_missao: int = 15, meta_tier: int = 1200) -> dict:
        """Retorna progresso_missao e progresso_tier como inteiros 0–100."""
        pontos = int(sum(s.calcular_peso_total() for s in solicitacoes) * 10)
        return {
            'progresso_missao': min(round((len(solicitacoes) / meta_missao) * 100), 100),
            'progresso_tier': min(round((pontos / meta_tier) * 100), 100),
        }

    @staticmethod
    def filtrar_por_estado(solicitacoes: List[SolicitacaoDescarte], estado: str = '') -> List[SolicitacaoDescarte]:
        """Filtra a lista pelo nome do estado (case-insensitive, substring). Sem filtro devolve tudo."""
        if not estado:
            return solicitacoes
        return [s for s in solicitacoes if estado.lower() in s.estado.obter_nome().lower()]

    @staticmethod
    def calcular_stats_estados(solicitacoes: List[SolicitacaoDescarte]) -> dict:
        """Conta solicitações por grupo de estado."""
        _finais = {'Reciclado', 'Reutilizado', 'Descartado'}
        return {
            'pendentes':   sum(1 for s in solicitacoes if s.estado.obter_nome() == 'Solicitado'),
            'em_coleta':   sum(1 for s in solicitacoes if s.estado.obter_nome() == 'Coletado'),
            'processando': sum(1 for s in solicitacoes if s.estado.obter_nome() == 'Em Processamento'),
            'finalizadas': sum(1 for s in solicitacoes if s.estado.obter_nome() in _finais),
        }

    @staticmethod
    def calcular_info_tier(pontos: int) -> dict:
        """Retorna nome, meta, proximo_nome e progresso_pct do tier atual."""
        for minimo, nome, meta, proximo in reversed(ServicoDescarte._TIERS):
            if pontos >= minimo:
                progresso_pct = min(round((pontos / meta) * 100), 100) if meta else 100
                return {
                    'nome': nome,
                    'meta': meta,
                    'proximo_nome': proximo or '-',
                    'progresso_pct': progresso_pct,
                }
        return {'nome': 'Bronze', 'meta': 300, 'proximo_nome': 'Prata', 'progresso_pct': 0}


class ServicoRelatorio:
    """Gera relatórios ambientais a partir das solicitações de descarte."""
    
    def gerar_relatorio_periodo(
        self,
        titulo: str,
        solicitacoes: List[SolicitacaoDescarte],
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None
    ) -> RelatorioAmbiental:
        """Cria relatório consolidando as solicitações do período."""
        relatorio = RelatorioAmbiental(titulo)

        for solicitacao in solicitacoes:
            if data_inicio and solicitacao._data_criacao < data_inicio:
                continue
            if data_fim and solicitacao._data_criacao > data_fim:
                continue
            relatorio.adicionar_solicitacao(solicitacao)

        return relatorio


class ServicoSaque:
    """Gerencia o saldo de pontos do usuário e solicitações de saque."""

    TAXA_PONTOS_POR_KG = 10       # pontos ganhos por kg descartado
    TAXA_REAIS_POR_PONTO = 0.01   # R$ por ponto (100 pts = R$ 1,00)

    def __init__(self, dados: Optional[RepositorioBase] = None):
        self._dados = dados

    def calcular_pontos(self, solicitacoes: List[SolicitacaoDescarte], id_usuario: str) -> int:
        """Retorna os pontos acumulados com base no peso total descartado."""
        peso_total = sum(
            s.calcular_peso_total()
            for s in solicitacoes
            if s.usuario.id == id_usuario
        )
        return int(peso_total * self.TAXA_PONTOS_POR_KG)

    def calcular_saldo_disponivel(
        self,
        solicitacoes: List[SolicitacaoDescarte],
        id_usuario: str
    ) -> float:
        """
        Calcula o saldo disponível em R$ para saque.

        Fórmula: (pontos_acumulados × 0,01) − total_já_sacado
        """
        pontos = self.calcular_pontos(solicitacoes, id_usuario)
        saldo_bruto = round(pontos * self.TAXA_REAIS_POR_PONTO, 2)

        total_sacado = 0.0
        if self._dados:
            total_sacado = self._dados.buscar_total_sacado_usuario(id_usuario)

        return max(0.0, round(saldo_bruto - total_sacado, 2))

    def solicitar_saque(
        self,
        id_usuario: str,
        valor: float,
        metodo: str,
        saldo_disponivel: float
    ) -> Dict:
        """
        Registra uma solicitação de saque.

        Raises:
            ValueError: Se o valor for inválido ou exceder o saldo disponível.
        """
        if valor <= 0:
            raise ValueError("O valor do saque deve ser positivo.")
        if valor > saldo_disponivel:
            raise ValueError(
                f"Saldo insuficiente. Disponível: R$ {saldo_disponivel:.2f}"
            )

        id_saque = str(uuid.uuid4())[:12]
        agora = datetime.now()
        data = agora.strftime('%d %b %Y')
        hora = agora.strftime('%H:%M')

        if self._dados:
            self._dados.salvar_saque(
                id_saque, id_usuario, valor, metodo, data, hora, 'pendente'
            )

        return {
            'id': id_saque,
            'valor': valor,
            'metodo': metodo,
            'data': data,
            'hora': hora,
            'status': 'pendente',
        }

    def listar_saques(self, id_usuario: str) -> List[Dict]:
        """Retorna o histórico de saques do usuário."""
        if not self._dados:
            return []
        rows = self._dados.buscar_saques_usuario(id_usuario)
        return [dict(r) for r in rows]


class ServicoAutenticacao:
    """Gerencia autenticação e ciclo de vida seguro da sessão."""

    TIPOS_VALIDOS = ('cidadao', 'empresa', 'administrador')

    _TIPO_NORMALIZACAO = {
        'cidadão': 'cidadao',
        'empresa': 'empresa',
        'administrador': 'administrador',
    }

    def __init__(self, servico_usuario: 'ServicoUsuario'):
        self._servico_usuario = servico_usuario

    def autenticar(self, tipo: str, credencial: str, senha: str) -> Optional[Usuario]:
        """
        Valida credencial e senha. Retorna o objeto Usuario ou None.

        Args:
            tipo: 'cidadao', 'empresa' ou 'administrador'.
            credencial: CPF (cidadao), CNPJ (empresa) ou e-mail (administrador).
            senha: Senha em texto claro (comparada ao hash armazenado).
        """
        if tipo not in self.TIPOS_VALIDOS:
            return None
        return self._servico_usuario.autenticar(tipo, credencial, senha)

    def criar_dados_sessao(self, usuario: Usuario) -> Dict:
        """Gera o dicionário de dados a serem gravados na sessão Flask."""
        tipo_raw = usuario.obter_tipo().split()[0].lower()
        tipo_normalizado = self._TIPO_NORMALIZACAO.get(tipo_raw, tipo_raw)
        return {
            'user_id': usuario.id,
            'user_nome': usuario.nome,
            'user_tipo': tipo_normalizado,
        }


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
            try:
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
            except (ValueError, KeyError):
                pass
    
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

