import 'package:ecotech_mobile/core/theme/app_theme.dart';
import 'package:ecotech_mobile/features/citizen/nova_solicitacao_screen.dart';
import 'package:ecotech_mobile/features/citizen/widgets/collection_fields.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

Future<void> pumpCollection(WidgetTester tester, {double scale = 1}) async {
  tester.view.physicalSize = const Size(390, 844);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);
  final router = GoRouter(
    initialLocation: '/nova',
    routes: [
      GoRoute(path: '/nova', builder: (_, _) => const NovaSolicitacaoScreen()),
      GoRoute(
        path: '/home',
        builder: (_, _) => const Scaffold(body: Text('Início')),
      ),
    ],
  );
  addTearDown(router.dispose);
  await tester.pumpWidget(
    ProviderScope(
      child: MaterialApp.router(
        theme: AppTheme.light(),
        routerConfig: router,
        builder: (context, child) => MediaQuery(
          data: MediaQuery.of(context)
              .copyWith(textScaler: TextScaler.linear(scale)),
          child: child!,
        ),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

Finder field(String label) => find.descendant(
  of: find.byWidgetPredicate(
    (widget) => widget is CollectionField && widget.label == label,
  ),
  matching: find.byType(TextField),
);

Future<void> tapVisible(WidgetTester tester, Finder finder) async {
  if (finder.evaluate().isEmpty) {
    await tester.scrollUntilVisible(
      finder,
      300,
      scrollable: find.byType(Scrollable).first,
    );
  }
  await tester.ensureVisible(finder);
  await tester.pumpAndSettle();
  await tester.tap(finder);
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('quantidade e categoria acompanham a edição e o retorno', (
    tester,
  ) async {
    await pumpCollection(tester);
    await tester.enterText(field('Modelo ou nome'), 'Notebook de teste');
    await tester.enterText(field('Quantidade'), '3');
    await tapVisible(
      tester,
      find.byType(DropdownButtonFormField<String>).first,
    );
    await tapVisible(tester, find.text('Computador').last);
    expect(find.text('Notebook'), findsOneWidget);
    await tapVisible(tester, find.text('Próximo'));
    await tapVisible(tester, find.text('Anterior'));
    expect(tester.widget<TextField>(field('Quantidade')).controller!.text, '3');
    expect(find.text('Notebook'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('ações ficam acessíveis e voltar retorna à etapa anterior', (
    tester,
  ) async {
    await pumpCollection(tester);
    expect(find.text('Próximo').hitTestable(), findsOneWidget);
    await tester.enterText(field('Modelo ou nome'), 'Celular de teste');
    await tapVisible(tester, find.text('Próximo'));
    expect(find.text('Etapa 2 de 3 · Endereço'), findsOneWidget);
    await tapVisible(tester, find.byTooltip('Voltar'));
    expect(find.text('Etapa 1 de 3 · Dispositivo'), findsOneWidget);
    expect(find.text('Celular de teste'), findsOneWidget);
    await tapVisible(tester, find.text('Cancelar'));
    expect(find.text('Início'), findsOneWidget);
  });

  testWidgets('apresenta a etapa e mantém a validação do dispositivo', (
    tester,
  ) async {
    await pumpCollection(tester);
    expect(find.text('COLETA DOMICILIAR'), findsOneWidget);
    expect(find.text('Etapa 1 de 3 · Dispositivo'), findsOneWidget);
    await tapVisible(tester, find.text('Próximo'));
    expect(find.text('Campo obrigatório.'), findsOneWidget);
    expect(field('Modelo ou nome'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
