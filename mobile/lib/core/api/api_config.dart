/// Configuracao de acesso ao backend EcoTech.
class ApiConfig {
  ApiConfig._();

  /// URL base da API. Em debug local no emulador Android, o host da maquina
  /// e acessado por 10.0.2.2; em iOS/desktop/web local, localhost funciona.
  static const baseUrl = String.fromEnvironment(
    'ECOTECH_API_BASE_URL',
    defaultValue: 'http://10.0.2.2:5000',
  );
}
