import 'package:dio/dio.dart';

import '../../core/api/api_client.dart';
import '../../core/api/api_exception.dart';
import 'plans_data.dart';

class PlansRepository {
  PlansRepository({ApiClient? apiClient})
    : _apiClient = apiClient ?? ApiClient();

  final ApiClient _apiClient;

  Future<PlansData> fetchPlans() async =>
      PlansData.fromJson(await _json('GET', '/api/v1/planos'));

  Future<PlansData> changePlan(String planId) async => PlansData.fromJson(
    await _json('POST', '/api/v1/planos/alterar', data: {'plano': planId}),
  );

  Future<Map<String, dynamic>> _json(
    String method,
    String path, {
    Map<String, dynamic>? data,
  }) async {
    try {
      final response = await _apiClient.dio.request(
        path,
        data: data,
        options: Options(method: method),
      );
      return Map<String, dynamic>.from(response.data as Map);
    } on DioException catch (error) {
      final body = error.response?.data;
      if (body is Map && body['erro'] is String) {
        throw ApiException(body['erro'] as String);
      }
      if (error.type == DioExceptionType.connectionError ||
          error.type == DioExceptionType.connectionTimeout ||
          error.type == DioExceptionType.receiveTimeout) {
        throw ApiException(
          'Sem conexão com o servidor. Verifique sua internet e tente novamente.',
        );
      }
      throw ApiException('Não foi possível concluir a operação.');
    }
  }
}
