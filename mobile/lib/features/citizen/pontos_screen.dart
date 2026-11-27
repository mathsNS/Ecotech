import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_colors.dart';
import '../../data/citizen/citizen_data.dart';
import '../../shared/widgets/app_back_button.dart';
import 'citizen_controller.dart';
import 'widgets/collection_point_card.dart';
import 'widgets/citizen_navigation.dart';
import 'widgets/citizen_states.dart';

class PontosScreen extends ConsumerStatefulWidget {
  const PontosScreen({this.selectionMode = false, this.selectedId, super.key});
  final bool selectionMode;
  final String? selectedId;

  @override
  ConsumerState<PontosScreen> createState() => _PontosScreenState();
}

class _PontosScreenState extends ConsumerState<PontosScreen> {
  final _search = TextEditingController();

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  void _select(PontoColetaData point) {
    if (widget.selectionMode) {
      Navigator.of(context).pop(point);
    } else {
      context.push(
        Uri(
          path: '/solicitacoes/nova',
          queryParameters: {'tipo': 'entrega_ponto', 'pontoId': point.id},
        ).toString(),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final scaffold = Scaffold(
      appBar: AppBar(
        leading: widget.selectionMode
            ? const BackButton()
            : const AppBackButton(),
      toolbarHeight: 32 + MediaQuery.textScalerOf(context).scale(24),
      title: const Text(
        'Pontos de coleta',
        maxLines: 2,
        softWrap: true,
        style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900),
      ),
      backgroundColor: AppColors.surfaceSubtle,
    ),
    body: SafeArea(
      child: ref
          .watch(pontosColetaProvider)
          .when(
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (error, _) => CitizenError(
              error: error,
              onRetry: () => ref.invalidate(pontosColetaProvider),
            ),
            data: (points) {
              final query = _search.text.trim().toLowerCase();
              final filtered = points
                  .where(
                    (p) => '${p.nome} ${p.empresa} ${p.endereco}'
                        .toLowerCase()
                        .contains(query),
                  )
                  .toList();
              return RefreshIndicator(
                onRefresh: () => ref.refresh(pontosColetaProvider.future),
                child: SingleChildScrollView(
                  physics: const AlwaysScrollableScrollPhysics(),
                  padding: const EdgeInsets.all(16),
                  child: Center(
                    child: ConstrainedBox(
                      constraints: const BoxConstraints(maxWidth: 576),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          const Text(
                            'Leve seu eletrônico a um ponto de coleta.',
                          ),
                          const SizedBox(height: 16),
                          TextField(
                            controller: _search,
                            onChanged: (_) => setState(() {}),
                            decoration: InputDecoration(
                              hintText: 'Buscar por nome ou bairro',
                              prefixIcon: const Icon(Icons.search),
                              suffixIcon: query.isEmpty
                                  ? null
                                  : IconButton(
                                      tooltip: 'Limpar busca',
                                      icon: const Icon(Icons.close),
                                      onPressed: () => setState(_search.clear),
                                    ),
                            ),
                          ),
                          const SizedBox(height: 24),
                          Text(
                            'Pontos de coleta (${filtered.length})',
                            style: Theme.of(context).textTheme.titleMedium,
                          ),
                          const SizedBox(height: 16),
                          if (filtered.isEmpty)
                            CitizenEmpty(
                              message: points.isEmpty
                                  ? 'Nenhum ponto de coleta está disponível no momento.'
                                  : 'Nenhum ponto encontrado. Tente outro nome ou bairro.',
                            ),
                          for (final point in filtered)
                            CollectionPointCard(
                              point: point,
                              selected: point.id == widget.selectedId,
                              onSelect: () => _select(point),
                            ),
                          if (!widget.selectionMode)
                            OutlinedButton.icon(
                              onPressed: () =>
                                  context.push('/solicitacoes/nova'),
                              icon: const Icon(Icons.home_outlined),
                              label: const Text(
                                'Prefere que busquem em casa? Agendar coleta',
                                textAlign: TextAlign.center,
                              ),
                            ),
                        ],
                      ),
                    ),
                  ),
                ),
              );
            },
          ),
    ),
    bottomNavigationBar: widget.selectionMode
        ? null
        : const CitizenNavigation(selectedIndex: -1),
    );
    return widget.selectionMode ? scaffold : AppBackScope(child: scaffold);
  }
}
