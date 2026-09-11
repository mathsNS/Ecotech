import 'package:dio/dio.dart';

import '../../core/api/api_client.dart';
import '../../core/api/api_exception.dart';
import 'company_data.dart';

class CompanyRepository {
  CompanyRepository({ApiClient? apiClient})
    : _apiClient = apiClient ?? ApiClient();

  final ApiClient _apiClient;

  Future<Map<String, dynamic>> consultarCep(String cep) async =>
      _request('GET', '/api/v1/cep/$cep');

  Future<List<PontoEmpresaData>> listarPontos() async {
    final json = await _request('GET', '/api/v1/empresa/pontos');
    return (json['pontos'] as List? ?? const [])
        .map(
          (item) =>
              PontoEmpresaData.fromJson(Map<String, dynamic>.from(item as Map)),
        )
        .toList();
  }

  Future<PontoEmpresaData> salvarPonto(
    Map<String, dynamic> dados, {
    String? id,
  }) async => PontoEmpresaData.fromJson(
    await _request(
      id == null ? 'POST' : 'PATCH',
      id == null ? '/api/v1/empresa/pontos' : '/api/v1/empresa/pontos/$id',
      data: dados,
    ),
  );

  Future<PontoEmpresaData> definirAtividadePonto(String id, bool ativa) async =>
      PontoEmpresaData.fromJson(
        await _request(
          'PATCH',
          '/api/v1/empresa/pontos/$id',
          data: {'ativo': ativa},
        ),
      );

  Future<void> confirmarEntrega(
    String pontoId,
    String solicitacaoId,
    double pesoKg,
  ) async => _request(
    'POST',
    '/api/v1/empresa/pontos/$pontoId/solicitacoes/$solicitacaoId/confirmar',
    data: {'peso_kg': pesoKg},
  );

  Future<List<BaseEmpresaData>> listarBases() async {
    final json = await _request('GET', '/api/v1/empresa/bases');
    return (json['bases'] as List? ?? const [])
        .map(
          (item) =>
              BaseEmpresaData.fromJson(Map<String, dynamic>.from(item as Map)),
        )
        .toList();
  }

  Future<BaseEmpresaData> salvarBase(
    Map<String, dynamic> dados, {
    String? id,
  }) async => BaseEmpresaData.fromJson(
    await _request(
      id == null ? 'POST' : 'PATCH',
      id == null ? '/api/v1/empresa/bases' : '/api/v1/empresa/bases/$id',
      data: dados,
    ),
  );

  Future<BaseEmpresaData> definirAtividadeBase(String id, bool ativa) async =>
      BaseEmpresaData.fromJson(
        await _request(
          'POST',
          '/api/v1/empresa/bases/$id/atividade',
          data: {'ativa': ativa},
        ),
      );

  Future<List<OportunidadeData>> listarOportunidades() async {
    final json = await _request('GET', '/api/v1/empresa/oportunidades');
    return (json['oportunidades'] as List? ?? const [])
        .map(
          (item) =>
              OportunidadeData.fromJson(Map<String, dynamic>.from(item as Map)),
        )
        .toList();
  }

  Future<AceiteOportunidadeData> aceitarOportunidade(String id) async =>
      AceiteOportunidadeData.fromJson(
        await _request('POST', '/api/v1/empresa/oportunidades/$id/aceitar'),
      );

  Future<void> recusarOportunidade(String id, {String motivo = ''}) async =>
      _request(
        'POST',
        '/api/v1/empresa/oportunidades/$id/recusar',
        data: {'motivo': motivo},
      );

  Future<Map<String, dynamic>> _request(
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
      throw ApiException(
        body is Map
            ? body['erro'] as String? ?? 'Não foi possível concluir a operação.'
            : 'Não foi possível concluir a operação.',
      );
    }
  }
}
