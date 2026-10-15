import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_exception.dart';
import '../../core/formatters/app_formatters.dart';
import '../../core/theme/app_colors.dart';
import '../../data/finance/finance_data.dart';
import '../../shared/widgets/app_back_button.dart';
import '../citizen/widgets/citizen_navigation.dart';
import '../communication/communication_controller.dart';
import '../communication/widgets/communication_actions.dart';
import '../company/widgets/company_states.dart';
import 'finance_controller.dart';
import 'widgets/wallet_balance_card.dart';

class CarteiraScreen extends ConsumerWidget {
  const CarteiraScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(carteiraProvider);
    return Scaffold(
      appBar: AppBar(
        leading: const AppBackButton(),
        title: const Text('Carteira'),
        backgroundColor: AppColors.surfaceSubtle,
        actions: const [CommunicationActions()],
      ),
      body: state.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => CompanyError(
          error: error,
          onRetry: () => ref.invalidate(carteiraProvider),
        ),
        data: (carteira) => RefreshIndicator(
          onRefresh: () => ref.refresh(carteiraProvider.future),
          child: ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
            children: [
              WalletBalanceCard(carteira),
              const SizedBox(height: 16),
              const Text(
                'Modo demonstrativo: os pedidos são registrados, sem transferência real de dinheiro.',
              ),
              const SizedBox(height: 12),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: carteira.saldo <= 0 || carteira.metodos.isEmpty
                      ? null
                      : () => _solicitarSaque(context, ref, carteira),
                  icon: const Icon(Icons.account_balance_wallet_outlined),
                  label: const Text('Solicitar saque'),
                ),
              ),
              const SizedBox(height: 22),
              Text(
                'Histórico de saques',
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: 8),
              if (carteira.saques.isEmpty)
                const Card(
                  child: Padding(
                    padding: EdgeInsets.all(18),
                    child: Text('Nenhum saque solicitado até o momento.'),
                  ),
                )
              else
                ...carteira.saques.map(_SaqueTile.new),
            ],
          ),
        ),
      ),
      bottomNavigationBar: const CitizenNavigation(selectedIndex: 2),
    );
  }

  Future<void> _solicitarSaque(
    BuildContext context,
    WidgetRef ref,
    CarteiraData carteira,
  ) async {
    final pedido = await showDialog<_PedidoSaque>(
      context: context,
      builder: (_) => _SaqueDialog(carteira),
    );
    if (pedido == null || !context.mounted) return;
    final confirmado = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Confirmar saque'),
        content: Text(
          'Deseja solicitar ${AppFormatters.moeda(pedido.valor)} via '
          '${pedido.metodoNome} para ${pedido.titular}?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext, false),
            child: const Text('Voltar'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(dialogContext, true),
            child: const Text('Confirmar'),
          ),
        ],
      ),
    );
    if (confirmado != true || !context.mounted) return;

    showDialog<void>(
      context: context,
      barrierDismissible: false,
      builder: (_) => const Center(child: CircularProgressIndicator()),
    );
    try {
      final resultado = await ref
          .read(financeRepositoryProvider)
          .solicitarSaque(
            valor: pedido.valor,
            metodo: pedido.metodo,
            titular: pedido.titular,
            idCliente: 'mobile-${DateTime.now().microsecondsSinceEpoch}',
          );
      ref.invalidate(carteiraProvider);
      ref.invalidate(notificacoesProvider);
      ref.invalidate(badgesProvider);
      if (!context.mounted) return;
      Navigator.of(context, rootNavigator: true).pop();
      await showDialog<void>(
        context: context,
        builder: (_) => _ReciboSaque(resultado.saque),
      );
    } catch (error) {
      if (!context.mounted) return;
      Navigator.of(context, rootNavigator: true).pop();
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(_mensagemErro(error))));
    }
  }

  static String _mensagemErro(Object error) => error is ApiException
      ? error.mensagem
      : 'Não foi possível solicitar o saque.';
}

class _SaqueTile extends StatelessWidget {
  const _SaqueTile(this.saque);

  final SaqueData saque;

  @override
  Widget build(BuildContext context) => Card(
    margin: const EdgeInsets.only(bottom: 8),
    child: ListTile(
      leading: const CircleAvatar(
        backgroundColor: AppColors.secondary,
        child: Icon(Icons.south_west, color: AppColors.primary),
      ),
      title: Text(
        AppFormatters.moeda(saque.valor),
        style: const TextStyle(fontWeight: FontWeight.w700),
      ),
      subtitle: Text(
        '${saque.metodo} · ${AppFormatters.dataHoraTexto(saque.dataHora)}',
      ),
      trailing: _StatusSaque(saque.status),
    ),
  );
}

class _StatusSaque extends StatelessWidget {
  const _StatusSaque(this.status);

  final String status;

