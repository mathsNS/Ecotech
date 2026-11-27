import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_providers.dart';
import '../../data/dashboard/dashboard_data.dart';
import '../../data/dashboard/dashboard_repository.dart';

final dashboardRepositoryProvider = Provider<DashboardRepository>(
  (ref) => DashboardRepository(apiClient: ref.watch(apiClientProvider)),
);

class DashboardController extends AsyncNotifier<DashboardData> {
  @override
  Future<DashboardData> build() =>
      ref.read(dashboardRepositoryProvider).carregar();

  Future<void> recarregar() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(
      () => ref.read(dashboardRepositoryProvider).carregar(),
    );
  }
}

final dashboardControllerProvider =
    AsyncNotifierProvider<DashboardController, DashboardData>(
      DashboardController.new,
    );
