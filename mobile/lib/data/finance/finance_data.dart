class CarteiraData {
  const CarteiraData({
    required this.saldo,
    required this.pontos,
    required this.pontosPorReal,
    required this.metodos,
    required this.titular,
    required this.saques,
  });

  factory CarteiraData.fromJson(Map<String, dynamic> json) {
    final conversao = Map<String, dynamic>.from(
      json['conversao'] as Map? ?? const {},
    );
    return CarteiraData(
      saldo: (json['saldo'] as num?)?.toDouble() ?? 0,
      pontos: (json['pontos'] as num?)?.toInt() ?? 0,
      pontosPorReal: (conversao['pontos_por_real'] as num?)?.toInt() ?? 100,
      metodos: (json['metodos'] as List? ?? const [])
          .map(
            (item) => MetodoSaqueData.fromJson(
              Map<String, dynamic>.from(item as Map),
            ),
          )
          .toList(),
      titular: TitularData.fromJson(
        Map<String, dynamic>.from(json['titular'] as Map? ?? const {}),
      ),
      saques: (json['saques'] as List? ?? const [])
          .map(
            (item) =>
                SaqueData.fromJson(Map<String, dynamic>.from(item as Map)),
          )
          .toList(),
    );
  }

  final double saldo;
  final int pontos;
  final int pontosPorReal;
  final List<MetodoSaqueData> metodos;
  final TitularData titular;
  final List<SaqueData> saques;
}

class MetodoSaqueData {
  const MetodoSaqueData({required this.id, required this.nome});

  factory MetodoSaqueData.fromJson(Map<String, dynamic> json) =>
      MetodoSaqueData(
        id: json['id'] as String? ?? '',
        nome: json['nome'] as String? ?? '',
      );

  final String id;
  final String nome;
}

class TitularData {
  const TitularData({
    required this.nome,
    required this.cpf,
    required this.email,
  });

  factory TitularData.fromJson(Map<String, dynamic> json) => TitularData(
    nome: json['nome'] as String? ?? '',
    cpf: json['cpf'] as String? ?? '',
    email: json['email'] as String? ?? '',
  );

  final String nome;
  final String cpf;
  final String email;
}

class SaqueData {
  const SaqueData({
    required this.id,
    required this.valor,
    required this.metodo,
    required this.dataHora,
    required this.status,
    this.titular,
  });

  factory SaqueData.fromJson(Map<String, dynamic> json) => SaqueData(
    id: json['id'] as String? ?? '',
    valor: (json['valor'] as num?)?.toDouble() ?? 0,
    metodo: json['metodo'] as String? ?? '',
    dataHora:
        json['data_hora'] as String? ??
        '${json['data'] ?? ''} ${json['hora'] ?? ''}'.trim(),
    status: json['status'] as String? ?? '',
    titular: json['titular'] as String?,
  );

  final String id;
  final double valor;
  final String metodo;
  final String dataHora;
  final String status;
  final String? titular;
}

class RelatorioData {
  const RelatorioData({
    required this.titulo,
    required this.geradoEm,
    required this.metricas,
    required this.finalizadas,
    required this.pnrs,
    required this.podeExportar,
    this.dataInicio,
    this.dataFim,
    this.plano,
  });

  factory RelatorioData.fromJson(Map<String, dynamic> json) {
    final periodo = Map<String, dynamic>.from(
      json['periodo'] as Map? ?? const {},
    );
    return RelatorioData(
      titulo: json['titulo'] as String? ?? 'Relatório ambiental',
      geradoEm: json['gerado_em'] as String? ?? '',
      dataInicio: periodo['data_inicio'] as String?,
      dataFim: periodo['data_fim'] as String?,
      metricas: MetricasRelatorioData.fromJson(
        Map<String, dynamic>.from(json['metricas'] as Map? ?? const {}),
      ),
      finalizadas: (json['finalizadas'] as List? ?? const [])
          .map(
            (item) => OperacaoRelatorioData.fromJson(
              Map<String, dynamic>.from(item as Map),
            ),
          )
          .toList(),
      pnrs: PnrsData.fromJson(
        Map<String, dynamic>.from(json['pnrs'] as Map? ?? const {}),
      ),
      plano: json['plano'] as String?,
      podeExportar: json['pode_exportar'] == true,
    );
  }

