import 'package:ecotech_mobile/core/theme/app_theme.dart';
import 'package:ecotech_mobile/data/company/company_data.dart';
import 'package:ecotech_mobile/data/company/company_repository.dart';
import 'package:ecotech_mobile/data/communication/communication_data.dart';
import 'package:ecotech_mobile/data/models/usuario.dart';
import 'package:ecotech_mobile/features/auth/auth_controller.dart';
import 'package:ecotech_mobile/features/communication/communication_controller.dart';
import 'package:ecotech_mobile/features/company/company_controller.dart';
import 'package:ecotech_mobile/features/company/oportunidades_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

class _Auth extends AuthController {
  @override
  Future<Usuario?> build() async =>
      const Usuario(id: 'empresa', nome: 'Parceiro', tipo: 'empresa');
}

class _Repository extends CompanyRepository {
  @override
  Future<AceiteOportunidadeData> aceitarOportunidade(String id) async =>
      const AceiteOportunidadeData(
        solicitacaoId: 'coleta-1',
        endereco: 'Rua privada',
        nomeContato: 'Contato privado',
        dataAgendamento: '2026-10-16T12:00:00',
      );
}

void main() {
  testWidgets('aceite libera contato e abre detalhes da empresa', (
    tester,
  ) async {
    final router = GoRouter(
      routes: [
        GoRoute(
          path: '/',
          builder: (_, _) => const OportunidadesEmpresaScreen(),
        ),
        GoRoute(
          path: '/empresa/operacoes/:id',
          builder: (_, state) =>
              Scaffold(body: Text('Operação ${state.pathParameters['id']}')),
        ),
      ],
    );
    addTearDown(router.dispose);
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authControllerProvider.overrideWith(_Auth.new),
          companyRepositoryProvider.overrideWithValue(_Repository()),
          badgesProvider.overrideWith(
            (ref) async => const BadgesData(
              notificacoes: 0,
              mensagens: 0,
              oportunidades: 1,
            ),
          ),
          oportunidadesEmpresaProvider.overrideWith(
            (ref) async => const [
              OportunidadeData(
                id: 'oferta',
                solicitacaoId: 'coleta-1',
                baseId: 'base',
                baseNome: 'Centro',
                distanciaKm: 1,
                expiraEm: '2026-10-16T12:00:00',
                categorias: ['celular'],
                pesoEstimadoKg: 2,
                agendadaPara: '2026-10-17T12:00:00',
              ),
            ],
          ),
        ],
        child: MaterialApp.router(
          theme: AppTheme.light(),
          routerConfig: router,
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.textContaining('Contato privado'), findsNothing);
    await tester.scrollUntilVisible(
      find.text('Aceitar coleta'),
      250,
      scrollable: find.byType(Scrollable).first,
    );
    await tester.pumpAndSettle();
    await tester.tap(find.text('Aceitar coleta'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 300));
    expect(find.textContaining('Contato privado'), findsOneWidget);
    await tester.tap(find.text('Ver solicitação'));
    await tester.pumpAndSettle();
    expect(find.text('Operação coleta-1'), findsOneWidget);
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox());
  });
}
