import 'package:dio/dio.dart';

import '../../core/api/api_client.dart';
import '../../core/api/api_exception.dart';
import 'communication_data.dart';

class CommunicationRepository {
  CommunicationRepository({ApiClient? apiClient})
    : _apiClient = apiClient ?? ApiClient();

  final ApiClient _apiClient;

  Future<AgendaData> buscarAgenda(String solicitacaoId) async =>
      AgendaData.fromJson(
        await _json('GET', '/api/v1/solicitacoes/$solicitacaoId/agendamento'),
      );

  Future<AgendaData> proporHorario(
    String solicitacaoId,
    DateTime inicio,
    DateTime fim,
  ) async => AgendaData.fromJson(
    await _json(
      'POST',
      '/api/v1/solicitacoes/$solicitacaoId/agendamento/propor',
      data: {'inicio': inicio.toIso8601String(), 'fim': fim.toIso8601String()},
    ),
  );

  Future<AgendaData> aceitarHorario(String solicitacaoId) async =>
      AgendaData.fromJson(
        await _json(
          'POST',
          '/api/v1/solicitacoes/$solicitacaoId/agendamento/aceitar',
        ),
      );

  Future<AgendaData> rejeitarHorario(String solicitacaoId) async =>
      AgendaData.fromJson(
        await _json(
          'POST',
          '/api/v1/solicitacoes/$solicitacaoId/agendamento/rejeitar',
        ),
      );

  Future<List<ConversaData>> listarConversas() async {
    final json = await _json('GET', '/api/v1/conversas');
    return (json['conversas'] as List? ?? const [])
        .map(
          (item) =>
              ConversaData.fromJson(Map<String, dynamic>.from(item as Map)),
        )
        .toList();
  }

  Future<MensagensPaginaData> listarMensagens(
    String solicitacaoId, {
    int pagina = 1,
  }) async => MensagensPaginaData.fromJson(
    await _json(
      'GET',
      '/api/v1/conversas/$solicitacaoId/mensagens',
      query: {'pagina': pagina, 'limite': 50},
    ),
  );

  Future<MensagemData> enviarMensagem(
    String solicitacaoId,
    String texto,
    String idCliente,
  ) async => MensagemData.fromJson(
    await _json(
      'POST',
      '/api/v1/conversas/$solicitacaoId/mensagens',
      data: {'texto': texto, 'id_cliente': idCliente},
    ),
  );

  Future<void> marcarConversaLida(String solicitacaoId) async =>
      _json('POST', '/api/v1/conversas/$solicitacaoId/leitura');

  Future<NotificacoesPaginaData> listarNotificacoes() async =>
      NotificacoesPaginaData.fromJson(
        await _json('GET', '/api/v1/notificacoes'),
      );

  Future<void> marcarNotificacoesLidas({int? id}) async =>
      _json('POST', '/api/v1/notificacoes/leitura', data: {'id': ?id});

  Future<BadgesData> buscarBadges() async =>
      BadgesData.fromJson(await _json('GET', '/api/v1/badges'));

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
