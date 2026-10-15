import 'package:ecotech_mobile/core/theme/app_theme.dart';
import 'package:ecotech_mobile/data/citizen/citizen_data.dart';
import 'package:ecotech_mobile/features/citizen/citizen_controller.dart';
import 'package:ecotech_mobile/features/citizen/pontos_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

final samplePoints = [
  PontoColetaData.fromJson({
    'id': 'central',
    'nome': 'Recicla Central',
    'empresa': 'Empresa parceira',
    'endereco': 'Rua Um, Centro, Crato',
    'capacidade_kg': 100,
    'ocupacao_kg': 25,
    'disponibilidade_percentual': 75,
  }),
  PontoColetaData.fromJson({
    'id': 'norte',
    'nome': 'Unidade Norte',
    'empresa': 'Outra empresa',
    'endereco': 'Rua Dois, Triângulo',
    'capacidade_kg': 200,
    'ocupacao_kg': 200,
    'disponibilidade_percentual': 0,
  }),
];

Future<void> pumpPoints(
  WidgetTester tester, {
  Future<List<PontoColetaData>> Function()? load,
  ValueChanged<PontoColetaData?>? onSelected,
  double scale = 1,
}) async {
  tester.view.physicalSize = const Size(320, 800);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        pontosColetaProvider.overrideWith(
          (ref) => load?.call() ?? Future.value(samplePoints),
        ),
      ],
      child: MaterialApp(
        theme: AppTheme.light(),
        builder: (context, child) => MediaQuery(
          data: MediaQuery.of(context)
              .copyWith(textScaler: TextScaler.linear(scale)),
          child: child!,
        ),
        home: Builder(
          builder: (context) => Scaffold(
            body: TextButton(
              onPressed: () async {
                final point = await Navigator.of(context).push<PontoColetaData>(
                  MaterialPageRoute(
                    builder: (_) => const PontosScreen(selectionMode: true),
                  ),
                );
                onSelected?.call(point);
              },
              child: const Text('Escolher ponto'),
            ),
          ),
        ),
      ),
    ),
  );
  await tester.tap(find.text('Escolher ponto'));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('busca por endereço, mostra vazio e permite limpar', (
    tester,
  ) async {
    await pumpPoints(tester);
    await tester.enterText(find.byType(TextField), 'centro');
    await tester.pumpAndSettle();
    expect(find.text('Recicla Central'), findsOneWidget);
    expect(find.text('Unidade Norte'), findsNothing);
    await tester.enterText(find.byType(TextField), 'inexistente');
    await tester.pumpAndSettle();
    expect(
      find.text('Nenhum ponto encontrado. Tente outro nome ou bairro.'),
      findsOneWidget,
    );
    await tester.tap(find.byTooltip('Limpar busca'));
    await tester.pumpAndSettle();
    expect(find.text('Unidade Norte'), findsOneWidget);
  });

  testWidgets('seleção retorna o ponto com fonte ampliada sem overflow', (
    tester,
  ) async {
    PontoColetaData? selected;
    await pumpPoints(tester, scale: 2, onSelected: (point) => selected = point);
    await tester.ensureVisible(find.text('Selecionar ponto').first);
    await tester.pumpAndSettle();
    await tester.tap(find.text('Selecionar ponto').first);
    await tester.pumpAndSettle();
    expect(selected?.id, 'central');
    expect(tester.takeException(), isNull);
  });

  testWidgets('erro permite recarregar e lista vazia permite atualização', (
    tester,
  ) async {
    var attempts = 0;
    await pumpPoints(
      tester,
      load: () async {
        if (attempts++ == 0) throw Exception('offline');
        return [];
      },
    );
    await tester.tap(find.text('Tentar novamente'));
    await tester.pumpAndSettle();
    expect(
      find.text('Nenhum ponto de coleta está disponível no momento.'),
      findsOneWidget,
    );
    await tester.drag(find.byType(SingleChildScrollView), const Offset(0, 350));
    await tester.pumpAndSettle();
    expect(attempts, 3);
  });
}
