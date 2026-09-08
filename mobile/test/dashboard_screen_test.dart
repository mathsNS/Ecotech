import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:ecotech_mobile/data/dashboard/dashboard_data.dart';
import 'package:ecotech_mobile/data/dashboard/dashboard_repository.dart';
import 'package:ecotech_mobile/data/models/usuario.dart';
import 'package:ecotech_mobile/features/dashboard/dashboard_controller.dart';
import 'package:ecotech_mobile/features/dashboard/dashboard_screen.dart';

class _DashboardRepositoryFake implements DashboardRepository {
  _DashboardRepositoryFake(this.dados);

  final DashboardData dados;

  @override
  Future<DashboardData> carregar() async => dados;
}

DashboardData _dashboard(String tipo) {
  final metricas = switch (tipo) {
    'empresa' => <String, dynamic>{
      'finalizadas': 12,
      'ativas': 3,
      'peso_processado_kg': 140.5,
      'saldo': 320.0,
      'co2_evitado_kg': 421.5,
      'taxa_reciclagem_percentual': 75.0,
    },
    'administrador' => <String, dynamic>{
      'peso_total_kg': 850,
      'solicitacoes': 40,
      'ativas': 8,
      'finalizadas': 32,
      'impacto_evitado_kg': 1200,
      'receita': 415.5,
    },
    _ => <String, dynamic>{
      'saldo': 18.5,
      'pontos': 450,
      'tier': 'Prata',
      'dispositivos': 7,
    },
  };
  return DashboardData(
    tipo: tipo,
    usuario: Usuario(
      id: 'usuario-1',
      nome: 'João Silva',
      tipo: tipo,
      email: 'joao@example.com',
    ),
    metricas: metricas,
    missao: tipo == 'cidadao'
        ? {
            'titulo': 'Recicle 15 aparelhos',
            'atual': 7,
            'meta': 15,
            'recompensa_pontos': 150,
          }
        : null,
    proximoTier: tipo == 'cidadao'
        ? {'nome': 'Ouro', 'meta': 600, 'progresso_percentual': 75}
        : null,
    meses: tipo == 'empresa'
        ? const [MesDashboard('08/26', 100), MesDashboard('09/26', 140.5)]
        : const [],
  );
}

Future<void> _abrir(WidgetTester tester, String tipo) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        dashboardRepositoryProvider.overrideWithValue(
          _DashboardRepositoryFake(_dashboard(tipo)),
        ),
      ],
      child: const MaterialApp(home: DashboardScreen()),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('cidadão visualiza pontos, missão e tier', (tester) async {
    await _abrir(tester, 'cidadao');

    expect(find.text('Pontos acumulados'), findsOneWidget);
    expect(find.text('Missão atual'), findsOneWidget);
    expect(find.text('Próxima recompensa'), findsOneWidget);
  });

  testWidgets('empresa visualiza desempenho e impacto', (tester) async {
    await _abrir(tester, 'empresa');

    expect(find.text('Peso processado'), findsAtLeastNWidgets(1));
    expect(find.text('Desempenho e impacto'), findsOneWidget);
    expect(find.text('Impacto acumulado'), findsOneWidget);
  });

  testWidgets('administrador visualiza panorama do sistema', (tester) async {
    await _abrir(tester, 'administrador');

    expect(find.text('Total processado'), findsOneWidget);
    expect(find.text('Receita EcoTech'), findsOneWidget);
    expect(find.text('Últimas solicitações do sistema'), findsOneWidget);
  });
}
