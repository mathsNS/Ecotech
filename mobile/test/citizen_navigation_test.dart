import 'package:ecotech_mobile/data/communication/communication_data.dart';
import 'package:ecotech_mobile/features/citizen/widgets/citizen_navigation.dart';
import 'package:ecotech_mobile/features/communication/communication_controller.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('navegação do cidadão mostra destinos e novidades', (
    tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          badgesProvider.overrideWith(
            (ref) async => const BadgesData(
              notificacoes: 2,
              mensagens: 1,
              oportunidades: 0,
            ),
          ),
        ],
        child: const MaterialApp(
          home: Scaffold(
            bottomNavigationBar: CitizenNavigation(selectedIndex: 0),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Dashboard'), findsOneWidget);
    expect(find.text('Operações'), findsOneWidget);
    expect(find.text('Carteira'), findsOneWidget);
    expect(find.text('Atividades'), findsOneWidget);
    expect(find.text('Conversas'), findsOneWidget);
    expect(find.text('2'), findsOneWidget);
    expect(find.text('1'), findsOneWidget);

    await tester.pumpWidget(const SizedBox());
  });
}
