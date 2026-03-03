from abc import ABC, abstractmethod
from typing import List, Dict
from datetime import datetime
from .dispositivos import DispositivoEletronico

# TODO: adicionar rastreamento de metodo aplicado
# TODO: criar relatorio de impacto por metodo

class MetodoTratamento(ABC):
    """Classe abstrata para métodos de tratamento ecológico.

    Utiliza o padrão *strategy* permitindo trocar o algoritmo de tratamento em
    tempo de execução. Fornece atributos básicos de custo e redução de impacto.
    """

    def __init__(self, custo_base_por_kg: float, reducao_impacto_percentual: float):
        """Inicializa um método de tratamento.

        Parâmetros
        ----------
        custo_base_por_kg : float
            Custo base por quilograma de material tratado.
        reducao_impacto_percentual : float
            Percentual de redução de impacto ambiental proporcionado pelo método.
        """
        self._custo_base_por_kg = custo_base_por_kg
        self._reducao_impacto_percentual = reducao_impacto_percentual

    @property
    def custo_base_por_kg(self) -> float:
        """Retorna o custo base por quilograma do método."""
        return self._custo_base_por_kg

    @property
    def reducao_impacto_percentual(self) -> float:
        """Retorna o percentual de redução de impacto ambiental."""
        return self._reducao_impacto_percentual

    @abstractmethod
    def obter_nome(self) -> str:
        """Retorna o nome identificador do método de tratamento."""
        pass

    @abstractmethod
    def calcular_custo(self, dispositivos: List[DispositivoEletronico]) -> float:
        """Calcula o custo total dado um conjunto de dispositivos.

        Parameters
        ----------
        dispositivos : List[DispositivoEletronico]
            Lista de dispositivos a serem processados.
        """
        pass

    @abstractmethod
    def calcular_impacto_ambiental(
        self, 
        dispositivos: List[DispositivoEletronico]
    ) -> float:
        """Calcula o impacto ambiental resultante do tratamento.

        Parameters
        ----------
        dispositivos : List[DispositivoEletronico]
            Dispositivos considerados no cálculo.
        """
        pass

    def __str__(self) -> str:
        """Representação em string é o nome do método."""
        return self.obter_nome()


class Reciclagem(MetodoTratamento):
    """Método de tratamento que desmonta e recupera materiais reutilizáveis.

    A reciclagem reduz significativamente o impacto ambiental e possui custo
    intermediário.
    """
    # metodo de reciclagem (desmonta e recupera os materiais que ainda tem utilidade) dai reduz impacto ambiental
    
    def __init__(self):
        """Inicializa Reciclagem com parâmetros fixos de custo e redução."""
        super().__init__(custo_base_por_kg=15.0, reducao_impacto_percentual=80.0)

    def obter_nome(self) -> str:
        """Retorna o nome deste método: "Reciclagem"."""
        return "Reciclagem"

    def calcular_custo(self, dispositivos: List[DispositivoEletronico]) -> float:
        """Calcula o custo da reciclagem com base no peso total."""
        # custo baseado no peso total * custo por kg
        peso_total = sum(d.peso_kg for d in dispositivos)
        return round(peso_total * self._custo_base_por_kg, 2)

    def calcular_impacto_ambiental(
        self, 
        dispositivos: List[DispositivoEletronico]
    ) -> float:
        """Calcula o impacto ambiental líquido após reciclagem."""
        # calcula impacto reduzido pela reciclagem
        impacto_total = sum(d.calcular_impacto_ambiental() for d in dispositivos)
        impacto_liquido = impacto_total * (1 - self._reducao_impacto_percentual / 100)
        return round(impacto_liquido, 2)


class Reuso(MetodoTratamento):
    """Método que recondiciona dispositivos para reutilização.

    O reuso reduz quase totalmente o impacto ambiental e possui baixo custo.
    """
    # metodo de reuso (recondiciona pra usar novamente)
    
    def __init__(self):
        """Inicializa Reuso com parâmetros predefinidos."""
        super().__init__(custo_base_por_kg=8.0, reducao_impacto_percentual=95.0)

    def obter_nome(self) -> str:
        """Retorna o nome deste método: "Reuso"."""
        return "Reuso"

    def calcular_custo(self, dispositivos: List[DispositivoEletronico]) -> float:
        """Calcula o custo do reuso baseado no peso total."""
        # reuso é mais barato que reciclagem
        peso_total = sum(d.peso_kg for d in dispositivos)
        return round(peso_total * self._custo_base_por_kg, 2)

    def calcular_impacto_ambiental(
        self, 
        dispositivos: List[DispositivoEletronico]
    ) -> float:
        """Calcula impacto ambiental líquido após reuso."""
        # reuso reduz mais o impacto (95%)
        impacto_total = sum(d.calcular_impacto_ambiental() for d in dispositivos)
        impacto_liquido = impacto_total * (1 - self._reducao_impacto_percentual / 100)
        return round(impacto_liquido, 2)


