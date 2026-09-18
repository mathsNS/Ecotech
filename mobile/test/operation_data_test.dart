import 'package:flutter_test/flutter_test.dart';

import 'package:ecotech_mobile/data/company/operation_data.dart';
import 'package:ecotech_mobile/data/citizen/citizen_data.dart';

void main() {
  test('detalhes da operacao carregam peso, avaliacao e precos', () {
    final operacao = OperacaoDetalhesData.fromJson({
      'id': 'sol-1',
      'cidadao': 'Joao Silva',
      'estado': 'Em Processamento',
      'peso_kg': 2.75,
      'peso_estimado_kg': 2,
      'peso_confirmado_kg': 2.75,
      'peso_origem': 'aferido',
      'quantidade_itens': 1,
      'data_criacao': '2026-09-11T10:30:00',
      'peso_informado_cidadao': false,
      'peso_confirmado_por': 'Recicla Kariri',
      'diferenca_peso_percentual': 37.5,
      'diferenca_peso_relevante': true,
      'avaliacao': {'estado_produto': 'defeito_leve'},
      'acoes': {
        'pode_avancar': true,
        'exige_peso': false,
        'exige_avaliacao': true,
      },
      'fotos': [],
      'historico': [],
      'itens': [
        {
          'nome': 'Notebook',
          'tipo': 'computador',
          'subcategoria': 'notebook',
          'quantidade': 1,
          'peso_kg': 2,
          'precos': {
            'funcionando': 900,
            'defeito_leve': 360,
            'defeito_grave': 135,
            'sucata': 40,
          },
        },
      ],
    });

    expect(operacao.pesoConfirmadoKg, 2.75);
    expect(operacao.diferencaPesoRelevante, isTrue);
    expect(operacao.exigeAvaliacao, isTrue);
    expect(operacao.itens.single.precos!.defeitoLeve, 360);
  });

  test('pagina de operacoes carrega estatisticas e paginacao', () {
    final pagina = OperacoesPaginaData.fromJson({
      'operacoes': [],
      'estatisticas': {'total': 18, 'Em Processamento': 3},
      'paginacao': {'pagina': 2, 'total_paginas': 4, 'total': 68},
    });

    expect(pagina.estatisticas['Em Processamento'], 3);
    expect(pagina.pagina, 2);
    expect(pagina.totalPaginas, 4);
    expect(pagina.total, 68);
  });

  test('pagina de solicitacoes carrega resumo por estado', () {
    final pagina = SolicitacoesPagina.fromJson({
      'itens': [],
      'pagina': 1,
      'total_paginas': 1,
      'total': 15,
      'estatisticas': {
        'pendentes': 4,
        'em_coleta': 4,
        'processando': 2,
        'finalizadas': 5,
      },
    });

    expect(pagina.estatisticas['pendentes'], 4);
    expect(pagina.estatisticas['finalizadas'], 5);
  });
}
