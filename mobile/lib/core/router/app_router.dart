import 'package:go_router/go_router.dart';

import '../../features/auth/cadastro_screen.dart';
import '../../features/auth/login_screen.dart';
import '../../features/home/home_placeholder_screen.dart';
import '../../features/splash/splash_screen.dart';

final appRouter = GoRouter(
  initialLocation: '/',
  routes: [
    GoRoute(path: '/', builder: (context, state) => const SplashScreen()),
    GoRoute(path: '/login', builder: (context, state) => const LoginScreen()),
    GoRoute(path: '/cadastro', builder: (context, state) => const CadastroScreen()),
    GoRoute(path: '/home', builder: (context, state) => const HomePlaceholderScreen()),
  ],
);
