import 'package:dio/dio.dart';

import '../../core/api/api_client.dart';
import '../../core/api/api_exception.dart';
import 'dashboard_data.dart';

class DashboardRepository {
  DashboardRepository({ApiClient? apiClient})
    : _apiClient = apiClient ?? ApiClient();

  final ApiClient _apiClient;

  Future<DashboardData> carregar() async {
    try {
      final resposta = await _apiClient.dio.get('/api/v1/dashboard');
      return DashboardData.fromJson(
        Map<String, dynamic>.from(resposta.data as Map),
      );
    } on DioException catch (erro) {
      final dados = erro.response?.data;
      final mensagem = dados is Map
          ? dados['erro'] as String? ?? 'Não foi possível carregar o dashboard.'
          : 'Não foi possível conectar ao servidor.';
      throw ApiException(mensagem);
    }
  }
}
