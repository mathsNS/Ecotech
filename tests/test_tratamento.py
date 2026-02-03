import pytest
from ecotech.domain.tratamento import Reciclagem, Reuso, DescarteControlado
from ecotech.domain.dispositivos import Celular

# TODO: adicionar testes de impacto ambiental
# TODO: testar combinacao de metodos

class TestTratamento:
    
    def test_criacao_reciclagem(self):
        # testa criacao de metodo de tratamento
        reciclagem = Reciclagem()
        assert reciclagem.obter_nome() == "Reciclagem"
        assert reciclagem.reducao_impacto_percentual == 80.0
    
    def test_strategy_calcular_custo(self):
        # testa se diferentes metodos calculam custos diferentes (Strategy)
        dispositivos = [Celular("1", "iPhone", 0.2)]
        
        reciclagem = Reciclagem()
        reuso = Reuso()
        
        custo_reciclagem = reciclagem.calcular_custo(dispositivos)
        custo_reuso = reuso.calcular_custo(dispositivos)
        
        # reuso deve ser mais barato que reciclagem
        assert custo_reuso < custo_reciclagem
    
    def test_reducao_impacto(self):
        # verifica que reuso reduz impacto ambiental
        dispositivos = [Celular("1", "iPhone", 0.2)]
        reuso = Reuso()
        
        impacto = reuso.calcular_impacto_ambiental(dispositivos)
        assert impacto > 0

