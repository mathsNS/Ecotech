import 'package:ecotech_mobile/data/citizen/citizen_data.dart';
import 'package:ecotech_mobile/data/communication/communication_data.dart';
import 'package:ecotech_mobile/data/company/operation_data.dart';
import 'package:ecotech_mobile/data/dashboard/dashboard_data.dart';
import 'package:ecotech_mobile/data/dashboard/dashboard_repository.dart';
import 'package:ecotech_mobile/data/finance/finance_data.dart';
import 'package:ecotech_mobile/data/models/usuario.dart';
import 'package:ecotech_mobile/features/auth/auth_controller.dart';
import 'package:ecotech_mobile/features/citizen/citizen_controller.dart';
import 'package:ecotech_mobile/features/citizen/solicitacao_detalhes_screen.dart';
import 'package:ecotech_mobile/features/communication/communication_controller.dart';
import 'package:ecotech_mobile/features/communication/conversas_screen.dart';
import 'package:ecotech_mobile/features/company/company_controller.dart';
import 'package:ecotech_mobile/features/company/operacoes_empresa_screen.dart';
import 'package:ecotech_mobile/features/dashboard/dashboard_controller.dart';
import 'package:ecotech_mobile/features/dashboard/dashboard_screen.dart';
import 'package:ecotech_mobile/features/finance/finance_controller.dart';
import 'package:ecotech_mobile/features/finance/relatorios_screen.dart';
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

class _AdminAuthController extends AuthController {
  @override
  Future<Usuario?> build() async => const Usuario(
    id: 'admin-1',
    nome: 'Admin EcoTech',
    tipo: 'administrador',
    email: 'admin@example.com',
  );
}

class _AdminDashboardRepo extends DashboardRepository {
  @override
  Future<DashboardData> carregar() async => DashboardData(
    tipo: 'administrador',
    usuario: const Usuario(
      id: 'admin-1',
      nome: 'Admin EcoTech',
      tipo: 'administrador',
    ),
    metricas: const {
      'peso_total_kg': 120.0,
      'solicitacoes': 4,
      'ativas': 2,
      'impacto_evitado_kg': 360.0,
      'receita': 90.0,
    },
    solicitacoesRecentes: [
      SolicitacaoResumo(
        id: 'sol-admin-01',
        cidadao: 'Maria Souza',
        estado: 'Solicitado',
        pesoKg: 3.5,
        dataCriacao: DateTime(2026, 9, 10),
      ),
    ],
  );
}

void main() {
  testWidgets('conversas mantém navegação da empresa e cabeçalho da marca', (
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

    expect(find.text('Central de conversas'), findsOneWidget);
    expect(find.byTooltip('Notificações'), findsOneWidget);
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

  testWidgets('retorno do sistema em rota sem pilha volta ao fallback', (
    tester,
  ) async {
    final router = GoRouter(
      initialLocation: '/aba',
      routes: [
        GoRoute(
          path: '/home',
          builder: (_, _) => const Scaffold(body: Text('Painel inicial')),
        ),
        GoRoute(
          path: '/aba',
          builder: (_, _) => const AppBackScope(
            child: Scaffold(body: Text('Aba secundaria')),
          ),
        ),
      ],
    );
    addTearDown(router.dispose);

    await tester.pumpWidget(MaterialApp.router(routerConfig: router));
    await tester.pumpAndSettle();
    await tester.binding.handlePopRoute();
    await tester.pumpAndSettle();

    expect(find.text('Painel inicial'), findsOneWidget);
  });

  testWidgets('detalhes de solicitacao possui botao voltar para solicitacoes', (
    tester,
  ) async {
    final router = GoRouter(
      initialLocation: '/solicitacoes/abc12345',
      routes: [
        GoRoute(
          path: '/solicitacoes',
          builder: (_, _) => const Scaffold(body: Text('Lista solicitacoes')),
        ),
        GoRoute(
          path: '/solicitacoes/:id',
          builder: (_, state) =>
              SolicitacaoDetalhesScreen(id: state.pathParameters['id']!),
        ),
      ],
    );
    addTearDown(router.dispose);

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          solicitacaoDetalhesProvider.overrideWith(
            (ref, id) async => SolicitacaoDetalhesData.fromJson({
              'id': id,
              'estado': 'Solicitado',
              'peso_estimado_kg': 2.0,
              'itens': const [],
            }),
          ),
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

    expect(find.byTooltip('Voltar'), findsOneWidget);
    await tester.tap(find.byTooltip('Voltar'));
    await tester.pumpAndSettle();
    expect(find.text('Lista solicitacoes'), findsOneWidget);
    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('admin acessa operacoes e relatorios com botao voltar', (
    tester,
  ) async {
    final router = GoRouter(
      initialLocation: '/home',
      routes: [
        GoRoute(path: '/home', builder: (_, _) => const DashboardScreen()),
        GoRoute(
          path: '/empresa/operacoes',
          builder: (_, _) => const OperacoesEmpresaScreen(),
        ),
        GoRoute(
          path: '/empresa/operacoes/:id',
          builder: (_, state) => Scaffold(
            body: Text('Detalhe admin ${state.pathParameters['id']}'),
          ),
        ),
        GoRoute(
          path: '/relatorios',
          builder: (_, _) => const RelatoriosScreen(),
        ),
      ],
    );
    addTearDown(router.dispose);

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authControllerProvider.overrideWith(_AdminAuthController.new),
          dashboardRepositoryProvider.overrideWithValue(_AdminDashboardRepo()),
          operacoesEmpresaProvider.overrideWith(
            (ref, query) async => const OperacoesPaginaData(
              operacoes: [],
              estatisticas: {},
              pagina: 1,
              totalPaginas: 1,
              total: 0,
            ),
          ),
          relatorioProvider.overrideWith(
            (ref, period) async => RelatorioData.fromJson({
              'metricas': {},
              'finalizadas': const [],
              'pnrs': {'disponivel': true},
              'pode_exportar': true,
            }),
          ),
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

    // Admin dashboard tem atalho para Operacoes e solicitações clicáveis.
    expect(find.text('Operações'), findsOneWidget);
    expect(find.text('Relatórios'), findsOneWidget);

    await tester.tap(find.text('Operações'));
    await tester.pumpAndSettle();
    expect(find.text('Gerenciamento de\nOperações'), findsOneWidget);
    expect(find.byTooltip('Voltar'), findsOneWidget);
    expect(find.text('Mais'), findsNothing);

    await tester.tap(find.byTooltip('Voltar'));
    await tester.pumpAndSettle();
    expect(find.text('Últimas solicitações do sistema'), findsOneWidget);

    await tester.tap(find.text('Relatórios'));
    await tester.pumpAndSettle();
    expect(find.text('Relatórios Ambientais'), findsOneWidget);
    expect(find.byTooltip('Voltar'), findsOneWidget);

    await tester.tap(find.byTooltip('Voltar'));
    await tester.pumpAndSettle();

    await tester.scrollUntilVisible(
      find.text('Solicitação #sol-admi'),
      200,
      scrollable: find.byType(Scrollable).first,
    );
    await tester.ensureVisible(find.text('Solicitação #sol-admi'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Solicitação #sol-admi'));
    await tester.pumpAndSettle();
    expect(find.text('Detalhe admin sol-admin-01'), findsOneWidget);

    await tester.pumpWidget(const SizedBox());
  });
}
