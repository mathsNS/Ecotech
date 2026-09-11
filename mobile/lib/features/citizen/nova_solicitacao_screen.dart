import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';

import '../../core/api/api_exception.dart';
import '../../core/formatters/app_formatters.dart';
import '../../core/theme/app_colors.dart';
import '../../data/citizen/citizen_repository.dart';
import '../dashboard/dashboard_controller.dart';
import 'citizen_controller.dart';

class NovaSolicitacaoScreen extends ConsumerStatefulWidget {
  const NovaSolicitacaoScreen({
    this.tipoInicial,
    this.pontoIdInicial,
    super.key,
  });

  final String? tipoInicial;
  final String? pontoIdInicial;

  @override
  ConsumerState<NovaSolicitacaoScreen> createState() =>
      _NovaSolicitacaoScreenState();
}

class _NovaSolicitacaoScreenState extends ConsumerState<NovaSolicitacaoScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nome = TextEditingController();
  final _peso = TextEditingController();
  final _observacoes = TextEditingController();
  final _cep = TextEditingController();
  final _logradouro = TextEditingController();
  final _numero = TextEditingController();
  final _complemento = TextEditingController();
  final _bairro = TextEditingController();
  final _cidade = TextEditingController();
  final _uf = TextEditingController();
  final _referencia = TextEditingController();
  final _contato = TextEditingController();

  int _etapa = 0;
  String _tipoDispositivo = 'celular';
  String _subcategoria = 'Smartphone';
  int _ano = 2020;
  int _quantidade = 1;
  bool _pesoDesconhecido = true;
  late String _tipoColeta;
  String? _pontoId;
  DateTime? _data;
  TimeOfDay? _inicio;
  TimeOfDay? _fim;
  List<XFile> _fotos = [];
  bool _consultandoCep = false;
  bool _enviando = false;

  static const _subcategorias = {
    'celular': ['Smartphone', 'Tablet', 'Acessório móvel'],
    'computador': ['Notebook', 'Desktop', 'Monitor', 'Periférico'],
    'eletrodomestico': [
      'Televisor',
      'Geladeira',
      'Micro-ondas',
      'Eletroportátil',
    ],
  };

  @override
  void initState() {
    super.initState();
    _tipoColeta = widget.tipoInicial == 'entrega_ponto'
        ? 'entrega_ponto'
        : 'domiciliar';
    _pontoId = widget.pontoIdInicial;
  }

  @override
  void dispose() {
    for (final controller in [
      _nome,
      _peso,
      _observacoes,
      _cep,
      _logradouro,
      _numero,
      _complemento,
      _bairro,
      _cidade,
      _uf,
      _referencia,
      _contato,
    ]) {
      controller.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Nova solicitação')),
    body: Form(
      key: _formKey,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 28),
        children: [
          _Stepper(etapa: _etapa),
          const SizedBox(height: 18),
          AnimatedSwitcher(
            duration: const Duration(milliseconds: 180),
            child: switch (_etapa) {
              0 => _produto(),
              1 => _entrega(),
              _ => _agenda(),
            },
          ),
          const SizedBox(height: 20),
          Row(
            children: [
              if (_etapa > 0)
                Expanded(
                  child: OutlinedButton(
                    onPressed: _enviando
                        ? null
                        : () => setState(() => _etapa--),
                    child: const Text('Anterior'),
                  ),
                ),
              if (_etapa > 0) const SizedBox(width: 10),
              Expanded(
                child: ElevatedButton(
                  onPressed: _enviando
                      ? null
                      : (_etapa == 2 ? _enviar : _avancar),
                  child: _enviando
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : Text(_etapa == 2 ? 'Criar solicitação' : 'Próximo'),
                ),
              ),
            ],
          ),
        ],
      ),
    ),
  );

  Widget _produto() => _CardEtapa(
    key: const ValueKey(0),
    titulo: 'Informações do dispositivo',
    child: Column(
      children: [
        DropdownButtonFormField<String>(
          initialValue: _tipoDispositivo,
          decoration: const InputDecoration(labelText: 'Tipo de dispositivo'),
          items: const [
            DropdownMenuItem(
              value: 'celular',
              child: Text('Celular / Smartphone'),
            ),
            DropdownMenuItem(value: 'computador', child: Text('Computador')),
            DropdownMenuItem(
              value: 'eletrodomestico',
              child: Text('Eletrodoméstico'),
            ),
          ],
          onChanged: (value) => setState(() {
            _tipoDispositivo = value!;
            _subcategoria = _subcategorias[value]!.first;
          }),
        ),
        const SizedBox(height: 12),
        DropdownButtonFormField<String>(
          initialValue: _subcategoria,
          decoration: const InputDecoration(labelText: 'Categoria específica'),
          items: _subcategorias[_tipoDispositivo]!
              .map((item) => DropdownMenuItem(value: item, child: Text(item)))
              .toList(),
          onChanged: (value) => _subcategoria = value!,
        ),
        const SizedBox(height: 12),
        TextFormField(
          controller: _nome,
          decoration: const InputDecoration(labelText: 'Modelo ou nome'),
          validator: _obrigatorio,
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: DropdownButtonFormField<int>(
                initialValue: _ano,
                decoration: const InputDecoration(labelText: 'Ano'),
                items: [
                  for (var ano = DateTime.now().year; ano >= 1990; ano--)
                    DropdownMenuItem(value: ano, child: Text('$ano')),
                ],
                onChanged: (value) => _ano = value!,
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: TextFormField(
                initialValue: '1',
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(labelText: 'Quantidade'),
                onChanged: (value) => _quantidade = int.tryParse(value) ?? 0,
                validator: (_) => _quantidade < 1 ? 'Mínimo 1.' : null,
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        CheckboxListTile(
          contentPadding: EdgeInsets.zero,
          value: _pesoDesconhecido,
          title: const Text('Não sei informar o peso'),
          subtitle: const Text('A empresa fará a pesagem no recebimento.'),
          onChanged: (value) => setState(() {
            _pesoDesconhecido = value ?? true;
            if (_pesoDesconhecido) _peso.clear();
          }),
        ),
        if (!_pesoDesconhecido)
          TextFormField(
            controller: _peso,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            decoration: const InputDecoration(
              labelText: 'Peso aproximado por unidade (kg)',
            ),
            validator: (value) {
              final peso = double.tryParse((value ?? '').replaceAll(',', '.'));
              return peso == null || peso <= 0
                  ? 'Informe um peso válido.'
                  : null;
            },
          ),
        const SizedBox(height: 12),
        TextFormField(
          controller: _observacoes,
          maxLines: 2,
          decoration: const InputDecoration(
            labelText: 'Estado e observações do produto',
          ),
        ),
        const SizedBox(height: 14),
        OutlinedButton.icon(
          onPressed: _selecionarFotos,
          icon: const Icon(Icons.add_photo_alternate_outlined),
          label: Text(
            _fotos.isEmpty
                ? 'Adicionar fotos'
                : '${_fotos.length} foto(s) selecionada(s)',
          ),
        ),
        const SizedBox(height: 5),
        Text(
          'Até 5 fotos JPG, PNG ou WebP, com 5 MB cada.',
          style: Theme.of(context).textTheme.bodyMedium,
        ),
      ],
    ),
  );

  Widget _entrega() => _CardEtapa(
    key: const ValueKey(1),
    titulo: 'Forma de entrega',
    child: Column(
      children: [
        SegmentedButton<String>(
          segments: const [
            ButtonSegment(
              value: 'domiciliar',
              label: Text('Em casa'),
              icon: Icon(Icons.home_outlined),
            ),
            ButtonSegment(
              value: 'entrega_ponto',
              label: Text('No ponto'),
              icon: Icon(Icons.location_on_outlined),
            ),
          ],
          selected: {_tipoColeta},
          onSelectionChanged: (value) =>
              setState(() => _tipoColeta = value.first),
        ),
        const SizedBox(height: 16),
        if (_tipoColeta == 'entrega_ponto') _selecaoPonto() else _endereco(),
        const SizedBox(height: 12),
        TextFormField(
          controller: _contato,
          decoration: const InputDecoration(labelText: 'Nome para contato'),
          validator: _obrigatorio,
        ),
      ],
    ),
  );

  Widget _selecaoPonto() => ref
      .watch(pontosColetaProvider)
      .when(
        loading: () => const CircularProgressIndicator(),
        error: (error, _) =>
            Text('Não foi possível carregar os pontos: $error'),
        data: (pontos) => DropdownButtonFormField<String>(
          initialValue: pontos.any((p) => p.id == _pontoId) ? _pontoId : null,
          decoration: const InputDecoration(labelText: 'Ponto de coleta'),
          items: pontos
              .map(
                (ponto) => DropdownMenuItem(
                  value: ponto.id,
                  child: Text(ponto.nome, overflow: TextOverflow.ellipsis),
                ),
              )
              .toList(),
          onChanged: (value) => _pontoId = value,
          validator: (value) => value == null ? 'Selecione um ponto.' : null,
        ),
      );

  Widget _endereco() => Column(
    children: [
      Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: TextFormField(
              controller: _cep,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(labelText: 'CEP'),
              validator: (value) =>
                  (value ?? '').replaceAll(RegExp(r'\D'), '').length != 8
                  ? 'CEP inválido.'
                  : null,
            ),
          ),
          const SizedBox(width: 8),
          Padding(
            padding: const EdgeInsets.only(top: 4),
            child: IconButton.filledTonal(
              tooltip: 'Buscar CEP',
              onPressed: _consultandoCep ? null : _buscarCep,
              icon: _consultandoCep
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
        controller: _logradouro,
        decoration: const InputDecoration(labelText: 'Endereço'),
        validator: _obrigatorio,
      ),
      const SizedBox(height: 12),
      Row(
        children: [
          Expanded(
            child: TextFormField(
              controller: _numero,
              decoration: const InputDecoration(labelText: 'Número'),
              validator: _obrigatorio,
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: TextFormField(
              controller: _complemento,
              decoration: const InputDecoration(labelText: 'Complemento'),
            ),
          ),
        ],
      ),
      const SizedBox(height: 12),
      TextFormField(
        controller: _bairro,
        decoration: const InputDecoration(labelText: 'Bairro'),
        validator: _obrigatorio,
      ),
      const SizedBox(height: 12),
      Row(
        children: [
          Expanded(
            flex: 3,
            child: TextFormField(
              controller: _cidade,
              decoration: const InputDecoration(labelText: 'Cidade'),
              validator: _obrigatorio,
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: TextFormField(
              controller: _uf,
              maxLength: 2,
              decoration: const InputDecoration(
                labelText: 'UF',
                counterText: '',
              ),
              validator: _obrigatorio,
            ),
          ),
        ],
      ),
      const SizedBox(height: 12),
      TextFormField(
        controller: _referencia,
        decoration: const InputDecoration(labelText: 'Ponto de referência'),
      ),
    ],
  );

  Widget _agenda() => _CardEtapa(
    key: const ValueKey(2),
    titulo: 'Agendamento e revisão',
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        ListTile(
          contentPadding: EdgeInsets.zero,
          leading: const Icon(Icons.calendar_today_outlined),
          title: const Text('Data da entrega ou coleta'),
          subtitle: Text(
            _data == null ? 'Selecione uma data' : AppFormatters.data(_data),
          ),
          trailing: const Icon(Icons.chevron_right),
          onTap: _selecionarData,
        ),
        Row(
          children: [
            Expanded(
              child: _Horario(
                label: 'Disponível a partir de',
                value: _inicio,
                onTap: () => _selecionarHorario(true),
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: _Horario(
                label: 'Disponível até',
                value: _fim,
                onTap: () => _selecionarHorario(false),
              ),
            ),
          ],
        ),
        const Divider(height: 30),
        Text('Resumo', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 10),
        _ResumoLinha('Produto', '${_quantidade}x ${_nome.text}'),
        _ResumoLinha('Categoria', _subcategoria),
        _ResumoLinha(
          'Peso',
          _pesoDesconhecido
              ? 'Estimado pelo sistema'
              : '${_peso.text} kg por unidade',
        ),
        _ResumoLinha(
          'Entrega',
          _tipoColeta == 'domiciliar'
              ? 'Coleta domiciliar'
              : 'Entrega em ponto',
        ),
      ],
    ),
  );

  void _avancar() {
    if (_formKey.currentState?.validate() != true) return;
    setState(() => _etapa++);
  }

  Future<void> _selecionarFotos() async {
    final selecionadas = await ImagePicker().pickMultiImage(imageQuality: 85);
    if (selecionadas.isEmpty) return;
    if (selecionadas.length > 5) {
      _mensagem('Selecione no máximo 5 fotos.', erro: true);
      return;
    }
    for (final foto in selecionadas) {
      if (await foto.length() > 5 * 1024 * 1024) {
        _mensagem('Cada foto pode ter no máximo 5 MB.', erro: true);
        return;
      }
    }
    setState(() => _fotos = selecionadas);
  }

  Future<void> _buscarCep() async {
    if ((_cep.text.replaceAll(RegExp(r'\D'), '')).length != 8) {
      _mensagem('Informe um CEP válido.', erro: true);
      return;
    }
    setState(() => _consultandoCep = true);
    try {
      final endereco = await ref
          .read(citizenRepositoryProvider)
          .consultarCep(_cep.text);
      _logradouro.text = endereco.logradouro;
      _bairro.text = endereco.bairro;
      _cidade.text = endereco.cidade;
      _uf.text = endereco.uf;
    } catch (error) {
      _mensagem(
        error is ApiException
            ? error.mensagem
            : 'Não foi possível consultar o CEP.',
        erro: true,
      );
    } finally {
      if (mounted) setState(() => _consultandoCep = false);
    }
  }

  Future<void> _selecionarData() async {
    final hoje = DateTime.now();
    final data = await showDatePicker(
      context: context,
      initialDate: hoje.add(const Duration(days: 1)),
      firstDate: hoje,
      lastDate: DateTime(hoje.year + 1),
    );
    if (data != null) setState(() => _data = data);
  }

  Future<void> _selecionarHorario(bool inicio) async {
    final horario = await showTimePicker(
      context: context,
      initialTime: inicio
          ? const TimeOfDay(hour: 9, minute: 0)
          : const TimeOfDay(hour: 11, minute: 0),
    );
    if (horario != null) {
      setState(() => inicio ? _inicio = horario : _fim = horario);
    }
  }

  Future<void> _enviar() async {
    if (_data == null || _inicio == null || _fim == null) {
      _mensagem('Selecione a data e a janela de horário.', erro: true);
      return;
    }
    final inicioMinutos = _inicio!.hour * 60 + _inicio!.minute;
    final fimMinutos = _fim!.hour * 60 + _fim!.minute;
    if (fimMinutos <= inicioMinutos) {
      _mensagem('O horário final deve ser posterior ao inicial.', erro: true);
      return;
    }
    setState(() => _enviando = true);
    try {
      final dataIso =
          '${_data!.year}-${_data!.month.toString().padLeft(2, '0')}-${_data!.day.toString().padLeft(2, '0')}';
      String hora(TimeOfDay value) =>
          '${value.hour.toString().padLeft(2, '0')}:${value.minute.toString().padLeft(2, '0')}';
      final detalhes = await ref
          .read(citizenRepositoryProvider)
          .criarSolicitacao(
            NovaSolicitacaoData(
              campos: {
                'tipo_dispositivo': _tipoDispositivo,
                'subcategoria': _subcategoria,
                'nome': _nome.text.trim(),
                'ano_fabricacao': _ano,
                'quantidade': _quantidade,
                'peso_kg': _pesoDesconhecido ? '' : _peso.text.trim(),
                'observacoes': _observacoes.text.trim(),
                'tipo_coleta': _tipoColeta,
                if (_tipoColeta == 'entrega_ponto') 'ponto_id': _pontoId,
                if (_tipoColeta == 'domiciliar') ...{
                  'cep': _cep.text,
                  'logradouro': _logradouro.text,
                  'numero': _numero.text,
                  'complemento': _complemento.text,
                  'bairro': _bairro.text,
                  'cidade': _cidade.text,
                  'uf': _uf.text,
                  'referencia': _referencia.text,
                },
                'nome_contato': _contato.text,
                'data_coleta': dataIso,
                'horario_inicio': hora(_inicio!),
                'horario_fim': hora(_fim!),
              },
              fotos: _fotos,
            ),
          );
      ref.invalidate(solicitacoesProvider);
      ref.invalidate(dashboardControllerProvider);
      if (mounted) context.go('/solicitacoes/${detalhes.id}');
    } catch (error) {
      _mensagem(
        error is ApiException
            ? error.mensagem
            : 'Não foi possível criar a solicitação.',
        erro: true,
      );
    } finally {
      if (mounted) setState(() => _enviando = false);
    }
  }

  String? _obrigatorio(String? value) =>
      value == null || value.trim().isEmpty ? 'Campo obrigatório.' : null;

  void _mensagem(String texto, {bool erro = false}) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(texto),
        backgroundColor: erro ? AppColors.error : AppColors.success,
      ),
    );
  }
}

