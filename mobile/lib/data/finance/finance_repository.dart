import 'dart:typed_data';

import 'package:dio/dio.dart';

import '../../core/api/api_client.dart';
import '../../core/api/api_exception.dart';
import 'finance_data.dart';

class FinanceRepository {
  FinanceRepository({ApiClient? apiClient})
    : _apiClient = apiClient ?? ApiClient();

  final ApiClient _apiClient;

  Future<CarteiraData> buscarCarteira() async =>
      CarteiraData.fromJson(await _json('GET', '/api/v1/carteira'));

  Future<({SaqueData saque, CarteiraData carteira})> solicitarSaque({
    required double valor,
    required String metodo,
    required String titular,
    required String idCliente,
  }) async {
    final json = await _json(
      'POST',
      '/api/v1/saques',
      data: {
        'valor': valor,
        'metodo': metodo,
        'titular': titular,
        'id_cliente': idCliente,
      },
    );
    return (
      saque: SaqueData.fromJson(
        Map<String, dynamic>.from(json['saque'] as Map),
      ),
      carteira: CarteiraData.fromJson(
        Map<String, dynamic>.from(json['carteira'] as Map),
      ),
    );
  }

  Future<RelatorioData> buscarRelatorio({
    DateTime? inicio,
    DateTime? fim,
  }) async => RelatorioData.fromJson(
    await _json(
      'GET',
      '/api/v1/relatorios',
      query: {
        if (inicio != null) 'data_inicio': _dataApi(inicio),
        if (fim != null) 'data_fim': _dataApi(fim),
      },
    ),
  );

  Future<Uint8List> baixarRelatorioCsv({
    DateTime? inicio,
    DateTime? fim,
  }) async {
    try {
      final response = await _apiClient.dio.get<List<int>>(
        '/api/v1/relatorios/exportar.csv',
        queryParameters: {
          if (inicio != null) 'data_inicio': _dataApi(inicio),
          if (fim != null) 'data_fim': _dataApi(fim),
        },
        options: Options(responseType: ResponseType.bytes),
      );
      return Uint8List.fromList(response.data ?? const []);
    } on DioException catch (error) {
      throw _erro(error, 'Não foi possível exportar o relatório.');
    }
  }

  Future<Map<String, dynamic>> _json(
    String method,
    String path, {
    Map<String, dynamic>? query,
    Map<String, dynamic>? data,
  }) async {
    try {
      final response = await _apiClient.dio.request(
        path,
        queryParameters: query,
        data: data,
        options: Options(method: method),
      );
      return Map<String, dynamic>.from(response.data as Map);
    } on DioException catch (error) {
      throw _erro(error, 'Não foi possível concluir a operação.');
    }
  }

  ApiException _erro(DioException error, String fallback) {
    final body = error.response?.data;
    if (body is Map && body['erro'] is String) {
      return ApiException(body['erro'] as String);
    }
    return ApiException(fallback);
  }

  static String _dataApi(DateTime data) =>
      '${data.year.toString().padLeft(4, '0')}-'
      '${data.month.toString().padLeft(2, '0')}-'
      '${data.day.toString().padLeft(2, '0')}';
}
