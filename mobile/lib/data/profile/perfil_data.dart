import '../models/usuario.dart';

class PerfilData {
  const PerfilData({
    required this.usuario,
    required this.resumo,
    this.cpf,
    this.cnpj,
    this.razaoSocial,
    this.dataCadastro,
  });

  factory PerfilData.fromJson(Map<String, dynamic> json) {
    final usuarioJson = Map<String, dynamic>.from(json['usuario'] as Map);
    return PerfilData(
      usuario: Usuario.fromJson(usuarioJson),
      resumo: Map<String, dynamic>.from(json['resumo'] as Map? ?? const {}),
      cpf: usuarioJson['cpf'] as String?,
      cnpj: usuarioJson['cnpj'] as String?,
      razaoSocial: usuarioJson['razao_social'] as String?,
      dataCadastro: usuarioJson['data_cadastro'] as String?,
    );
  }

  final Usuario usuario;
  final Map<String, dynamic> resumo;
  final String? cpf;
  final String? cnpj;
  final String? razaoSocial;
  final String? dataCadastro;
}