  @override
  Widget build(BuildContext context) {
    final cancelado = status.toLowerCase() == 'cancelado';
    final finalizado = status.toLowerCase() == 'finalizado';
    final cor = cancelado
        ? AppColors.error
        : finalizado
        ? AppColors.success
        : AppColors.warning;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: cor.withValues(alpha: .12),
        borderRadius: BorderRadius.circular(15),
      ),
      child: Text(
        status.isEmpty ? 'Pendente' : status,
        style: TextStyle(color: cor, fontSize: 11, fontWeight: FontWeight.w700),
      ),
    );
  }
}

class _PedidoSaque {
  const _PedidoSaque({
    required this.valor,
    required this.metodo,
    required this.metodoNome,
    required this.titular,
  });

  final double valor;
  final String metodo;
  final String metodoNome;
  final String titular;
}

class _SaqueDialog extends StatefulWidget {
  const _SaqueDialog(this.carteira);

  final CarteiraData carteira;

  @override
  State<_SaqueDialog> createState() => _SaqueDialogState();
}

class _SaqueDialogState extends State<_SaqueDialog> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _titular;
  late final TextEditingController _valor;
  late String _metodo;

  @override
  void initState() {
    super.initState();
    _titular = TextEditingController(text: widget.carteira.titular.nome);
    _valor = TextEditingController(
      text: widget.carteira.saldo.toStringAsFixed(2).replaceAll('.', ','),
    );
    _metodo = widget.carteira.metodos.firstOrNull?.id ?? 'Pix';
  }

  @override
  void dispose() {
    _titular.dispose();
    _valor.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
    title: const Text('Solicitar saque'),
    content: Form(
      key: _formKey,
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextFormField(
              controller: _titular,
              textCapitalization: TextCapitalization.words,
              decoration: const InputDecoration(labelText: 'Titular'),
              validator: (value) => (value?.trim().length ?? 0) < 3
                  ? 'Informe o nome completo.'
                  : null,
            ),
            const SizedBox(height: 14),
            DropdownButtonFormField<String>(
              initialValue: _metodo,
              decoration: const InputDecoration(labelText: 'Método'),
              items: widget.carteira.metodos
                  .map(
                    (item) => DropdownMenuItem(
                      value: item.id,
                      child: Text(item.nome),
                    ),
                  )
                  .toList(),
              onChanged: (value) => setState(() => _metodo = value ?? _metodo),
            ),
            const SizedBox(height: 14),
            TextFormField(
              controller: _valor,
              keyboardType: const TextInputType.numberWithOptions(
                decimal: true,
              ),
              decoration: const InputDecoration(
                labelText: 'Valor do saque',
                prefixText: 'R\$ ',
              ),
              validator: (value) {
                final numero = double.tryParse(
                  (value ?? '').replaceAll(',', '.'),
                );
                if (numero == null || numero <= 0) {
                  return 'Informe um valor positivo.';
                }
                if (numero > widget.carteira.saldo) {
                  return 'O valor excede o saldo disponível.';
                }
                return null;
              },
            ),
            const SizedBox(height: 10),
            Text(
              'Saldo: ${AppFormatters.moeda(widget.carteira.saldo)}',
              style: Theme.of(context).textTheme.bodyMedium,
            ),
          ],
        ),
      ),
    ),
    actions: [
      TextButton(
        onPressed: () => Navigator.pop(context),
        child: const Text('Cancelar'),
      ),
      ElevatedButton(onPressed: _continuar, child: const Text('Continuar')),
    ],
  );

  void _continuar() {
    if (!_formKey.currentState!.validate()) return;
    final metodo = widget.carteira.metodos.firstWhere(
      (item) => item.id == _metodo,
      orElse: () => MetodoSaqueData(id: _metodo, nome: _metodo),
    );
    Navigator.pop(
      context,
      _PedidoSaque(
        valor: double.parse(_valor.text.replaceAll(',', '.')),
        metodo: metodo.id,
        metodoNome: metodo.nome,
        titular: _titular.text.trim(),
      ),
    );
  }
}

class _ReciboSaque extends StatelessWidget {
  const _ReciboSaque(this.saque);

  final SaqueData saque;

  @override
  Widget build(BuildContext context) => AlertDialog(
    icon: const Icon(Icons.check_circle, color: AppColors.success, size: 48),
    title: const Text('Saque solicitado'),
    content: Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(
          AppFormatters.moeda(saque.valor),
          style: Theme.of(context).textTheme.headlineSmall,
        ),
        const SizedBox(height: 8),
        Text('Método: ${saque.metodo}'),
        Text('Protocolo: ${saque.id}'),
        Text('Data: ${AppFormatters.dataHoraTexto(saque.dataHora)}'),
        const SizedBox(height: 8),
        const Text(
          'A solicitação ficará pendente até o processamento financeiro.',
        ),
      ],
    ),
    actions: [
      ElevatedButton(
        onPressed: () => Navigator.pop(context),
        child: const Text('Concluir'),
      ),
    ],
  );
}
