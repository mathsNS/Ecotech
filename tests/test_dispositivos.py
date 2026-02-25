# A- testes para modulo de dispositivos eletronicos
# valida criacao de dispositivos e calculo de impacto

import pytest
from ecotech.domain.dispositivos import Celular, Computador, Eletrodomestico

# Testes de validacoes implementadas - ABNER 24/02
# Testes de excecoes implementados - ABNER 24/02


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


class TestValidacaoMarca:
    # ABNER 24/02 - Testes para validacoes de marca

    def test_marca_valida(self):
        # ABNER 24/02 - Marca valida deve ser aceita
        celular = Celular("1", "iPhone", 0.2, marca="Apple")
        assert celular.marca == "Apple"

    def test_marca_vazia(self):
        # ABNER 24/02 - Marca vazia (default) deve ser aceita
        celular = Celular("1", "iPhone", 0.2, marca="")
        assert celular.marca == ""

    def test_marca_nao_string(self):
        # ABNER 24/02 - Marca que nao e string deve lancar erro
        with pytest.raises(ValueError, match="marca deve ser uma string"):
            Celular("1", "iPhone", 0.2, marca=123)

    def test_marca_apenas_espacos(self):
        # ABNER 24/02 - Marca com apenas espacos deve lancar erro
        with pytest.raises(ValueError, match="marca nao pode conter apenas espacos"):
            Celular("1", "iPhone", 0.2, marca="   ")

    def test_marca_muito_longa(self):
        # ABNER 24/02 - Marca com mais de 100 caracteres deve lancar erro
        marca_longa = "A" * 101
        with pytest.raises(ValueError, match="marca nao pode ter mais de 100 caracteres"):
            Celular("1", "iPhone", 0.2, marca=marca_longa)

    def test_marca_limite_100_caracteres(self):
        # ABNER 24/02 - Marca com exatamente 100 caracteres deve ser aceita
        marca_limite = "A" * 100
        celular = Celular("1", "iPhone", 0.2, marca=marca_limite)
        assert celular.marca == marca_limite


class TestValidacaoModelo:
    # ABNER 24/02 - Testes para validacoes de modelo

    def test_modelo_valido(self):
        # ABNER 24/02 - Modelo valido deve ser aceito
        celular = Celular("1", "iPhone", 0.2, modelo="13 Pro")
        assert celular.modelo == "13 Pro"

    def test_modelo_vazio(self):
        # ABNER 24/02 - Modelo vazio (default) deve ser aceito
        celular = Celular("1", "iPhone", 0.2, modelo="")
        assert celular.modelo == ""

    def test_modelo_nao_string(self):
        # ABNER 24/02 - Modelo que nao e string deve lancar erro
        with pytest.raises(ValueError, match="modelo deve ser uma string"):
            Celular("1", "iPhone", 0.2, modelo=999)

    def test_modelo_apenas_espacos(self):
        # ABNER 24/02 - Modelo com apenas espacos deve lancar erro
        with pytest.raises(ValueError, match="modelo nao pode conter apenas espacos"):
            Celular("1", "iPhone", 0.2, modelo="   ")

    def test_modelo_muito_longo(self):
        # ABNER 24/02 - Modelo com mais de 100 caracteres deve lancar erro
        modelo_longo = "X" * 101
        with pytest.raises(ValueError, match="modelo nao pode ter mais de 100 caracteres"):
            Celular("1", "iPhone", 0.2, modelo=modelo_longo)

    def test_modelo_limite_100_caracteres(self):
        # ABNER 24/02 - Modelo com exatamente 100 caracteres deve ser aceito
        modelo_limite = "X" * 100
        celular = Celular("1", "iPhone", 0.2, modelo=modelo_limite)
        assert celular.modelo == modelo_limite


class TestValidacaoPeso:
    # ABNER 24/02 - Testes para validacoes de peso

    def test_peso_valido(self):
        # ABNER 24/02 - Peso valido deve ser aceito
        celular = Celular("1", "iPhone", 0.2)
        assert celular.peso_kg == 0.2

    def test_peso_negativo(self):
        # ABNER 24/02 - Peso negativo deve lancar erro
        with pytest.raises(ValueError, match="peso deve ser positivo"):
            Celular("1", "iPhone", -0.5)

    def test_peso_zero(self):
        # ABNER 24/02 - Peso zero deve lancar erro
        with pytest.raises(ValueError, match="peso deve ser positivo"):
            Celular("1", "iPhone", 0)

    def test_peso_muito_grande(self):
        # ABNER 24/02 - Peso muito grande deve ser aceito (sem limite superior)
        computador = Computador("1", "Server", 500.0)
        assert computador.peso_kg == 500.0


class TestValorRevenda:
    # ABNER 24/02 - Testes para calculo de valor de revenda

    def test_valor_revenda_celular(self):
        # ABNER 24/02 - Celular: valor = peso * 10%
        celular = Celular("1", "iPhone", 0.2)
        assert celular.calcular_valor_revenda() == 0.2 * 10.0

    def test_valor_revenda_computador(self):
        # ABNER 24/02 - Computador: valor = peso * 25%
        computador = Computador("2", "Dell", 2.5)
        assert computador.calcular_valor_revenda() == 2.5 * 25.0

    def test_valor_revenda_eletrodomestico(self):
        # ABNER 24/02 - Eletrodomestico: valor = peso * 15%
        eletro = Eletrodomestico("3", "Microondas", 15.0)
        assert eletro.calcular_valor_revenda() == 15.0 * 15.0

    def test_valor_revenda_diferenca_tipos(self):
        # ABNER 24/02 - Verificar que tipos diferentes tem valores diferentes
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
    # ABNER 24/02 - Testes para calculo de impacto ambiental

    def test_impacto_celular(self):
        # ABNER 24/02 - Celular: impacto = peso * 5.0
        celular = Celular("1", "iPhone", 0.2)
        assert celular.calcular_impacto_ambiental() == 0.2 * 5.0

    def test_impacto_computador(self):
        # ABNER 24/02 - Computador: impacto = peso * 15.0
        computador = Computador("2", "Dell", 2.5)
        assert computador.calcular_impacto_ambiental() == 2.5 * 15.0

    def test_impacto_eletrodomestico(self):
        # ABNER 24/02 - Eletrodomestico: impacto = peso * 8.0
        eletro = Eletrodomestico("3", "Microondas", 15.0)
        assert eletro.calcular_impacto_ambiental() == 15.0 * 8.0

    def test_impacto_positivo(self):
        # ABNER 24/02 - Impacto sempre deve ser positivo
        celular = Celular("1", "iPhone", 0.5)
        assert celular.calcular_impacto_ambiental() > 0


class TestTodosCombinados:
    # ABNER 24/02 - Testes combinando validacoes

    def test_dispositivo_completo_valido(self):
        # ABNER 24/02 - Criar dispositivo com todas as validacoes passando
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
        # ABNER 24/02 - Properties devem ser somente leitura
        celular = Celular("1", "iPhone", 0.2, marca="Apple", modelo="13")
        # Tentar atribuir deve falhar (properties nao tem setter)
        with pytest.raises(AttributeError):
            celular.peso_kg = 0.5
