import 'package:dio/dio.dart';

import '../../core/api/api_client.dart';
import '../../core/api/api_exception.dart';
import 'perfil_data.dart';

class PerfilRepository {
  PerfilRepository({ApiClient? apiClient})
    : _apiClient = apiClient ?? ApiClient();

  final ApiClient _apiClient;

  Future<PerfilData> carregar() => _requisitar('GET');

  Future<PerfilData> atualizar({
    required String nome,
    required String email,
    String senhaAtual = '',
    String novaSenha = '',
    String confirmaSenha = '',
  }) => _requisitar(
    'PATCH',
    dados: {
      'nome': nome,
      'email': email,
      'senha_atual': senhaAtual,
      'nova_senha': novaSenha,
      'confirma_senha': confirmaSenha,
    },
  );

  Future<PerfilData> _requisitar(
    String metodo, {
    Map<String, dynamic>? dados,
  }) async {
    try {
      final resposta = await _apiClient.dio.request(
        '/api/v1/perfil',
        data: dados,
        options: Options(method: metodo),
      );
      return PerfilData.fromJson(
        Map<String, dynamic>.from(resposta.data as Map),
      );
    } on DioException catch (erro) {
      final corpo = erro.response?.data;
      final mensagem = corpo is Map
          ? corpo['erro'] as String? ?? 'Não foi possível atualizar o perfil.'
          : 'Não foi possível conectar ao servidor.';
      throw ApiException(mensagem);
    }
  }
}
