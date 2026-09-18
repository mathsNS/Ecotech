import '../models/usuario.dart';

double _double(dynamic valor) => (valor as num?)?.toDouble() ?? 0;
int _int(dynamic valor) => (valor as num?)?.toInt() ?? 0;

class SolicitacaoResumo {
  const SolicitacaoResumo({
    required this.id,
    required this.cidadao,
    required this.estado,
    required this.pesoKg,
    required this.dataCriacao,
    this.pontoColeta,
    this.baseOperacional,
  });

  factory SolicitacaoResumo.fromJson(Map<String, dynamic> json) =>
      SolicitacaoResumo(
        id: json['id'] as String,
        cidadao: json['cidadao'] as String? ?? '',
        estado: json['estado'] as String? ?? '',
        pesoKg: _double(json['peso_kg']),
        dataCriacao: DateTime.tryParse(json['data_criacao'] as String? ?? ''),
        pontoColeta: json['ponto_coleta'] as String?,
        baseOperacional: json['base_operacional'] as String?,
      );

  final String id;
  final String cidadao;
  final String estado;
  final double pesoKg;
  final DateTime? dataCriacao;
  final String? pontoColeta;
  final String? baseOperacional;
}

class EntregaResumo {
  const EntregaResumo({
    required this.id,
    required this.valor,
    required this.empresa,
    required this.data,
    required this.status,
  });

  factory EntregaResumo.fromJson(Map<String, dynamic> json) => EntregaResumo(
    id: json['id'] as String,
    valor: _double(json['valor']),
    empresa: json['empresa'] as String? ?? '',
    data: json['data'] as String? ?? '',
    status: json['status'] as String? ?? '',
  );

  final String id;
  final double valor;
  final String empresa;
  final String data;
  final String status;
}

class MesDashboard {
  const MesDashboard(this.mes, this.pesoKg);

  factory MesDashboard.fromJson(Map<String, dynamic> json) =>
      MesDashboard(json['mes'] as String? ?? '', _double(json['peso_kg']));

  final String mes;
  final double pesoKg;
}

class CategoriaDashboard {
  const CategoriaDashboard(this.nome, this.pesoKg);

  factory CategoriaDashboard.fromJson(Map<String, dynamic> json) =>
      CategoriaDashboard(
        json['nome'] as String? ?? '',
        _double(json['peso_kg']),
      );

  final String nome;
  final double pesoKg;
}

class DashboardData {
  const DashboardData({
    required this.tipo,
    required this.usuario,
    required this.metricas,
    this.missao,
    this.proximoTier,
    this.comparativoMensal,
    this.totalEntregasConcluidas = 0,
    this.totalEmProcessamento = 0,
    this.entregas = const [],
    this.solicitacoesAtivas = const [],
    this.emProcessamento = const [],
    this.solicitacoesRecentes = const [],
    this.meses = const [],
    this.categorias = const [],
  });

  factory DashboardData.fromJson(Map<String, dynamic> json) {
    List<T> lista<T>(String chave, T Function(Map<String, dynamic>) criar) =>
        ((json[chave] as List?) ?? const [])
            .map((item) => criar(Map<String, dynamic>.from(item as Map)))
            .toList();

    return DashboardData(
      tipo: json['tipo'] as String,
      usuario: Usuario.fromJson(
        Map<String, dynamic>.from(json['usuario'] as Map),
      ),
      metricas: Map<String, dynamic>.from(json['metricas'] as Map? ?? const {}),
      missao: json['missao'] == null
          ? null
          : Map<String, dynamic>.from(json['missao'] as Map),
      proximoTier: json['proximo_tier'] == null
          ? null
          : Map<String, dynamic>.from(json['proximo_tier'] as Map),
      comparativoMensal: json['comparativo_mensal_percentual'] == null
          ? null
          : _double(json['comparativo_mensal_percentual']),
      totalEntregasConcluidas: _int(json['total_entregas_concluidas']),
      totalEmProcessamento: _int(json['total_em_processamento']),
      entregas: lista('entregas_recentes', EntregaResumo.fromJson),
      solicitacoesAtivas: lista(
        'solicitacoes_ativas',
        SolicitacaoResumo.fromJson,
      ),
      emProcessamento: lista('em_processamento', SolicitacaoResumo.fromJson),
      solicitacoesRecentes: lista(
        'solicitacoes_recentes',
        SolicitacaoResumo.fromJson,
      ),
      meses: lista('meses', MesDashboard.fromJson),
      categorias: lista('categorias', CategoriaDashboard.fromJson),
    );
  }

  final String tipo;
  final Usuario usuario;
  final Map<String, dynamic> metricas;
  final Map<String, dynamic>? missao;
  final Map<String, dynamic>? proximoTier;
  final double? comparativoMensal;
  final int totalEntregasConcluidas;
  final int totalEmProcessamento;
  final List<EntregaResumo> entregas;
  final List<SolicitacaoResumo> solicitacoesAtivas;
  final List<SolicitacaoResumo> emProcessamento;
  final List<SolicitacaoResumo> solicitacoesRecentes;
  final List<MesDashboard> meses;
  final List<CategoriaDashboard> categorias;
}
