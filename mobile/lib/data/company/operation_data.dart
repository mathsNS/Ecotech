import '../citizen/citizen_data.dart';

double _double(dynamic value) => (value as num?)?.toDouble() ?? 0;
int _int(dynamic value) => (value as num?)?.toInt() ?? 0;

class OperacaoResumoData {
  const OperacaoResumoData({
    required this.id,
    required this.cidadao,
    required this.estado,
    required this.pesoKg,
    required this.pesoEstimadoKg,
    required this.pesoOrigem,
    required this.quantidadeItens,
    required this.dataCriacao,
    this.pesoConfirmadoKg,
    this.empresa,
    this.pontoColeta,
    this.tipoColeta,
  });

  factory OperacaoResumoData.fromJson(Map<String, dynamic> json) =>
      OperacaoResumoData(
        id: json['id'] as String,
        cidadao: json['cidadao'] as String? ?? '',
        estado: json['estado'] as String? ?? '',
        pesoKg: _double(json['peso_kg']),
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
  final String cidadao;
  final String estado;
  final double pesoKg;
  final double pesoEstimadoKg;
  final double? pesoConfirmadoKg;
  final String pesoOrigem;
  final int quantidadeItens;
  final String? empresa;
  final String? pontoColeta;
  final String? tipoColeta;
  final DateTime? dataCriacao;
}

class OperacoesPaginaData {
  const OperacoesPaginaData({
    required this.operacoes,
    required this.estatisticas,
    required this.pagina,
    required this.totalPaginas,
    required this.total,
  });

  factory OperacoesPaginaData.fromJson(Map<String, dynamic> json) {
    final paginacao = Map<String, dynamic>.from(
      json['paginacao'] as Map? ?? const {},
    );
    return OperacoesPaginaData(
      operacoes: (json['operacoes'] as List? ?? const [])
          .map(
            (item) => OperacaoResumoData.fromJson(
              Map<String, dynamic>.from(item as Map),
            ),
          )
          .toList(),
      estatisticas: Map<String, dynamic>.from(
        json['estatisticas'] as Map? ?? const {},
      ).map((key, value) => MapEntry(key, _int(value))),
      pagina: _int(paginacao['pagina']),
      totalPaginas: _int(paginacao['total_paginas']),
      total: _int(paginacao['total']),
    );
  }

  final List<OperacaoResumoData> operacoes;
  final Map<String, int> estatisticas;
  final int pagina;
  final int totalPaginas;
  final int total;
}

class PrecosProdutoData {
  const PrecosProdutoData({
    required this.funcionando,
    required this.defeitoLeve,
    required this.defeitoGrave,
    required this.sucata,
  });

  factory PrecosProdutoData.fromJson(Map<String, dynamic> json) =>
      PrecosProdutoData(
        funcionando: _double(json['funcionando']),
        defeitoLeve: _double(json['defeito_leve']),
        defeitoGrave: _double(json['defeito_grave']),
        sucata: _double(json['sucata']),
      );

  final double funcionando;
  final double defeitoLeve;
  final double defeitoGrave;
  final double sucata;
}

class ItemOperacaoData extends ItemSolicitacaoData {
  const ItemOperacaoData({
    required super.nome,
    required super.tipo,
    required super.subcategoria,
    required super.quantidade,
    required super.pesoUnitarioKg,
    super.modelo,
    super.anoFabricacao,
    super.observacoes,
    this.precos,
  });

  factory ItemOperacaoData.fromJson(Map<String, dynamic> json) =>
      ItemOperacaoData(
        nome: json['nome'] as String? ?? '',
        tipo: json['tipo'] as String? ?? '',
        subcategoria: json['subcategoria'] as String? ?? '',
        quantidade: _int(json['quantidade']),
        pesoUnitarioKg: _double(json['peso_kg']),
        modelo: json['modelo'] as String?,
        anoFabricacao: (json['ano_fabricacao'] as num?)?.toInt(),
        observacoes: json['observacoes'] as String?,
        precos: json['precos'] == null
            ? null
            : PrecosProdutoData.fromJson(
                Map<String, dynamic>.from(json['precos'] as Map),
              ),
      );

