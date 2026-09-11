import 'package:flutter_test/flutter_test.dart';

import 'package:ecotech_mobile/data/company/company_data.dart';

void main() {
  test('ponto calcula ocupacao e carrega entregas pendentes', () {
    final ponto = PontoEmpresaData.fromJson({
      'id': 'ponto-1',
      'nome': 'Ponto Centro',
      'endereco': 'Rua A, 10',
      'capacidade_kg': 100,
      'ocupacao_kg': 25,
      'ativa': true,
      'solicitacoes': [
        {
          'id': 'sol-1',
          'cidadao': 'João Silva',
          'estado': 'Solicitado',
          'peso_kg': 2.5,
          'peso_informado_cidadao': false,
          'confirmado_empresa': false,
          'pode_confirmar': true,
        },
      ],
    });

    expect(ponto.ocupacaoPercentual, 0.25);
    expect(ponto.solicitacoes.single.podeConfirmar, isTrue);
    expect(ponto.solicitacoes.single.pesoInformadoCidadao, isFalse);
  });

  test('base apresenta capacidade operacional sem coordenadas', () {
    final base = BaseEmpresaData.fromJson({
      'id': 'base-1',
      'nome': 'Base Centro',
      'endereco': 'Rua A, 10',
      'raio_atendimento_km': 25,
      'capacidade_kg': 500,
      'ocupacao_kg': 80,
      'capacidade_disponivel_kg': 420,
      'realiza_coleta_domiciliar': true,
      'ativa': true,
    });

    expect(base.raioAtendimentoKm, 25);
    expect(base.capacidadeDisponivelKg, 420);
    expect(base.realizaColetaDomiciliar, isTrue);
  });

  test('oportunidade carrega apenas dados liberados antes do aceite', () {
    final oportunidade = OportunidadeData.fromJson({
      'id': 'oferta-1',
      'solicitacao_id': 'sol-1',
      'base_operacional_id': 'base-1',
      'base_nome': 'Base Centro',
      'distancia_km': 3.4,
      'expira_em': '2026-09-11T15:00:00',
      'dados': {
        'categorias': ['celular'],
        'peso_estimado_kg': 1.2,
        'agendada_para': '2026-09-12T10:00:00',
      },
    });

    expect(oportunidade.categorias, ['celular']);
    expect(oportunidade.pesoEstimadoKg, 1.2);
    expect(oportunidade.baseNome, 'Base Centro');
  });
}
