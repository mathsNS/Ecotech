import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../data/company/company_data.dart';
import '../../data/company/company_repository.dart';
import '../../data/company/operation_data.dart';
import '../../data/company/operation_repository.dart';

final companyRepositoryProvider = Provider<CompanyRepository>(
  (ref) => CompanyRepository(),
);

final pontosEmpresaProvider = FutureProvider<List<PontoEmpresaData>>(
  (ref) => ref.read(companyRepositoryProvider).listarPontos(),
);

final basesEmpresaProvider = FutureProvider<List<BaseEmpresaData>>(
  (ref) => ref.read(companyRepositoryProvider).listarBases(),
);

final oportunidadesEmpresaProvider = FutureProvider<List<OportunidadeData>>(
  (ref) => ref.read(companyRepositoryProvider).listarOportunidades(),
);

final operationRepositoryProvider = Provider<OperationRepository>(
  (ref) => OperationRepository(),
);

typedef OperacoesConsulta = ({String estado, String busca, int pagina});

final operacoesEmpresaProvider =
    FutureProvider.family<OperacoesPaginaData, OperacoesConsulta>(
      (ref, consulta) => ref
          .read(operationRepositoryProvider)
          .listar(
            estado: consulta.estado,
            busca: consulta.busca,
            pagina: consulta.pagina,
          ),
    );

final operacaoDetalhesProvider =
    FutureProvider.family<OperacaoDetalhesData, String>(
      (ref, id) => ref.read(operationRepositoryProvider).buscar(id),
    );
