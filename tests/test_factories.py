import pytest
from unittest.mock import Mock
from ecotech.application.factories import DispositivoFactory, UsuarioFactory
from ecotech.application.services import ServicoDescarte
from ecotech.domain.usuarios import Cidadao


class TestFactories:
    
    def test_factory_celular(self):
        # A- testa se factory cria celular corretamente
        celular = DispositivoFactory.criar_celular("1", "iPhone", 0.2)
        assert celular.nome == "iPhone"
        assert celular.peso_kg == 0.2
    
    def test_factory_usuario(self):
        # M- testa criacao de usuario via factory
        cidadao = UsuarioFactory.criar_cidadao("1", "João", "joao@test.com", "123")
        assert cidadao.nome == "João"


class TestServicos:
    
    def test_criar_solicitacao_com_mock(self):
        servico = ServicoDescarte()
        mock_usuario = Mock()
        
        solicitacao = servico.criar_solicitacao(mock_usuario)
        assert solicitacao is not None
    
    def test_listar_solicitacoes(self):
        servico = ServicoDescarte()
        cidadao = Cidadao("1", "João", "joao@test.com", "123")
        
        servico.criar_solicitacao(cidadao)
        servico.criar_solicitacao(cidadao)
        
        solicitacoes = servico.listar_solicitacoes()
        assert len(solicitacoes) == 2
