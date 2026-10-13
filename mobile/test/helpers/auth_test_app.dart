import 'dart:async';

import 'package:ecotech_mobile/core/theme/app_theme.dart';
import 'package:ecotech_mobile/data/auth/auth_repository.dart';
import 'package:ecotech_mobile/data/models/usuario.dart';
import 'package:ecotech_mobile/features/auth/auth_controller.dart';
import 'package:ecotech_mobile/features/auth/cadastro_screen.dart';
import 'package:ecotech_mobile/features/auth/login_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

class PendingAuthRepository extends AuthRepository {
  final response = Completer<Usuario>();
  final requests = <Map<String, String?>>[];

  @override
  Future<Usuario?> usuarioAtual() async => null;

  @override
  Future<Usuario> login({
    required String tipo,
    required String credencial,
    required String senha,
  }) {
    requests.add({'tipo': tipo, 'credencial': credencial, 'senha': senha});
    return response.future;
  }

  @override
  Future<Usuario> registrar({
    required String tipo,
    required String nome,
    required String email,
    required String senha,
    required String senhaConfirmacao,
    String? cpf,
    String? cnpj,
    String? razaoSocial,
  }) {
    requests.add({
      'tipo': tipo,
      'nome': nome,
      'email': email,
      'senha': senha,
      'senha_confirmacao': senhaConfirmacao,
      'cpf': cpf,
      'cnpj': cnpj,
      'razao_social': razaoSocial,
    });
    return response.future;
  }
}

Future<void> pumpAuth(
  WidgetTester tester,
  PendingAuthRepository repository, {
  String route = '/login',
  double scale = 1,
  Size size = const Size(390, 844),
}) async {
  tester.view.physicalSize = size;
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);
  final router = GoRouter(
    initialLocation: route,
    routes: [
      GoRoute(path: '/login', builder: (_, _) => const LoginScreen()),
      GoRoute(path: '/cadastro', builder: (_, _) => const CadastroScreen()),
      GoRoute(
        path: '/home',
        builder: (_, _) => const Scaffold(body: Text('Área autenticada')),
      ),
    ],
  );
  addTearDown(router.dispose);
  await tester.pumpWidget(
    ProviderScope(
      overrides: [authRepositoryProvider.overrideWithValue(repository)],
      child: MaterialApp.router(
        theme: AppTheme.light(),
        routerConfig: router,
        builder: (context, child) => MediaQuery(
          data: MediaQuery.of(context)
              .copyWith(textScaler: TextScaler.linear(scale)),
          child: child!,
        ),
      ),
    ),
  );
  await tester.pumpAndSettle();
}
