import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

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
    final total =
        ref.watch(oportunidadesEmpresaProvider).valueOrNull?.length ?? 0;
    return NavigationBar(
      selectedIndex: widget.selectedIndex,
      onDestinationSelected: (index) {
        const paths = [
          '/home',
          '/empresa/oportunidades',
          '/empresa/operacoes',
          '/empresa/pontos',
          '/empresa/bases',
          '/perfil',
          '/planos',
        ];
        context.go(paths[index]);
      },
      destinations: [
        const NavigationDestination(
          icon: Icon(Icons.home_outlined),
          label: 'Início',
        ),
        NavigationDestination(
          icon: Badge.count(
            count: total,
            isLabelVisible: total > 0,
            child: const Icon(Icons.campaign_outlined),
          ),
          selectedIcon: Badge.count(
            count: total,
            isLabelVisible: total > 0,
            child: const Icon(Icons.campaign),
          ),
          label: 'Oportunidades',
        ),
        const NavigationDestination(
          icon: Icon(Icons.inventory_2_outlined),
          selectedIcon: Icon(Icons.inventory_2),
          label: 'Operacoes',
        ),
        const NavigationDestination(
          icon: Icon(Icons.location_on_outlined),
          label: 'Pontos',
        ),
        const NavigationDestination(
          icon: Icon(Icons.warehouse_outlined),
          label: 'Bases',
        ),
        const NavigationDestination(
          icon: Icon(Icons.person_outline),
          label: 'Perfil',
        ),
        const NavigationDestination(
          icon: Icon(Icons.workspace_premium_outlined),
          selectedIcon: Icon(Icons.workspace_premium),
          label: 'Planos',
        ),
      ],
      labelBehavior: NavigationDestinationLabelBehavior.onlyShowSelected,
    );
  }
}
