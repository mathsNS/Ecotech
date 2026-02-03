# M- testes para modulo de usuarios
# valida criacao de usuarios e regras de negocio

import pytest
from ecotech.domain.usuarios import Cidadao, Empresa, Administrador

# M- TODO: adicionar testes de validacao de email
# M- TODO: testar encapsulamento de atributos

class TestUsuarios:
    # M- testa comportamento dos diferentes tipos de usuario
    
    def test_criacao_cidadao(self):
        # M- verifica criacao basica de cidadao
        cidadao = Cidadao("1", "João Silva", "joao@example.com", "123.456.789-00")
        assert cidadao.nome == "João Silva"
        assert cidadao.pode_solicitar_descarte() is True
    
    def test_empresa_limite_mensal(self):
        # M- testa se limite mensal de empresa funciona corretamente
        empresa = Empresa("1", "EcoTech", "contato@eco.com", "12.345.678/0001-99", "EcoTech LTDA")
        assert empresa.pode_solicitar_descarte() is True
        
        # M- registra descarte acima do limite (1000kg)
        empresa.registrar_descarte_kg(1500)
        assert empresa.pode_solicitar_descarte() is False  # nao pode mais solicitar
