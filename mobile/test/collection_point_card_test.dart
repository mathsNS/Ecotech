import 'package:ecotech_mobile/core/theme/app_theme.dart';
import 'package:ecotech_mobile/data/citizen/citizen_data.dart';
import 'package:ecotech_mobile/features/citizen/widgets/collection_point_card.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('ponto sem capacidade não permite entrega nem produz NaN', (
    tester,
  ) async {
    var selected = false;
    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.light(),
        home: Scaffold(
          body: CollectionPointCard(
            point: PontoColetaData.fromJson({
              'id': 'zero',
              'nome': 'Ponto indisponível',
              'capacidade_kg': 0,
              'ocupacao_kg': 0,
              'disponibilidade_percentual': 100,
            }),
            onSelect: () => selected = true,
          ),
        ),
      ),
    );
    expect(
      tester
          .widget<LinearProgressIndicator>(find.byType(LinearProgressIndicator))
          .value,
      0,
    );
    expect(
      tester.widget<ElevatedButton>(find.byType(ElevatedButton)).onPressed,
      isNull,
    );
    expect(selected, isFalse);
    expect(find.text('0,0% livre'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('capacidade livre é apresentada e ponto pode ser selecionado', (
    tester,
  ) async {
    var selected = false;
    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.light(),
        home: Scaffold(
          body: CollectionPointCard(
            point: PontoColetaData.fromJson({
              'id': 'livre',
              'nome': 'Ponto Central',
              'capacidade_kg': 100,
              'ocupacao_kg': 25,
              'disponibilidade_percentual': 75,
            }),
            onSelect: () => selected = true,
          ),
        ),
      ),
    );
    expect(
      tester
          .widget<LinearProgressIndicator>(find.byType(LinearProgressIndicator))
          .value,
      .75,
    );
    await tester.tap(find.text('Selecionar ponto'));
    expect(selected, isTrue);
  });
}
