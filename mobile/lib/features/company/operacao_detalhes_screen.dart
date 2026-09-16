import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:share_plus/share_plus.dart';

import '../../core/api/api_exception.dart';
import '../../core/formatters/app_formatters.dart';
import '../../core/theme/app_colors.dart';
import '../../data/citizen/citizen_data.dart';
import '../../data/company/operation_data.dart';
import '../../shared/widgets/dashboard_widgets.dart';
import '../communication/widgets/communication_actions.dart';
import 'company_controller.dart';
import 'widgets/company_states.dart';

class OperacaoDetalhesScreen extends ConsumerWidget {
  const OperacaoDetalhesScreen({required this.id, super.key});
  final String id;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(operacaoDetalhesProvider(id));
    return Scaffold(
      appBar: AppBar(
        title: Text('Operacao #${id.substring(0, 8)}'),
        actions: const [CommunicationActions()],
      ),
      body: state.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => CompanyError(
          error: error,
          onRetry: () => ref.invalidate(operacaoDetalhesProvider(id)),
        ),
        data: (dados) => RefreshIndicator(
          onRefresh: () => ref.refresh(operacaoDetalhesProvider(id).future),
          child: ListView(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
            children: [
              _Cabecalho(dados),
              const SizedBox(height: 12),
              _PesoCard(dados),
              const SizedBox(height: 12),
              _Secao(
                titulo: 'Produtos recebidos',
                child: Column(
                  children: dados.itens.map(_ProdutoTile.new).toList(),
                ),
              ),
              if (dados.fotos.isNotEmpty) ...[
                const SizedBox(height: 12),
                _Fotos(dados.fotos),
              ],
              const SizedBox(height: 12),
              _Logistica(dados),
              if (dados.avaliacao != null) ...[
                const SizedBox(height: 12),
                _AvaliacaoAtual(dados.avaliacao!),
              ],
              const SizedBox(height: 12),
              _Historico(dados.historico),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: () => context.push('/solicitacoes/$id/agenda'),
                      icon: const Icon(Icons.calendar_month_outlined),
                      label: const Text('Agenda'),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: ElevatedButton.icon(
                      onPressed: () => context.push('/conversas/$id'),
                      icon: const Icon(Icons.chat_bubble_outline),
                      label: const Text('Conversa'),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 18),
              _Acoes(dados: dados),
            ],
          ),
        ),
      ),
    );
  }
}

class _Cabecalho extends StatelessWidget {
  const _Cabecalho(this.dados);
  final OperacaoDetalhesData dados;

