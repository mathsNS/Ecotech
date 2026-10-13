import 'package:ecotech_mobile/data/models/usuario.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'helpers/auth_test_app.dart';

Future<void> fillField(WidgetTester tester, String label, String value) async {
  final field = find.byKey(ValueKey(label));
  await tester.ensureVisible(field);
  await tester.enterText(field, value);
}

void main() {
  testWidgets('cadastro cidadão preserva contrato e bloqueia envio duplicado', (
    tester,
  ) async {
    final repository = PendingAuthRepository();
    await pumpAuth(tester, repository, route: '/cadastro');
    await fillField(tester, 'Nome completo', '  Ana Silva  ');
    await fillField(tester, 'CPF', '12345678901');
    await fillField(tester, 'E-mail', ' ana@example.com ');
    await fillField(tester, 'Senha', 'senha-segura');
    await fillField(tester, 'Confirmar senha', 'senha-segura');
    final submit = find.widgetWithText(ElevatedButton, 'Criar conta');
    await tester.ensureVisible(submit);
    await tester.tap(submit);
    await tester.tap(submit);
    await tester.pump();
    expect(repository.requests, [
      {
        'tipo': 'cidadao',
        'nome': 'Ana Silva',
        'email': 'ana@example.com',
        'senha': 'senha-segura',
        'senha_confirmacao': 'senha-segura',
        'cpf': '12345678901',
        'cnpj': null,
        'razao_social': null,
      },
    ]);
    repository.response.complete(
      const Usuario(id: '1', nome: 'Ana Silva', tipo: 'cidadao'),
    );
    await tester.pumpAndSettle();
    expect(find.text('Área autenticada'), findsOneWidget);
  });
}
