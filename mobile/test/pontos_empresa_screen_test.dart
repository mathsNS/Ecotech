import 'package:ecotech_mobile/data/communication/communication_data.dart';
import 'package:ecotech_mobile/data/company/company_data.dart';
import 'package:ecotech_mobile/features/communication/communication_controller.dart';
import 'package:ecotech_mobile/features/company/company_controller.dart';
import 'package:ecotech_mobile/features/company/pontos_empresa_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

void main() {
  testWidgets('entrega em ponto da empresa abre detalhe operacional da empresa', (
    tester,
  ) async {
    final router = GoRouter(
      initialLocation: '/empresa/pontos',
      routes: [
        GoRoute(
          path: '/empresa/pontos',
          builder: (_, _) => const PontosEmpresaScreen(),
        ),
        GoRoute(
          path: '/empresa/operacoes/:id',
          builder: (_, state) => Scaffold(
            body: Text('Operacao empresa ${state.pathParameters['id']}'),
          ),
        ),
      ],
    );
    addTearDown(router.dispose);

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          pontosEmpresaProvider.overrideWith(
            (ref) async => [
              PontoEmpresaData(
                id: 'ponto-1',
                nome: 'Ponto Centro',
                endereco: 'Rua Central, 100',
                capacidadeKg: 500,
                ocupacaoKg: 50,
                ativa: true,
                solicitacoes: const [
                  EntregaPontoData(
                    id: 'op-999',
                    cidadao: 'Carlos Lima',
                    estado: 'Solicitado',
                    pesoKg: 4.5,
                    pesoInformadoCidadao: true,
                    confirmadoEmpresa: false,
                    podeConfirmar: false,
                  ),
                ],
              ),
            ],
          ),
          oportunidadesEmpresaProvider.overrideWith((ref) async => const []),
          badgesProvider.overrideWith(
            (ref) async => const BadgesData(
              notificacoes: 0,
              mensagens: 0,
              oportunidades: 0,
            ),
          ),
        ],
        child: MaterialApp.router(routerConfig: router),
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.text('Entregas associadas'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Carlos Lima'));
    await tester.pumpAndSettle();

    expect(find.text('Operacao empresa op-999'), findsOneWidget);
    await tester.pumpWidget(const SizedBox());
  });
}
