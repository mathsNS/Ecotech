import 'package:ecotech_mobile/data/models/usuario.dart';
import 'package:ecotech_mobile/core/api/api_exception.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'helpers/auth_test_app.dart';

Future<void> fillField(WidgetTester tester, String label, String value) async {
  final field = find.byKey(ValueKey(label));
  await tester.ensureVisible(field);
  await tester.enterText(field, value);
}

void main() {
  testWidgets(
    'cadastro valida senhas antes de enviar e conserva dados após erro',
    (tester) async {
      final repository = PendingAuthRepository();
      await pumpAuth(tester, repository, route: '/cadastro');
      await fillField(tester, 'Nome completo', 'Ana');
      await fillField(tester, 'CPF', '12345678901');
      await fillField(tester, 'E-mail', 'ana@example.com');
      await fillField(tester, 'Senha', '123');
      await fillField(tester, 'Confirmar senha', '456');
      final submit = find.widgetWithText(ElevatedButton, 'Criar conta');
      await tester.ensureVisible(submit);
      await tester.tap(submit);
      await tester.pumpAndSettle();
      expect(find.text('Use pelo menos 6 caracteres'), findsOneWidget);
      expect(find.text('As senhas não conferem'), findsOneWidget);
      expect(repository.requests, isEmpty);
      await fillField(tester, 'Senha', 'senha-segura');
      await fillField(tester, 'Confirmar senha', 'senha-segura');
      await tester.ensureVisible(submit);
      await tester.tap(submit);
      await tester.pump();
      repository.response.completeError(ApiException('E-mail já cadastrado'));
      await tester.pumpAndSettle();
      expect(find.text('E-mail já cadastrado'), findsOneWidget);
      expect(
        tester
            .widget<TextFormField>(find.byKey(const ValueKey('E-mail')))
            .controller!
            .text,
        'ana@example.com',
      );
      expect(tester.widget<ElevatedButton>(submit).onPressed, isNotNull);
    },
  );

  testWidgets(
    'empresa preserva campos ao trocar perfil e envia apenas seu documento',
    (tester) async {
      final repository = PendingAuthRepository();
      await pumpAuth(tester, repository, route: '/cadastro');
      await fillField(tester, 'CPF', '12345678901');
      await tester.ensureVisible(find.text('Empresa'));
      await tester.tap(find.text('Empresa'));
      await tester.pumpAndSettle();
      await fillField(tester, 'Razão social', '  Recicla LTDA  ');
      await fillField(tester, 'CNPJ', '12345678000199');
      await fillField(tester, 'Nome da empresa', 'Recicla');
      await tester.ensureVisible(find.text('Cidadão'));
      await tester.tap(find.text('Cidadão'));
      await tester.pumpAndSettle();
      expect(
        tester
            .widget<TextFormField>(find.byKey(const ValueKey('CPF')))
            .controller!
            .text,
        '12345678901',
      );
      await tester.tap(find.text('Empresa'));
      await tester.pumpAndSettle();
      expect(
        tester
            .widget<TextFormField>(find.byKey(const ValueKey('CNPJ')))
            .controller!
            .text,
        '12345678000199',
      );
      await fillField(tester, 'E-mail', 'contato@example.com');
      await fillField(tester, 'Senha', 'senha-segura');
      await fillField(tester, 'Confirmar senha', 'senha-segura');
      final submit = find.widgetWithText(ElevatedButton, 'Criar conta');
      await tester.ensureVisible(submit);
      await tester.tap(submit);
      await tester.pump();
      expect(repository.requests.single, {
        'tipo': 'empresa',
        'nome': 'Recicla',
        'email': 'contato@example.com',
        'senha': 'senha-segura',
        'senha_confirmacao': 'senha-segura',
        'cpf': null,
        'cnpj': '12345678000199',
        'razao_social': 'Recicla LTDA',
      });
      repository.response.complete(
        const Usuario(id: '2', nome: 'Recicla', tipo: 'empresa'),
      );
      await tester.pumpAndSettle();
      expect(find.text('Área autenticada'), findsOneWidget);
    },
  );

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
