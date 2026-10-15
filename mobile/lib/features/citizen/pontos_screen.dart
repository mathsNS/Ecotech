import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'citizen_controller.dart';
import 'widgets/collection_point_card.dart';
import 'widgets/citizen_navigation.dart';
import 'widgets/citizen_states.dart';

class PontosScreen extends ConsumerWidget {
  const PontosScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(pontosColetaProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Pontos de coleta')),
      body: state.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => CitizenError(
          error: error,
          onRetry: () => ref.invalidate(pontosColetaProvider),
        ),
        data: (pontos) => RefreshIndicator(
          onRefresh: () => ref.refresh(pontosColetaProvider.future),
          child: pontos.isEmpty
              ? ListView(
                  children: [
                    SizedBox(height: 130),
                    CitizenEmpty(
                      message:
                          'Nenhum ponto de coleta está disponível no momento.',
                    ),
                  ],
                )
              : ListView.builder(
                  physics: const AlwaysScrollableScrollPhysics(),
                  padding: const EdgeInsets.all(16),
                  itemCount: pontos.length + 1,
                  itemBuilder: (context, index) {
                    if (index == 0) {
                      return const Padding(
                        padding: EdgeInsets.only(bottom: 14),
                        child: Text(
                          'Escolha onde deseja entregar seus eletrônicos. A capacidade é atualizada pelo sistema.',
                        ),
                      );
                    }
                    final ponto = pontos[index - 1];
                    return CollectionPointCard(
                      point: ponto,
                      onSelect: () => context.push(
                        Uri(
                          path: '/solicitacoes/nova',
                          queryParameters: {
                            'tipo': 'entrega_ponto',
                            'pontoId': ponto.id,
                          },
                        ).toString(),
                      ),
                    );
                  },
                ),
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => context.push('/solicitacoes/nova'),
        icon: const Icon(Icons.add),
        label: const Text('Nova solicitação'),
      ),
      bottomNavigationBar: const CitizenNavigation(selectedIndex: -1),
    );
  }
}
