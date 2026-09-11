import 'package:flutter_test/flutter_test.dart';

import 'package:ecotech_mobile/core/formatters/app_formatters.dart';
import 'package:ecotech_mobile/data/citizen/citizen_data.dart';

void main() {
  test('solicitacao usa peso estimado enquanto empresa nao confirma', () {
    final solicitacao = SolicitacaoData.fromJson({
      'id': 'sol-1',
      'estado': 'pendente',
      'peso_estimado_kg': 4.8,
      'peso_confirmado_kg': null,
      'peso_origem': 'estimado',
      'quantidade_itens': 2,
      'data_criacao': '2026-09-10T14:30:00',
    });

    expect(solicitacao.pesoExibidoKg, 4.8);
    expect(solicitacao.dataCriacao, DateTime(2026, 9, 10, 14, 30));
  });

  test('peso confirmado substitui estimativa nos detalhes', () {
    final solicitacao = SolicitacaoDetalhesData.fromJson({
      'id': 'sol-2',
      'estado': 'recebido',
      'peso_estimado_kg': 4.8,
      'peso_confirmado_kg': 5.2,
      'peso_origem': 'aferido',
      'peso_informado_cidadao': false,
      'quantidade_itens': 1,
      'itens': [
        {
          'nome': 'Notebook',
          'tipo': 'computador',
          'subcategoria': 'Notebook',
          'quantidade': 1,
          'peso_kg': 4.8,
          'ano_fabricacao': 2021,
        },
      ],
      'fotos': [],
      'historico': [],
    });

    expect(solicitacao.pesoExibidoKg, 5.2);
    expect(solicitacao.itens.single.anoFabricacao, 2021);
  });

  test('datas da API seguem o padrao brasileiro', () {
    expect(AppFormatters.dataTexto('2026-09-10T14:30:12'), '10/09/2026');
    expect(
      AppFormatters.dataHoraTexto('2026-09-10T14:30:12'),
      '10/09/2026 14:30',
    );
    expect(
      AppFormatters.dataHoraTexto('10/09/2026 14:30:12'),
      '10/09/2026 14:30',
    );
  });
}
