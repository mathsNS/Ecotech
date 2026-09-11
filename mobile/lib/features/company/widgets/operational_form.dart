import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_exception.dart';
import '../../../core/theme/app_colors.dart';
import '../company_controller.dart';

class OperationalForm extends ConsumerStatefulWidget {
  const OperationalForm({
    required this.title,
    required this.onSave,
    this.initialName = '',
    this.currentAddress,
    this.initialCapacity = 1000,
    this.initialRadius,
    this.initialHomeCollection = true,
    super.key,
  });

  final String title;
  final String initialName;
  final String? currentAddress;
  final double initialCapacity;
  final double? initialRadius;
  final bool initialHomeCollection;
  final Future<void> Function(Map<String, dynamic> data) onSave;

  @override
  ConsumerState<OperationalForm> createState() => _OperationalFormState();
}

class _OperationalFormState extends ConsumerState<OperationalForm> {
  final _key = GlobalKey<FormState>();
  late final TextEditingController _name;
  final _cep = TextEditingController();
  final _street = TextEditingController();
  final _number = TextEditingController();
  final _complement = TextEditingController();
  final _neighborhood = TextEditingController();
  final _city = TextEditingController();
  final _state = TextEditingController();
  late final TextEditingController _capacity;
  TextEditingController? _radius;
  late bool _homeCollection;
  bool _loadingCep = false;
  bool _saving = false;

  bool get _isEditing => widget.currentAddress != null;
  bool get _changingAddress => _cep.text.trim().isNotEmpty;

  @override
  void initState() {
    super.initState();
    _name = TextEditingController(text: widget.initialName);
    _capacity = TextEditingController(
      text: widget.initialCapacity.toStringAsFixed(1),
    );
    if (widget.initialRadius != null) {
      _radius = TextEditingController(
        text: widget.initialRadius!.toStringAsFixed(1),
      );
    }
    _homeCollection = widget.initialHomeCollection;
  }

