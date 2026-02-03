import pytest
from unittest.mock import Mock
from ecotech.domain.estados import Solicitado, Coletado, EmProcessamento
from ecotech.domain.descarte import SolicitacaoDescarte
from ecotech.domain.usuarios import Cidadao

# TODO: testar todas as transicoes possiveis
# TODO: adicionar testes de estado invalido

class TestEstados:
    
    def test_estado_inicial(self):
        estado = Solicitado()
        assert estado.obter_nome() == "Solicitado"
        assert estado.pode_avancar() is True
    
    def test_transicao_estado_com_mock(self):
        estado = Solicitado()
        mock_solicitacao = Mock()
        
        proximo = estado.avancar(mock_solicitacao)
        assert isinstance(proximo, Coletado)
    
    def test_fluxo_solicitacao(self):
        cidadao = Cidadao("1", "João", "joao@test.com", "123")
        solicitacao = SolicitacaoDescarte("1", cidadao)
        
        assert isinstance(solicitacao.estado, Solicitado)
        solicitacao.avancar_estado()
        assert isinstance(solicitacao.estado, Coletado)
