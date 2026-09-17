import 'package:ecotech_mobile/data/admin/admin_data.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('usuarios administrativos preservam mascara status e paginacao', () {
    final dados = AdminUsuariosData.fromJson({
      'usuarios': [
        {
          'id': 'cid-1',
          'nome': 'João Silva',
          'email': 'jo***@ecotech.com',
          'documento': '***.***.***-09',
          'tipo': 'cidadao',
          'ativo': false,
          'data_cadastro': '2026-09-17T10:00:00',
          'pontos': 120,
        },
      ],
      'metricas': {
        'total': 4,
        'cidadaos': 3,
        'empresas': 1,
        'ativos': 3,
        'inativos': 1,
      },
      'paginacao': {
        'pagina': 2,
        'total_paginas': 3,
        'total': 4,
      },
    });

    expect(dados.usuarios.single.ativo, isFalse);
    expect(dados.usuarios.single.documento, contains('*'));
    expect(dados.metricas.inativos, 1);
    expect(dados.pagina, 2);
  });

  test('diagnostico identifica empresa base rodada e horario do alerta', () {
    final dados = DespachoAdminData.fromJson({
      'metricas': {'solicitacoes_ofertadas': 2},
      'resumo': [
        {'status': 'ATIVA', 'total': 1},
      ],
      'pendentes': [],
      'destinatarios': [
        {
          'solicitacao_id': 'sol-1',
          'empresa_nome': 'Recicla Kariri',
          'base_nome': 'Base Centro',
          'rodada': 2,
          'status': 'ATIVA',
          'enviada_em': '2026-09-17T10:00:00',
        },
      ],
      'atribuicoes': [],
    });

    expect(dados.destinatarios.single.empresaNome, 'Recicla Kariri');
    expect(dados.destinatarios.single.baseNome, 'Base Centro');
    expect(dados.destinatarios.single.rodada, 2);
  });

  test('override e preco carregam limites financeiros', () {
    final override = OverrideAdminData.fromJson({
      'solicitacao_id': 'sol-1',
      'data_criacao': '2026-09-17T10:00:00',
      'cidadao': 'João Silva',
      'empresa': 'Recicla Kariri',
      'estado_produto': 'funcionando',
      'valor_proposto': 1000,
      'valor_base': 600,
      'valor_minimo': 10,
      'limite_override': 900,
      'valor_recalculado': 600,
      'justificativa': 'Laudo técnico',
    });
    final preco = PrecoAdminData.fromJson({
      'subcategoria': 'smartphone_medio',
      'categoria': 'celular',
      'valor_base': 600,
      'valor_minimo': 10,
      'limite_override': 900,
    });

    expect(override.limiteOverride, 900);
    expect(override.empresa, 'Recicla Kariri');
    expect(preco.limiteOverride, preco.valorBase * 1.5);
  });
}
