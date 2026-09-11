class AgendaData {
  const AgendaData({
    required this.solicitacaoId,
    required this.cidadao,
    required this.estado,
    required this.historico,
    required this.podePropor,
    required this.podeAceitar,
    required this.podeRejeitar,
    this.status,
    this.janelaInicio,
    this.janelaFim,
    this.propostaInicio,
    this.propostaFim,
    this.inicioConfirmado,
    this.fimConfirmado,
    this.propostaAutorNome,
    this.propostaAutorTipo,
  });

  factory AgendaData.fromJson(Map<String, dynamic> json) {
    final solicitacao = Map<String, dynamic>.from(
      json['solicitacao'] as Map? ?? const {},
    );
    final agenda = json['agenda'] == null
        ? <String, dynamic>{}
        : Map<String, dynamic>.from(json['agenda'] as Map);
    final autor = json['proposta_autor'] == null
        ? <String, dynamic>{}
        : Map<String, dynamic>.from(json['proposta_autor'] as Map);
    final acoes = Map<String, dynamic>.from(json['acoes'] as Map? ?? const {});
    return AgendaData(
      solicitacaoId: solicitacao['id'] as String? ?? '',
      cidadao: solicitacao['cidadao'] as String? ?? '',
      estado: solicitacao['estado'] as String? ?? '',
      status: agenda['status'] as String?,
      janelaInicio: agenda['janela_inicio'] as String?,
      janelaFim: agenda['janela_fim'] as String?,
      propostaInicio: agenda['proposta_inicio'] as String?,
      propostaFim: agenda['proposta_fim'] as String?,
      inicioConfirmado: agenda['inicio_confirmado'] as String?,
      fimConfirmado: agenda['fim_confirmado'] as String?,
      propostaAutorNome: autor['nome'] as String?,
      propostaAutorTipo: autor['tipo'] as String?,
      historico: (json['historico'] as List? ?? const [])
          .map(
            (item) => EventoAgendaData.fromJson(
              Map<String, dynamic>.from(item as Map),
            ),
          )
          .toList(),
      podePropor: acoes['pode_propor'] == true,
      podeAceitar: acoes['pode_aceitar'] == true,
      podeRejeitar: acoes['pode_rejeitar'] == true,
    );
  }

  final String solicitacaoId;
  final String cidadao;
  final String estado;
  final String? status;
  final String? janelaInicio;
  final String? janelaFim;
  final String? propostaInicio;
  final String? propostaFim;
  final String? inicioConfirmado;
  final String? fimConfirmado;
  final String? propostaAutorNome;
  final String? propostaAutorTipo;
  final List<EventoAgendaData> historico;
  final bool podePropor;
  final bool podeAceitar;
  final bool podeRejeitar;
}

class EventoAgendaData {
  const EventoAgendaData({
    required this.acao,
    required this.autorNome,
    required this.autorTipo,
    required this.criadoEm,
    this.inicio,
    this.fim,
  });

  factory EventoAgendaData.fromJson(Map<String, dynamic> json) =>
      EventoAgendaData(
        acao: json['acao'] as String? ?? '',
        autorNome: json['autor_nome'] as String? ?? 'EcoTech',
        autorTipo: json['autor_tipo'] as String? ?? 'sistema',
        criadoEm: json['criado_em'] as String? ?? '',
        inicio: json['inicio'] as String?,
        fim: json['fim'] as String?,
      );

  final String acao;
  final String autorNome;
  final String autorTipo;
  final String criadoEm;
  final String? inicio;
  final String? fim;
}

class ConversaData {
  const ConversaData({
    required this.solicitacaoId,
    required this.contatoNome,
    required this.contatoTipo,
    required this.estado,
    required this.ultimaMensagem,
    required this.ultimaMensagemEm,
    required this.naoLidas,
    required this.encerrada,
  });

  factory ConversaData.fromJson(Map<String, dynamic> json) => ConversaData(
    solicitacaoId: json['solicitacao_id'] as String,
    contatoNome: json['contato_nome'] as String? ?? '',
    contatoTipo: json['contato_tipo'] as String? ?? '',
    estado: json['estado'] as String? ?? '',
    ultimaMensagem: json['ultima_mensagem'] as String? ?? '',
    ultimaMensagemEm: json['ultima_mensagem_em'] as String? ?? '',
    naoLidas: (json['nao_lidas'] as num?)?.toInt() ?? 0,
    encerrada: json['encerrada_em'] != null,
  );

