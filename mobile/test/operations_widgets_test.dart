import 'package:ecotech_mobile/core/theme/app_theme.dart';
import 'package:ecotech_mobile/features/operations/operations_widgets.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('indicadores acomodam fonte ampliada sem cortar o estado', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(320, 800);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.light(),
        home: MediaQuery(
          data: const MediaQueryData(textScaler: TextScaler.linear(2)),
          child: Scaffold(
            body: ListView(
              children: [
                const Row(
                  children: [
                    Expanded(
                      child: OperationsMetric(
                        icon: Icons.recycling,
                        value: 1234,
                        label: 'Em processamento',
                      ),
                    ),
                    Expanded(
                      child: OperationsMetric(
                        icon: Icons.check,
                        value: 42,
                        label: 'Finalizadas',
                      ),
                    ),
                  ],
                ),
                OperationsFilters(selected: '', onSelected: (_) {}),
              ],
            ),
          ),
        ),
      ),
    );
    expect(tester.takeException(), isNull);
    expect(
      tester.widget<Text>(find.text('Em processamento').first).maxLines,
      isNull,
    );
  });
}
