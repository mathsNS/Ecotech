// Teste basico de fumaca: o app deve abrir na tela de login quando nao ha
// sessao ativa.

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:ecotech_mobile/data/auth/auth_repository.dart';
import 'package:ecotech_mobile/data/models/usuario.dart';
import 'package:ecotech_mobile/features/auth/auth_controller.dart';
import 'package:ecotech_mobile/main.dart';

/// Evita depender do canal de plataforma do secure storage nos testes.
class _AuthRepositorySemSessao implements AuthRepository {
  @override
  Future<Usuario?> usuarioAtual() async => null;

  @override
  Future<Usuario> login({
    required String tipo,
    required String credencial,
    required String senha,
  }) =>
      throw UnimplementedError();

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
  }) =>
      throw UnimplementedError();

  @override
  Future<void> logout() async {}
}

void main() {
  testWidgets('App abre na tela de login sem sessao ativa', (WidgetTester tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authRepositoryProvider.overrideWithValue(_AuthRepositorySemSessao()),
        ],
        child: const EcoTechApp(),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Entrar no sistema'), findsOneWidget);
  });
}


