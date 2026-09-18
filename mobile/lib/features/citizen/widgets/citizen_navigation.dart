import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/theme/app_colors.dart';
import '../../communication/communication_controller.dart';

class CitizenNavigation extends ConsumerStatefulWidget {
  const CitizenNavigation({required this.selectedIndex, super.key});

  final int selectedIndex;

  @override
  ConsumerState<CitizenNavigation> createState() => _CitizenNavigationState();
}

class _CitizenNavigationState extends ConsumerState<CitizenNavigation> {
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
    return DecoratedBox(
      decoration: const BoxDecoration(
        color: Colors.white,
        border: Border(top: BorderSide(color: Color(0xFFDDE1E4))),
      ),
      child: SafeArea(
        top: false,
        child: SizedBox(
          height: 72,
          child: Row(
            children: [
              _CitizenNavItem(
                icon: Icons.grid_view_rounded,
                label: 'Dashboard',
                selected: widget.selectedIndex == 0,
                onTap: () => context.go('/home'),
              ),
              _CitizenNavItem(
                icon: Icons.inventory_2_outlined,
                label: 'Operações',
                selected: widget.selectedIndex == 1,
                onTap: () => context.go('/solicitacoes'),
              ),
              _CitizenNavItem(
                icon: Icons.account_balance_wallet_outlined,
                label: 'Carteira',
                selected: widget.selectedIndex == 2,
                onTap: () => context.go('/carteira'),
              ),
              _CitizenNavItem(
                icon: Icons.auto_awesome_outlined,
                label: 'Atividades',
                selected: widget.selectedIndex == 3,
                badge: badges?.notificacoes ?? 0,
                onTap: () => context.go('/notificacoes'),
              ),
              _CitizenNavItem(
                icon: Icons.chat_bubble_outline_rounded,
                label: 'Conversas',
                selected: widget.selectedIndex == 4,
                badge: badges?.mensagens ?? 0,
                onTap: () => context.go('/conversas'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _CitizenNavItem extends StatelessWidget {
  const _CitizenNavItem({
    required this.icon,
    required this.label,
    required this.selected,
    required this.onTap,
    this.badge = 0,
  });

  final IconData icon;
  final String label;
  final bool selected;
  final VoidCallback onTap;
  final int badge;

  @override
  Widget build(BuildContext context) => Expanded(
    child: InkWell(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 7),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 36,
              height: 30,
              decoration: BoxDecoration(
                color: selected ? const Color(0xFFEAF3EE) : Colors.transparent,
                borderRadius: BorderRadius.circular(18),
              ),
              child: Center(
                child: Badge.count(
                  count: badge,
                  isLabelVisible: badge > 0,
                  backgroundColor: const Color(0xFFE30620),
                  child: Icon(
                    icon,
                    size: 22,
                    color: selected
                        ? AppColors.primary
                        : const Color(0xFF56606A),
                  ),
                ),
              ),
            ),
            const SizedBox(height: 2),
            Text(
              label,
              maxLines: 1,
              style: TextStyle(
                fontSize: 10.5,
                color: selected ? AppColors.primary : const Color(0xFF56606A),
                fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    ),
  );
}
