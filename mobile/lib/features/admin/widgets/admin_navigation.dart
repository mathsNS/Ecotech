import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class AdminNavigation extends StatelessWidget {
  const AdminNavigation({required this.selectedIndex, super.key});

  final int selectedIndex;

  @override
  Widget build(BuildContext context) => NavigationBar(
    selectedIndex: selectedIndex,
    labelBehavior: NavigationDestinationLabelBehavior.onlyShowSelected,
    onDestinationSelected: (index) {
      const caminhos = [
        '/home',
        '/admin/usuarios',
        '/admin/despacho',
        '/admin/overrides',
        '/admin/precos',
      ];
      context.go(caminhos[index]);
    },
    destinations: const [
      NavigationDestination(icon: Icon(Icons.home_outlined), label: 'Início'),
      NavigationDestination(
        icon: Icon(Icons.people_outline),
        selectedIcon: Icon(Icons.people),
        label: 'Usuários',
      ),
      NavigationDestination(
        icon: Icon(Icons.route_outlined),
        selectedIcon: Icon(Icons.route),
        label: 'Despacho',
      ),
      NavigationDestination(
        icon: Icon(Icons.rule_outlined),
        selectedIcon: Icon(Icons.rule),
        label: 'Overrides',
      ),
      NavigationDestination(
        icon: Icon(Icons.price_change_outlined),
        selectedIcon: Icon(Icons.price_change),
        label: 'Preços',
      ),
    ],
  );
}
