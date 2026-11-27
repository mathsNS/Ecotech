import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_providers.dart';
import '../../core/session/session_providers.dart';
import '../../data/auth/auth_repository.dart';
import '../../data/models/usuario.dart';

final authRepositoryProvider = Provider<AuthRepository>(
  (ref) => AuthRepository(
    apiClient: ref.watch(apiClientProvider),
    tokenStorage: ref.watch(tokenStorageProvider),
  ),
);

/// Estado de autenticacao do app: null = deslogado, Usuario = logado.
class AuthController extends AsyncNotifier<Usuario?> {
  bool _expirandoSessao = false;

  @override
  Future<Usuario?> build() {
    final subscription = ref.read(unauthorizedSignalProvider).stream.listen((_) {
      unawaited(expirarSessao());
    });
    ref.onDispose(subscription.cancel);
    return ref.read(authRepositoryProvider).usuarioAtual();
  }

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
    final resultado = await AsyncValue.guard(
      () => ref
          .read(authRepositoryProvider)
          .login(tipo: tipo, credencial: credencial, senha: senha),
    );
    if (resultado.hasValue && resultado.value != null) {
      invalidarProvidersSessao(ref);
    }
    state = resultado;
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
    final resultado = await AsyncValue.guard(
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
    if (resultado.hasValue && resultado.value != null) {
      invalidarProvidersSessao(ref);
    }
    state = resultado;
  }

  Future<void> logout() async {
    await ref.read(authRepositoryProvider).logout();
    invalidarProvidersSessao(ref);
    state = const AsyncData(null);
  }

  Future<void> expirarSessao() async {
    if (_expirandoSessao) return;
    if (state.valueOrNull == null) return;
    _expirandoSessao = true;
    try {
      await ref.read(authRepositoryProvider).logout();
    } catch (_) {
      // Token ja limpo ou armazenamento indisponivel.
    } finally {
      invalidarProvidersSessao(ref);
      state = const AsyncData(null);
      _expirandoSessao = false;
    }
  }

  void atualizarUsuario(Usuario usuario) {
    state = AsyncData(usuario);
  }
}

final authControllerProvider = AsyncNotifierProvider<AuthController, Usuario?>(
  AuthController.new,
);
