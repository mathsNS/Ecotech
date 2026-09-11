import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/formatters/app_formatters.dart';
import '../../data/citizen/citizen_data.dart';
import 'citizen_controller.dart';
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
                    return _PontoCard(pontos[index - 1]);
                  },
                ),
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => context.push('/solicitacoes/nova'),
        icon: const Icon(Icons.add),
        label: const Text('Nova solicitação'),
      ),
      bottomNavigationBar: const CitizenNavigation(selectedIndex: 2),
    );
  }
}

class _PontoCard extends StatelessWidget {
  const _PontoCard(this.ponto);
  final PontoColetaData ponto;

  @override
  Widget build(BuildContext context) => Card(
    margin: const EdgeInsets.only(bottom: 12),
    child: Padding(
      padding: const EdgeInsets.all(17),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Image.asset(
                'assets/images/localizacao.png',
                width: 36,
                height: 36,
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      ponto.nome,
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(height: 3),
                    Text(
                      ponto.empresa,
                      style: Theme.of(context).textTheme.bodyMedium,
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 13),
          Text(ponto.endereco),
          const SizedBox(height: 14),
          Row(
            children: [
              Expanded(
                child: LinearProgressIndicator(
                  value: (ponto.ocupacaoKg / ponto.capacidadeKg)
                      .clamp(0, 1)
                      .toDouble(),
                  minHeight: 8,
                  borderRadius: BorderRadius.circular(8),
                ),
              ),
              const SizedBox(width: 10),
              Text(
                '${AppFormatters.numero(ponto.ocupacaoKg)} / ${AppFormatters.numero(ponto.capacidadeKg)} kg',
              ),
            ],
          ),
          const SizedBox(height: 14),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: ponto.disponibilidadePercentual <= 0
                  ? null
                  : () => context.push(
                      '/solicitacoes/nova?tipo=entrega_ponto&pontoId=${ponto.id}',
                    ),
              icon: const Icon(Icons.inventory_2_outlined),
              label: const Text('Descartar neste ponto'),
            ),
          ),
        ],
      ),
    ),
  );
}
