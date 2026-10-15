import 'package:flutter/material.dart';

import '../../../core/formatters/app_formatters.dart';
import '../../../data/finance/finance_data.dart';
import 'wallet_balance_card.dart';

class WithdrawalRequest {
  const WithdrawalRequest({
    required this.cents,
    required this.method,
    required this.holder,
  });
  final int cents;
  final MetodoSaqueData method;
  final String holder;
}

class WithdrawalForm extends StatefulWidget {
  const WithdrawalForm({
    required this.wallet,
    required this.onContinue,
    this.initial,
    super.key,
  });
  final CarteiraData wallet;
  final WithdrawalRequest? initial;
  final ValueChanged<WithdrawalRequest> onContinue;

  @override
  State<WithdrawalForm> createState() => _WithdrawalFormState();
}

class _WithdrawalFormState extends State<WithdrawalForm> {
  final _form = GlobalKey<FormState>();
  late final TextEditingController _amount;
  late final TextEditingController _holder;
  String? _method;
  int get _balance => (widget.wallet.saldo * 100).round();

  @override
  void initState() {
    super.initState();
    _amount = TextEditingController(
      text: _money(widget.initial?.cents ?? _balance),
    );
    _holder = TextEditingController(
      text: widget.initial?.holder ?? widget.wallet.titular.nome,
    );
    _method =
        widget.initial?.method.id ?? widget.wallet.metodos.firstOrNull?.id;
  }

  String _money(int cents) =>
      (cents / 100).toStringAsFixed(2).replaceAll('.', ',');

  int? _parse(String value) {
    final text = value.trim();
    if (!RegExp(r'^\d+([.,]\d{1,2})?$').hasMatch(text)) return null;
    final parts = text.replaceAll(',', '.').split('.');
    final reais = int.tryParse(parts.first);
    if (reais == null || reais > _balance) return null;
    return reais * 100 +
        (parts.length == 1 ? 0 : int.parse(parts[1].padRight(2, '0')));
  }

  @override
  void dispose() {
    _amount.dispose();
    _holder.dispose();
    super.dispose();
  }

  Widget _card(List<Widget> children) => Card(
    margin: const EdgeInsets.only(top: 20),
    child: Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: children,
      ),
    ),
  );

  @override
  Widget build(BuildContext context) => Form(
    key: _form,
    child: Column(
      children: [
        Expanded(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Center(
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 576),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    WalletBalanceCard(widget.wallet),
                    const SizedBox(height: 16),
                    const Text(
                      'Demonstração: registra o pedido, sem transferência de dinheiro.',
                    ),
                    _card([
                      Text(
                        'Quanto quer sacar?',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: 16),
                      TextFormField(
                        controller: _amount,
                        keyboardType: const TextInputType.numberWithOptions(
                          decimal: true,
                        ),
                        decoration: const InputDecoration(
                          labelText: 'Valor do saque',
                          prefixText: 'R\$ ',
                        ),
                        validator: (value) {
                          final cents = _parse(value ?? '');
                          if (cents == null || cents <= 0) {
                            return 'Informe um valor positivo com até 2 casas decimais.';
                          }
                          if (cents > _balance) {
                            return 'O valor excede o saldo disponível.';
                          }
                          return null;
                        },
                      ),
                      const SizedBox(height: 12),
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: [
                          for (final percent in [25, 50, 75, 100])
                            OutlinedButton(
                              onPressed: () => _amount.text = _money(
                                _balance * percent ~/ 100,
                              ),
                              child: Text(
                                percent == 100 ? 'Tudo' : '$percent%',
                              ),
                            ),
                        ],
                      ),
                    ]),
                    _card([
                      Text(
                        'Receber por',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: 12),
                      if (widget.wallet.metodos.isEmpty)
                        const Text('Nenhum método disponível no momento.')
                      else
                        Wrap(
                          spacing: 8,
                          runSpacing: 8,
                          children: [
                            for (final method in widget.wallet.metodos)
                              ChoiceChip(
                                label: Text(method.nome),
                                selected: method.id == _method,
                                onSelected: (_) =>
                                    setState(() => _method = method.id),
                              ),
                          ],
                        ),
                      const SizedBox(height: 16),
                      TextFormField(
                        controller: _holder,
                        textCapitalization: TextCapitalization.words,
                        decoration: const InputDecoration(labelText: 'Titular'),
                        validator: (value) => (value?.trim().length ?? 0) < 3
                            ? 'Informe o nome completo.'
                            : null,
                      ),
                      const SizedBox(height: 12),
                      const Text(
                        'Neste demonstrativo, não é necessário informar chave Pix ou dados bancários.',
                      ),
                    ]),
                    const SizedBox(height: 16),
                    Text(
                      'Saldo disponível: ${AppFormatters.moeda(widget.wallet.saldo)}',
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
        SafeArea(
          top: false,
          minimum: const EdgeInsets.all(16),
          child: SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: _method == null || _balance <= 0
                  ? null
                  : () {
                      if (!_form.currentState!.validate()) return;
                      FocusScope.of(context).unfocus();
                      widget.onContinue(
                        WithdrawalRequest(
                          cents: _parse(_amount.text)!,
                          method: widget.wallet.metodos.firstWhere(
                            (m) => m.id == _method,
                          ),
                          holder: _holder.text.trim(),
                        ),
                      );
                    },
              child: const Text('Revisar saque'),
            ),
          ),
        ),
      ],
    ),
  );
}
