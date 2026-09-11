import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../data/company/company_data.dart';
import '../../data/company/company_repository.dart';

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
