"""Testes para o módulo de dispositivos eletrônicos."""

import pytest
from ecotech.domain.dispositivos import Celular, Computador, Eletrodomestico


class TestDispositivos:

    def test_criacao_celular(self):
        celular = Celular("1", "iPhone 11", 0.2)
        assert celular.nome == "iPhone 11"
        assert celular.peso_kg == 0.2

    def test_polimorfismo_calcular_impacto(self):
        celular = Celular("1", "iPhone", 0.2)
        computador = Computador("2", "Dell", 2.5)

        impacto_celular = celular.calcular_impacto_ambiental()
        impacto_computador = computador.calcular_impacto_ambiental()

        assert impacto_celular > 0
        assert impacto_computador > 0
        assert impacto_computador > impacto_celular


class TestValidacaoMarca:

    def test_marca_valida(self):
        celular = Celular("1", "iPhone", 0.2, marca="Apple")
        assert celular.marca == "Apple"

    def test_marca_vazia(self):
        celular = Celular("1", "iPhone", 0.2, marca="")
        assert celular.marca == ""

    def test_marca_nao_string(self):
        with pytest.raises(ValueError, match="marca deve ser uma string"):
            Celular("1", "iPhone", 0.2, marca=123)

    def test_marca_apenas_espacos(self):
        with pytest.raises(ValueError, match="marca nao pode conter apenas espacos"):
            Celular("1", "iPhone", 0.2, marca="   ")

    def test_marca_muito_longa(self):
        marca_longa = "A" * 101
        with pytest.raises(ValueError, match="marca nao pode ter mais de 100 caracteres"):
            Celular("1", "iPhone", 0.2, marca=marca_longa)

    def test_marca_limite_100_caracteres(self):
        marca_limite = "A" * 100
        celular = Celular("1", "iPhone", 0.2, marca=marca_limite)
        assert celular.marca == marca_limite


class TestValidacaoModelo:

    def test_modelo_valido(self):
        celular = Celular("1", "iPhone", 0.2, modelo="13 Pro")
        assert celular.modelo == "13 Pro"

    def test_modelo_vazio(self):
        celular = Celular("1", "iPhone", 0.2, modelo="")
        assert celular.modelo == ""

    def test_modelo_nao_string(self):
        with pytest.raises(ValueError, match="modelo deve ser uma string"):
            Celular("1", "iPhone", 0.2, modelo=999)

    def test_modelo_apenas_espacos(self):
        with pytest.raises(ValueError, match="modelo nao pode conter apenas espacos"):
            Celular("1", "iPhone", 0.2, modelo="   ")

    def test_modelo_muito_longo(self):
        modelo_longo = "X" * 101
        with pytest.raises(ValueError, match="modelo nao pode ter mais de 100 caracteres"):
            Celular("1", "iPhone", 0.2, modelo=modelo_longo)

    def test_modelo_limite_100_caracteres(self):
        modelo_limite = "X" * 100
        celular = Celular("1", "iPhone", 0.2, modelo=modelo_limite)
        assert celular.modelo == modelo_limite


class TestValidacaoPeso:

    def test_peso_valido(self):
        celular = Celular("1", "iPhone", 0.2)
        assert celular.peso_kg == 0.2

    def test_peso_negativo(self):
        with pytest.raises(ValueError, match="peso deve ser positivo"):
            Celular("1", "iPhone", -0.5)

    def test_peso_zero(self):
        with pytest.raises(ValueError, match="peso deve ser positivo"):
            Celular("1", "iPhone", 0)

    def test_peso_muito_grande(self):
        computador = Computador("1", "Server", 500.0)
        assert computador.peso_kg == 500.0


class TestValorRevenda:

    def test_valor_revenda_celular(self):
        celular = Celular("1", "iPhone", 0.2)
        assert celular.calcular_valor_revenda() == 0.2 * 10.0

    def test_valor_revenda_computador(self):
        computador = Computador("2", "Dell", 2.5)
        assert computador.calcular_valor_revenda() == 2.5 * 25.0

    def test_valor_revenda_eletrodomestico(self):
        eletro = Eletrodomestico("3", "Microondas", 15.0)
        assert eletro.calcular_valor_revenda() == 15.0 * 15.0

    def test_valor_revenda_diferenca_tipos(self):
        celular = Celular("1", "iPhone", 1.0)
        computador = Computador("2", "Dell", 1.0)
        eletro = Eletrodomestico("3", "Micro", 1.0)

        valor_celular = celular.calcular_valor_revenda()
        valor_computador = computador.calcular_valor_revenda()
        valor_eletro = eletro.calcular_valor_revenda()

        # Computador tem maior valor (25%)
        assert valor_computador > valor_eletro
        # Eletro tem maior valor que celular (15% > 10%)
        assert valor_eletro > valor_celular


class TestImpactoAmbiental:

    def test_impacto_celular(self):
        celular = Celular("1", "iPhone", 0.2)
        assert celular.calcular_impacto_ambiental() == 0.2 * 5.0

    def test_impacto_computador(self):
        computador = Computador("2", "Dell", 2.5)
        assert computador.calcular_impacto_ambiental() == 2.5 * 15.0

    def test_impacto_eletrodomestico(self):
        eletro = Eletrodomestico("3", "Microondas", 15.0)
        assert eletro.calcular_impacto_ambiental() == 15.0 * 8.0

    def test_impacto_positivo(self):
        celular = Celular("1", "iPhone", 0.5)
        assert celular.calcular_impacto_ambiental() > 0


class TestTodosCombinados:

    def test_dispositivo_completo_valido(self):
        celular = Celular(
            id="1",
            nome="iPhone 13 Pro",
            peso_kg=0.203,
            marca="Apple",
            modelo="A2635"
        )
        assert celular.id == "1"
        assert celular.nome == "iPhone 13 Pro"
        assert celular.peso_kg == 0.203
        assert celular.marca == "Apple"
        assert celular.modelo == "A2635"
        assert celular.obter_tipo() == "Celular"
        assert celular.calcular_impacto_ambiental() == 0.203 * 5.0
        assert celular.calcular_valor_revenda() == 0.203 * 10.0

    def test_propriedades_imutaveis(self):
        celular = Celular("1", "iPhone", 0.2, marca="Apple", modelo="13")
        # Tentar atribuir deve falhar (properties nao tem setter)
        with pytest.raises(AttributeError):
            celular.peso_kg = 0.5
