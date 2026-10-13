import 'package:ecotech_mobile/core/api/api_exception.dart';
import 'package:ecotech_mobile/data/models/usuario.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'helpers/auth_test_app.dart';

void main() {
  for (final profile in [
    ('Cidadão', 'cidadao', '12345678901'),
    ('Empresa', 'empresa', '12345678000199'),
    ('Admin', 'administrador', 'admin@example.com'),
  ]) {
    testWidgets('login envia perfil ${profile.$2} uma vez e abre o painel', (
      tester,
    ) async {
      final repository = PendingAuthRepository();
      await pumpAuth(tester, repository);
      await tester.tap(find.text(profile.$1));
      await tester.pumpAndSettle();
      await tester.enterText(find.byType(TextFormField).first, profile.$3);
      await tester.enterText(find.byType(TextFormField).last, 'senha-segura');
      await tester.ensureVisible(find.text('Entrar'));
      await tester.tap(find.text('Entrar'));
      await tester.tap(find.text('Entrar'));
      await tester.pump();
      expect(repository.requests, [
        {'tipo': profile.$2, 'credencial': profile.$3, 'senha': 'senha-segura'},
      ]);
      expect(
        tester.widget<TextFormField>(find.byType(TextFormField).first).enabled,
        isFalse,
      );
      repository.response.complete(
        Usuario(id: '1', nome: 'Teste', tipo: profile.$2),
      );
      await tester.pumpAndSettle();
      expect(find.text('Área autenticada'), findsOneWidget);
    });
  }

  testWidgets(
    'login valida vazio, revela senha e permite corrigir erro do servidor',
    (tester) async {
      final repository = PendingAuthRepository();
      await pumpAuth(tester, repository);
      await tester.tap(find.text('Entrar'));
      await tester.pumpAndSettle();
      expect(find.text('Campo obrigatório'), findsNWidgets(2));
      expect(repository.requests, isEmpty);
      await tester.enterText(find.byType(TextFormField).first, '12345678901');
      await tester.enterText(find.byType(TextFormField).last, 'senha-segura');
      await tester.tap(find.byTooltip('Mostrar senha'));
      await tester.pump();
      expect(
        tester.widget<EditableText>(find.byType(EditableText).last).obscureText,
        isFalse,
      );
      await tester.ensureVisible(find.text('Entrar'));
      await tester.tap(find.text('Entrar'));
      await tester.pump();
      repository.response.completeError(ApiException('Credenciais inválidas'));
      await tester.pumpAndSettle();
      expect(find.text('Credenciais inválidas'), findsOneWidget);
      expect(
        tester.widget<TextFormField>(find.byType(TextFormField).first).enabled,
        isTrue,
      );
      expect(find.text('Que bom te ver'), findsOneWidget);
    },
  );
}
