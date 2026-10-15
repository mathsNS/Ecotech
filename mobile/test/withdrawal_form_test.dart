import 'package:ecotech_mobile/core/theme/app_theme.dart';
import 'package:ecotech_mobile/data/finance/finance_data.dart';
import 'package:ecotech_mobile/features/finance/widgets/withdrawal_form.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

const walletFixture = CarteiraData(
  saldo: 140.03,
  pontos: 14003,
  pontosPorReal: 100,
  metodos: [
    MetodoSaqueData(id: 'Pix', nome: 'Pix'),
    MetodoSaqueData(id: 'Transferencia', nome: 'Transferência'),
  ],
  titular: TitularData(nome: 'Maria Silva', cpf: '', email: ''),
  saques: [],
);

Finder withdrawalField(String label) => find.byWidgetPredicate(
  (w) => w is TextField && w.decoration?.labelText == label,
);

Future<void> pumpForm(
  WidgetTester tester,
  ValueChanged<WithdrawalRequest> onContinue,
) async {
  tester.view.physicalSize = const Size(390, 844);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);
  await tester.pumpWidget(
    MaterialApp(
      theme: AppTheme.light(),
      home: Scaffold(
        body: WithdrawalForm(wallet: walletFixture, onContinue: onContinue),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('atalhos usam centavos e seleção mantém valor e titular', (
    tester,
  ) async {
    WithdrawalRequest? request;
    await pumpForm(tester, (value) => request = value);
    await tester.ensureVisible(find.text('25%'));
    await tester.tap(find.text('25%'));
    await tester.ensureVisible(find.text('Transferência'));
    await tester.tap(find.text('Transferência'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Revisar saque'));
    await tester.pumpAndSettle();
    expect(request?.cents, 3500);
    expect(request?.method.id, 'Transferencia');
    expect(request?.holder, 'Maria Silva');
  });

  testWidgets('rejeita saldo excedido, precisão inválida, NaN e zero', (
    tester,
  ) async {
    var requests = 0;
    await pumpForm(tester, (_) => requests++);
    for (final value in ['140,04', '1,001', 'NaN', 'Infinity', '0', '-1']) {
      await tester.enterText(withdrawalField('Valor do saque'), value);
      await tester.tap(find.text('Revisar saque'));
      await tester.pumpAndSettle();
      expect(requests, 0, reason: value);
    }
    await tester.enterText(withdrawalField('Valor do saque'), '140,03');
    await tester.tap(find.text('Revisar saque'));
    await tester.pumpAndSettle();
    expect(requests, 1);
  });
}
