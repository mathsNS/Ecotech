import 'dart:typed_data';

import 'package:dio/dio.dart';

import '../../core/api/api_client.dart';
import '../../core/api/api_exception.dart';
import 'operation_data.dart';

class OperationRepository {
  OperationRepository({ApiClient? apiClient})
    : _apiClient = apiClient ?? ApiClient();

  final ApiClient _apiClient;

  Future<OperacoesPaginaData> listar({
    String estado = '',
    String busca = '',
    int pagina = 1,
  }) async => OperacoesPaginaData.fromJson(
    await _json(
      'GET',
      '/api/v1/operacoes',
      query: {
        'pagina': pagina,
        'por_pagina': 20,
        if (estado.isNotEmpty) 'estado': estado,
        if (busca.isNotEmpty) 'busca': busca,
      },
    ),
  );

  Future<OperacaoDetalhesData> buscar(String id) async =>
      OperacaoDetalhesData.fromJson(
        await _json('GET', '/api/v1/operacoes/$id'),
      );

  Future<void> aferirPeso(String id, double pesoKg) async => _json(
    'POST',
    '/api/v1/operacoes/$id/peso',
    data: {'peso_kg': pesoKg},
  );

  Future<OperacaoDetalhesData> avancar(
    String id, {
    double? pesoKg,
    String? metodo,
    String? estadoProduto,
    double? valorProposto,
    String justificativa = '',
  }) async {
    final json = await _json(
      'POST',
      '/api/v1/operacoes/$id/avancar',
      data: {
        if (pesoKg != null) 'peso_kg': pesoKg,
        if (metodo != null) 'metodo': metodo,
        if (estadoProduto != null) 'estado_produto': estadoProduto,
        if (valorProposto != null) 'valor_proposto': valorProposto,
        if (justificativa.isNotEmpty) 'justificativa': justificativa,
      },
    );
    return OperacaoDetalhesData.fromJson(
      Map<String, dynamic>.from(json['operacao'] as Map),
    );
  }

  Future<Uint8List> baixarMtr(String id) async {
    try {
      final response = await _apiClient.dio.get<List<int>>(
        '/api/v1/operacoes/$id/mtr',
        options: Options(responseType: ResponseType.bytes),
      );
      return Uint8List.fromList(response.data ?? const []);
    } on DioException catch (error) {
      throw _erro(error, 'Nao foi possivel gerar o MTR.');
    }
  }

  Future<Uint8List> baixarFoto(String url) async {
    try {
      final response = await _apiClient.dio.get<List<int>>(
        url,
        options: Options(responseType: ResponseType.bytes),
      );
      return Uint8List.fromList(response.data ?? const []);
    } on DioException catch (error) {
      throw _erro(error, 'Nao foi possivel carregar a foto.');
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
      throw _erro(error, 'Nao foi possivel concluir a operacao.');
    }
  }

  ApiException _erro(DioException error, String fallback) {
    final body = error.response?.data;
    return ApiException(
      body is Map ? body['erro'] as String? ?? fallback : fallback,
    );
  }
}