  @override
  Widget build(BuildContext context) => Card(
    margin: EdgeInsets.zero,
    child: Padding(
      padding: const EdgeInsets.all(17),
      child: Row(
        children: [
          const CircleAvatar(
            radius: 26,
            backgroundColor: AppColors.secondary,
            child: Icon(Icons.inventory_2_outlined, color: AppColors.primary),
          ),
          const SizedBox(width: 13),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  dados.cidadao,
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 6),
                StatusBadge(dados.estado),
                const SizedBox(height: 6),
                Text(
                  'Criada em ${AppFormatters.data(dados.dataCriacao)}',
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

class _PesoCard extends StatelessWidget {
  const _PesoCard(this.dados);
  final OperacaoDetalhesData dados;

  @override
  Widget build(BuildContext context) => _Secao(
    titulo: 'Conferencia de peso',
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(
              child: _Metrica(
                label: 'Estimado',
                valor:
                    '${AppFormatters.numero(dados.pesoEstimadoKg, casas: 2)} kg',
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: _Metrica(
                label: 'Aferido',
                valor: dados.pesoConfirmadoKg == null
                    ? 'Pendente'
                    : '${AppFormatters.numero(dados.pesoConfirmadoKg, casas: 2)} kg',
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: _Metrica(
                label: 'Diferenca',
                valor: dados.diferencaPesoPercentual == null
                    ? 'Pendente'
                    : '${dados.diferencaPesoPercentual! > 0 ? '+' : ''}'
                          '${AppFormatters.numero(dados.diferencaPesoPercentual, casas: 1)}%',
                alerta: dados.diferencaPesoRelevante,
              ),
            ),
          ],
        ),
        if (dados.pesoConfirmadoPor != null) ...[
          const SizedBox(height: 11),
          Text(
            'Aferido por ${dados.pesoConfirmadoPor} em '
            '${AppFormatters.dataHoraTexto(dados.pesoConfirmadoEm ?? '')}',
            style: Theme.of(context).textTheme.bodyMedium,
          ),
        ],
        if (dados.diferencaPesoRelevante) ...[
          const SizedBox(height: 11),
          const Text(
            'A diferenca em relacao a estimativa e superior a 20%. Confira o material antes de prosseguir.',
            style: TextStyle(
              color: AppColors.error,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ],
    ),
  );
}

class _Metrica extends StatelessWidget {
  const _Metrica({
    required this.label,
    required this.valor,
    this.alerta = false,
  });
  final String label;
  final String valor;
  final bool alerta;

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(10),
    decoration: BoxDecoration(
      color: alerta
          ? AppColors.error.withValues(alpha: 0.08)
          : AppColors.secondary,
      borderRadius: BorderRadius.circular(10),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          valor,
          maxLines: 1,
          style: TextStyle(
            fontWeight: FontWeight.w700,
            color: alerta ? AppColors.error : null,
          ),
        ),
        const SizedBox(height: 3),
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
  final ItemOperacaoData item;

  @override
  Widget build(BuildContext context) => ExpansionTile(
    tilePadding: EdgeInsets.zero,
    title: Text(item.nome),
    subtitle: Text('${item.quantidade} unidade(s) | ${item.subcategoria}'),
    children: [
      _Dado('Tipo', item.tipo),
      _Dado(
        'Modelo',
        item.modelo?.isNotEmpty == true ? item.modelo! : 'Nao informado',
      ),
      _Dado('Ano', item.anoFabricacao?.toString() ?? 'Nao informado'),
      _Dado(
        'Peso unitario',
        '${AppFormatters.numero(item.pesoUnitarioKg, casas: 2)} kg',
      ),
      if (item.observacoes?.isNotEmpty == true)
        _Dado('Observacoes', item.observacoes!),
      if (item.precos != null) ...[
        const Divider(),
        _Dado('Funcionando', AppFormatters.moeda(item.precos!.funcionando)),
        _Dado('Defeito leve', AppFormatters.moeda(item.precos!.defeitoLeve)),
        _Dado('Defeito grave', AppFormatters.moeda(item.precos!.defeitoGrave)),
        _Dado('Sucata', AppFormatters.moeda(item.precos!.sucata)),
      ],
    ],
  );
}

class _Fotos extends ConsumerWidget {
  const _Fotos(this.fotos);
  final List<FotoSolicitacaoData> fotos;

  @override
  Widget build(BuildContext context, WidgetRef ref) => _Secao(
    titulo: 'Fotos do produto',
    child: SizedBox(
      height: 155,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: fotos.length,
        separatorBuilder: (_, _) => const SizedBox(width: 10),
        itemBuilder: (context, index) => FutureBuilder<Uint8List>(
          future: ref
              .read(operationRepositoryProvider)
              .baixarFoto(fotos[index].url),
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
        ),
      ),
    ),
  );
}

class _Logistica extends StatelessWidget {
  const _Logistica(this.dados);
  final OperacaoDetalhesData dados;

  @override
  Widget build(BuildContext context) => _Secao(
    titulo: 'Coleta e atribuicao',
    child: Column(
      children: [
        _Dado('Empresa', dados.empresa ?? 'Nao definida'),
        _Dado('Base', dados.base?['nome'] as String? ?? 'Nao definida'),
        _Dado('Ponto', dados.pontoColeta ?? 'Coleta domiciliar'),
        _Dado('Endereco', dados.enderecoColeta ?? 'Nao informado'),
        _Dado('Contato', dados.nomeContato ?? 'Nao informado'),
        _Dado(
          'Agendamento',
          AppFormatters.dataHoraTexto(dados.dataAgendamento ?? 'Nao definido'),
        ),
        _Dado(
          'Atribuida em',
          AppFormatters.dataHoraTexto(dados.atribuidaEm ?? 'Nao informado'),
        ),
        _Dado('Tratamento', dados.metodoTratamento ?? 'Ainda nao definido'),
      ],
    ),
  );
}

class _AvaliacaoAtual extends StatelessWidget {
  const _AvaliacaoAtual(this.avaliacao);
  final Map<String, dynamic> avaliacao;

  @override
  Widget build(BuildContext context) => _Secao(
    titulo: 'Avaliacao registrada',
    child: Column(
      children: [
        _Dado('Estado do produto', _rotulo(avaliacao['estado_produto'])),
        _Dado(
          'Valor avaliado',
          AppFormatters.moeda(avaliacao['valor_proposto']),
        ),
        _Dado('Override', _rotulo(avaliacao['status_override'])),
        if ((avaliacao['justificativa_valor'] as String?)?.isNotEmpty == true)
          _Dado('Justificativa', avaliacao['justificativa_valor'] as String),
      ],
    ),
  );

  static String _rotulo(dynamic valor) =>
      (valor?.toString() ?? 'Nao informado').replaceAll('_', ' ');
}

class _Historico extends StatelessWidget {
  const _Historico(this.itens);
  final List<HistoricoSolicitacaoData> itens;

  @override
  Widget build(BuildContext context) => _Secao(
    titulo: 'Historico operacional',
    child: itens.isEmpty
        ? const Text('Nenhum evento operacional registrado.')
        : Column(
            children: itens
                .map(
                  (item) => ListTile(
                    contentPadding: EdgeInsets.zero,
                    leading: const Icon(Icons.check_circle_outline),
                    title: Text(item.mensagem),
                    subtitle: Text(AppFormatters.dataHoraTexto(item.timestamp)),
                  ),
                )
                .toList(),
          ),
  );
}

class _Acoes extends ConsumerStatefulWidget {
  const _Acoes({required this.dados});
  final OperacaoDetalhesData dados;

  @override
  ConsumerState<_Acoes> createState() => _AcoesState();
}

class _AcoesState extends ConsumerState<_Acoes> {
  bool _processando = false;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      OutlinedButton.icon(
        onPressed: _processando ? null : _compartilharMtr,
        icon: const Icon(Icons.picture_as_pdf_outlined),
        label: const Text('Baixar ou compartilhar MTR'),
      ),
      if (widget.dados.podeAvancar) ...[
        const SizedBox(height: 10),
        ElevatedButton.icon(
          onPressed: _processando ? null : _avancar,
          icon: const Icon(Icons.arrow_forward),
          label: Text(_rotuloAvanco(widget.dados)),
        ),
      ],
    ],
  );

  Future<void> _avancar() async {
    final payload = widget.dados.exigeAvaliacao
        ? await showDialog<_AvaliacaoPayload>(
            context: context,
            builder: (_) => const _AvaliacaoDialog(),
          )
        : widget.dados.exigePeso
        ? await showDialog<_AvaliacaoPayload>(
            context: context,
            builder: (_) => const _PesoDialog(),
          )
        : const _AvaliacaoPayload();
    if (payload == null || !mounted) return;
    setState(() => _processando = true);
    try {
      await ref
          .read(operationRepositoryProvider)
          .avancar(
            widget.dados.id,
            pesoKg: payload.peso,
            metodo: payload.metodo,
            estadoProduto: payload.estadoProduto,
            valorProposto: payload.valor,
            justificativa: payload.justificativa,
          );
      ref.invalidate(operacaoDetalhesProvider(widget.dados.id));
      ref.invalidate(operacoesEmpresaProvider);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Operacao atualizada com sucesso.')),
        );
      }
    } catch (error) {
      _erro(error);
    } finally {
      if (mounted) setState(() => _processando = false);
    }
  }

  Future<void> _compartilharMtr() async {
    setState(() => _processando = true);
    try {
      final bytes = await ref
          .read(operationRepositoryProvider)
          .baixarMtr(widget.dados.id);
      if (!mounted) return;
      final box = context.findRenderObject() as RenderBox?;
      await SharePlus.instance.share(
        ShareParams(
          title: 'MTR EcoTech',
          files: [XFile.fromData(bytes, mimeType: 'application/pdf')],
          fileNameOverrides: ['MTR-${widget.dados.id.substring(0, 8)}.pdf'],
          sharePositionOrigin: box == null
              ? null
              : box.localToGlobal(Offset.zero) & box.size,
        ),
      );
    } catch (error) {
      _erro(error);
    } finally {
      if (mounted) setState(() => _processando = false);
    }
  }

  void _erro(Object error) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          error is ApiException
              ? error.mensagem
              : 'Nao foi possivel concluir a operacao.',
        ),
        backgroundColor: AppColors.error,
      ),
    );
  }

  static String _rotuloAvanco(OperacaoDetalhesData dados) {
    if (dados.exigePeso) return 'Confirmar recebimento e peso';
    if (dados.exigeAvaliacao) return 'Avaliar e finalizar';
    return 'Avancar operacao';
  }
}

