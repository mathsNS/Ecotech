import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Guarda o token de acesso da API de forma segura no dispositivo.
class TokenStorage {
  TokenStorage({FlutterSecureStorage? storage})
      : _storage = storage ?? const FlutterSecureStorage();

  static const _chaveToken = 'ecotech_access_token';

  final FlutterSecureStorage _storage;

  Future<void> salvar(String token) => _storage.write(key: _chaveToken, value: token);

  Future<String?> ler() => _storage.read(key: _chaveToken);

  Future<void> limpar() => _storage.delete(key: _chaveToken);
}
