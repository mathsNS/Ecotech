import 'package:dio/dio.dart';

import '../storage/token_storage.dart';
import 'api_config.dart';

typedef UnauthorizedCallback = Future<void> Function();

/// Cliente HTTP unico do app, com o token de acesso anexado automaticamente.
class ApiClient {
  ApiClient({
    TokenStorage? tokenStorage,
    this.onUnauthorized,
  }) : _tokenStorage = tokenStorage ?? TokenStorage(),
       dio = Dio(
         BaseOptions(
           baseUrl: ApiConfig.baseUrl,
           connectTimeout: const Duration(seconds: 15),
           receiveTimeout: const Duration(seconds: 15),
         ),
       ) {
    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          final token = await _tokenStorage.ler();
          if (token != null) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          handler.next(options);
        },
        onError: (error, handler) async {
          if (error.response?.statusCode == 401 &&
              deveExpirarSessao(error.requestOptions.path)) {
            await _notificarNaoAutorizado();
            handler.next(error);
            return;
          }
          final offline =
              error.type == DioExceptionType.connectionError ||
              error.type == DioExceptionType.connectionTimeout ||
              error.type == DioExceptionType.receiveTimeout ||
              error.type == DioExceptionType.sendTimeout;
          if (!offline) {
            handler.next(error);
            return;
          }
          handler.reject(
            error.copyWith(
              response: Response<Map<String, dynamic>>(
                requestOptions: error.requestOptions,
                statusCode: 0,
                data: const {
                  'erro':
                      'Sem conexão com o servidor. Verifique sua internet e tente novamente.',
                },
              ),
            ),
          );
        },
      ),
    );
  }

  final Dio dio;
  final TokenStorage _tokenStorage;
  final UnauthorizedCallback? onUnauthorized;
  bool _notificandoNaoAutorizado = false;

  static bool deveExpirarSessao(String path) {
    final normalizado = path.trim().toLowerCase();
    return !normalizado.endsWith('/auth/login') &&
        !normalizado.endsWith('/auth/registrar') &&
        !normalizado.endsWith('/auth/me');
  }

  Future<void> _notificarNaoAutorizado() async {
    if (_notificandoNaoAutorizado) return;
    _notificandoNaoAutorizado = true;
    try {
      try {
        await _tokenStorage.limpar();
      } catch (_) {
        // Ignora erro de canal local para nao impedir limpeza de estado.
      }
      try {
        await onUnauthorized?.call();
      } catch (_) {
        // Nao bloqueia a propagacao do erro HTTP original.
      }
    } finally {
      _notificandoNaoAutorizado = false;
    }
  }
}
