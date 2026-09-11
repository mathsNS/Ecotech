double _double(dynamic value) => (value as num?)?.toDouble() ?? 0;

class EntregaPontoData {
  const EntregaPontoData({
    required this.id,
    required this.cidadao,
    required this.estado,
    required this.pesoKg,
    required this.pesoInformadoCidadao,
    required this.confirmadoEmpresa,
    required this.podeConfirmar,
    this.dataAgendamento,
    this.pesoConfirmadoKg,
  });

  factory EntregaPontoData.fromJson(Map<String, dynamic> json) =>
      EntregaPontoData(
        id: json['id'] as String,
        cidadao: json['cidadao'] as String? ?? '',
        estado: json['estado'] as String? ?? '',
        pesoKg: _double(json['peso_kg']),
        pesoInformadoCidadao: json['peso_informado_cidadao'] == true,
        confirmadoEmpresa: json['confirmado_empresa'] == true,
        podeConfirmar: json['pode_confirmar'] == true,
        dataAgendamento: json['data_agendamento'] as String?,
        pesoConfirmadoKg: json['peso_confirmado_kg'] == null
            ? null
            : _double(json['peso_confirmado_kg']),
      );

  final String id;
  final String cidadao;
  final String estado;
  final double pesoKg;
  final bool pesoInformadoCidadao;
  final bool confirmadoEmpresa;
  final bool podeConfirmar;
  final String? dataAgendamento;
  final double? pesoConfirmadoKg;
}

class PontoEmpresaData {
  const PontoEmpresaData({
    required this.id,
    required this.nome,
    required this.endereco,
    required this.capacidadeKg,
    required this.ocupacaoKg,
    required this.ativa,
    required this.solicitacoes,
  });

  factory PontoEmpresaData.fromJson(Map<String, dynamic> json) =>
      PontoEmpresaData(
        id: json['id'] as String,
        nome: json['nome'] as String? ?? '',
        endereco: json['endereco'] as String? ?? '',
        capacidadeKg: _double(json['capacidade_kg']),
        ocupacaoKg: _double(json['ocupacao_kg']),
        ativa: json['ativa'] == true,
        solicitacoes: (json['solicitacoes'] as List? ?? const [])
            .map(
              (item) => EntregaPontoData.fromJson(
                Map<String, dynamic>.from(item as Map),
              ),
            )
            .toList(),
      );

  final String id;
  final String nome;
  final String endereco;
  final double capacidadeKg;
  final double ocupacaoKg;
  final bool ativa;
  final List<EntregaPontoData> solicitacoes;

  double get ocupacaoPercentual => capacidadeKg <= 0
      ? 0
      : (ocupacaoKg / capacidadeKg).clamp(0, 1).toDouble();
}

class BaseEmpresaData {
  const BaseEmpresaData({
    required this.id,
    required this.nome,
    required this.endereco,
    required this.raioAtendimentoKm,
    required this.capacidadeKg,
    required this.ocupacaoKg,
    required this.capacidadeDisponivelKg,
    required this.realizaColetaDomiciliar,
    required this.ativa,
    this.pontoColetaId,
  });

  factory BaseEmpresaData.fromJson(Map<String, dynamic> json) =>
      BaseEmpresaData(
        id: json['id'] as String,
        nome: json['nome'] as String? ?? '',
        endereco: json['endereco'] as String? ?? '',
        raioAtendimentoKm: _double(json['raio_atendimento_km']),
        capacidadeKg: _double(json['capacidade_kg']),
        ocupacaoKg: _double(json['ocupacao_kg']),
        capacidadeDisponivelKg: _double(json['capacidade_disponivel_kg']),
        realizaColetaDomiciliar: json['realiza_coleta_domiciliar'] == true,
        ativa: json['ativa'] == true,
        pontoColetaId: json['ponto_coleta_id'] as String?,
      );

  final String id;
  final String nome;
  final String endereco;
  final double raioAtendimentoKm;
  final double capacidadeKg;
  final double ocupacaoKg;
  final double capacidadeDisponivelKg;
  final bool realizaColetaDomiciliar;
  final bool ativa;
  final String? pontoColetaId;
}

class OportunidadeData {
  const OportunidadeData({
    required this.id,
    required this.solicitacaoId,
    required this.baseId,
    required this.baseNome,
    required this.distanciaKm,
    required this.expiraEm,
    required this.categorias,
    required this.pesoEstimadoKg,
    required this.agendadaPara,
  });

  factory OportunidadeData.fromJson(Map<String, dynamic> json) {
    final dados = Map<String, dynamic>.from(json['dados'] as Map? ?? const {});
    return OportunidadeData(
      id: json['id'] as String,
      solicitacaoId: json['solicitacao_id'] as String,
      baseId: json['base_operacional_id'] as String,
      baseNome: json['base_nome'] as String? ?? '',
      distanciaKm: _double(json['distancia_km']),
      expiraEm: json['expira_em'] as String? ?? '',
      categorias: (dados['categorias'] as List? ?? const [])
          .map((item) => item.toString())
          .toList(),
      pesoEstimadoKg: _double(dados['peso_estimado_kg']),
      agendadaPara: dados['agendada_para'] as String? ?? '',
    );
  }

  final String id;
  final String solicitacaoId;
  final String baseId;
  final String baseNome;
  final double distanciaKm;
  final String expiraEm;
  final List<String> categorias;
  final double pesoEstimadoKg;
  final String agendadaPara;
}

class AceiteOportunidadeData {
  const AceiteOportunidadeData({
    required this.solicitacaoId,
    required this.endereco,
    required this.nomeContato,
    required this.dataAgendamento,
  });

  factory AceiteOportunidadeData.fromJson(Map<String, dynamic> json) =>
      AceiteOportunidadeData(
        solicitacaoId: json['solicitacao_id'] as String,
        endereco: json['endereco_coleta'] as String? ?? '',
        nomeContato: json['nome_contato'] as String? ?? '',
        dataAgendamento: json['data_agendamento'] as String? ?? '',
      );

  final String solicitacaoId;
  final String endereco;
  final String nomeContato;
  final String dataAgendamento;
}
