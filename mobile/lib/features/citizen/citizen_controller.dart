import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../data/citizen/citizen_data.dart';
import '../../data/citizen/citizen_repository.dart';

final citizenRepositoryProvider = Provider<CitizenRepository>(
  (ref) => CitizenRepository(),
);

final pontosColetaProvider = FutureProvider<List<PontoColetaData>>(
  (ref) => ref.read(citizenRepositoryProvider).listarPontos(),
);

final solicitacoesProvider = FutureProvider.family<SolicitacoesPagina, String>(
  (ref, estado) =>
      ref.read(citizenRepositoryProvider).listarSolicitacoes(estado: estado),
);

final solicitacaoDetalhesProvider =
    FutureProvider.family<SolicitacaoDetalhesData, String>(
      (ref, id) => ref.read(citizenRepositoryProvider).buscarSolicitacao(id),
    );

final entregasProvider = FutureProvider<List<EntregaData>>(
  (ref) => ref.read(citizenRepositoryProvider).listarEntregas(),
);
