import 'package:dio/dio.dart';

import '../storage/token_storage.dart';
import 'api_config.dart';

/// Cliente HTTP unico do app, com o token de acesso anexado automaticamente.
class ApiClient {
  ApiClient({TokenStorage? tokenStorage})
    : _tokenStorage = tokenStorage ?? TokenStorage(),
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
        onError: (error, handler) {
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
                  'erro': 'Sem conexão com o servidor. Verifique sua internet e tente novamente.',
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
}
