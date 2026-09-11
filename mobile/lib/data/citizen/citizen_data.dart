double _double(dynamic value) => (value as num?)?.toDouble() ?? 0;
int _int(dynamic value) => (value as num?)?.toInt() ?? 0;

class PontoColetaData {
  const PontoColetaData({
    required this.id,
    required this.nome,
    required this.empresa,
    required this.endereco,
    required this.capacidadeKg,
    required this.ocupacaoKg,
    required this.disponibilidadePercentual,
  });

  factory PontoColetaData.fromJson(Map<String, dynamic> json) =>
      PontoColetaData(
        id: json['id'] as String,
        nome: json['nome'] as String? ?? '',
        empresa: json['empresa'] as String? ?? '',
        endereco: json['endereco'] as String? ?? '',
        capacidadeKg: _double(json['capacidade_kg']),
        ocupacaoKg: _double(json['ocupacao_kg']),
        disponibilidadePercentual: _double(json['disponibilidade_percentual']),
      );

  final String id;
  final String nome;
  final String empresa;
  final String endereco;
  final double capacidadeKg;
  final double ocupacaoKg;
  final double disponibilidadePercentual;
}

class SolicitacaoData {
  const SolicitacaoData({
    required this.id,
    required this.estado,
    required this.pesoEstimadoKg,
    required this.pesoConfirmadoKg,
    required this.pesoOrigem,
    required this.quantidadeItens,
    this.empresa,
    this.pontoColeta,
    this.tipoColeta,
    this.dataCriacao,
  });

  factory SolicitacaoData.fromJson(Map<String, dynamic> json) =>
      SolicitacaoData(
        id: json['id'] as String,
        estado: json['estado'] as String? ?? '',
        pesoEstimadoKg: _double(json['peso_estimado_kg']),
        pesoConfirmadoKg: json['peso_confirmado_kg'] == null
            ? null
            : _double(json['peso_confirmado_kg']),
        pesoOrigem: json['peso_origem'] as String? ?? 'estimado',
        quantidadeItens: _int(json['quantidade_itens']),
        empresa: json['empresa'] as String?,
        pontoColeta: json['ponto_coleta'] as String?,
        tipoColeta: json['tipo_coleta'] as String?,
        dataCriacao: DateTime.tryParse(json['data_criacao'] as String? ?? ''),
      );

  final String id;
  final String estado;
  final double pesoEstimadoKg;
  final double? pesoConfirmadoKg;
  final String pesoOrigem;
  final int quantidadeItens;
  final String? empresa;
  final String? pontoColeta;
  final String? tipoColeta;
  final DateTime? dataCriacao;

  double get pesoExibidoKg => pesoConfirmadoKg ?? pesoEstimadoKg;
}

class SolicitacoesPagina {
  const SolicitacoesPagina({
    required this.itens,
    required this.pagina,
    required this.totalPaginas,
    required this.total,
  });

  factory SolicitacoesPagina.fromJson(Map<String, dynamic> json) =>
      SolicitacoesPagina(
        itens: (json['itens'] as List? ?? const [])
            .map(
              (item) => SolicitacaoData.fromJson(
                Map<String, dynamic>.from(item as Map),
              ),
            )
            .toList(),
        pagina: _int(json['pagina']),
        totalPaginas: _int(json['total_paginas']),
        total: _int(json['total']),
      );

  final List<SolicitacaoData> itens;
  final int pagina;
  final int totalPaginas;
  final int total;
}

class ItemSolicitacaoData {
  const ItemSolicitacaoData({
    required this.nome,
    required this.tipo,
    required this.subcategoria,
    required this.quantidade,
    required this.pesoUnitarioKg,
    this.modelo,
    this.anoFabricacao,
    this.observacoes,
  });

  factory ItemSolicitacaoData.fromJson(Map<String, dynamic> json) =>
      ItemSolicitacaoData(
        nome: json['nome'] as String? ?? '',
        tipo: json['tipo'] as String? ?? '',
        subcategoria: json['subcategoria'] as String? ?? '',
        quantidade: _int(json['quantidade']),
        pesoUnitarioKg: _double(json['peso_kg']),
        modelo: json['modelo'] as String?,
        anoFabricacao: (json['ano_fabricacao'] as num?)?.toInt(),
        observacoes: json['observacoes'] as String?,
      );

  final String nome;
  final String tipo;
  final String subcategoria;
  final int quantidade;
  final double pesoUnitarioKg;
  final String? modelo;
  final int? anoFabricacao;
  final String? observacoes;
}

class FotoSolicitacaoData {
  const FotoSolicitacaoData({
    required this.id,
    required this.nome,
    required this.url,
  });

  factory FotoSolicitacaoData.fromJson(Map<String, dynamic> json) =>
      FotoSolicitacaoData(
        id: json['id'] as String,
        nome: json['nome_arquivo'] as String? ?? 'Foto do produto',
        url: json['url'] as String,
      );

