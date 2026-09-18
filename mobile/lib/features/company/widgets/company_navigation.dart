import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/theme/app_colors.dart';
import '../company_controller.dart';

class CompanyNavigation extends ConsumerStatefulWidget {
  const CompanyNavigation({required this.selectedIndex, super.key});

  final int selectedIndex;

  @override
  ConsumerState<CompanyNavigation> createState() => _CompanyNavigationState();
}

class _CompanyNavigationState extends ConsumerState<CompanyNavigation> {
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _timer = Timer.periodic(
      const Duration(seconds: 30),
      (_) => ref.invalidate(oportunidadesEmpresaProvider),
    );
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final opportunities =
        ref.watch(oportunidadesEmpresaProvider).valueOrNull?.length ?? 0;
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
              _NavigationItem(
                icon: Icons.grid_view_rounded,
                label: 'Dashboard',
                selected: widget.selectedIndex == 0,
                onTap: () => context.go('/home'),
              ),
              _NavigationItem(
                icon: Icons.inventory_2_outlined,
                label: 'Operações',
                selected: widget.selectedIndex == 1,
                onTap: () => context.go('/empresa/operacoes'),
              ),
              _NavigationItem(
                icon: Icons.insert_chart_outlined_rounded,
                label: 'Relatórios',
                selected: widget.selectedIndex == 2,
                onTap: () => context.go('/relatorios'),
              ),
              _NavigationItem(
                icon: Icons.chat_bubble_outline_rounded,
                label: 'Conversas',
                selected: widget.selectedIndex == 3,
                onTap: () => context.go('/conversas'),
              ),
              _NavigationItem(
                icon: Icons.menu_rounded,
                label: 'Mais',
                selected: widget.selectedIndex == 4,
                badge: opportunities,
                onTap: () => _showMore(context),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _showMore(BuildContext context) => showModalBottomSheet(
    context: context,
    showDragHandle: true,
    isScrollControlled: true,
    builder: (sheetContext) => SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 0, 16, 18),
        child: ListView(
          shrinkWrap: true,
          children: [
            _MoreItem(
              icon: Icons.campaign_outlined,
              label: 'Oportunidades',
              route: '/empresa/oportunidades',
              badge:
                  ref.read(oportunidadesEmpresaProvider).valueOrNull?.length ??
                  0,
            ),
            const _MoreItem(
              icon: Icons.location_on_outlined,
              label: 'Pontos de coleta',
              route: '/empresa/pontos',
            ),
            const _MoreItem(
              icon: Icons.warehouse_outlined,
              label: 'Bases operacionais',
              route: '/empresa/bases',
            ),
            const _MoreItem(
              icon: Icons.workspace_premium_outlined,
              label: 'Planos',
              route: '/planos',
            ),
            const _MoreItem(
              icon: Icons.person_outline,
              label: 'Perfil',
              route: '/perfil',
            ),
          ],
        ),
      ),
    ),
  );
}

class _NavigationItem extends StatelessWidget {
  const _NavigationItem({
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
              width: 34,
              height: 30,
              decoration: BoxDecoration(
                color: selected ? const Color(0xFFEAF3EE) : Colors.transparent,
                borderRadius: BorderRadius.circular(18),
              ),
              child: Center(
                child: Badge.count(
                  count: badge,
                  isLabelVisible: badge > 0,
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

class _MoreItem extends StatelessWidget {
  const _MoreItem({
    required this.icon,
    required this.label,
    required this.route,
    this.badge = 0,
  });

  final IconData icon;
  final String label;
  final String route;
  final int badge;

  @override
  Widget build(BuildContext context) => ListTile(
    leading: Badge.count(
      count: badge,
      isLabelVisible: badge > 0,
      child: Icon(icon, color: AppColors.primary),
    ),
    title: Text(label),
    trailing: const Icon(Icons.chevron_right),
    onTap: () {
      final router = GoRouter.of(context);
      Navigator.pop(context);
      router.go(route);
    },
  );
}