class DescarteControlado(MetodoTratamento):
    """Método de descarte em aterro especializado.

    Custo elevado e redução de impacto moderada comparado aos demais métodos.
    """
    # metodo de descarte controlado (vai pra um aterro especializado, diferente de um lixao etc)
    
    def __init__(self):
        """Inicializa DescarteControlado com parâmetros fixos."""
        super().__init__(custo_base_por_kg=25.0, reducao_impacto_percentual=40.0)

    def obter_nome(self) -> str:
        """Retorna o nome deste método: "Descarte Controlado"."""
        return "Descarte Controlado"

    def calcular_custo(self, dispositivos: List[DispositivoEletronico]) -> float:
        """Calcula o custo do descarte controlado com base no peso."""

        peso_total = sum(d.peso_kg for d in dispositivos)
        return round(peso_total * self._custo_base_por_kg, 2)

    def calcular_impacto_ambiental(
        self, 
        dispositivos: List[DispositivoEletronico]
    ) -> float:
        """Calcula impacto ambiental líquido após descarte controlado."""
        # descarte controlado reduz menos o impacto (40%)
        impacto_total = sum(d.calcular_impacto_ambiental() for d in dispositivos)
        impacto_liquido = impacto_total * (1 - self._reducao_impacto_percentual / 100)
        return round(impacto_liquido, 2)


class RastreamentoMetodo:  # ABNER 24/02 - Rastreamento de metodo aplicado
    """Registra aplicação de um método de tratamento.

    Armazena informações de quando, onde e com que peso o método foi usado,
    permitindo auditoria e análise histórica.
    """
    # ABNER 24/02 - rastreia quando e onde um metodo de tratamento foi aplicado
    # permite auditoria e analise historica de aplicacoes

    def __init__(self, id_aplicacao: str, metodo: MetodoTratamento, peso_total_kg: float):
        """Inicializa um registro de rastreamento de método.

        Parâmetros
        ----------
        id_aplicacao : str
            Identificador único da aplicação.
        metodo : MetodoTratamento
            Instância do método utilizado.
        peso_total_kg : float
            Peso total tratado em quilogramas.
        """
        self._id_aplicacao = id_aplicacao  # ABNER 24/02
        self._metodo = metodo  # ABNER 24/02
        self._peso_total_kg = peso_total_kg  # ABNER 24/02
        self._data_aplicacao = datetime.now()  # ABNER 24/02
        self._custo = metodo.custo_base_por_kg * peso_total_kg  # ABNER 24/02
        self._impacto_evitado = (
            metodo.reducao_impacto_percentual / 100) * 100  # ABNER 24/02

    @property
    def id_aplicacao(self) -> str:
        """Retorna o identificador da aplicação rastreada."""
        return self._id_aplicacao

    @property
    def metodo(self) -> MetodoTratamento:
        """Retorna o método de tratamento aplicado."""
        return self._metodo

    @property
    def peso_total_kg(self) -> float:
        """Retorna o peso total (kg) tratado nessa aplicação."""
        return self._peso_total_kg

    @property
    def data_aplicacao(self) -> datetime:
        """Retorna a data/hora da aplicação."""
        return self._data_aplicacao

    @property
    def custo(self) -> float:
        """Retorna o custo calculado da aplicação (arredondado)."""
        return round(self._custo, 2)

    @property
    def impacto_evitado(self) -> float:
        """Retorna percentual de impacto ambiental evitado (arredondado)."""
        return round(self._impacto_evitado, 1)

    def obter_resumo(self) -> Dict:  # ABNER 24/02
        """Retorna um dicionário resumo dos dados do rastreamento."""
        return {
            "id_aplicacao": self._id_aplicacao,
            "metodo": self._metodo.obter_nome(),
            "peso_kg": self._peso_total_kg,
            "data": self._data_aplicacao.isoformat(),
            "custo": self.custo,
            "impacto_evitado_percentual": self.impacto_evitado
        }

    def __str__(self) -> str:
        """Representação em string do rastreamento."""
        return f"Rastreamento {self._id_aplicacao}: {self._metodo.obter_nome()} ({self._peso_total_kg}kg)"


