import 'package:ecotech_mobile/data/finance/finance_data.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('carteira carrega saldo, conversao, titular e saques', () {
    final carteira = CarteiraData.fromJson({
      'saldo': 42.5,
      'pontos': 5000,
      'conversao': {'pontos_por_real': 100, 'reais_por_ponto': 0.01},
      'metodos': [
        {'id': 'Pix', 'nome': 'Pix'},
      ],
      'titular': {
        'nome': 'João Silva',
        'cpf': '12345678909',
        'email': 'joao@example.com',
      },
      'saques': [
        {
          'id': 'saque-1',
          'valor': 7.5,
          'metodo': 'Pix',
          'data_hora': '2026-09-16T10:30:00',
          'status': 'pendente',
        },
      ],
    });

    expect(carteira.saldo, 42.5);
    expect(carteira.pontosPorReal, 100);
    expect(carteira.titular.nome, 'João Silva');
    expect(carteira.saques.single.dataHora, '2026-09-16T10:30:00');
  });

  test(
    'relatorio diferencia descarte controlado e permissao de exportacao',
    () {
      final relatorio = RelatorioData.fromJson({
        'titulo': 'Relatório de Recicla Kariri',
        'gerado_em': '2026-09-16T11:00:00',
        'periodo': {'data_inicio': '2026-09-01', 'data_fim': '2026-09-30'},
        'metricas': {
          'total_solicitacoes': 3,
          'peso_reciclado_kg': 10,
          'peso_reutilizado_kg': 5,
          'peso_descartado_kg': 2,
          'peso_total_kg': 17,
          'impacto_evitado': 30,
          'taxa_reciclagem_pct': 58.82,
        },
        'finalizadas': [
          {
            'id': 'sol-1',
            'cidadao': 'João Silva',
            'peso_kg': 2,
            'impacto_kg': 1,
            'metodo': 'Descarte Controlado',
            'estado': 'Descartado',
            'data': '2026-09-10T12:00:00',
          },
        ],
        'pnrs': {
          'disponivel': true,
          'destinacao_adequada_pct': 88.24,
          'peso_total_gerenciado_kg': 17,
          'solicitacoes_atendidas': 3,
        },
        'plano': 'professional',
        'pode_exportar': true,
      });

      expect(relatorio.metricas.pesoDescartadoKg, 2);
      expect(relatorio.finalizadas.single.estado, 'Descartado');
      expect(relatorio.pnrs.disponivel, isTrue);
      expect(relatorio.podeExportar, isTrue);
    },
  );
}
