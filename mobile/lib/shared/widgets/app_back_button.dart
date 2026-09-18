import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class AppBackButton extends StatelessWidget {
  const AppBackButton({this.fallbackRoute = '/home', super.key});

  final String fallbackRoute;

  @override
  Widget build(BuildContext context) => IconButton(
    tooltip: 'Voltar',
    icon: const Icon(Icons.arrow_back),
    onPressed: () {
      if (context.canPop()) {
        context.pop();
      } else {
        context.go(fallbackRoute);
      }
    },
  );
}
