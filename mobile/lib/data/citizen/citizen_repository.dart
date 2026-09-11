import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:image_picker/image_picker.dart';

import '../../core/api/api_client.dart';
import '../../core/api/api_exception.dart';
import 'citizen_data.dart';

class NovaSolicitacaoData {
  const NovaSolicitacaoData({required this.campos, this.fotos = const []});
  final Map<String, dynamic> campos;
  final List<XFile> fotos;
}

class CitizenRepository {
  CitizenRepository({ApiClient? apiClient})
    : _apiClient = apiClient ?? ApiClient();

  final ApiClient _apiClient;

  Future<List<PontoColetaData>> listarPontos() async {
    final json = await _get('/api/v1/pontos-coleta');
    return (json['pontos'] as List? ?? const [])
        .map(
          (item) =>
              PontoColetaData.fromJson(Map<String, dynamic>.from(item as Map)),
        )
        .toList();
  }

  Future<EnderecoCepData> consultarCep(String cep) async =>
      EnderecoCepData.fromJson(await _get('/api/v1/cep/$cep'));

  Future<SolicitacoesPagina> listarSolicitacoes({
    String estado = '',
    int pagina = 1,
  }) async {
    final json = await _get(
      '/api/v1/solicitacoes',
      query: {
        'pagina': pagina,
        'limite': 20,
        if (estado.isNotEmpty) 'estado': estado,
      },
    );
    return SolicitacoesPagina.fromJson(json);
  }

  Future<SolicitacaoDetalhesData> buscarSolicitacao(String id) async =>
      SolicitacaoDetalhesData.fromJson(await _get('/api/v1/solicitacoes/$id'));

  Future<List<EntregaData>> listarEntregas() async {
    final json = await _get('/api/v1/entregas');
    return (json['entregas'] as List? ?? const [])
        .map(
          (item) =>
              EntregaData.fromJson(Map<String, dynamic>.from(item as Map)),
        )
        .toList();
  }

  Future<SolicitacaoDetalhesData> criarSolicitacao(
    NovaSolicitacaoData dados,
  ) async {
    final form = FormData.fromMap(dados.campos);
    for (final foto in dados.fotos) {
      form.files.add(
        MapEntry(
          'fotos',
          MultipartFile.fromBytes(
            await foto.readAsBytes(),
            filename: foto.name,
          ),
        ),
      );
    }
    try {
      final response = await _apiClient.dio.post(
        '/api/v1/solicitacoes',
        data: form,
      );
      return SolicitacaoDetalhesData.fromJson(
        Map<String, dynamic>.from(response.data as Map),
      );
    } on DioException catch (error) {
      throw _apiException(error, 'Não foi possível criar a solicitação.');
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
      throw _apiException(error, 'Não foi possível carregar a foto.');
    }
  }

  Future<Map<String, dynamic>> _get(
    String path, {
    Map<String, dynamic>? query,
  }) async {
    try {
      final response = await _apiClient.dio.get(path, queryParameters: query);
      return Map<String, dynamic>.from(response.data as Map);
    } on DioException catch (error) {
      throw _apiException(error, 'Não foi possível carregar os dados.');
    }
  }

  ApiException _apiException(DioException error, String fallback) {
    final body = error.response?.data;
    return ApiException(
      body is Map ? body['erro'] as String? ?? fallback : fallback,
    );
  }
}
