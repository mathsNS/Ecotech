import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';

import '../../core/api/api_exception.dart';
import '../../core/formatters/app_formatters.dart';
import '../../core/theme/app_colors.dart';
import '../../data/citizen/citizen_repository.dart';
import '../../data/citizen/citizen_data.dart';
import '../dashboard/dashboard_controller.dart';
import 'citizen_controller.dart';
import 'pontos_screen.dart';
import 'widgets/point_delivery_header.dart';
import 'widgets/citizen_states.dart';
import 'widgets/collection_progress.dart';
import 'widgets/collection_fields.dart';
import 'widgets/collection_tips.dart';

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
  final _actionsKey = GlobalKey();
  final _scroll = ScrollController();
  final _nome = TextEditingController();
  final _quantidadeInput = TextEditingController(text: '1');
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
  bool get _entregaPresencial => widget.tipoInicial == 'entrega_ponto';
  String _tipoDispositivo = 'celular';
  String _subcategoria = 'Smartphone';
  int _ano = 2020;
  int get _quantidade => int.tryParse(_quantidadeInput.text) ?? 0;
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
    _scroll.dispose();
    for (final controller in [
      _nome,
      _quantidadeInput,
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
  Widget build(BuildContext context) => PopScope(
    canPop: _etapa == 0 && !_enviando,
    onPopInvokedWithResult: (didPop, result) {
      if (!didPop && !_enviando && _etapa > 0) _voltar();
    },
    child: Scaffold(
      appBar: AppBar(
        leading: IconButton(
          tooltip: 'Voltar',
          onPressed: _enviando ? null : _voltar,
          icon: const Icon(Icons.arrow_back),
        ),
        backgroundColor: AppColors.surfaceSubtle,
        toolbarHeight: 40 + MediaQuery.textScalerOf(context).scale(36),
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              _tipoColeta == 'domiciliar'
                  ? 'COLETA DOMICILIAR'
                  : 'ENTREGA NO PONTO',
              style: const TextStyle(
                fontSize: 11,
                color: AppColors.primary,
                fontWeight: FontWeight.w900,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              _entregaPresencial
                  ? 'Descarte no ponto'
                  : 'Nova solicitação de descarte',
              maxLines: 3,
              softWrap: true,
              overflow: TextOverflow.visible,
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w900),
            ),
          ],
        ),
      ),
      body: SafeArea(
        child: Column(
          children: [
            Expanded(
              child: SingleChildScrollView(
                controller: _scroll,
                padding: const EdgeInsets.fromLTRB(16, 16, 16, 28),
                child: Center(
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 576),
                    child: AbsorbPointer(
                      absorbing: _enviando,
                      child: Form(
                        key: _formKey,
                        child: Column(
                          children: [
                            if (_entregaPresencial)
                              _resumoPonto()
                            else
                              CollectionProgress(
                                step: _etapa,
                                atCollectionPoint:
                                    _tipoColeta == 'entrega_ponto',
                              ),
                            const SizedBox(height: 24),
                            switch (_etapa) {
                              0 => _produto(),
                              1 => _entrega(),
                              _ => _agenda(),
                            },
                            const SizedBox(height: 20),
                            const CollectionTips(),
                          ],
                        ),
                      ),
                    ),
                  ),
                ),
              ),
            ),
            _acoes(),
          ],
        ),
      ),
    ),
  );

  Widget _acoes() => Container(
    key: _actionsKey,
    width: double.infinity,
    padding: const EdgeInsets.all(16),
    decoration: const BoxDecoration(
      color: Colors.white,
      border: Border(top: BorderSide(color: AppColors.border)),
    ),
    child: Center(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 576),
        child: LayoutBuilder(
          builder: (context, constraints) {
            final stacked =
                constraints.maxWidth < 360 &&
                MediaQuery.textScalerOf(context).scale(14) > 18;
            final back = OutlinedButton(
              onPressed: _enviando
                  ? null
                  : (_entregaPresencial && _etapa == 0
                        ? _trocarPonto
                        : _voltar),
              child: Text(
                _etapa == 0
                    ? (_entregaPresencial ? 'Trocar ponto' : 'Cancelar')
                    : 'Anterior',
                textAlign: TextAlign.center,
              ),
            );
            final next = ElevatedButton(
              onPressed: _enviando ? null : (_etapa == 2 ? _enviar : _avancar),
              child: _enviando
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Colors.white,
                      ),
                    )
                  : Text(
                      _etapa == 2
                          ? (_entregaPresencial
                                ? 'Solicitar entrega'
                                : 'Criar solicitação')
                          : 'Próximo',
                      textAlign: TextAlign.center,
                    ),
            );
            return stacked
                ? Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [next, const SizedBox(height: 8), back],
                  )
                : Row(
                    children: [
                      Expanded(child: back),
                      const SizedBox(width: 12),
                      Expanded(flex: 2, child: next),
                    ],
                  );
          },
        ),
      ),
    ),
  );

  Widget _produto() => _CardEtapa(
    key: const ValueKey(0),
    titulo: 'Informações do dispositivo',
    icon: Icons.phone_android_outlined,
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        CollectionField(
          'Tipo de dispositivo',
          child: DropdownButtonFormField<String>(
            isExpanded: true,
            initialValue: _tipoDispositivo,
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
        ),
        const SizedBox(height: 16),
        CollectionField(
          'Categoria específica',
          child: DropdownButtonFormField<String>(
            key: ValueKey(_tipoDispositivo),
            isExpanded: true,
            initialValue: _subcategoria,
            items: _subcategorias[_tipoDispositivo]!
                .map((item) => DropdownMenuItem(value: item, child: Text(item)))
                .toList(),
            onChanged: (value) => _subcategoria = value!,
          ),
        ),
        const SizedBox(height: 16),
        CollectionField(
          'Modelo ou nome',
          child: TextFormField(
            controller: _nome,
            textCapitalization: TextCapitalization.sentences,
            decoration: const InputDecoration(
              hintText: 'Ex.: Samsung Galaxy S20',
            ),
            validator: _obrigatorio,
          ),
        ),
        const SizedBox(height: 16),
        CheckboxListTile(
          contentPadding: EdgeInsets.zero,
          controlAffinity: ListTileControlAffinity.leading,
          value: _pesoDesconhecido,
          title: const Text('Não sei informar o peso'),
          subtitle: const Text('A empresa fará a pesagem no recebimento.'),
          onChanged: (value) => setState(() {
            _pesoDesconhecido = value ?? true;
            if (_pesoDesconhecido) _peso.clear();
          }),
        ),
        if (!_pesoDesconhecido) ...[
          CollectionField(
            'Peso aproximado por unidade (kg)',
            child: TextFormField(
              controller: _peso,
              keyboardType: const TextInputType.numberWithOptions(
                decimal: true,
              ),
              decoration: const InputDecoration(
                hintText: 'Ex.: 0,5',
                suffixText: 'kg',
              ),
              validator: (value) {
                final peso = double.tryParse(
                  (value ?? '').replaceAll(',', '.'),
                );
                return peso == null || !peso.isFinite || peso <= 0
                    ? 'Informe um peso válido.'
                    : null;
              },
            ),
          ),
          const SizedBox(height: 16),
        ],
        CollectionPair(
          first: CollectionField(
            'Ano de fabricação',
            child: DropdownButtonFormField<int>(
              isExpanded: true,
              initialValue: _ano,
              items: [
                for (var ano = DateTime.now().year; ano >= 1990; ano--)
                  DropdownMenuItem(value: ano, child: Text('$ano')),
              ],
              onChanged: (value) => _ano = value!,
            ),
          ),
          second: CollectionField(
            'Quantidade',
            child: TextFormField(
              controller: _quantidadeInput,
              keyboardType: TextInputType.number,
              validator: (value) =>
                  (int.tryParse(value ?? '') ?? 0) < 1 ? 'Mínimo 1.' : null,
            ),
          ),
        ),
        const SizedBox(height: 16),
        CollectionField(
          'Estado e observações do produto (opcional)',
          child: TextFormField(
            controller: _observacoes,
            maxLines: 3,
            decoration: const InputDecoration(
              hintText: 'Informe o estado do aparelho.',
            ),
          ),
        ),
        const SizedBox(height: 16),
        OutlinedButton.icon(
          onPressed: _selecionarFotos,
          style: OutlinedButton.styleFrom(
            backgroundColor: AppColors.surfaceSubtle,
            padding: const EdgeInsets.all(20),
          ),
          icon: const Icon(Icons.add_photo_alternate_outlined),
          label: Text(
            _fotos.isEmpty
                ? 'Adicionar fotos'
                : 'Trocar fotos (${_fotos.length}/5)',
          ),
        ),
        const SizedBox(height: 6),
        Text(
          'Opcional. Até 5 fotos JPG, PNG ou WebP, com 5 MB cada.',
          style: Theme.of(context).textTheme.bodySmall,
        ),
        for (final foto in _fotos)
          Row(
            children: [
              const Icon(
                Icons.image_outlined,
                size: 20,
                color: AppColors.primary,
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  foto.name,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              IconButton(
                tooltip: 'Remover ${foto.name}',
                onPressed: () => setState(() => _fotos.remove(foto)),
                icon: const Icon(Icons.close, size: 20),
              ),
            ],
          ),
        if (_entregaPresencial) ...[
          const SizedBox(height: 16),
          _campoContato(),
        ],
      ],
    ),
  );

  Widget _entrega() => _CardEtapa(
    key: const ValueKey(1),
    titulo: _tipoColeta == 'domiciliar'
        ? 'Endereço da coleta'
        : 'Local de entrega',
    icon: _tipoColeta == 'domiciliar'
        ? Icons.home_outlined
        : Icons.location_on_outlined,
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
        _campoContato(),
      ],
    ),
  );

  Widget _campoContato() => CollectionField(
    'Nome para contato',
    child: TextFormField(
      controller: _contato,
      textCapitalization: TextCapitalization.words,
      decoration: const InputDecoration(
        hintText: 'Quem acompanhará a entrega ou coleta?',
      ),
      validator: _obrigatorio,
    ),
  );

  PontoColetaData? get _pontoSelecionado => ref
      .read(pontosColetaProvider)
      .valueOrNull
      ?.where((point) => point.id == _pontoId)
      .firstOrNull;

  Widget _resumoPonto() => ref
      .watch(pontosColetaProvider)
      .when(
        loading: () => const LinearProgressIndicator(),
        error: (error, _) => CitizenError(
          error: error,
          onRetry: () => ref.invalidate(pontosColetaProvider),
        ),
        data: (_) => _pontoSelecionado == null
            ? const Text(
                'Ponto não encontrado. Toque em Trocar ponto para escolher outro.',
              )
            : PointDeliveryHeader(
                point: _pontoSelecionado!,
                scheduling: _etapa == 2,
              ),
      );

  Future<void> _trocarPonto() async {
    FocusScope.of(context).unfocus();
    final point = await Navigator.of(context).push<PontoColetaData>(
      MaterialPageRoute(
        builder: (_) => PontosScreen(selectionMode: true, selectedId: _pontoId),
      ),
    );
    if (!mounted || point == null) return;
    setState(() => _pontoId = point.id);
    _mudarEtapa(0);
  }

  Widget _selecaoPonto() => ref
      .watch(pontosColetaProvider)
      .when(
        loading: () => const CircularProgressIndicator(),
        error: (error, _) => Column(
          children: [
            const Text('Não foi possível carregar os pontos.'),
            TextButton(
              onPressed: () => ref.invalidate(pontosColetaProvider),
              child: const Text('Tentar novamente'),
            ),
          ],
        ),
        data: (pontos) => DropdownButtonFormField<String>(
          isExpanded: true,
          initialValue: pontos.any((p) => p.id == _pontoId) ? _pontoId : null,
          decoration: const InputDecoration(labelText: 'Ponto de coleta'),
          items: pontos
              .map(
                (ponto) => DropdownMenuItem(
                  value: ponto.id,
                  enabled: ponto.aceitaEntrega,
                  child: Text(ponto.nome, overflow: TextOverflow.ellipsis),
                ),
              )
              .toList(),
          onChanged: (value) => _pontoId = value,
          validator: (value) => value == null ? 'Selecione um ponto.' : null,
        ),
      );

  Widget _endereco() => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      CollectionPair(
        first: CollectionField(
          'CEP',
          child: TextFormField(
            controller: _cep,
            keyboardType: TextInputType.number,
            decoration: InputDecoration(
              hintText: '00000-000',
              suffixIcon: IconButton(
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
            validator: (value) =>
                (value ?? '').replaceAll(RegExp(r'\D'), '').length != 8
                ? 'CEP inválido.'
                : null,
          ),
        ),
        second: CollectionField(
          'Número',
          child: TextFormField(controller: _numero, validator: _obrigatorio),
        ),
      ),
      const SizedBox(height: 8),
      Text(
        'Busque pelo CEP ou preencha o endereço manualmente.',
        style: Theme.of(context).textTheme.bodySmall,
      ),
      const SizedBox(height: 16),
      CollectionField(
        'Endereço',
        child: TextFormField(
          controller: _logradouro,
          validator: _obrigatorio,
          textCapitalization: TextCapitalization.words,
          decoration: const InputDecoration(hintText: 'Rua ou avenida'),
        ),
      ),
      const SizedBox(height: 16),
      CollectionField(
        'Complemento (opcional)',
        child: TextFormField(
          controller: _complemento,
          decoration: const InputDecoration(
            hintText: 'Apartamento, bloco, casa…',
          ),
        ),
      ),
      const SizedBox(height: 16),
      CollectionPair(
        first: CollectionField(
          'Bairro',
          child: TextFormField(
            controller: _bairro,
            validator: _obrigatorio,
            textCapitalization: TextCapitalization.words,
          ),
        ),
        second: CollectionField(
          'Cidade',
          child: TextFormField(
            controller: _cidade,
            validator: _obrigatorio,
            textCapitalization: TextCapitalization.words,
          ),
        ),
      ),
      const SizedBox(height: 16),
      CollectionField(
        'UF',
        child: TextFormField(
          controller: _uf,
          maxLength: 2,
          textCapitalization: TextCapitalization.characters,
          decoration: const InputDecoration(
            hintText: 'Ex.: CE',
            counterText: '',
          ),
          validator: (value) =>
              RegExp(r'^[a-zA-Z]{2}$').hasMatch((value ?? '').trim())
              ? null
              : 'Informe a sigla do estado.',
        ),
      ),
      const SizedBox(height: 16),
      CollectionField(
        'Ponto de referência (opcional)',
        child: TextFormField(
          controller: _referencia,
          decoration: const InputDecoration(hintText: 'Ex.: próximo à praça'),
        ),
      ),
    ],
  );

  Widget _agenda() => _CardEtapa(
    key: const ValueKey(2),
    titulo: _entregaPresencial
        ? 'Horário e revisão da entrega'
        : 'Agendamento e revisão',
    icon: Icons.calendar_month_outlined,
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        ListTile(
          contentPadding: EdgeInsets.zero,
          leading: const Icon(Icons.calendar_today_outlined),
          title: Text(
            _entregaPresencial ? 'Dia da visita' : 'Data da entrega ou coleta',
          ),
          subtitle: Text(
            _data == null ? 'Selecione uma data' : AppFormatters.data(_data),
          ),
          trailing: const Icon(Icons.chevron_right),
          onTap: _selecionarData,
        ),
        CollectionPair(
          first: _Horario(
            label: 'Disponível a partir de',
            value: _inicio,
            onTap: () => _selecionarHorario(true),
          ),
          second: _Horario(
            label: 'Disponível até',
            value: _fim,
            onTap: () => _selecionarHorario(false),
          ),
        ),
        const SizedBox(height: 16),
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: AppColors.surfaceSubtle,
            borderRadius: BorderRadius.circular(16),
          ),
          child: Text(
            _tipoColeta == 'domiciliar'
                ? 'Esta é a sua disponibilidade. A coleta depende do aceite da empresa e da confirmação do agendamento.'
                : 'Confira a disponibilidade do ponto. Acompanhe a confirmação do agendamento nos detalhes da solicitação.',
            style: const TextStyle(color: AppColors.primaryDark),
          ),
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
        if (_tipoColeta == 'entrega_ponto' && _pontoSelecionado != null)
          _ResumoLinha(
            'Ponto',
            '${_pontoSelecionado!.nome}\n${_pontoSelecionado!.endereco}',
          ),
        if (_tipoColeta == 'domiciliar')
          _ResumoLinha(
            'Endereço',
            '${_logradouro.text}, ${_numero.text}\n'
                '${_bairro.text} · ${_cidade.text}/${_uf.text.toUpperCase()}',
          ),
        _ResumoLinha('Contato', _contato.text),
        if (_fotos.isNotEmpty)
          _ResumoLinha('Fotos', '${_fotos.length} anexada(s)'),
      ],
    ),
  );

  void _avancar() {
    if (_enviando || _etapa >= 2) return;
    if ((_entregaPresencial || _etapa == 1) && _tipoColeta == 'entrega_ponto') {
      if (_pontoSelecionado?.aceitaEntrega != true) {
        _mensagem('Selecione um ponto de coleta disponível.', erro: true);
        return;
      }
    }
    if (_formKey.currentState?.validate() != true) return;
    _mudarEtapa(_entregaPresencial ? 2 : _etapa + 1);
  }

  void _mudarEtapa(int etapa) {
    FocusScope.of(context).unfocus();
    setState(() => _etapa = etapa);
    if (_scroll.hasClients) _scroll.jumpTo(0);
  }

  void _voltar() {
    if (_enviando) return;
    if (_etapa > 0) {
      _mudarEtapa(_entregaPresencial ? 0 : _etapa - 1);
    } else if (context.canPop()) {
      context.pop();
    } else {
      context.go('/home');
    }
  }

  Future<void> _selecionarFotos() async {
    try {
      final selecionadas = await ImagePicker().pickMultiImage(imageQuality: 85);
      if (!mounted || selecionadas.isEmpty) return;
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
      if (mounted) setState(() => _fotos = selecionadas);
    } catch (_) {
      _mensagem(
        'Não foi possível abrir as fotos. Tente novamente.',
        erro: true,
      );
    }
  }

  Future<void> _buscarCep() async {
    if (_consultandoCep) return;
    final cepConsultado = _cep.text;
    if ((_cep.text.replaceAll(RegExp(r'\D'), '')).length != 8) {
      _mensagem('Informe um CEP válido.', erro: true);
      return;
    }
    setState(() => _consultandoCep = true);
    try {
      final endereco = await ref
          .read(citizenRepositoryProvider)
          .consultarCep(cepConsultado);
      if (!mounted || _cep.text != cepConsultado) return;
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
    final hoje = DateUtils.dateOnly(DateTime.now());
    final data = await showDatePicker(
      context: context,
      initialDate: _data != null && !_data!.isBefore(hoje)
          ? _data!
          : hoje.add(const Duration(days: 1)),
      firstDate: hoje,
      lastDate: DateTime(hoje.year + 1),
    );
    if (mounted && data != null) setState(() => _data = data);
  }

  Future<void> _selecionarHorario(bool inicio) async {
    final horario = await showTimePicker(
      context: context,
      initialTime: inicio
          ? _inicio ?? const TimeOfDay(hour: 9, minute: 0)
          : _fim ?? const TimeOfDay(hour: 11, minute: 0),
    );
    if (mounted && horario != null) {
      setState(() => inicio ? _inicio = horario : _fim = horario);
    }
  }

  Future<void> _enviar() async {
    if (_enviando) return;
    if (_tipoColeta == 'entrega_ponto' &&
        _pontoSelecionado?.aceitaEntrega != true) {
      _mensagem(
        'O ponto não está disponível. Escolha outro antes de enviar.',
        erro: true,
      );
      _mudarEtapa(_entregaPresencial ? 0 : 1);
      return;
    }
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
                  'uf': _uf.text.trim().toUpperCase(),
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
      if (!mounted) return;
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
    if (!mounted) return;
    final actions =
        _actionsKey.currentContext?.findRenderObject() as RenderBox?;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        behavior: SnackBarBehavior.floating,
        margin: EdgeInsets.fromLTRB(
          16,
          0,
          16,
          (actions?.size.height ?? 80) + 8,
        ),
        content: Text(texto),
        backgroundColor: erro ? AppColors.error : AppColors.success,
      ),
    );
  }
}

class _CardEtapa extends StatelessWidget {
  const _CardEtapa({
    required this.titulo,
    required this.child,
    this.icon,
    super.key,
  });
  final String titulo;
  final Widget child;
  final IconData? icon;
  @override
  Widget build(BuildContext context) => Card(
    margin: EdgeInsets.zero,
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(24),
      side: const BorderSide(color: AppColors.border),
    ),
    child: Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (icon != null) ...[
                Icon(icon, size: 22, color: AppColors.primary),
                const SizedBox(width: 10),
              ],
              Expanded(
                child: Text(
                  titulo,
                  style: Theme.of(context).textTheme.titleMedium,
                ),
              ),
            ],
          ),
          const SizedBox(height: 24),
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
    borderRadius: BorderRadius.circular(12),
    child: CollectionField(
      label,
      child: InputDecorator(
        decoration: const InputDecoration(
          suffixIcon: Icon(Icons.schedule, size: 20),
        ),
        child: Text(value?.format(context) ?? 'Selecionar'),
      ),
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
