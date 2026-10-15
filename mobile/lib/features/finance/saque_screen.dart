import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_exception.dart';
import '../../core/formatters/app_formatters.dart';
import '../../core/theme/app_colors.dart';
import '../../data/finance/finance_data.dart';
import '../communication/communication_controller.dart';
import 'finance_controller.dart';
import 'widgets/withdrawal_form.dart';
import 'widgets/withdrawal_receipt.dart';

class SaqueScreen extends ConsumerStatefulWidget {
  const SaqueScreen({required this.wallet, super.key});
  final CarteiraData wallet;

  @override
  ConsumerState<SaqueScreen> createState() => _SaqueScreenState();
}

class _SaqueScreenState extends ConsumerState<SaqueScreen> {
  final _requestId = 'mobile-${DateTime.now().microsecondsSinceEpoch}';
  WithdrawalRequest? _request;
  SaqueData? _result;
  bool _review = false;
  bool _sending = false;
  String? _error;

  void _back() {
    if (_sending) return;
    if (_review && _result == null) {
      setState(() {
        _review = false;
        _error = null;
      });
    } else {
      Navigator.of(context).pop();
    }
  }

  Future<void> _submit() async {
    if (_sending || _result != null || _request == null) return;
    final request = _request!;
    setState(() {
      _sending = true;
      _error = null;
    });
    try {
      final result = await ref
          .read(financeRepositoryProvider)
          .solicitarSaque(
            valor: request.cents / 100,
            metodo: request.method.id,
            titular: request.holder,
            idCliente: _requestId,
          );
      if (!mounted) return;
      ref.invalidate(carteiraProvider);
      ref.invalidate(notificacoesProvider);
      ref.invalidate(badgesProvider);
      setState(() => _result = result.saque);
    } catch (error) {
      if (mounted) {
        setState(
          () => _error = error is ApiException
              ? error.mensagem
              : 'Não foi possível registrar o pedido. Tente novamente.',
        );
      }
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  @override
  Widget build(BuildContext context) => PopScope(
    canPop: !_sending && (!_review || _result != null),
    onPopInvokedWithResult: (didPop, _) {
      if (!didPop && !_sending) _back();
    },
    child: Scaffold(
      appBar: AppBar(
        backgroundColor: AppColors.surfaceSubtle,
        leading: IconButton(
          tooltip: 'Voltar',
          onPressed: _sending ? null : _back,
          icon: const Icon(Icons.arrow_back),
        ),
        title: const Text(
          'Saque demonstrativo',
          maxLines: 2,
          softWrap: true,
          style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900),
        ),
        toolbarHeight: 32 + MediaQuery.textScalerOf(context).scale(24),
      ),
      body: !_review
          ? WithdrawalForm(
              wallet: widget.wallet,
              initial: _request,
              onContinue: (request) => setState(() {
                _request = request;
                _review = true;
              }),
            )
          : Column(
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
                            if (_result != null)
                              WithdrawalReceipt(_result!)
                            else
                              Card(
                                child: Padding(
                                  padding: const EdgeInsets.all(24),
                                  child: Column(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.stretch,
                                    children: [
                                      Text(
                                        'Revise seu pedido',
                                        style: Theme.of(context)
                                            .textTheme
                                            .titleLarge,
                                      ),
                                      const SizedBox(height: 24),
                                      Text(
                                        AppFormatters.moeda(
                                          _request!.cents / 100,
                                        ),
                                        style: Theme.of(context)
                                            .textTheme
                                            .headlineMedium,
                                      ),
                                      const SizedBox(height: 16),
                                      Text('Método: ${_request!.method.nome}'),
                                      Text('Titular: ${_request!.holder}'),
                                      const Divider(height: 32),
                                      const Text(
                                        'O pedido será registrado no histórico da carteira. '
                                        'Esta demonstração não transfere dinheiro.',
                                      ),
                                    ],
                                  ),
                                ),
                              ),
                            if (_error != null)
                              Padding(
                                padding: const EdgeInsets.all(16),
                                child: Semantics(
                                  liveRegion: true,
                                  child: Text(
                                    _error!,
                                    style: const TextStyle(
                                      color: AppColors.error,
                                    ),
                                  ),
                                ),
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
                      onPressed: _sending
                          ? null
                          : _result != null
                          ? _back
                          : _submit,
                      child: _sending
                          ? const SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : Text(
                              _result != null
                                  ? 'Voltar à carteira'
                                  : 'Confirmar pedido',
                            ),
                    ),
                  ),
                ),
              ],
            ),
    ),
  );
}
