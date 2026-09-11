import 'package:go_router/go_router.dart';

import '../../features/auth/cadastro_screen.dart';
import '../../features/auth/login_screen.dart';
import '../../features/citizen/entregas_screen.dart';
import '../../features/citizen/nova_solicitacao_screen.dart';
import '../../features/citizen/pontos_screen.dart';
import '../../features/citizen/solicitacao_detalhes_screen.dart';
import '../../features/citizen/solicitacoes_screen.dart';
import '../../features/dashboard/dashboard_screen.dart';
import '../../features/profile/perfil_screen.dart';
import '../../features/splash/splash_screen.dart';

final appRouter = GoRouter(
  initialLocation: '/',
  routes: [
    GoRoute(path: '/', builder: (context, state) => const SplashScreen()),
    GoRoute(path: '/login', builder: (context, state) => const LoginScreen()),
    GoRoute(
      path: '/cadastro',
      builder: (context, state) => const CadastroScreen(),
    ),
    GoRoute(
      path: '/home',
      builder: (context, state) => const DashboardScreen(),
    ),
    GoRoute(path: '/perfil', builder: (context, state) => const PerfilScreen()),
    GoRoute(path: '/pontos', builder: (context, state) => const PontosScreen()),
    GoRoute(
      path: '/solicitacoes',
      builder: (context, state) => const SolicitacoesScreen(),
    ),
    GoRoute(
      path: '/solicitacoes/nova',
      builder: (context, state) => NovaSolicitacaoScreen(
        tipoInicial: state.uri.queryParameters['tipo'],
        pontoIdInicial: state.uri.queryParameters['pontoId'],
      ),
    ),
    GoRoute(
      path: '/solicitacoes/:id',
      builder: (context, state) =>
          SolicitacaoDetalhesScreen(id: state.pathParameters['id']!),
    ),
    GoRoute(
      path: '/entregas',
      builder: (context, state) => const EntregasScreen(),
    ),
  ],
);
