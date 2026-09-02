import 'package:dio/dio.dart';

import '../../core/api/api_client.dart';
import '../../core/api/api_exception.dart';
import '../../core/storage/token_storage.dart';
import '../models/usuario.dart';

/// Fala com /api/v1/auth/*. Nenhuma regra de negocio aqui, so tradução HTTP.
class AuthRepository {
  AuthRepository({ApiClient? apiClient, TokenStorage? tokenStorage})
      : _apiClient = apiClient ?? ApiClient(),
        _tokenStorage = tokenStorage ?? TokenStorage();

  final ApiClient _apiClient;
  final TokenStorage _tokenStorage;

  Future<Usuario> login({
    required String tipo,
    required String credencial,
    required String senha,
  }) async {
    final corpo = await _post('/api/v1/auth/login', {
      'tipo': tipo,
      'credencial': credencial,
      'senha': senha,
    });
    return _salvarTokenERetornarUsuario(corpo);
  }

  Future<Usuario> registrar({
    required String tipo,
    required String nome,
    required String email,
    required String senha,
    required String senhaConfirmacao,
    String? cpf,
    String? cnpj,
    String? razaoSocial,
  }) async {
    final corpo = await _post('/api/v1/auth/registrar', {
      'tipo': tipo,
      'nome': nome,
      'email': email,
      'senha': senha,
      'senha_confirmacao': senhaConfirmacao,
      'cpf': ?cpf,
      'cnpj': ?cnpj,
      'razao_social': ?razaoSocial,
    });
    return _salvarTokenERetornarUsuario(corpo);
  }

  Future<Usuario?> usuarioAtual() async {
    final token = await _tokenStorage.ler();
    if (token == null) return null;

    try {
      final resposta = await _apiClient.dio.get('/api/v1/auth/me');
      return Usuario.fromJson(resposta.data as Map<String, dynamic>);
    } on DioException catch (erro) {
      if (erro.response?.statusCode == 401) {
        await _tokenStorage.limpar();
        return null;
      }
      rethrow;
    }
  }

  Future<void> logout() => _tokenStorage.limpar();

  Future<Map<String, dynamic>> _post(String caminho, Map<String, dynamic> corpo) async {
    try {
      final resposta = await _apiClient.dio.post(caminho, data: corpo);
      return resposta.data as Map<String, dynamic>;
    } on DioException catch (erro) {
      final mensagem = erro.response?.data is Map
          ? (erro.response?.data['erro'] as String? ?? 'Erro inesperado, tente novamente.')
          : 'Nao foi possivel conectar ao servidor.';
      throw ApiException(mensagem);
    }
  }

  Future<Usuario> _salvarTokenERetornarUsuario(Map<String, dynamic> corpo) async {
    await _tokenStorage.salvar(corpo['access_token'] as String);
    return Usuario.fromJson(corpo['usuario'] as Map<String, dynamic>);
  }
}