class RelatorioImpactoPorMetodo:  # ABNER 24/02 - Relatorio de impacto por metodo
    """Consolida informações de rastreamentos para análise comparativa.

    Gera métricas de peso, custo e impacto evitado por método de tratamento.
    """
    # ABNER 24/02 - consolida dados e gera relatorios de impacto por tipo de tratamento
    # permite analise comparativa entre diferentes metodos

    def __init__(self, titulo: str = "Relatorio de Impacto por Metodo"):
        """Inicializa relatório com título opcional."""
        self._titulo = titulo  # ABNER 24/02
        self._rastreamentos: List[RastreamentoMetodo] = []  # ABNER 24/02
        self._data_geracao = datetime.now()  # ABNER 24/02

    @property
    def titulo(self) -> str:
        """Retorna o título do relatório."""
        return self._titulo

    @property
    def data_geracao(self) -> datetime:
        """Retorna a data/hora de geração do relatório."""
        return self._data_geracao

    def adicionar_rastreamento(self, rastreamento: RastreamentoMetodo):  # ABNER 24/02
        """Adiciona um registro de rastreamento ao relatório."""

        self._rastreamentos.append(rastreamento)

    # ABNER 24/02
    def calcular_total_peso_por_metodo(self) -> Dict[str, float]:
        """Calcula o peso total tratado por cada método."""

        totais = {}
        for rastr in self._rastreamentos:
            nome_metodo = rastr.metodo.obter_nome()
            if nome_metodo not in totais:
                totais[nome_metodo] = 0.0
            totais[nome_metodo] += rastr.peso_total_kg
        return {k: round(v, 2) for k, v in totais.items()}

    # ABNER 24/02
    def calcular_custo_total_por_metodo(self) -> Dict[str, float]:
        """Calcula o custo acumulado por método."""

        totais = {}
        for rastr in self._rastreamentos:
            nome_metodo = rastr.metodo.obter_nome()
            if nome_metodo not in totais:
                totais[nome_metodo] = 0.0
            totais[nome_metodo] += rastr.custo
        return {k: round(v, 2) for k, v in totais.items()}

    # ABNER 24/02
    def calcular_impacto_evitado_por_metodo(self) -> Dict[str, float]:
        """Calcula o total de impacto ambiental evitado por cada método."""

        totais = {}
        for rastr in self._rastreamentos:
            nome_metodo = rastr.metodo.obter_nome()
            if nome_metodo not in totais:
                totais[nome_metodo] = 0.0
            # calcula quanto de impacto foi evitado
            impacto_evitado = (
                rastr.metodo.reducao_impacto_percentual / 100) * rastr.peso_total_kg
            totais[nome_metodo] += impacto_evitado
        return {k: round(v, 2) for k, v in totais.items()}

    def contar_aplicacoes_por_metodo(self) -> Dict[str, int]:  # ABNER 24/02
        """Conta quantas aplicações foram feitas por método."""
        # ABNER 24/02 - conta quantas vezes cada metodo foi aplicado
        contagens = {}
        for rastr in self._rastreamentos:
            nome_metodo = rastr.metodo.obter_nome()
            contagens[nome_metodo] = contagens.get(nome_metodo, 0) + 1
        return contagens

    def gerar_relatorio_completo(self) -> Dict:  # ABNER 24/02
        """Gera um dicionário consolidado com todas as métricas do relatório."""
        # ABNER 24/02 - gera relatorio consolidado com todas as metricas
        return {
            "titulo": self._titulo,
            "data_geracao": self._data_geracao.isoformat(),
            "total_rastreamentos": len(self._rastreamentos),
            "peso_por_metodo_kg": self.calcular_total_peso_por_metodo(),
            "custo_por_metodo": self.calcular_custo_total_por_metodo(),
            "impacto_evitado_por_metodo": self.calcular_impacto_evitado_por_metodo(),
            "aplicacoes_por_metodo": self.contar_aplicacoes_por_metodo()
        }

    def __str__(self) -> str:
        """Representação textual do relatório com número de rastreamentos."""
        return f"Relatorio '{self._titulo}' com {len(self._rastreamentos)} rastreamentos"
