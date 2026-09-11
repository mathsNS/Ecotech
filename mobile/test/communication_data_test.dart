import 'package:flutter_test/flutter_test.dart';

import 'package:ecotech_mobile/data/communication/communication_data.dart';

void main() {
  test('agenda identifica proposta, autor e acoes permitidas', () {
    final agenda = AgendaData.fromJson({
      'solicitacao': {
        'id': 'sol-1',
        'cidadao': 'João Silva',
        'estado': 'Solicitado',
      },
      'agenda': {
        'status': 'PROPOSTA_PENDENTE',
        'janela_inicio': '2026-09-14T10:00:00',
        'janela_fim': '2026-09-14T12:00:00',
        'proposta_inicio': '2026-09-14T14:00:00',
        'proposta_fim': '2026-09-14T16:00:00',
      },
      'proposta_autor': {'nome': 'Recicla Kariri', 'tipo': 'empresa'},
      'historico': [
        {
          'acao': 'PROPOSTA',
          'autor_nome': 'Recicla Kariri',
          'autor_tipo': 'empresa',
          'criado_em': '2026-09-11T10:00:00',
        },
      ],
      'acoes': {
        'pode_propor': true,
        'pode_aceitar': true,
        'pode_rejeitar': true,
      },
    });

    expect(agenda.status, 'PROPOSTA_PENDENTE');
    expect(agenda.propostaAutorNome, 'Recicla Kariri');
    expect(agenda.historico.single.autorTipo, 'empresa');
    expect(agenda.podeAceitar, isTrue);
  });

  test('mensagem preserva texto e identifica remetente e lado da bolha', () {
    final mensagem = MensagemData.fromJson({
      'id': 'msg-1',
      'tipo': 'MENSAGEM',
      'texto': '<script>texto</script>',
      'criado_em': '2026-09-11T10:30:00',
      'propria': false,
      'remetente': {'nome': 'João Silva', 'tipo': 'cidadao'},
    });

    expect(mensagem.texto, '<script>texto</script>');
    expect(mensagem.remetenteNome, 'João Silva');
    expect(mensagem.propria, isFalse);
    expect(mensagem.evento, isFalse);
  });

  test('notificacao carrega leitura, destino e badge', () {
    final pagina = NotificacoesPaginaData.fromJson({
      'nao_lidas': 2,
      'tem_mais': false,
      'notificacoes': [
        {
          'id': 10,
          'titulo': 'Nova mensagem',
          'mensagem': 'Você recebeu uma mensagem.',
          'tipo': 'mensagem',
          'criada_em': '11/09/2026 10:30:00',
          'lida': false,
          'destino': '/conversas/sol-1',
        },
      ],
    });
    final badges = BadgesData.fromJson({
      'notificacoes': 2,
      'mensagens': 1,
      'oportunidades': 3,
    });

    expect(pagina.itens.single.destino, '/conversas/sol-1');
    expect(pagina.itens.single.lida, isFalse);
    expect(badges.notificacoes, 2);
    expect(badges.mensagens, 1);
  });
}
