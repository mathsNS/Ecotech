import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:ecotech_mobile/data/company/company_data.dart';
import 'package:ecotech_mobile/features/company/company_controller.dart';
import 'package:ecotech_mobile/features/company/widgets/company_navigation.dart';

void main() {
  testWidgets('navegacao destaca quantidade de novas oportunidades', (
    tester,
  ) async {
    final oportunidades = List.generate(
      3,
      (index) => OportunidadeData(
        id: 'oferta-$index',
        solicitacaoId: 'sol-$index',
        baseId: 'base-1',
        baseNome: 'Base Centro',
        distanciaKm: 2,
        expiraEm: '2026-09-11T15:00:00',
        categorias: const ['celular'],
        pesoEstimadoKg: 1,
        agendadaPara: '2026-09-12T10:00:00',
      ),
    );

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          oportunidadesEmpresaProvider.overrideWith(
            (ref) async => oportunidades,
          ),
        ],
        child: const MaterialApp(
          home: Scaffold(
            bottomNavigationBar: CompanyNavigation(selectedIndex: 0),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('3'), findsOneWidget);
    expect(find.text('Oportunidades'), findsOneWidget);

    await tester.pumpWidget(const SizedBox());
  });
}
