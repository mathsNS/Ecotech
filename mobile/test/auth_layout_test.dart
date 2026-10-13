import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'helpers/auth_test_app.dart';

void main() {
  for (final route in ['/login', '/cadastro']) {
    testWidgets('$route permite rolagem com fonte ampliada e teclado', (
      tester,
    ) async {
      await pumpAuth(
        tester,
        PendingAuthRepository(),
        route: route,
        scale: 2,
        size: const Size(320, 700),
      );
      final lastField = find.byType(TextFormField).last;
      await tester.ensureVisible(lastField);
      await tester.tap(lastField);
      tester.view.viewInsets = const FakeViewPadding(bottom: 300);
      addTearDown(tester.view.resetViewInsets);
      await tester.pumpAndSettle();
      await tester.ensureVisible(lastField);
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
      expect(tester.getBottomLeft(lastField).dy, lessThanOrEqualTo(400));
      final submit = find.byType(ElevatedButton);
      await tester.ensureVisible(submit);
      await tester.tap(submit);
      await tester.pumpAndSettle();
      expect(find.text('Campo obrigatório'), findsWidgets);
      expect(tester.takeException(), isNull);
    });
  }

  testWidgets('links conectam login e cadastro e permitem voltar', (
    tester,
  ) async {
    await pumpAuth(tester, PendingAuthRepository());
    final create = find.text('Não tem uma conta? Criar conta');
    await tester.ensureVisible(create);
    await tester.tap(create);
    await tester.pumpAndSettle();
    final login = find.text('Já tem uma conta? Entrar');
    await tester.ensureVisible(login);
    await tester.tap(login);
    await tester.pumpAndSettle();
    expect(find.text('Que bom te ver'), findsOneWidget);
  });
}
