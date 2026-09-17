import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../data/admin/admin_data.dart';
import '../../data/admin/admin_repository.dart';

final adminRepositoryProvider = Provider<AdminRepository>(
  (ref) => AdminRepository(),
);

class FiltroUsuariosAdmin {
  const FiltroUsuariosAdmin({
    this.tipo = 'todos',
    this.busca = '',
    this.pagina = 1,
  });

  final String tipo;
  final String busca;
  final int pagina;

  @override
  bool operator ==(Object other) =>
      other is FiltroUsuariosAdmin &&
      other.tipo == tipo &&
      other.busca == busca &&
      other.pagina == pagina;

  @override
  int get hashCode => Object.hash(tipo, busca, pagina);
}

final usuariosAdminProvider =
    FutureProvider.family<AdminUsuariosData, FiltroUsuariosAdmin>(
      (ref, filtro) => ref
          .read(adminRepositoryProvider)
          .listarUsuarios(
            tipo: filtro.tipo,
            busca: filtro.busca,
            pagina: filtro.pagina,
          ),
    );

final despachoAdminProvider = FutureProvider<DespachoAdminData>(
  (ref) => ref.read(adminRepositoryProvider).buscarDespacho(),
);

final overridesAdminProvider = FutureProvider<List<OverrideAdminData>>(
  (ref) => ref.read(adminRepositoryProvider).listarOverrides(),
);

final precosAdminProvider = FutureProvider<List<PrecoAdminData>>(
  (ref) => ref.read(adminRepositoryProvider).listarPrecos(),
);
