import 'package:ecotech_mobile/data/communication/communication_data.dart';
import 'package:ecotech_mobile/features/communication/communication_controller.dart';
import 'package:ecotech_mobile/features/communication/widgets/communication_actions.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('exibe contadores e sino ativo quando existem novidades', (
    tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          badgesProvider.overrideWith(
            (ref) async => const BadgesData(
              notificacoes: 4,
              mensagens: 2,
              oportunidades: 1,
            ),
          ),
        ],
        child: MaterialApp(
          home: Scaffold(
            appBar: AppBar(actions: const [CommunicationActions()]),
          ),
        ),
      ),
    );
    await tester.pump();

    expect(find.byIcon(Icons.chat_bubble_outline), findsOneWidget);
    expect(find.byIcon(Icons.notifications_active), findsOneWidget);
    expect(find.text('2'), findsOneWidget);
    expect(find.text('4'), findsOneWidget);

    await tester.pumpWidget(const SizedBox());
  });
}