class _AvaliacaoPayload {
  const _AvaliacaoPayload({
    this.peso,
    this.metodo,
    this.estadoProduto,
    this.valor,
    this.justificativa = '',
  });
  final double? peso;
  final String? metodo;
  final String? estadoProduto;
  final double? valor;
  final String justificativa;
}

class _PesoDialog extends StatefulWidget {
  const _PesoDialog();

  @override
  State<_PesoDialog> createState() => _PesoDialogState();
}

class _PesoDialogState extends State<_PesoDialog> {
  final _controller = TextEditingController();
  String? _erro;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
    title: const Text('Confirmar recebimento'),
    content: TextField(
      controller: _controller,
      keyboardType: const TextInputType.numberWithOptions(decimal: true),
      decoration: InputDecoration(
        labelText: 'Peso aferido (kg)',
        errorText: _erro,
      ),
    ),
    actions: [
      TextButton(
        onPressed: () => Navigator.pop(context),
        child: const Text('Cancelar'),
      ),
      ElevatedButton(onPressed: _confirmar, child: const Text('Confirmar')),
    ],
  );

  void _confirmar() {
    final peso = double.tryParse(_controller.text.replaceAll(',', '.'));
    if (peso == null || peso <= 0) {
      setState(() => _erro = 'Informe um peso maior que zero');
      return;
    }
    Navigator.pop(context, _AvaliacaoPayload(peso: peso));
  }
}