  final String id;
  final String nome;
  final String url;
}

class HistoricoSolicitacaoData {
  const HistoricoSolicitacaoData(this.mensagem, this.timestamp);

  factory HistoricoSolicitacaoData.fromJson(Map<String, dynamic> json) =>
      HistoricoSolicitacaoData(
        json['mensagem'] as String? ?? '',
        json['timestamp'] as String? ?? '',
      );

  final String mensagem;
  final String timestamp;
}

class SolicitacaoDetalhesData extends SolicitacaoData {
  const SolicitacaoDetalhesData({
    required super.id,
    required super.estado,
    required super.pesoEstimadoKg,
    required super.pesoConfirmadoKg,
    required super.pesoOrigem,
    required super.quantidadeItens,
    required this.pesoInformadoCidadao,
    required this.itens,
    required this.fotos,
    required this.historico,
    super.empresa,
    super.pontoColeta,
    super.tipoColeta,
    super.dataCriacao,
    this.enderecoColeta,
    this.nomeContato,
    this.dataAgendamento,
    this.metodoTratamento,
    this.pesoConfirmadoEm,
    this.agendamento,
    this.avaliacao,
  });

  factory SolicitacaoDetalhesData.fromJson(Map<String, dynamic> json) {
    final base = SolicitacaoData.fromJson(json);
    List<T> lista<T>(String key, T Function(Map<String, dynamic>) parse) =>
        (json[key] as List? ?? const [])
            .map((item) => parse(Map<String, dynamic>.from(item as Map)))
            .toList();
    return SolicitacaoDetalhesData(
      id: base.id,
      estado: base.estado,
      pesoEstimadoKg: base.pesoEstimadoKg,
      pesoConfirmadoKg: base.pesoConfirmadoKg,
      pesoOrigem: base.pesoOrigem,
      quantidadeItens: base.quantidadeItens,
      empresa: base.empresa,
      pontoColeta: base.pontoColeta,
      tipoColeta: base.tipoColeta,
      dataCriacao: base.dataCriacao,
      pesoInformadoCidadao: json['peso_informado_cidadao'] == true,
      enderecoColeta: json['endereco_coleta'] as String?,
      nomeContato: json['nome_contato'] as String?,
      dataAgendamento: json['data_agendamento'] as String?,
      metodoTratamento: json['metodo_tratamento'] as String?,
      pesoConfirmadoEm: json['peso_confirmado_em'] as String?,
      itens: lista('itens', ItemSolicitacaoData.fromJson),
      fotos: lista('fotos', FotoSolicitacaoData.fromJson),
      historico: lista('historico', HistoricoSolicitacaoData.fromJson),
      agendamento: json['agendamento'] == null
          ? null
          : Map<String, dynamic>.from(json['agendamento'] as Map),
      avaliacao: json['avaliacao'] == null
          ? null
          : Map<String, dynamic>.from(json['avaliacao'] as Map),
    );
  }

  final bool pesoInformadoCidadao;
  final String? enderecoColeta;
  final String? nomeContato;
  final String? dataAgendamento;
  final String? metodoTratamento;
  final String? pesoConfirmadoEm;
  final List<ItemSolicitacaoData> itens;
  final List<FotoSolicitacaoData> fotos;
  final List<HistoricoSolicitacaoData> historico;
  final Map<String, dynamic>? agendamento;
  final Map<String, dynamic>? avaliacao;
}

class EntregaData {
  const EntregaData({
    required this.id,
    required this.valor,
    required this.empresa,
    required this.data,
    required this.hora,
    required this.status,
    this.solicitacaoId,
  });

  factory EntregaData.fromJson(Map<String, dynamic> json) => EntregaData(
    id: json['id'] as String,
    valor: _double(json['valor']),
    empresa: json['empresa'] as String? ?? '',
    data: json['data'] as String? ?? '',
    hora: json['hora'] as String? ?? '',
    status: json['status'] as String? ?? '',
    solicitacaoId: json['id_solicitacao'] as String?,
  );

  final String id;
  final double valor;
  final String empresa;
  final String data;
  final String hora;
  final String status;
  final String? solicitacaoId;
}

class EnderecoCepData {
  const EnderecoCepData({
    required this.cep,
    required this.logradouro,
    required this.bairro,
    required this.cidade,
    required this.uf,
  });

  factory EnderecoCepData.fromJson(Map<String, dynamic> json) =>
      EnderecoCepData(
        cep: json['cep'] as String? ?? '',
        logradouro: json['logradouro'] as String? ?? '',
        bairro: json['bairro'] as String? ?? '',
        cidade: json['cidade'] as String? ?? '',
        uf: json['uf'] as String? ?? '',
      );

  final String cep;
  final String logradouro;
  final String bairro;
  final String cidade;
  final String uf;
}
