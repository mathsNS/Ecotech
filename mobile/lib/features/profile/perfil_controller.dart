import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../data/profile/perfil_data.dart';
import '../../data/profile/perfil_repository.dart';

final perfilRepositoryProvider = Provider<PerfilRepository>(
  (ref) => PerfilRepository(),
);

class PerfilController extends AsyncNotifier<PerfilData> {
  @override
  Future<PerfilData> build() => ref.read(perfilRepositoryProvider).carregar();

  Future<PerfilData?> salvar({
    required String nome,
    required String email,
    String senhaAtual = '',
    String novaSenha = '',
    String confirmaSenha = '',
  }) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(
      () => ref
          .read(perfilRepositoryProvider)
          .atualizar(
            nome: nome,
            email: email,
            senhaAtual: senhaAtual,
            novaSenha: novaSenha,
            confirmaSenha: confirmaSenha,
          ),
    );
    return state.value;
  }

  Future<void> recarregar() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(
      () => ref.read(perfilRepositoryProvider).carregar(),
    );
  }
}

final perfilControllerProvider =
    AsyncNotifierProvider<PerfilController, PerfilData>(PerfilController.new);
