import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/formatters/app_formatters.dart';
import '../../core/theme/app_colors.dart';
import '../../data/admin/admin_data.dart';
import '../communication/widgets/communication_actions.dart';
import '../company/widgets/company_states.dart';
import 'admin_controller.dart';
import 'widgets/admin_navigation.dart';

class DespachoAdminScreen extends ConsumerWidget {
  const DespachoAdminScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(despachoAdminProvider);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Diagnóstico de despacho'),
        actions: const [CommunicationActions()],
      ),
      bottomNavigationBar: const AdminNavigation(selectedIndex: 2),
      body: state.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => CompanyError(
          error: error,
          onRetry: () => ref.invalidate(despachoAdminProvider),
        ),
        data: (dados) => RefreshIndicator(
          onRefresh: () => ref.refresh(despachoAdminProvider.future),
          child: ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.fromLTRB(16, 14, 16, 30),
            children: [
              const _SomenteLeitura(),
              const SizedBox(height: 12),
              _MetricasDespacho(dados.metricas),
              const SizedBox(height: 16),
              _ResumoStatus(dados.resumo),
              const SizedBox(height: 12),
              _Pendentes(dados.pendentes),
              const SizedBox(height: 12),
              _Destinatarios(dados.destinatarios),
              const SizedBox(height: 12),
              _Atribuicoes(dados.atribuicoes),
            ],
          ),
        ),
      ),
    );
  }
}

class _SomenteLeitura extends StatelessWidget {
  const _SomenteLeitura();
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(14),
    decoration: BoxDecoration(
      color: AppColors.secondary,
      borderRadius: BorderRadius.circular(12),
    ),
    child: const Row(
      children: [
        Icon(Icons.visibility_outlined, color: AppColors.primary),
        SizedBox(width: 10),
        Expanded(
          child: Text(
            'Painel somente leitura com o diagnóstico das ofertas de coleta domiciliar.',
          ),
        ),
      ],
    ),
  );
}

class _MetricasDespacho extends StatelessWidget {
  const _MetricasDespacho(this.metricas);
  final Map<String, dynamic> metricas;

  @override
  Widget build(BuildContext context) {
    final itens = [
      ('Ofertadas', metricas['solicitacoes_ofertadas'] ?? 0),
      ('Aceitas', metricas['aceitas'] ?? 0),
      ('Taxa de aceite', '${_numero(metricas['taxa_aceite'])}%'),
      ('Taxa de recusa', '${_numero(metricas['taxa_recusa'])}%'),
      ('Min. até oferta', _numero(metricas['minutos_ate_primeira_oferta'])),
      ('Min. até aceite', _numero(metricas['minutos_ate_aceite'])),
      ('Média de rodadas', _numero(metricas['media_rodadas'])),
      ('Sem empresa', metricas['sem_empresa'] ?? 0),
      ('Conflitos', metricas['conflitos'] ?? 0),
      ('Falhas de endereço', metricas['falhas_geocodificacao'] ?? 0),
    ];
    return LayoutBuilder(
      builder: (context, constraints) {
        final largura = (constraints.maxWidth - 8) / 2;
        return Wrap(
          spacing: 8,
          runSpacing: 8,
          children: itens
              .map(
                (item) => Container(
                  width: largura,
                  padding: const EdgeInsets.all(13),
                  decoration: BoxDecoration(
                    color: AppColors.backgroundAlt,
                    border: Border.all(color: AppColors.border),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('${item.$2}', style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 18)),
                      const SizedBox(height: 3),
                      Text(item.$1, style: const TextStyle(fontSize: 11, color: AppColors.textLight)),
                    ],
                  ),
                ),
              )
              .toList(),
        );
      },
    );
  }

  static String _numero(dynamic valor) => AppFormatters.numero(valor, casas: 1);
}

class _ResumoStatus extends StatelessWidget {
  const _ResumoStatus(this.itens);
  final List<ResumoOfertaData> itens;

