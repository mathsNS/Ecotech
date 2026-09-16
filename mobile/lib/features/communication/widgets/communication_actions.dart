import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../communication_controller.dart';

class CommunicationActions extends ConsumerStatefulWidget {
  const CommunicationActions({super.key});

  @override
  ConsumerState<CommunicationActions> createState() =>
      _CommunicationActionsState();
}

class _CommunicationActionsState extends ConsumerState<CommunicationActions> {
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _timer = Timer.periodic(
      const Duration(seconds: 30),
      (_) => ref.invalidate(badgesProvider),
    );
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final badges = ref.watch(badgesProvider).valueOrNull;
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        IconButton(
          tooltip: 'Conversas',
          onPressed: () => context.push('/conversas'),
          icon: Badge.count(
            count: badges?.mensagens ?? 0,
            isLabelVisible: (badges?.mensagens ?? 0) > 0,
            child: const Icon(Icons.chat_bubble_outline),
          ),
        ),
        IconButton(
          tooltip: 'Notificações',
          onPressed: () => context.push('/notificacoes'),
          icon: Badge.count(
            count: badges?.notificacoes ?? 0,
            isLabelVisible: (badges?.notificacoes ?? 0) > 0,
            child: Icon(
              (badges?.notificacoes ?? 0) > 0
                  ? Icons.notifications_active
                  : Icons.notifications_outlined,
            ),
          ),
        ),
      ],
    );
  }
}
