import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/formatters/app_formatters.dart';
import '../../core/theme/app_colors.dart';
import '../../data/citizen/citizen_data.dart';
import '../../shared/widgets/dashboard_widgets.dart';
import 'citizen_controller.dart';
import 'widgets/citizen_states.dart';

class SolicitacaoDetalhesScreen extends ConsumerWidget {
  const SolicitacaoDetalhesScreen({required this.id, super.key});
  final String id;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(solicitacaoDetalhesProvider(id));
    return Scaffold(
      appBar: AppBar(title: Text('Solicitação #${id.substring(0, 8)}')),
      body: state.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => CitizenError(
          error: error,
          onRetry: () => ref.invalidate(solicitacaoDetalhesProvider(id)),
        ),
        data: (dados) => RefreshIndicator(
          onRefresh: () => ref.refresh(solicitacaoDetalhesProvider(id).future),
          child: ListView(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
            children: [
              _Cabecalho(dados),
              const SizedBox(height: 12),
              _Pesos(dados),
              const SizedBox(height: 12),
              _Secao(
                titulo: 'Produtos',
                child: Column(
                  children: dados.itens.map(_ProdutoTile.new).toList(),
                ),
              ),
              if (dados.fotos.isNotEmpty) ...[
                const SizedBox(height: 12),
                _Secao(
                  titulo: 'Fotos do produto',
                  child: SizedBox(
                    height: 150,
                    child: ListView.separated(
                      scrollDirection: Axis.horizontal,
                      itemCount: dados.fotos.length,
                      separatorBuilder: (_, _) => const SizedBox(width: 10),
                      itemBuilder: (context, index) =>
                          _FotoProtegida(dados.fotos[index]),
                    ),
                  ),
                ),
              ],
              const SizedBox(height: 12),
              _Secao(
                titulo: 'Entrega e contato',
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _Dado('Forma de entrega', _tipoColeta(dados.tipoColeta)),
                    _Dado(
                      'Ponto de coleta',
                      dados.pontoColeta ?? 'Não se aplica',
                    ),
                    _Dado(
                      'Endereço',
                      dados.enderecoColeta ?? 'Liberado após atribuição',
                    ),
                    _Dado('Contato', dados.nomeContato ?? 'Não informado'),
                    _Dado(
                      'Agendamento',
                      AppFormatters.dataTexto(
                        dados.dataAgendamento ?? 'Não definido',
                      ),
                    ),
                    _Dado(
                      'Tratamento',
                      dados.metodoTratamento ?? 'Ainda não definido',
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 12),
              _Secao(
                titulo: 'Acompanhamento',
                child: dados.historico.isEmpty
                    ? const Text(
                        'A solicitação foi registrada e aguarda atualização.',
                      )
                    : Column(
                        children: dados.historico
                            .map(_HistoricoTile.new)
                            .toList(),
                      ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _tipoColeta(String? tipo) => tipo == 'entrega_ponto'
      ? 'Entrega em ponto de coleta'
      : 'Coleta domiciliar';
}

class _Cabecalho extends StatelessWidget {
  const _Cabecalho(this.dados);
  final SolicitacaoDetalhesData dados;
  @override
  Widget build(BuildContext context) => Card(
    margin: EdgeInsets.zero,
    child: Padding(
      padding: const EdgeInsets.all(18),
      child: Row(
        children: [
          Image.asset('assets/images/coleta.png', width: 52, height: 52),
          const SizedBox(width: 13),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                StatusBadge(dados.estado),
                const SizedBox(height: 8),
                Text(dados.empresa ?? 'Buscando empresa responsável'),
                Text(
                  AppFormatters.data(dados.dataCriacao),
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
              ],
            ),
          ),
        ],
      ),
    ),
  );
}

class _Pesos extends StatelessWidget {
  const _Pesos(this.dados);
  final SolicitacaoDetalhesData dados;
  @override
  Widget build(BuildContext context) => _Secao(
    titulo: 'Peso do material',
    child: Row(
      children: [
        Expanded(
          child: _PesoItem(
            'Estimado',
            '${AppFormatters.numero(dados.pesoEstimadoKg, casas: 2)} kg',
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: _PesoItem(
            'Informado por você',
            dados.pesoInformadoCidadao ? 'Sim' : 'Não',
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: _PesoItem(
            'Aferido pela empresa',
            dados.pesoConfirmadoKg == null
                ? 'Pendente'
                : '${AppFormatters.numero(dados.pesoConfirmadoKg, casas: 2)} kg',
          ),
        ),
      ],
    ),
  );
}

class _PesoItem extends StatelessWidget {
  const _PesoItem(this.label, this.value);
  final String label;
  final String value;
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(10),
    decoration: BoxDecoration(
      color: AppColors.secondary,
      borderRadius: BorderRadius.circular(10),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(value, style: const TextStyle(fontWeight: FontWeight.w700)),
        const SizedBox(height: 4),
        Text(
          label,
          style: const TextStyle(fontSize: 10, color: AppColors.textLight),
        ),
      ],
    ),
  );
}

class _ProdutoTile extends StatelessWidget {
  const _ProdutoTile(this.item);
  final ItemSolicitacaoData item;
  @override
  Widget build(BuildContext context) => ExpansionTile(
    tilePadding: EdgeInsets.zero,
    title: Text(item.nome),
    subtitle: Text('${item.quantidade} unidade(s) · ${item.subcategoria}'),
    children: [
      _Dado('Tipo', item.tipo),
      _Dado('Modelo', item.modelo ?? item.nome),
      _Dado(
        'Ano de fabricação',
        item.anoFabricacao?.toString() ?? 'Não informado',
      ),
      _Dado(
        'Peso unitário estimado',
        '${AppFormatters.numero(item.pesoUnitarioKg, casas: 2)} kg',
      ),
      if (item.observacoes?.isNotEmpty == true)
        _Dado('Observações', item.observacoes!),
    ],
  );
}

class _HistoricoTile extends StatelessWidget {
  const _HistoricoTile(this.item);
  final HistoricoSolicitacaoData item;
  @override
  Widget build(BuildContext context) => Row(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Container(
        margin: const EdgeInsets.only(top: 5),
        width: 10,
        height: 10,
        decoration: const BoxDecoration(
          color: AppColors.primary,
          shape: BoxShape.circle,
        ),
      ),
      const SizedBox(width: 10),
      Expanded(
        child: Padding(
          padding: const EdgeInsets.only(bottom: 14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(item.mensagem),
              Text(
                AppFormatters.dataHoraTexto(item.timestamp),
                style: Theme.of(context).textTheme.bodyMedium,
              ),
            ],
          ),
        ),
      ),
    ],
  );
}

class _FotoProtegida extends ConsumerWidget {
  const _FotoProtegida(this.foto);
  final FotoSolicitacaoData foto;
  @override
  Widget build(BuildContext context, WidgetRef ref) => FutureBuilder<Uint8List>(
    future: ref.read(citizenRepositoryProvider).baixarFoto(foto.url),
    builder: (context, snapshot) => Container(
      width: 190,
      clipBehavior: Clip.antiAlias,
      decoration: BoxDecoration(
        color: AppColors.backgroundAlt,
        borderRadius: BorderRadius.circular(10),
      ),
      child: snapshot.hasData
          ? Image.memory(snapshot.data!, fit: BoxFit.cover)
          : const Center(child: CircularProgressIndicator()),
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
      padding: const EdgeInsets.all(17),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(titulo, style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 12),
          child,
        ],
      ),
    ),
  );
}

class _Dado extends StatelessWidget {
  const _Dado(this.label, this.value);
  final String label;
  final String value;
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: 9),
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: 125,
          child: Text(label, style: Theme.of(context).textTheme.bodyMedium),
        ),
        Expanded(
          child: Text(
            value,
            style: const TextStyle(fontWeight: FontWeight.w600),
          ),
        ),
      ],
    ),
  );
}
