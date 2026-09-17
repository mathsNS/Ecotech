import 'package:ecotech_mobile/data/plans/plans_data.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('interpreta plano atual limites recursos e flags', () {
    final data = PlansData.fromJson({
      'plano_atual': 'professional',
      'ambiente_demonstracao': true,
      'feature_flags': {'mtr': true, 'api_integracao': false},
      'planos': [
        {
          'id': 'free',
          'nome': 'Free',
          'preco_mensal': 0,
          'destaque': false,
          'limite_solicitacoes_mes': 30,
          'recursos': ['Histórico de coletas'],
          'feature_flags': {'mtr': false},
        },
        {
          'id': 'professional',
          'nome': 'Professional',
          'preco_mensal': 249,
          'destaque': true,
          'limite_solicitacoes_mes': null,
          'recursos': ['MTR profissional'],
          'feature_flags': {'mtr': true},
        },
      ],
    });

    expect(data.currentPlan, 'professional');
    expect(data.demoEnvironment, isTrue);
    expect(data.featureFlags['mtr'], isTrue);
    expect(data.plans.first.monthlyRequestLimit, 30);
    expect(data.plans.last.monthlyRequestLimit, isNull);
    expect(data.plans.last.highlighted, isTrue);
  });
}