  final String titulo;
  final String geradoEm;
  final String? dataInicio;
  final String? dataFim;
  final MetricasRelatorioData metricas;
  final List<OperacaoRelatorioData> finalizadas;
  final PnrsData pnrs;
  final String? plano;
  final bool podeExportar;
}

class MetricasRelatorioData {
  const MetricasRelatorioData({
    required this.totalSolicitacoes,
    required this.pesoRecicladoKg,
    required this.pesoReutilizadoKg,
    required this.pesoDescartadoKg,
    required this.pesoTotalKg,
    required this.impactoEvitadoKg,
    required this.taxaReciclagem,
  });

  factory MetricasRelatorioData.fromJson(Map<String, dynamic> json) =>
      MetricasRelatorioData(
        totalSolicitacoes: (json['total_solicitacoes'] as num?)?.toInt() ?? 0,
        pesoRecicladoKg: (json['peso_reciclado_kg'] as num?)?.toDouble() ?? 0,
        pesoReutilizadoKg:
            (json['peso_reutilizado_kg'] as num?)?.toDouble() ?? 0,
        pesoDescartadoKg: (json['peso_descartado_kg'] as num?)?.toDouble() ?? 0,
        pesoTotalKg: (json['peso_total_kg'] as num?)?.toDouble() ?? 0,
        impactoEvitadoKg: (json['impacto_evitado'] as num?)?.toDouble() ?? 0,
        taxaReciclagem: (json['taxa_reciclagem_pct'] as num?)?.toDouble() ?? 0,
      );

  final int totalSolicitacoes;
  final double pesoRecicladoKg;
  final double pesoReutilizadoKg;
  final double pesoDescartadoKg;
  final double pesoTotalKg;
  final double impactoEvitadoKg;
  final double taxaReciclagem;
}

class PnrsData {
  const PnrsData({
    required this.disponivel,
    required this.destinacaoAdequada,
    required this.pesoGerenciadoKg,
    required this.solicitacoesAtendidas,
  });

  factory PnrsData.fromJson(Map<String, dynamic> json) => PnrsData(
    disponivel: json['disponivel'] == true,
    destinacaoAdequada:
        (json['destinacao_adequada_pct'] as num?)?.toDouble() ?? 0,
    pesoGerenciadoKg:
        (json['peso_total_gerenciado_kg'] as num?)?.toDouble() ?? 0,
    solicitacoesAtendidas:
        (json['solicitacoes_atendidas'] as num?)?.toInt() ?? 0,
  );

  final bool disponivel;
  final double destinacaoAdequada;
  final double pesoGerenciadoKg;
  final int solicitacoesAtendidas;
}

class OperacaoRelatorioData {
  const OperacaoRelatorioData({
    required this.id,
    required this.cidadao,
    required this.pesoKg,
    required this.impactoKg,
    required this.estado,
    required this.data,
    this.metodo,
  });

  factory OperacaoRelatorioData.fromJson(Map<String, dynamic> json) =>
      OperacaoRelatorioData(
        id: json['id'] as String? ?? '',
        cidadao: json['cidadao'] as String? ?? '',
        pesoKg: (json['peso_kg'] as num?)?.toDouble() ?? 0,
        impactoKg: (json['impacto_kg'] as num?)?.toDouble() ?? 0,
        metodo: json['metodo'] as String?,
        estado: json['estado'] as String? ?? '',
        data: json['data'] as String? ?? '',
      );

  final String id;
  final String cidadao;
  final double pesoKg;
  final double impactoKg;
  final String? metodo;
  final String estado;
  final String data;
}
