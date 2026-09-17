import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../auth/auth_controller.dart';

/// Tela de partida: decide se o usuario ja tem sessao valida ou precisa logar.
class SplashScreen extends ConsumerWidget {
  const SplashScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    ref.listen(authControllerProvider, (previous, proximo) {
      proximo.whenData((usuario) {
        context.go(usuario != null ? '/home' : '/login');
      });
    });

    final state = ref.watch(authControllerProvider);
    return Scaffold(
      body: state.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        data: (_) => const Center(child: CircularProgressIndicator()),
        error: (_, _) => Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 420),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.cloud_off_outlined, size: 52),
                  const SizedBox(height: 16),
                  Text(
                    'Não foi possível verificar sua sessão',
                    style: Theme.of(context).textTheme.titleLarge,
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'O EcoTech precisa se conectar ao servidor. Verifique sua internet e tente novamente.',
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 20),
                  ElevatedButton.icon(
                    onPressed: () =>
                        ref.read(authControllerProvider.notifier).reload(),
                    icon: const Icon(Icons.refresh),
                    label: const Text('Tentar novamente'),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
