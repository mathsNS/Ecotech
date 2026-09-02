/// Representa o usuario autenticado, dados minimos devolvidos por /api/v1/auth.
class Usuario {
  const Usuario({
    required this.id,
    required this.nome,
    required this.tipo,
    this.email,
  });

  factory Usuario.fromJson(Map<String, dynamic> json) => Usuario(
        id: json['id'] as String,
        nome: json['nome'] as String,
        tipo: json['tipo'] as String,
        email: json['email'] as String?,
      );

  final String id;
  final String nome;
  final String tipo;
  final String? email;
}
