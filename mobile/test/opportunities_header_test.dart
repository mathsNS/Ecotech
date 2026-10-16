import 'package:ecotech_mobile/core/theme/app_theme.dart';
import 'package:ecotech_mobile/features/company/widgets/opportunities_header.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

void main() {
  testWidgets('privacidade legível e acesso às bases com fonte ampliada', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(320, 800);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final router = GoRouter(
      routes: [
        GoRoute(
          path: '/',
          builder: (_, _) =>
              Scaffold(body: ListView(children: const [OpportunitiesHeader()])),
        ),
        GoRoute(
          path: '/empresa/bases',
          builder: (_, _) => const Scaffold(body: Text('Bases da empresa')),
        ),
      ],
    );
    addTearDown(router.dispose);
    await tester.pumpWidget(
      MaterialApp.router(
        theme: AppTheme.light(),
        routerConfig: router,
        builder: (context, child) => MediaQuery(
          data: MediaQuery.of(context)
              .copyWith(textScaler: const TextScaler.linear(2)),
          child: child!,
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text('Privacidade protegida'), findsOneWidget);
    expect(tester.takeException(), isNull);
    await tester.ensureVisible(find.text('Gerenciar bases'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Gerenciar bases'));
    await tester.pumpAndSettle();
    expect(find.text('Bases da empresa'), findsOneWidget);
  });
}
