import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_colors.dart';
import '../../shared/widgets/app_back_button.dart';
import '../communication/communication_controller.dart';

class EcoTechDashboardHeader extends ConsumerStatefulWidget
    implements PreferredSizeWidget {
  const EcoTechDashboardHeader({
    required this.name,
    this.showBackButton = false,
    this.fallbackRoute = '/home',
    super.key,
  });

  final String name;
  final bool showBackButton;
  final String fallbackRoute;

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
      automaticallyImplyLeading: false,
      leading: widget.showBackButton
          ? AppBackButton(fallbackRoute: widget.fallbackRoute)
          : null,
      toolbarHeight: 60,
      backgroundColor: AppColors.surfaceSubtle,
      shape: const Border(bottom: BorderSide(color: AppColors.border)),
      titleSpacing: widget.showBackButton ? 0 : 16,
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
            onTap: () => context.push('/perfil'),
            child: CircleAvatar(
              radius: 21,
              backgroundColor: AppColors.secondary,
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
