import 'dart:async';

import 'package:ecotech_mobile/core/api/api_exception.dart';
import 'package:ecotech_mobile/core/theme/app_theme.dart';
import 'package:ecotech_mobile/data/communication/communication_data.dart';
import 'package:ecotech_mobile/data/finance/finance_data.dart';
import 'package:ecotech_mobile/data/finance/finance_repository.dart';
import 'package:ecotech_mobile/features/communication/communication_controller.dart';
import 'package:ecotech_mobile/features/finance/carteira_screen.dart';
import 'package:ecotech_mobile/features/finance/finance_controller.dart';
import 'package:ecotech_mobile/features/finance/saque_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'withdrawal_form_test.dart' show walletFixture, withdrawalField;

typedef WithdrawalResult = ({SaqueData saque, CarteiraData carteira});

class PendingFinanceRepository extends FinanceRepository {
  CarteiraData wallet = walletFixture;
  final requests = <Map<String, Object>>[];
  final pending = <Completer<WithdrawalResult>>[];
  @override
  Future<CarteiraData> buscarCarteira() async => wallet;
  @override
  Future<WithdrawalResult> solicitarSaque({
    required double valor,
    required String metodo,
    required String titular,
    required String idCliente,
  }) {
    requests.add({
      'valor': valor,
      'metodo': metodo,
      'titular': titular,
      'id_cliente': idCliente,
    });
    final request = Completer<WithdrawalResult>();
    pending.add(request);
    return request.future;
  }
}

Future<void> pumpWithdrawal(
  WidgetTester tester,
  PendingFinanceRepository repository, {
  bool wallet = false,
  double scale = 1,
  bool open = true,
}) async {
  tester.view.physicalSize = const Size(320, 800);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        financeRepositoryProvider.overrideWithValue(repository),
        badgesProvider.overrideWith(
          (ref) async =>
              const BadgesData(notificacoes: 0, mensagens: 0, oportunidades: 0),
        ),
      ],
      child: MaterialApp(
        theme: AppTheme.light(),
        builder: (context, child) => MediaQuery(
          data: MediaQuery.of(context)
              .copyWith(textScaler: TextScaler.linear(scale)),
          child: child!,
        ),
        home: wallet
            ? const CarteiraScreen()
            : Builder(
                builder: (context) => Scaffold(
                  body: TextButton(
                    onPressed: () => Navigator.of(context).push(
                      MaterialPageRoute<void>(
                        builder: (_) => SaqueScreen(wallet: repository.wallet),
                      ),
                    ),
                    child: const Text('Abrir saque'),
                  ),
                ),
              ),
      ),
    ),
  );
  await tester.pumpAndSettle();
  if (!open) return;
  final button = find.text(wallet ? 'Solicitar saque' : 'Abrir saque');
  await tester.ensureVisible(button);
  await tester.tap(button);
  await tester.pumpAndSettle();
}

const receipt = SaqueData(
  id: 'pedido-123',
  valor: 35,
  metodo: 'Pix',
  dataHora: '2026-10-15T10:00:00',
  status: 'pendente',
  titular: 'Maria Silva',
);

void main() {
  testWidgets('carteira desabilita saque sem saldo ou sem métodos', (
    tester,
  ) async {
    for (final noMethods in [false, true]) {
      final repository = PendingFinanceRepository();
      repository.wallet = CarteiraData(
        saldo: noMethods ? 140 : 0,
        pontos: 0,
        pontosPorReal: 100,
        metodos: noMethods ? [] : walletFixture.metodos,
        titular: walletFixture.titular,
        saques: [],
      );
      await pumpWithdrawal(tester, repository, wallet: true, open: false);
      expect(
        tester
            .widget<ElevatedButton>(
              find.widgetWithText(ElevatedButton, 'Solicitar saque'),
            )
            .onPressed,
        isNull,
      );
      expect(
        find.text('Nenhum saque solicitado até o momento.'),
        findsOneWidget,
      );
      await tester.pumpWidget(const SizedBox());
    }
  });

  testWidgets(
    'envio único registra protocolo e atualiza histórico da carteira',
    (tester) async {
      final repository = PendingFinanceRepository();
      await pumpWithdrawal(tester, repository, wallet: true);
      await tester.enterText(withdrawalField('Valor do saque'), '35,00');
      await tester.tap(find.text('Revisar saque'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Confirmar pedido'));
      await tester.tap(find.text('Confirmar pedido'));
      await tester.pump();
      expect(repository.requests, hasLength(1));
      expect(repository.requests.single['valor'], 35);
      repository.wallet = CarteiraData(
        saldo: 105.03,
        pontos: 14003,
        pontosPorReal: 100,
        metodos: walletFixture.metodos,
        titular: walletFixture.titular,
        saques: [receipt],
      );
      repository.pending.single.complete((
        saque: receipt,
        carteira: repository.wallet,
      ));
      await tester.pumpAndSettle();
      expect(find.text('Protocolo: pedido-123'), findsOneWidget);
      expect(find.text('Status: pendente'), findsOneWidget);
      await tester.tap(find.text('Voltar à carteira'));
      await tester.pumpAndSettle();
      expect(find.text('R\$ 105,03'), findsOneWidget);
      expect(find.text('R\$ 35,00'), findsOneWidget);
      await tester.ensureVisible(find.text('Ver registro'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Ver registro'));
      await tester.pumpAndSettle();
      expect(find.text('Protocolo: pedido-123'), findsOneWidget);
      await tester.ensureVisible(find.text('Fechar'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Fechar'));
      await tester.pumpAndSettle();
      await tester.pumpWidget(const SizedBox());
    },
  );

  testWidgets('falha preserva revisão e reutiliza identificação na tentativa', (
    tester,
  ) async {
    final repository = PendingFinanceRepository();
    await pumpWithdrawal(tester, repository);
    await tester.tap(find.text('Revisar saque'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Confirmar pedido'));
    await tester.pump();
    await tester.binding.handlePopRoute();
    await tester.pump();
    expect(find.text('Revise seu pedido'), findsOneWidget);
    repository.pending.first.completeError(ApiException('Falha de conexão.'));
    await tester.pumpAndSettle();
    expect(find.text('Falha de conexão.'), findsOneWidget);
    await tester.tap(find.text('Confirmar pedido'));
    await tester.pump();
    expect(repository.requests, hasLength(2));
    expect(repository.requests[1], repository.requests[0]);
    repository.pending.last.complete((
      saque: receipt,
      carteira: repository.wallet,
    ));
    await tester.pumpAndSettle();
    expect(find.text('Registro do saque'), findsOneWidget);
  });

  testWidgets(
    'voltar preserva edição e fonte ampliada com teclado cabe na tela',
    (tester) async {
      final repository = PendingFinanceRepository();
      await pumpWithdrawal(tester, repository, scale: 2);
      await tester.enterText(withdrawalField('Valor do saque'), '20,25');
      await tester.tap(find.text('Revisar saque'));
      await tester.pumpAndSettle();
      await tester.binding.handlePopRoute();
      await tester.pumpAndSettle();
      expect(
        tester
            .widget<TextField>(withdrawalField('Valor do saque'))
            .controller!
            .text,
        '20,25',
      );
      tester.view.viewInsets = const FakeViewPadding(bottom: 250);
      addTearDown(tester.view.resetViewInsets);
      await tester.ensureVisible(withdrawalField('Titular'));
      await tester.pumpAndSettle();
      expect(find.text('Revisar saque').hitTestable(), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );
}
