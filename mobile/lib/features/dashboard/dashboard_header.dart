import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_colors.dart';
import '../communication/communication_controller.dart';

class EcoTechDashboardHeader extends ConsumerStatefulWidget
    implements PreferredSizeWidget {
  const EcoTechDashboardHeader({required this.name, super.key});

  final String name;

  @override
  Size get preferredSize => const Size.fromHeight(60);

  @override
  ConsumerState<EcoTechDashboardHeader> createState() =>
      _EcoTechDashboardHeaderState();
}

class _EcoTechDashboardHeaderState
    extends ConsumerState<EcoTechDashboardHeader> {
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
    final notifications =
        ref.watch(badgesProvider).valueOrNull?.notificacoes ?? 0;
    final initial = widget.name.trim().isEmpty
        ? 'E'
        : widget.name.trim().substring(0, 1).toUpperCase();
    return AppBar(
      toolbarHeight: 60,
      backgroundColor: const Color(0xFFF2F6F3),
      shape: const Border(bottom: BorderSide(color: Color(0xFFDDE4E0))),
      titleSpacing: 16,
      title: Image.asset(
        'assets/images/ecotech navbar.png',
        width: 104,
        fit: BoxFit.contain,
      ),
      actions: [
        IconButton(
          tooltip: 'Notificações',
          onPressed: () => context.push('/notificacoes'),
          icon: Badge.count(
            count: notifications,
            isLabelVisible: notifications > 0,
            backgroundColor: const Color(0xFFE30620),
            child: const Icon(Icons.notifications_none_rounded, size: 25),
          ),
        ),
        const SizedBox(width: 4),
        Semantics(
          button: true,
          label: 'Abrir perfil',
          child: InkWell(
            customBorder: const CircleBorder(),
            onTap: () => context.go('/perfil'),
            child: CircleAvatar(
              radius: 21,
              backgroundColor: const Color(0xFFDFF2E7),
              child: Text(
                initial,
                style: const TextStyle(
                  color: AppColors.primaryDark,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
          ),
        ),
        const SizedBox(width: 16),
      ],
    );
  }
}