  final String solicitacaoId;
  final String contatoNome;
  final String contatoTipo;
  final String estado;
  final String ultimaMensagem;
  final String ultimaMensagemEm;
  final int naoLidas;
  final bool encerrada;
}

class MensagemData {
  const MensagemData({
    required this.id,
    required this.tipo,
    required this.texto,
    required this.criadoEm,
    required this.propria,
    required this.remetenteNome,
    required this.remetenteTipo,
  });

  factory MensagemData.fromJson(Map<String, dynamic> json) {
    final remetente = Map<String, dynamic>.from(
      json['remetente'] as Map? ?? const {},
    );
    return MensagemData(
      id: json['id'] as String,
      tipo: json['tipo'] as String? ?? 'MENSAGEM',
      texto: json['texto'] as String? ?? '',
      criadoEm: json['criado_em'] as String? ?? '',
      propria: json['propria'] == true,
      remetenteNome: remetente['nome'] as String? ?? 'EcoTech',
      remetenteTipo: remetente['tipo'] as String? ?? 'sistema',
    );
  }

  final String id;
  final String tipo;
  final String texto;
  final String criadoEm;
  final bool propria;
  final String remetenteNome;
  final String remetenteTipo;
  bool get evento => tipo != 'MENSAGEM';
}

class MensagensPaginaData {
  const MensagensPaginaData({
    required this.mensagens,
    required this.pagina,
    required this.temMais,
    required this.cidadao,
    required this.estado,
  });

  factory MensagensPaginaData.fromJson(Map<String, dynamic> json) {
    final solicitacao = Map<String, dynamic>.from(
      json['solicitacao'] as Map? ?? const {},
    );
    return MensagensPaginaData(
      mensagens: (json['mensagens'] as List? ?? const [])
          .map(
            (item) =>
                MensagemData.fromJson(Map<String, dynamic>.from(item as Map)),
          )
          .toList(),
      pagina: (json['pagina'] as num?)?.toInt() ?? 1,
      temMais: json['tem_mais'] == true,
      cidadao: solicitacao['cidadao'] as String? ?? '',
      estado: solicitacao['estado'] as String? ?? '',
    );
  }

  final List<MensagemData> mensagens;
  final int pagina;
  final bool temMais;
  final String cidadao;
  final String estado;
}

class NotificacaoData {
  const NotificacaoData({
    required this.id,
    required this.titulo,
    required this.mensagem,
    required this.tipo,
    required this.criadaEm,
    required this.lida,
    required this.destino,
  });

  factory NotificacaoData.fromJson(Map<String, dynamic> json) =>
      NotificacaoData(
        id: (json['id'] as num).toInt(),
        titulo: json['titulo'] as String? ?? '',
        mensagem: json['mensagem'] as String? ?? '',
        tipo: json['tipo'] as String? ?? 'coleta',
        criadaEm: json['criada_em'] as String? ?? '',
        lida: json['lida'] == true,
        destino: json['destino'] as String? ?? '/notificacoes',
      );

  final int id;
  final String titulo;
  final String mensagem;
  final String tipo;
  final String criadaEm;
  final bool lida;
  final String destino;
}

class NotificacoesPaginaData {
  const NotificacoesPaginaData({
    required this.itens,
    required this.naoLidas,
    required this.temMais,
  });

  factory NotificacoesPaginaData.fromJson(Map<String, dynamic> json) =>
      NotificacoesPaginaData(
        itens: (json['notificacoes'] as List? ?? const [])
            .map(
              (item) => NotificacaoData.fromJson(
                Map<String, dynamic>.from(item as Map),
              ),
            )
            .toList(),
        naoLidas: (json['nao_lidas'] as num?)?.toInt() ?? 0,
        temMais: json['tem_mais'] == true,
      );

  final List<NotificacaoData> itens;
  final int naoLidas;
  final bool temMais;
}

class BadgesData {
  const BadgesData({
    required this.notificacoes,
    required this.mensagens,
    required this.oportunidades,
  });

  factory BadgesData.fromJson(Map<String, dynamic> json) => BadgesData(
    notificacoes: (json['notificacoes'] as num?)?.toInt() ?? 0,
    mensagens: (json['mensagens'] as num?)?.toInt() ?? 0,
    oportunidades: (json['oportunidades'] as num?)?.toInt() ?? 0,
  );

  final int notificacoes;
  final int mensagens;
  final int oportunidades;
}
