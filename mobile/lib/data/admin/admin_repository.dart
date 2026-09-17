import 'package:dio/dio.dart';

import '../../core/api/api_client.dart';
import '../../core/api/api_exception.dart';
import 'admin_data.dart';

class AdminRepository {
  AdminRepository({ApiClient? apiClient}) : _apiClient = apiClient ?? ApiClient();

  final ApiClient _apiClient;

  Future<AdminUsuariosData> listarUsuarios({
    String tipo = 'todos',
    String busca = '',
    int pagina = 1,
  }) async => AdminUsuariosData.fromJson(
    await _json(
      'GET',
      '/api/v1/admin/usuarios',
      query: {'tipo': tipo, 'busca': busca, 'pagina': pagina, 'por_pagina': 20},
    ),
  );

  Future<AdminUsuarioData> cadastrarUsuario(Map<String, dynamic> dados) async =>
      AdminUsuarioData.fromJson(
        await _json('POST', '/api/v1/admin/usuarios', data: dados),
      );

  Future<void> desativarUsuario(String id) async =>
      _json('POST', '/api/v1/admin/usuarios/$id/desativar');

  Future<DespachoAdminData> buscarDespacho() async => DespachoAdminData.fromJson(
    await _json('GET', '/api/v1/admin/despacho'),
  );

  Future<List<OverrideAdminData>> listarOverrides() async {
    final json = await _json('GET', '/api/v1/admin/overrides');
    return (json['overrides'] as List? ?? const [])
        .map(
          (item) => OverrideAdminData.fromJson(
            Map<String, dynamic>.from(item as Map),
          ),
        )
        .toList();
  }

  Future<void> decidirOverride(String id, String decisao) async => _json(
    'POST',
    '/api/v1/admin/overrides/$id/decisao',
    data: {'decisao': decisao},
  );

  Future<List<PrecoAdminData>> listarPrecos() async {
    final json = await _json('GET', '/api/v1/admin/precos');
    return (json['precos'] as List? ?? const [])
        .map(
          (item) =>
              PrecoAdminData.fromJson(Map<String, dynamic>.from(item as Map)),
        )
        .toList();
  }

  Future<List<PrecoAdminData>> atualizarPreco({
    required String subcategoria,
    required double valorBase,
    required double valorMinimo,
  }) async {
    final json = await _json(
      'PATCH',
      '/api/v1/admin/precos',
      data: {
        'subcategoria': subcategoria,
        'valor_base': valorBase,
        'valor_minimo': valorMinimo,
      },
    );
    return (json['precos'] as List? ?? const [])
        .map(
          (item) =>
              PrecoAdminData.fromJson(Map<String, dynamic>.from(item as Map)),
        )
        .toList();
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
      final body = error.response?.data;
      throw ApiException(
        body is Map
            ? body['erro'] as String? ?? 'Não foi possível concluir a operação.'
            : 'Não foi possível concluir a operação.',
      );
    }
  }
}
