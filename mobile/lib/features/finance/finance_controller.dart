import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../data/finance/finance_data.dart';
import '../../data/finance/finance_repository.dart';

final financeRepositoryProvider = Provider<FinanceRepository>(
  (ref) => FinanceRepository(),
);

final carteiraProvider = FutureProvider<CarteiraData>(
  (ref) => ref.read(financeRepositoryProvider).buscarCarteira(),
);

class PeriodoRelatorio {
  const PeriodoRelatorio({this.inicio, this.fim});

  final DateTime? inicio;
  final DateTime? fim;

  @override
  bool operator ==(Object other) =>
      other is PeriodoRelatorio && other.inicio == inicio && other.fim == fim;

  @override
  int get hashCode => Object.hash(inicio, fim);
}

final relatorioProvider =
    FutureProvider.family<RelatorioData, PeriodoRelatorio>(
      (ref, periodo) => ref
          .read(financeRepositoryProvider)
          .buscarRelatorio(inicio: periodo.inicio, fim: periodo.fim),
    );