class _AvaliacaoDialog extends StatefulWidget {
  const _AvaliacaoDialog();

  @override
  State<_AvaliacaoDialog> createState() => _AvaliacaoDialogState();
}

class _AvaliacaoDialogState extends State<_AvaliacaoDialog> {
  String _estado = 'funcionando';
  String _metodo = 'reciclagem';
  final _valor = TextEditingController();
  final _justificativa = TextEditingController();
  String? _erro;

  @override
  void dispose() {
    _valor.dispose();
    _justificativa.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
    title: const Text('Avaliar material'),
    content: SingleChildScrollView(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          DropdownButtonFormField<String>(
            initialValue: _estado,
            decoration: const InputDecoration(labelText: 'Estado do produto'),
            items: const [
              DropdownMenuItem(
                value: 'funcionando',
                child: Text('Funcionando'),
              ),
              DropdownMenuItem(
                value: 'defeito_leve',
                child: Text('Defeito leve'),
              ),
              DropdownMenuItem(
                value: 'defeito_grave',
                child: Text('Defeito grave'),
              ),
              DropdownMenuItem(value: 'sucata', child: Text('Sucata')),
            ],
            onChanged: (value) => setState(() => _estado = value!),
          ),
          const SizedBox(height: 12),
          DropdownButtonFormField<String>(
            initialValue: _metodo,
            decoration: const InputDecoration(labelText: 'Tratamento'),
            items: const [
              DropdownMenuItem(value: 'reciclagem', child: Text('Reciclagem')),
              DropdownMenuItem(value: 'reuso', child: Text('Reuso')),
              DropdownMenuItem(
                value: 'descarte_controlado',
                child: Text('Descarte controlado'),
              ),
            ],
            onChanged: (value) => setState(() => _metodo = value!),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _valor,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            decoration: const InputDecoration(
              labelText: 'Valor por item (opcional)',
              helperText: 'Em branco usa a tabela de precos',
            ),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _justificativa,
            maxLines: 3,
            decoration: InputDecoration(
              labelText: 'Justificativa do valor',
              errorText: _erro,
            ),
          ),
        ],
      ),
    ),
    actions: [
      TextButton(
        onPressed: () => Navigator.pop(context),
        child: const Text('Cancelar'),
      ),
      ElevatedButton(onPressed: _confirmar, child: const Text('Finalizar')),
    ],
  );

  void _confirmar() {
    final textoValor = _valor.text.trim().replaceAll(',', '.');
    final valor = textoValor.isEmpty ? null : double.tryParse(textoValor);
    if (textoValor.isNotEmpty && (valor == null || valor < 0)) {
      setState(() => _erro = 'Informe um valor valido');
      return;
    }
    Navigator.pop(
      context,
      _AvaliacaoPayload(
        metodo: _metodo,
        estadoProduto: _estado,
        valor: valor,
        justificativa: _justificativa.text.trim(),
      ),
    );
  }
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
          width: 115,
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
