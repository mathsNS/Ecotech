import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/formatters/app_formatters.dart';
import '../../core/theme/app_colors.dart';
import '../../data/citizen/citizen_data.dart';
import 'citizen_controller.dart';
import 'widgets/citizen_states.dart';

class EntregasScreen extends ConsumerWidget {
  const EntregasScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(entregasProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Histórico de incentivos')),
      body: state.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => CitizenError(
          error: error,
          onRetry: () => ref.invalidate(entregasProvider),
        ),
        data: (entregas) => RefreshIndicator(
          onRefresh: () => ref.refresh(entregasProvider.future),
          child: entregas.isEmpty
              ? ListView(
                  children: [
                    SizedBox(height: 120),
                    CitizenEmpty(
                      message: 'Nenhum incentivo registrado. Conclua um descarte para receber créditos.',
                    ),
                  ],
                )
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: entregas.length,
                  itemBuilder: (context, index) =>
                      _EntregaCard(entregas[index]),
                ),
        ),
      ),
    );
  }
}

class _EntregaCard extends StatelessWidget {
  const _EntregaCard(this.entrega);
  final EntregaData entrega;

  @override
  Widget build(BuildContext context) => Card(
    margin: const EdgeInsets.only(bottom: 12),
    child: InkWell(
      onTap: entrega.solicitacaoId == null
          ? null
          : () => context.push('/solicitacoes/${entrega.solicitacaoId}'),
      borderRadius: BorderRadius.circular(12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            CircleAvatar(
              backgroundColor: AppColors.secondary,
              child: Image.asset('assets/images/pacote.png', width: 28),
            ),
            const SizedBox(width: 13),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Incentivo por coleta',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 3),
                  Text(entrega.empresa),
                  const SizedBox(height: 5),
                  Text(
                    '${AppFormatters.dataTexto(entrega.data)} às ${entrega.hora}',
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                ],
              ),
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  AppFormatters.moeda(entrega.valor),
                  style: const TextStyle(
                    color: AppColors.success,
                    fontSize: 17,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 5),
                Text(
                  entrega.status.toUpperCase(),
                  style: const TextStyle(fontSize: 11),
                ),
              ],
            ),
          ],
        ),
      ),
    ),
  );
}
