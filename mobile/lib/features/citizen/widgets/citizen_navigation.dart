import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class CitizenNavigation extends StatelessWidget {
  const CitizenNavigation({required this.selectedIndex, super.key});

  final int selectedIndex;

  @override
  Widget build(BuildContext context) => NavigationBar(
    selectedIndex: selectedIndex,
    onDestinationSelected: (index) {
      const paths = ['/home', '/solicitacoes', '/pontos', '/perfil'];
      context.go(paths[index]);
    },
    destinations: const [
      NavigationDestination(icon: Icon(Icons.home_outlined), label: 'Início'),
      NavigationDestination(
        icon: Icon(Icons.inventory_2_outlined),
        label: 'Solicitações',
      ),
      NavigationDestination(
        icon: Icon(Icons.location_on_outlined),
        label: 'Pontos',
      ),
      NavigationDestination(icon: Icon(Icons.person_outline), label: 'Perfil'),
    ],
  );
}
