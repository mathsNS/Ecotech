import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../data/auth/auth_repository.dart';
import '../../data/models/usuario.dart';

final authRepositoryProvider = Provider<AuthRepository>(
  (ref) => AuthRepository(),
);

/// Estado de autenticacao do app: null = deslogado, Usuario = logado.
class AuthController extends AsyncNotifier<Usuario?> {
  @override
  Future<Usuario?> build() => ref.read(authRepositoryProvider).usuarioAtual();

  Future<void> reload() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(
      () => ref.read(authRepositoryProvider).usuarioAtual(),
    );
  }

  Future<void> login({
    required String tipo,
    required String credencial,
    required String senha,
  }) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(
      () => ref
          .read(authRepositoryProvider)
          .login(tipo: tipo, credencial: credencial, senha: senha),
    );
  }

  Future<void> registrar({
    required String tipo,
    required String nome,
    required String email,
    required String senha,
    required String senhaConfirmacao,
    String? cpf,
    String? cnpj,
    String? razaoSocial,
  }) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(
      () => ref
          .read(authRepositoryProvider)
          .registrar(
            tipo: tipo,
            nome: nome,
            email: email,
            senha: senha,
            senhaConfirmacao: senhaConfirmacao,
            cpf: cpf,
            cnpj: cnpj,
            razaoSocial: razaoSocial,
          ),
    );
  }

  Future<void> logout() async {
    await ref.read(authRepositoryProvider).logout();
    state = const AsyncData(null);
  }

  void atualizarUsuario(Usuario usuario) {
    state = AsyncData(usuario);
  }
}

final authControllerProvider = AsyncNotifierProvider<AuthController, Usuario?>(
  AuthController.new,
);
