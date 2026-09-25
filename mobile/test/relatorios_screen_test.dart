import 'package:ecotech_mobile/core/theme/app_theme.dart';
import 'package:ecotech_mobile/data/communication/communication_data.dart';
import 'package:ecotech_mobile/data/finance/finance_data.dart';
import 'package:ecotech_mobile/data/models/usuario.dart';
import 'package:ecotech_mobile/features/auth/auth_controller.dart';
import 'package:ecotech_mobile/features/communication/communication_controller.dart';
import 'package:ecotech_mobile/features/company/company_controller.dart';
import 'package:ecotech_mobile/features/finance/finance_controller.dart';
import 'package:ecotech_mobile/features/finance/relatorios_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

class _Auth extends AuthController {
  @override
  Future<Usuario?> build() async =>
      const Usuario(id: 'empresa', nome: 'Recicla Kariri', tipo: 'empresa');
}

RelatorioData _report({bool available = true}) => RelatorioData.fromJson({
  'metricas': {
    'total_solicitacoes': 15,
    'peso_reciclado_kg': 22.8,
    'peso_reutilizado_kg': 19.2,
    'peso_total_kg': 42.0,
    'impacto_evitado': 2874.5,
    'taxa_reciclagem_pct': 54.3,
  },
  'finalizadas': List.generate(
    5,
    (i) => {
      'id': '$i', // IDs curtos também devem ser renderizados.
      'cidadao': 'Cidadão $i',
      'peso_kg': 5.4,
      'impacto_kg': 43.2,
      'metodo': 'Reciclagem',
      'estado': 'Reciclado',
      'data': '2026-08-31',
    },
  ),
  'pnrs': {
    'disponivel': available,
    'destinacao_adequada_pct': 100.0,
    'peso_total_gerenciado_kg': 42.0,
    'solicitacoes_atendidas': 15,
  },
  'pode_exportar': available,
});

Future<void> _mount(
  WidgetTester tester, {
  bool available = true,
  double width = 390,
  double scale = 1,
  List<PeriodoRelatorio>? requests,
}) async {
  tester.view.physicalSize = Size(width, 844);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        authControllerProvider.overrideWith(_Auth.new),
        relatorioProvider.overrideWith((ref, period) async {
          requests?.add(period);
          return _report(available: available);
        }),
        oportunidadesEmpresaProvider.overrideWith((ref) async => const []),
        badgesProvider.overrideWith(
          (ref) async =>
              const BadgesData(notificacoes: 4, mensagens: 0, oportunidades: 0),
        ),
      ],
      child: MaterialApp(
        theme: AppTheme.light(),
        builder: (context, child) => MediaQuery(
          data: MediaQuery.of(context)
              .copyWith(textScaler: TextScaler.linear(scale)),
          child: child!,
        ),
        home: const RelatoriosScreen(),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('relatório expande e recolhe operações mantendo dados reais', (
    tester,
  ) async {
    await _mount(tester);
    expect(find.text('Relatórios Ambientais'), findsOneWidget);
    expect(find.text('2874,5 kg CO₂'), findsOneWidget);
    expect(tester.takeException(), isNull);
    final scroll = find.byType(Scrollable).first;
    for (
      var i = 0;
      i < 15 &&
          find
              .text('Mostrar mais (2 restantes)')
              .hitTestable()
              .evaluate()
              .isEmpty;
      i++
    ) {
      await tester.drag(scroll, const Offset(0, -300));
      await tester.pumpAndSettle();
    }
    expect(find.text('Cidadão 4'), findsNothing);
    await tester.tap(find.text('Mostrar mais (2 restantes)'));
    await tester.pumpAndSettle();
    for (
      var i = 0;
      i < 15 && find.text('Mostrar menos').hitTestable().evaluate().isEmpty;
      i++
    ) {
      await tester.drag(scroll, const Offset(0, -250));
      await tester.pumpAndSettle();
    }
    expect(find.text('Cidadão 4'), findsOneWidget);
    await tester.tap(find.text('Mostrar menos'));
    await tester.pumpAndSettle();
    expect(find.text('Cidadão 4'), findsNothing);
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('plano restrito e fonte ampliada não quebram o relatório', (
    tester,
  ) async {
    await _mount(tester, available: false, width: 320, scale: 1.3);
    final export = tester.widget<FilledButton>(
      find.widgetWithText(FilledButton, 'Exportar CSV'),
    );
    expect(export.onPressed, isNull);
    await tester.scrollUntilVisible(
      find.text('Restrito'),
      300,
      scrollable: find.byType(Scrollable).first,
    );
    expect(
      find.text('Faça upgrade do plano para liberar PNRS e exportação CSV.'),
      findsOneWidget,
    );
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('período só é consultado ao aplicar o filtro', (tester) async {
    final requests = <PeriodoRelatorio>[];
    await _mount(tester, requests: requests);
    expect(requests.length, 1);
    await tester.tap(find.text('dd/mm/aaaa').first);
    await tester.pumpAndSettle();
    await tester.tap(find.text('OK'));
    await tester.pumpAndSettle();
    expect(requests.length, 1);
    await tester.tap(find.text('Filtrar'));
    await tester.pumpAndSettle();
    expect(requests.last.inicio, isNotNull);
    expect(requests.length, 2);
    await tester.tap(find.text('Limpar período'));
    await tester.pumpAndSettle();
    expect(find.text('dd/mm/aaaa'), findsNWidgets(2));
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox());
  });
}