  @override
  Widget build(BuildContext context) => _Secao(
    titulo: 'Situação das ofertas',
    child: itens.isEmpty
        ? const Text('Nenhuma oferta registrada.')
        : Wrap(
            spacing: 8,
            runSpacing: 8,
            children: itens
                .map(
                  (item) => Chip(
                    avatar: CircleAvatar(child: Text('${item.total}')),
                    label: Text(_rotulo(item.status)),
                  ),
                )
                .toList(),
          ),
  );
}

class _Pendentes extends StatelessWidget {
  const _Pendentes(this.itens);
  final List<DespachoPendenteData> itens;

  @override
  Widget build(BuildContext context) => _Secao(
    titulo: 'Buscando empresa',
    child: itens.isEmpty
        ? const Text('Nenhuma solicitação aguardando empresa.')
        : Column(
            children: itens
                .map(
                  (item) => ListTile(
                    contentPadding: EdgeInsets.zero,
                    leading: const Icon(Icons.hourglass_top_outlined),
                    title: Text('#${item.id.substring(0, 8)}'),
                    subtitle: Text(AppFormatters.dataHoraTexto(item.dataCriacao)),
                    trailing: Text(
                      item.esgotadoEm == null ? 'Em andamento' : 'Sem empresa',
                      style: TextStyle(
                        color: item.esgotadoEm == null
                            ? AppColors.warning
                            : AppColors.textLight,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                )
                .toList(),
          ),
  );
}

class _Destinatarios extends StatelessWidget {
  const _Destinatarios(this.itens);
  final List<DestinatarioOfertaData> itens;

  @override
  Widget build(BuildContext context) => _Secao(
    titulo: 'Empresas alertadas',
    child: itens.isEmpty
        ? const Text('Nenhuma empresa alertada ainda.')
        : Column(
            children: itens
                .map(
                  (item) => ExpansionTile(
                    tilePadding: EdgeInsets.zero,
                    leading: const Icon(Icons.notifications_active_outlined),
                    title: Text(item.empresaNome),
                    subtitle: Text('${item.baseNome} · rodada ${item.rodada}'),
                    trailing: _Status(item.status),
                    children: [
                      _Dado('Solicitação', '#${item.solicitacaoId.substring(0, 8)}'),
                      _Dado('Alerta enviado', AppFormatters.dataHoraTexto(item.enviadaEm)),
                    ],
                  ),
                )
                .toList(),
          ),
  );
}

class _Atribuicoes extends StatelessWidget {
  const _Atribuicoes(this.itens);
  final List<AtribuicaoData> itens;

  @override
  Widget build(BuildContext context) => _Secao(
    titulo: 'Atribuições recentes',
    child: itens.isEmpty
        ? const Text('Nenhuma atribuição registrada.')
        : Column(
            children: itens
                .map(
                  (item) => ListTile(
                    contentPadding: EdgeInsets.zero,
                    leading: const Icon(Icons.assignment_turned_in_outlined),
                    title: Text(item.empresaNome),
                    subtitle: Text(
                      '#${item.id.substring(0, 8)} · ${item.totalOfertas} ofertas · ${item.rodadas} rodadas',
                    ),
                    trailing: Text(AppFormatters.dataHoraTexto(item.atribuidaEm)),
                  ),
                )
                .toList(),
          ),
  );
}

class _Secao extends StatelessWidget {
  const _Secao({required this.titulo, required this.child});
  final String titulo;
  final Widget child;
  @override
  Widget build(BuildContext context) => Card(
    margin: EdgeInsets.zero,
    child: Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(titulo, style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 10),
          child,
        ],
      ),
    ),
  );
}

class _Status extends StatelessWidget {
  const _Status(this.status);
  final String status;
  @override
  Widget build(BuildContext context) => Text(
    _rotulo(status),
    style: const TextStyle(fontSize: 11, color: AppColors.primary, fontWeight: FontWeight.w700),
  );
}

class _Dado extends StatelessWidget {
  const _Dado(this.rotulo, this.valor);
  final String rotulo;
  final String valor;
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: 7),
    child: Row(
      children: [
        Expanded(child: Text(rotulo)),
        Text(valor, style: const TextStyle(fontWeight: FontWeight.w600)),
      ],
    ),
  );
}

String _rotulo(String valor) => valor.replaceAll('_', ' ').toLowerCase();
