class AdminUsuariosData {
  const AdminUsuariosData({
    required this.usuarios,
    required this.metricas,
    required this.pagina,
    required this.totalPaginas,
    required this.total,
  });

  factory AdminUsuariosData.fromJson(Map<String, dynamic> json) {
    final paginacao = Map<String, dynamic>.from(
      json['paginacao'] as Map? ?? const {},
    );
    return AdminUsuariosData(
      usuarios: (json['usuarios'] as List? ?? const [])
          .map(
            (item) => AdminUsuarioData.fromJson(
              Map<String, dynamic>.from(item as Map),
            ),
          )
          .toList(),
      metricas: AdminMetricasUsuariosData.fromJson(
        Map<String, dynamic>.from(json['metricas'] as Map? ?? const {}),
      ),
      pagina: (paginacao['pagina'] as num?)?.toInt() ?? 1,
      totalPaginas: (paginacao['total_paginas'] as num?)?.toInt() ?? 1,
      total: (paginacao['total'] as num?)?.toInt() ?? 0,
    );
  }

  final List<AdminUsuarioData> usuarios;
  final AdminMetricasUsuariosData metricas;
  final int pagina;
  final int totalPaginas;
  final int total;
}

class AdminMetricasUsuariosData {
  const AdminMetricasUsuariosData({
    required this.total,
    required this.cidadaos,
    required this.empresas,
    required this.ativos,
    required this.inativos,
  });

  factory AdminMetricasUsuariosData.fromJson(Map<String, dynamic> json) =>
      AdminMetricasUsuariosData(
        total: (json['total'] as num?)?.toInt() ?? 0,
        cidadaos: (json['cidadaos'] as num?)?.toInt() ?? 0,
        empresas: (json['empresas'] as num?)?.toInt() ?? 0,
        ativos: (json['ativos'] as num?)?.toInt() ?? 0,
        inativos: (json['inativos'] as num?)?.toInt() ?? 0,
      );

  final int total;
  final int cidadaos;
  final int empresas;
  final int ativos;
  final int inativos;
}

class AdminUsuarioData {
  const AdminUsuarioData({
    required this.id,
    required this.nome,
    required this.email,
    required this.documento,
    required this.tipo,
    required this.ativo,
    required this.dataCadastro,
    this.pontos,
    this.descartadoMesKg,
    this.plano,
  });

  factory AdminUsuarioData.fromJson(Map<String, dynamic> json) =>
      AdminUsuarioData(
        id: json['id'] as String? ?? '',
        nome: json['nome'] as String? ?? '',
        email: json['email'] as String? ?? '',
        documento: json['documento'] as String? ?? '',
        tipo: json['tipo'] as String? ?? '',
        ativo: json['ativo'] == true,
        dataCadastro: json['data_cadastro'] as String? ?? '',
        pontos: (json['pontos'] as num?)?.toInt(),
        descartadoMesKg: (json['descartado_mes_kg'] as num?)?.toDouble(),
        plano: json['plano'] as String?,
      );

  final String id;
  final String nome;
  final String email;
  final String documento;
  final String tipo;
  final bool ativo;
  final String dataCadastro;
  final int? pontos;
  final double? descartadoMesKg;
  final String? plano;
}

class DespachoAdminData {
  const DespachoAdminData({
    required this.metricas,
    required this.resumo,
    required this.pendentes,
    required this.destinatarios,
    required this.atribuicoes,
  });

  factory DespachoAdminData.fromJson(Map<String, dynamic> json) =>
      DespachoAdminData(
        metricas: Map<String, dynamic>.from(
          json['metricas'] as Map? ?? const {},
        ),
        resumo: (json['resumo'] as List? ?? const [])
            .map(
              (item) => ResumoOfertaData.fromJson(
                Map<String, dynamic>.from(item as Map),
              ),
            )
            .toList(),
        pendentes: (json['pendentes'] as List? ?? const [])
            .map(
              (item) => DespachoPendenteData.fromJson(
                Map<String, dynamic>.from(item as Map),
              ),
            )
            .toList(),
        destinatarios: (json['destinatarios'] as List? ?? const [])
            .map(
              (item) => DestinatarioOfertaData.fromJson(
                Map<String, dynamic>.from(item as Map),
              ),
            )
            .toList(),
        atribuicoes: (json['atribuicoes'] as List? ?? const [])
            .map(
              (item) => AtribuicaoData.fromJson(
                Map<String, dynamic>.from(item as Map),
              ),
            )
            .toList(),
      );

  final Map<String, dynamic> metricas;
  final List<ResumoOfertaData> resumo;
  final List<DespachoPendenteData> pendentes;
  final List<DestinatarioOfertaData> destinatarios;
  final List<AtribuicaoData> atribuicoes;
}

