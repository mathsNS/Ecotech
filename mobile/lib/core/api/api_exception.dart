/// Erro de negocio vindo da API (mensagem ja pronta para exibir ao usuario).
class ApiException implements Exception {
  ApiException(this.mensagem);

  final String mensagem;

  @override
  String toString() => mensagem;
}
