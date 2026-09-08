import 'package:flutter/foundation.dart';

/// Configuracao de acesso ao backend EcoTech.
class ApiConfig {
  ApiConfig._();

  static const _baseUrlConfigurada = String.fromEnvironment(
    'ECOTECH_API_BASE_URL',
    defaultValue: '',
  );

  /// Seleciona automaticamente o host local correto em cada plataforma.
  /// O valor ainda pode ser sobrescrito com --dart-define para dispositivo
  /// fisico ou ambiente publicado.
  static String get baseUrl {
    if (_baseUrlConfigurada.isNotEmpty) return _baseUrlConfigurada;
    if (kIsWeb) return 'http://localhost:5000';
    if (defaultTargetPlatform == TargetPlatform.android) {
      return 'http://10.0.2.2:5000';
    }
    return 'http://localhost:5000';
  }
}