class ResumoOfertaData {
  const ResumoOfertaData({required this.status, required this.total});
  factory ResumoOfertaData.fromJson(Map<String, dynamic> json) =>
      ResumoOfertaData(
        status: json['status'] as String? ?? '',
        total: (json['total'] as num?)?.toInt() ?? 0,
      );
  final String status;
  final int total;
}

class DespachoPendenteData {
  const DespachoPendenteData({
    required this.id,
    required this.dataCriacao,
    this.esgotadoEm,
  });
  factory DespachoPendenteData.fromJson(Map<String, dynamic> json) =>
      DespachoPendenteData(
        id: json['id'] as String? ?? '',
        dataCriacao: json['data_criacao'] as String? ?? '',
        esgotadoEm: json['despacho_esgotado_em'] as String?,
      );
  final String id;
  final String dataCriacao;
  final String? esgotadoEm;
}

class DestinatarioOfertaData {
  const DestinatarioOfertaData({
    required this.solicitacaoId,
    required this.empresaNome,
    required this.baseNome,
    required this.rodada,
    required this.status,
    required this.enviadaEm,
  });
  factory DestinatarioOfertaData.fromJson(Map<String, dynamic> json) =>
      DestinatarioOfertaData(
        solicitacaoId: json['solicitacao_id'] as String? ?? '',
        empresaNome: json['empresa_nome'] as String? ?? '',
        baseNome: json['base_nome'] as String? ?? '',
        rodada: (json['rodada'] as num?)?.toInt() ?? 0,
        status: json['status'] as String? ?? '',
        enviadaEm: json['enviada_em'] as String? ?? '',
      );
  final String solicitacaoId;
  final String empresaNome;
  final String baseNome;
  final int rodada;
  final String status;
  final String enviadaEm;
}

class AtribuicaoData {
  const AtribuicaoData({
    required this.id,
    required this.empresaNome,
    required this.totalOfertas,
    required this.rodadas,
    required this.atribuidaEm,
  });
  factory AtribuicaoData.fromJson(Map<String, dynamic> json) => AtribuicaoData(
    id: json['id'] as String? ?? '',
    empresaNome: json['empresa_nome'] as String? ?? '',
    totalOfertas: (json['total_ofertas'] as num?)?.toInt() ?? 0,
    rodadas: (json['rodadas'] as num?)?.toInt() ?? 0,
    atribuidaEm: json['atribuida_em'] as String? ?? '',
  );
  final String id;
  final String empresaNome;
  final int totalOfertas;
  final int rodadas;
  final String atribuidaEm;
}

class OverrideAdminData {
  const OverrideAdminData({
    required this.solicitacaoId,
    required this.dataCriacao,
    required this.cidadao,
    required this.empresa,
    required this.estadoProduto,
    required this.valorProposto,
    required this.valorBase,
    required this.valorMinimo,
    required this.limiteOverride,
    required this.valorRecalculado,
    required this.justificativa,
  });

  factory OverrideAdminData.fromJson(Map<String, dynamic> json) =>
      OverrideAdminData(
        solicitacaoId: json['solicitacao_id'] as String? ?? '',
        dataCriacao: json['data_criacao'] as String? ?? '',
        cidadao: json['cidadao'] as String? ?? '',
        empresa: json['empresa'] as String? ?? '',
        estadoProduto: json['estado_produto'] as String? ?? '',
        valorProposto: (json['valor_proposto'] as num?)?.toDouble() ?? 0,
        valorBase: (json['valor_base'] as num?)?.toDouble() ?? 0,
        valorMinimo: (json['valor_minimo'] as num?)?.toDouble() ?? 0,
        limiteOverride: (json['limite_override'] as num?)?.toDouble() ?? 0,
        valorRecalculado:
            (json['valor_recalculado'] as num?)?.toDouble() ?? 0,
        justificativa: json['justificativa'] as String? ?? '',
      );

  final String solicitacaoId;
  final String dataCriacao;
  final String cidadao;
  final String empresa;
  final String estadoProduto;
  final double valorProposto;
  final double valorBase;
  final double valorMinimo;
  final double limiteOverride;
  final double valorRecalculado;
  final String justificativa;
}

class PrecoAdminData {
  const PrecoAdminData({
    required this.subcategoria,
    required this.categoria,
    required this.valorBase,
    required this.valorMinimo,
    required this.limiteOverride,
  });

  factory PrecoAdminData.fromJson(Map<String, dynamic> json) => PrecoAdminData(
    subcategoria: json['subcategoria'] as String? ?? '',
    categoria: json['categoria'] as String? ?? '',
    valorBase: (json['valor_base'] as num?)?.toDouble() ?? 0,
    valorMinimo: (json['valor_minimo'] as num?)?.toDouble() ?? 0,
    limiteOverride: (json['limite_override'] as num?)?.toDouble() ?? 0,
  );

  final String subcategoria;
  final String categoria;
  final double valorBase;
  final double valorMinimo;
  final double limiteOverride;
}
