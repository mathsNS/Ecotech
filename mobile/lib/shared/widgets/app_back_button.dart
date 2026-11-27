import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class AppBackButton extends StatelessWidget {
  const AppBackButton({this.fallbackRoute = '/home', super.key});

  final String fallbackRoute;

  @override
  Widget build(BuildContext context) => IconButton(
    tooltip: 'Voltar',
    icon: const Icon(Icons.arrow_back),
    onPressed: () {
      if (context.canPop()) {
        context.pop();
      } else {
        context.go(fallbackRoute);
      }
    },
  );
}

/// Intercepta o retorno do sistema em rotas sem historico, evitando fechar o app.
class AppBackScope extends StatelessWidget {
  const AppBackScope({
    required this.child,
    this.fallbackRoute = '/home',
    super.key,
  });

  final Widget child;
  final String fallbackRoute;

  @override
  Widget build(BuildContext context) {
    final router = GoRouter.maybeOf(context);
    final canPopNavigator = Navigator.maybeOf(context)?.canPop() ?? false;
    final canPopRouter = router?.canPop() ?? false;
    final canPop = router == null || canPopRouter || canPopNavigator;
    return PopScope(
      canPop: canPop,
      onPopInvokedWithResult: (didPop, _) {
        if (didPop || router == null) return;
        if (router.canPop()) {
          router.pop();
        } else {
          router.go(fallbackRoute);
        }
      },
      child: child,
    );
  }
}
