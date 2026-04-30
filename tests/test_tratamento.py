import pytest
from ecotech.domain.tratamento import Reciclagem, Reuso, DescarteControlado
from ecotech.domain.dispositivos import Celular, StatusDispositivo


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


# -----------------------------------------
# TESTES validar_compatibilidade (Item 15)
# -----------------------------------------

class TestValidarCompatibilidade:

    def test_reuso_rejeita_dispositivo_danificado(self):
        """Reuso não deve aceitar dispositivo com status DANIFICADO."""
        celular = Celular("1", "iPhone", 0.2, status=StatusDispositivo.DANIFICADO)
        reuso = Reuso()

        with pytest.raises(ValueError, match="danificado"):
            reuso.validar_compatibilidade([celular])

    def test_reuso_aceita_dispositivo_funcionando(self):
        """Reuso deve aceitar dispositivo FUNCIONANDO sem erro."""
        celular = Celular("1", "iPhone", 0.2, status=StatusDispositivo.FUNCIONANDO)
        Reuso().validar_compatibilidade([celular])

    def test_reuso_aceita_parcialmente_funcional(self):
        """Reuso deve aceitar dispositivo PARCIALMENTE_FUNCIONAL."""
        celular = Celular("1", "iPhone", 0.2, status=StatusDispositivo.PARCIALMENTE_FUNCIONAL)
        Reuso().validar_compatibilidade([celular])

    def test_reciclagem_aceita_qualquer_status(self):
        """Reciclagem deve aceitar dispositivo em qualquer estado sem erro."""
        celular = Celular("1", "iPhone", 0.2, status=StatusDispositivo.DANIFICADO)
        Reciclagem().validar_compatibilidade([celular])

    def test_descarte_controlado_aceita_qualquer_status(self):
        """DescarteControlado deve aceitar dispositivo em qualquer estado."""
        celular = Celular("1", "iPhone", 0.2, status=StatusDispositivo.DANIFICADO)
        DescarteControlado().validar_compatibilidade([celular])

