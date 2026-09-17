import 'package:ecotech_mobile/data/company/company_data.dart';
import 'package:ecotech_mobile/data/plans/plans_data.dart';
import 'package:ecotech_mobile/data/plans/plans_repository.dart';
import 'package:ecotech_mobile/features/company/company_controller.dart';
import 'package:ecotech_mobile/features/plans/plans_controller.dart';
import 'package:ecotech_mobile/features/plans/plans_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

class _PlansRepositoryFake extends PlansRepository {
  _PlansRepositoryFake(this.data);

  PlansData data;
  String? changedTo;

  @override
  Future<PlansData> fetchPlans() async => data;

  @override
  Future<PlansData> changePlan(String planId) async {
    changedTo = planId;
    data = PlansData(
      currentPlan: planId,
      plans: data.plans,
      featureFlags: data.plans
          .firstWhere((plan) => plan.id == planId)
          .featureFlags,
      demoEnvironment: true,
    );
    return data;
  }
}

const _free = PlanData(
  id: 'free',
  name: 'Free',
  monthlyPrice: 0,
  highlighted: false,
  monthlyRequestLimit: 30,
  features: ['Histórico de coletas'],
  featureFlags: {'mtr': false},
);

const _professional = PlanData(
  id: 'professional',
  name: 'Professional',
  monthlyPrice: 249,
  highlighted: true,
  monthlyRequestLimit: null,
  features: ['MTR profissional', 'Exportação CSV'],
  featureFlags: {'mtr': true, 'exportacao_dados': true},
);

void main() {
  testWidgets('compara planos e confirma alteracao', (tester) async {
    final repository = _PlansRepositoryFake(
      const PlansData(
        currentPlan: 'free',
        plans: [_free, _professional],
        featureFlags: {'mtr': false},
        demoEnvironment: true,
      ),
    );

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          plansRepositoryProvider.overrideWithValue(repository),
          oportunidadesEmpresaProvider.overrideWith(
            (ref) async => <OportunidadeData>[],
          ),
        ],
        child: const MaterialApp(home: PlansScreen()),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Planos EcoTech'), findsOneWidget);
    expect(find.text('Plano atual'), findsOneWidget);
    expect(find.text('Professional'), findsOneWidget);
    expect(find.text('MTR profissional'), findsOneWidget);

    await tester.ensureVisible(find.text('Selecionar plano'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Selecionar plano'));
    await tester.pumpAndSettle();
    expect(find.text('Alterar para Professional?'), findsOneWidget);

    await tester.tap(find.text('Confirmar alteração'));
    await tester.pumpAndSettle();

    expect(repository.changedTo, 'professional');
    expect(
      find.text('Plano Professional ativado com sucesso.'),
      findsOneWidget,
    );
  });
}
