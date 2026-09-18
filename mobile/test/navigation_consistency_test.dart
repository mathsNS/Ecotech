import 'package:ecotech_mobile/data/communication/communication_data.dart';
import 'package:ecotech_mobile/data/models/usuario.dart';
import 'package:ecotech_mobile/features/auth/auth_controller.dart';
import 'package:ecotech_mobile/features/communication/communication_controller.dart';
import 'package:ecotech_mobile/features/communication/conversas_screen.dart';
import 'package:ecotech_mobile/features/company/company_controller.dart';
import 'package:ecotech_mobile/shared/widgets/app_back_button.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

class _CompanyAuthController extends AuthController {
  @override
  Future<Usuario?> build() async => const Usuario(
    id: 'empresa-1',
    nome: 'Recicla Kariri',
    tipo: 'empresa',
    email: 'empresa@example.com',
  );
}

void main() {
  testWidgets('conversas mantém navegação da empresa e retorno visível', (
    tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authControllerProvider.overrideWith(_CompanyAuthController.new),
          conversasProvider.overrideWith((ref) async => const []),
          oportunidadesEmpresaProvider.overrideWith((ref) async => const []),
          badgesProvider.overrideWith(
            (ref) async => const BadgesData(
              notificacoes: 0,
              mensagens: 0,
              oportunidades: 0,
            ),
          ),
        ],
        child: const MaterialApp(home: ConversasScreen()),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.byTooltip('Voltar'), findsOneWidget);
    expect(find.text('Dashboard'), findsOneWidget);
    expect(find.text('Operações'), findsOneWidget);
    expect(find.text('Relatórios'), findsOneWidget);
    expect(find.text('Conversas'), findsAtLeastNWidgets(1));
    expect(find.text('Mais'), findsOneWidget);

    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('botão voltar retorna ao início quando não existe histórico', (
    tester,
  ) async {
    final router = GoRouter(
      initialLocation: '/secundaria',
      routes: [
        GoRoute(
          path: '/home',
          builder: (context, state) => const Scaffold(body: Text('Início')),
        ),
        GoRoute(
          path: '/secundaria',
          builder: (context, state) => Scaffold(
            appBar: AppBar(leading: const AppBackButton()),
            body: const Text('Tela secundária'),
          ),
        ),
      ],
    );

    await tester.pumpWidget(MaterialApp.router(routerConfig: router));
    await tester.pumpAndSettle();
    await tester.tap(find.byTooltip('Voltar'));
    await tester.pumpAndSettle();

    expect(find.text('Início'), findsOneWidget);
    expect(find.text('Tela secundária'), findsNothing);
  });
}