class _Stepper extends StatelessWidget {
  const _Stepper({required this.etapa});
  final int etapa;
  @override
  Widget build(BuildContext context) => Row(
    children: [
      for (var i = 0; i < 3; i++) ...[
        CircleAvatar(
          radius: 17,
          backgroundColor: i <= etapa ? AppColors.primary : AppColors.border,
          foregroundColor: i <= etapa ? Colors.white : AppColors.textLight,
          child: Text('${i + 1}'),
        ),
        if (i < 2)
          Expanded(
            child: Container(
              height: 2,
              color: i < etapa ? AppColors.primary : AppColors.border,
            ),
          ),
      ],
    ],
  );
}

class _CardEtapa extends StatelessWidget {
  const _CardEtapa({required this.titulo, required this.child, super.key});
  final String titulo;
  final Widget child;
  @override
  Widget build(BuildContext context) => Card(
    margin: EdgeInsets.zero,
    child: Padding(
      padding: const EdgeInsets.all(18),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(titulo, style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 16),
          child,
        ],
      ),
    ),
  );
}

class _Horario extends StatelessWidget {
  const _Horario({
    required this.label,
    required this.value,
    required this.onTap,
  });
  final String label;
  final TimeOfDay? value;
  final VoidCallback onTap;
  @override
  Widget build(BuildContext context) => InkWell(
    onTap: onTap,
    child: InputDecorator(
      decoration: InputDecoration(labelText: label),
      child: Text(value?.format(context) ?? 'Selecionar'),
    ),
  );
}

class _ResumoLinha extends StatelessWidget {
  const _ResumoLinha(this.label, this.value);
  final String label;
  final String value;
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: 8),
    child: Row(
      children: [
        SizedBox(
          width: 90,
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