  @override
  void dispose() {
    for (final controller in [
      _name,
      _cep,
      _street,
      _number,
      _complement,
      _neighborhood,
      _city,
      _state,
      _capacity,
      ?_radius,
    ]) {
      controller.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: Text(widget.title)),
    body: Form(
      key: _key,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
        children: [
          TextFormField(
            controller: _name,
            decoration: const InputDecoration(labelText: 'Nome'),
            validator: _required,
          ),
          if (_isEditing) ...[
            const SizedBox(height: 12),
            InputDecorator(
              decoration: const InputDecoration(labelText: 'Endereço atual'),
              child: Text(widget.currentAddress!),
            ),
            const SizedBox(height: 7),
            const Text(
              'Para alterar o endereço, informe um novo CEP e complete os campos abaixo.',
              style: TextStyle(color: AppColors.textLight, fontSize: 12),
            ),
          ],
          const SizedBox(height: 12),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: TextFormField(
                  controller: _cep,
                  keyboardType: TextInputType.number,
                  decoration: InputDecoration(
                    labelText: _isEditing ? 'Novo CEP (opcional)' : 'CEP',
                  ),
                  validator: (value) {
                    final digits = (value ?? '').replaceAll(RegExp(r'\D'), '');
                    if (_isEditing && digits.isEmpty) return null;
                    return digits.length == 8 ? null : 'Informe 8 dígitos.';
                  },
                ),
              ),
              const SizedBox(width: 8),
              Padding(
                padding: const EdgeInsets.only(top: 4),
                child: IconButton.filledTonal(
                  tooltip: 'Buscar CEP',
                  onPressed: _loadingCep ? null : _lookupCep,
                  icon: _loadingCep
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.search),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          TextFormField(
            controller: _street,
            decoration: const InputDecoration(labelText: 'Logradouro'),
            validator: _addressRequired,
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: TextFormField(
                  controller: _number,
                  decoration: const InputDecoration(labelText: 'Número'),
                  validator: _addressRequired,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: TextFormField(
                  controller: _complement,
                  decoration: const InputDecoration(labelText: 'Complemento'),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          TextFormField(
            controller: _neighborhood,
            decoration: const InputDecoration(labelText: 'Bairro'),
            validator: _addressRequired,
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                flex: 3,
                child: TextFormField(
                  controller: _city,
                  decoration: const InputDecoration(labelText: 'Cidade'),
                  validator: _addressRequired,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: TextFormField(
                  controller: _state,
                  maxLength: 2,
                  textCapitalization: TextCapitalization.characters,
                  decoration: const InputDecoration(
                    labelText: 'UF',
                    counterText: '',
                  ),
                  validator: _addressRequired,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          TextFormField(
            controller: _capacity,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            decoration: const InputDecoration(labelText: 'Capacidade (kg)'),
            validator: _positiveNumber,
          ),
          if (_radius != null) ...[
            const SizedBox(height: 12),
            TextFormField(
              controller: _radius,
              keyboardType: const TextInputType.numberWithOptions(
                decimal: true,
              ),
              decoration: const InputDecoration(
                labelText: 'Raio de atendimento (km)',
              ),
              validator: _positiveNumber,
            ),
            const SizedBox(height: 8),
            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              title: const Text('Realiza coleta domiciliar'),
              subtitle: const Text(
                'A base poderá receber oportunidades dentro do raio configurado.',
              ),
              value: _homeCollection,
              onChanged: (value) => setState(() => _homeCollection = value),
            ),
          ],
          const SizedBox(height: 20),
          ElevatedButton(
            onPressed: _saving ? null : _save,
            child: _saving
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      color: Colors.white,
                    ),
                  )
                : const Text('Salvar'),
          ),
        ],
      ),
    ),
  );

  Future<void> _lookupCep() async {
    final digits = _cep.text.replaceAll(RegExp(r'\D'), '');
    if (digits.length != 8) {
      _message('Informe um CEP válido.', error: true);
      return;
    }
    setState(() => _loadingCep = true);
    try {
      final data = await ref
          .read(companyRepositoryProvider)
          .consultarCep(digits);
      _street.text = data['logradouro'] as String? ?? '';
      _neighborhood.text = data['bairro'] as String? ?? '';
      _city.text = data['cidade'] as String? ?? '';
      _state.text = data['uf'] as String? ?? '';
    } catch (error) {
      _message(
        error is ApiException
            ? error.mensagem
            : 'Não foi possível consultar o CEP.',
        error: true,
      );
    } finally {
      if (mounted) setState(() => _loadingCep = false);
    }
  }

  Future<void> _save() async {
    if (_key.currentState?.validate() != true) return;
    setState(() => _saving = true);
    try {
      await widget.onSave({
        'nome': _name.text.trim(),
        'capacidade_kg': _numberValue(_capacity.text),
        if (_radius != null) 'raio_atendimento_km': _numberValue(_radius!.text),
        if (_radius != null) 'realiza_coleta_domiciliar': _homeCollection,
        if (!_isEditing || _changingAddress) ...{
          'cep': _cep.text,
          'logradouro': _street.text.trim(),
          'numero': _number.text.trim(),
          'complemento': _complement.text.trim(),
          'bairro': _neighborhood.text.trim(),
          'cidade': _city.text.trim(),
          'uf': _state.text.trim().toUpperCase(),
        },
      });
      if (mounted) Navigator.pop(context, true);
    } catch (error) {
      _message(
        error is ApiException ? error.mensagem : 'Não foi possível salvar.',
        error: true,
      );
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  String? _required(String? value) =>
      value == null || value.trim().isEmpty ? 'Campo obrigatório.' : null;

  String? _addressRequired(String? value) {
    if (_isEditing && !_changingAddress) return null;
    return _required(value);
  }

  String? _positiveNumber(String? value) {
    final number = _numberValue(value ?? '');
    return number <= 0 ? 'Informe um valor maior que zero.' : null;
  }

  double _numberValue(String value) =>
      double.tryParse(value.replaceAll(',', '.')) ?? 0;

  void _message(String text, {required bool error}) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(text),
        backgroundColor: error ? AppColors.error : AppColors.success,
      ),
    );
  }
}