  final PrecosProdutoData? precos;
}

class OperacaoDetalhesData extends OperacaoResumoData {
  const OperacaoDetalhesData({
    required super.id,
    required super.cidadao,
    required super.estado,
    required super.pesoKg,
    required super.pesoEstimadoKg,
    required super.pesoConfirmadoKg,
    required super.pesoOrigem,
    required super.quantidadeItens,
    required super.dataCriacao,
    required this.pesoInformadoCidadao,
    required this.diferencaPesoRelevante,
    required this.itens,
    required this.fotos,
    required this.historico,
    required this.podeAvancar,
    required this.exigePeso,
    required this.exigeAvaliacao,
    super.empresa,
    super.pontoColeta,
    super.tipoColeta,
    this.enderecoColeta,
    this.nomeContato,
    this.dataAgendamento,
    this.metodoTratamento,
    this.pesoConfirmadoEm,
    this.pesoConfirmadoPor,
    this.diferencaPesoPercentual,
    this.base,
    this.atribuidaEm,
    this.avaliacao,
  });

  factory OperacaoDetalhesData.fromJson(Map<String, dynamic> json) {
    final resumo = OperacaoResumoData.fromJson(json);
    final acoes = Map<String, dynamic>.from(json['acoes'] as Map? ?? const {});
    return OperacaoDetalhesData(
      id: resumo.id,
      cidadao: resumo.cidadao,
      estado: resumo.estado,
      pesoKg: resumo.pesoKg,
      pesoEstimadoKg: resumo.pesoEstimadoKg,
      pesoConfirmadoKg: resumo.pesoConfirmadoKg,
      pesoOrigem: resumo.pesoOrigem,
      quantidadeItens: resumo.quantidadeItens,
      dataCriacao: resumo.dataCriacao,
      empresa: resumo.empresa,
      pontoColeta: resumo.pontoColeta,
      tipoColeta: resumo.tipoColeta,
      enderecoColeta: json['endereco_coleta'] as String?,
      nomeContato: json['nome_contato'] as String?,
      dataAgendamento: json['data_agendamento'] as String?,
      metodoTratamento: json['metodo_tratamento'] as String?,
      pesoInformadoCidadao: json['peso_informado_cidadao'] == true,
      pesoConfirmadoEm: json['peso_confirmado_em'] as String?,
      pesoConfirmadoPor: json['peso_confirmado_por'] as String?,
      diferencaPesoPercentual: json['diferenca_peso_percentual'] == null
          ? null
          : _double(json['diferenca_peso_percentual']),
      diferencaPesoRelevante: json['diferenca_peso_relevante'] == true,
      base: json['base'] == null
          ? null
          : Map<String, dynamic>.from(json['base'] as Map),
      atribuidaEm: json['atribuida_em'] as String?,
      avaliacao: json['avaliacao'] == null
          ? null
          : Map<String, dynamic>.from(json['avaliacao'] as Map),
      itens: (json['itens'] as List? ?? const [])
          .map(
            (item) => ItemOperacaoData.fromJson(
              Map<String, dynamic>.from(item as Map),
            ),
          )
          .toList(),
      fotos: (json['fotos'] as List? ?? const [])
          .map(
            (item) => FotoSolicitacaoData.fromJson(
              Map<String, dynamic>.from(item as Map),
            ),
          )
          .toList(),
      historico: (json['historico'] as List? ?? const [])
          .map(
            (item) => HistoricoSolicitacaoData.fromJson(
              Map<String, dynamic>.from(item as Map),
            ),
          )
          .toList(),
      podeAvancar: acoes['pode_avancar'] == true,
      exigePeso: acoes['exige_peso'] == true,
      exigeAvaliacao: acoes['exige_avaliacao'] == true,
    );
  }

  final bool pesoInformadoCidadao;
  final String? enderecoColeta;
  final String? nomeContato;
  final String? dataAgendamento;
  final String? metodoTratamento;
  final String? pesoConfirmadoEm;
  final String? pesoConfirmadoPor;
  final double? diferencaPesoPercentual;
  final bool diferencaPesoRelevante;
  final Map<String, dynamic>? base;
  final String? atribuidaEm;
  final Map<String, dynamic>? avaliacao;
  final List<ItemOperacaoData> itens;
  final List<FotoSolicitacaoData> fotos;
  final List<HistoricoSolicitacaoData> historico;
  final bool podeAvancar;
  final bool exigePeso;
  final bool exigeAvaliacao;
}
