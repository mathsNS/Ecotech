# A- testes para modulo de dispositivos eletronicos
# valida criacao de dispositivos e calculo de impacto

import pytest
from ecotech.domain.dispositivos import Celular, Computador, Eletrodomestico

# A- TODO: adicionar mais testes de validacao
# A- TODO: testar excecoes

class TestDispositivos:
    # A- testa criacao e comportamento dos dispositivos
    
    def test_criacao_celular(self):
        # A- verifica se celular e criado corretamente
        celular = Celular("1", "iPhone 11", 0.2)
        assert celular.nome == "iPhone 11"
        assert celular.peso_kg == 0.2
    
    def test_polimorfismo_calcular_impacto(self):
        # A- testa se diferentes tipos calculam impacto corretamente (polimorfismo)
        celular = Celular("1", "iPhone", 0.2)
        computador = Computador("2", "Dell", 2.5)
        
        impacto_celular = celular.calcular_impacto_ambiental()
        impacto_computador = computador.calcular_impacto_ambiental()
        
        # A- verifica que ambos calculam impacto positivo
        assert impacto_celular > 0
        assert impacto_computador > 0
        # A- computador tem impacto maior que o celular
        assert impacto_computador > impacto_celular
