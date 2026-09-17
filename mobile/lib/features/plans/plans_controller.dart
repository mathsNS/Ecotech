import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../data/plans/plans_data.dart';
import '../../data/plans/plans_repository.dart';
import '../dashboard/dashboard_controller.dart';

final plansRepositoryProvider = Provider<PlansRepository>(
  (ref) => PlansRepository(),
);

class PlansController extends AsyncNotifier<PlansData> {
  @override
  Future<PlansData> build() => ref.read(plansRepositoryProvider).fetchPlans();

  Future<bool> changePlan(String planId) async {
    final previous = state.valueOrNull;
    state = const AsyncLoading();
    try {
      final updated = await ref.read(plansRepositoryProvider).changePlan(planId);
      state = AsyncData(updated);
      ref.invalidate(dashboardControllerProvider);
      return true;
    } catch (error, stackTrace) {
      state = AsyncError(error, stackTrace);
      if (previous != null) state = AsyncData(previous);
      rethrow;
    }
  }

  Future<void> reload() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(
      () => ref.read(plansRepositoryProvider).fetchPlans(),
    );
  }
}

final plansControllerProvider =
    AsyncNotifierProvider<PlansController, PlansData>(PlansController.new);
