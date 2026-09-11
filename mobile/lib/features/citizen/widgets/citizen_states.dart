import 'package:flutter/material.dart';

import '../../../core/api/api_exception.dart';
import '../../../core/theme/app_colors.dart';

class CitizenError extends StatelessWidget {
  const CitizenError({required this.error, required this.onRetry, super.key});
  final Object error;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) => Center(
    child: Padding(
      padding: const EdgeInsets.all(28),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(
            Icons.cloud_off_outlined,
            size: 46,
            color: AppColors.textLight,
          ),
          const SizedBox(height: 12),
          Text(
            error is ApiException
                ? (error as ApiException).mensagem
                : 'Não foi possível carregar os dados.',
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 14),
          ElevatedButton(
            onPressed: onRetry,
            child: const Text('Tentar novamente'),
          ),
        ],
      ),
    ),
  );
}

class CitizenEmpty extends StatelessWidget {
  const CitizenEmpty({required this.message, this.action, super.key});
  final String message;
  final Widget? action;

  @override
  Widget build(BuildContext context) => Center(
    child: Padding(
      padding: const EdgeInsets.all(30),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Image.asset('assets/images/icon-pendente.png', width: 64, height: 64),
          const SizedBox(height: 16),
          Text(message, textAlign: TextAlign.center),
          if (action != null) ...[const SizedBox(height: 16), action!],
        ],
      ),
    ),
  );
}
