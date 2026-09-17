import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_exception.dart';
import '../../core/formatters/app_formatters.dart';
import '../../core/theme/app_colors.dart';
import '../../data/admin/admin_data.dart';
import '../communication/widgets/communication_actions.dart';
import '../company/widgets/company_states.dart';
import 'admin_controller.dart';
import 'widgets/admin_navigation.dart';

class UsuariosAdminScreen extends ConsumerStatefulWidget {
  const UsuariosAdminScreen({super.key});

  @override
  ConsumerState<UsuariosAdminScreen> createState() => _UsuariosAdminScreenState();
}

class _UsuariosAdminScreenState extends ConsumerState<UsuariosAdminScreen> {
  final _busca = TextEditingController();
  Timer? _debounce;
  String _tipo = 'todos';
  String _termo = '';
  int _pagina = 1;

  FiltroUsuariosAdmin get _filtro => FiltroUsuariosAdmin(
    tipo: _tipo,
    busca: _termo,
    pagina: _pagina,
  );

  @override
  void dispose() {
    _debounce?.cancel();
    _busca.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(usuariosAdminProvider(_filtro));
    return Scaffold(
      appBar: AppBar(
        title: const Text('Gestão de usuários'),
        actions: const [CommunicationActions()],
      ),
      bottomNavigationBar: const AdminNavigation(selectedIndex: 1),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _cadastrar,
        icon: const Icon(Icons.person_add_outlined),
        label: const Text('Cadastrar'),
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
            child: Column(
              children: [
                TextField(
                  controller: _busca,
                  decoration: const InputDecoration(
                    hintText: 'Buscar por nome, e-mail ou documento',
                    prefixIcon: Icon(Icons.search),
                  ),
                  onChanged: _buscar,
                ),
                const SizedBox(height: 8),
                SegmentedButton<String>(
                  segments: const [
                    ButtonSegment(value: 'todos', label: Text('Todos')),
                    ButtonSegment(value: 'cidadao', label: Text('Cidadãos')),
                    ButtonSegment(value: 'empresa', label: Text('Empresas')),
                  ],
                  selected: {_tipo},
                  onSelectionChanged: (valor) => setState(() {
                    _tipo = valor.first;
                    _pagina = 1;
                  }),
                ),
              ],
            ),
          ),
          Expanded(
            child: state.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (error, _) => CompanyError(
                error: error,
                onRetry: () => ref.invalidate(usuariosAdminProvider(_filtro)),
              ),
              data: (dados) => RefreshIndicator(
                onRefresh: () => ref.refresh(usuariosAdminProvider(_filtro).future),
                child: ListView(
                  physics: const AlwaysScrollableScrollPhysics(),
                  padding: const EdgeInsets.fromLTRB(16, 6, 16, 100),
                  children: [
                    _MetricasUsuarios(dados.metricas),
                    const SizedBox(height: 12),
                    if (dados.usuarios.isEmpty)
                      const CompanyEmpty(message: 'Nenhum usuário encontrado.')
                    else
                      ...dados.usuarios.map(
                        (usuario) => _UsuarioCard(
                          usuario,
                          onDesativar: usuario.ativo
                              ? () => _desativar(usuario)
                              : null,
                        ),
                      ),
                    if (dados.totalPaginas > 1)
                      _Paginacao(
                        pagina: dados.pagina,
                        total: dados.totalPaginas,
                        onAnterior: dados.pagina > 1
                            ? () => setState(() => _pagina--)
                            : null,
                        onProxima: dados.pagina < dados.totalPaginas
                            ? () => setState(() => _pagina++)
                            : null,
                      ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  void _buscar(String valor) {
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 400), () {
      if (!mounted) return;
      setState(() {
        _termo = valor.trim();
        _pagina = 1;
      });
    });
  }

  Future<void> _cadastrar() async {
    final dados = await showDialog<Map<String, dynamic>>(
      context: context,
      builder: (_) => const _CadastroUsuarioDialog(),
    );
    if (dados == null || !mounted) return;
    try {
      await ref.read(adminRepositoryProvider).cadastrarUsuario(dados);
      ref.invalidate(usuariosAdminProvider);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Usuário cadastrado com sucesso.')),
        );
      }
    } catch (error) {
      _erro(error);
    }
  }

  Future<void> _desativar(AdminUsuarioData usuario) async {
    final confirmar = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Desativar usuário'),
        content: Text(
          'Desativar ${usuario.nome}? O histórico será preservado e a conta não poderá mais entrar.',
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(dialogContext, false), child: const Text('Cancelar')),
          ElevatedButton(onPressed: () => Navigator.pop(dialogContext, true), child: const Text('Desativar')),
        ],
      ),
    );
    if (confirmar != true) return;
    try {
      await ref.read(adminRepositoryProvider).desativarUsuario(usuario.id);
      ref.invalidate(usuariosAdminProvider);
    } catch (error) {
      _erro(error);
    }
  }

  void _erro(Object error) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          error is ApiException ? error.mensagem : 'Não foi possível concluir a operação.',
        ),
      ),
    );
  }
}

class _MetricasUsuarios extends StatelessWidget {
  const _MetricasUsuarios(this.metricas);
  final AdminMetricasUsuariosData metricas;

  @override
  Widget build(BuildContext context) => Wrap(
    spacing: 8,
    runSpacing: 8,
    children: [
      _Metrica('Total', metricas.total, Icons.groups_outlined),
      _Metrica('Cidadãos', metricas.cidadaos, Icons.person_outline),
      _Metrica('Empresas', metricas.empresas, Icons.business_outlined),
      _Metrica('Inativos', metricas.inativos, Icons.person_off_outlined),
    ],
  );
}

class _Metrica extends StatelessWidget {
  const _Metrica(this.rotulo, this.valor, this.icone);
  final String rotulo;
  final int valor;
  final IconData icone;

  @override
  Widget build(BuildContext context) => Container(
    width: (MediaQuery.sizeOf(context).width - 48) / 2,
    padding: const EdgeInsets.all(13),
    decoration: BoxDecoration(
      color: AppColors.secondary,
      borderRadius: BorderRadius.circular(12),
    ),
    child: Row(
      children: [
        Icon(icone, color: AppColors.primary),
        const SizedBox(width: 9),
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('$valor', style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 18)),
            Text(rotulo, style: const TextStyle(fontSize: 11)),
          ],
        ),
      ],
    ),
  );
}

class _UsuarioCard extends StatelessWidget {
  const _UsuarioCard(this.usuario, {required this.onDesativar});
  final AdminUsuarioData usuario;
  final VoidCallback? onDesativar;

  @override
  Widget build(BuildContext context) => Card(
    margin: const EdgeInsets.only(bottom: 9),
    child: Padding(
      padding: const EdgeInsets.all(14),
      child: Row(
        children: [
          CircleAvatar(
            backgroundColor: usuario.ativo ? AppColors.secondary : AppColors.backgroundAlt,
            child: Icon(
              usuario.tipo == 'empresa' ? Icons.business_outlined : Icons.person_outline,
              color: usuario.ativo ? AppColors.primary : AppColors.textLight,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(child: Text(usuario.nome, style: const TextStyle(fontWeight: FontWeight.w700))),
                    _AtivoBadge(usuario.ativo),
                  ],
                ),
                const SizedBox(height: 3),
                Text(usuario.email),
                Text(usuario.documento),
                Text(
                  usuario.tipo == 'empresa'
                      ? '${usuario.plano ?? 'free'} · ${AppFormatters.numero(usuario.descartadoMesKg)} kg no mês'
                      : '${usuario.pontos ?? 0} pontos',
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
                Text(
                  'Cadastro: ${AppFormatters.dataHoraTexto(usuario.dataCadastro)}',
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
              ],
            ),
          ),
          if (onDesativar != null)
            IconButton(
              tooltip: 'Desativar',
              onPressed: onDesativar,
              icon: const Icon(Icons.person_off_outlined, color: AppColors.error),
            ),
        ],
      ),
    ),
  );
}

class _AtivoBadge extends StatelessWidget {
  const _AtivoBadge(this.ativo);
  final bool ativo;
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
    decoration: BoxDecoration(
      color: (ativo ? AppColors.success : AppColors.textLight).withValues(alpha: .12),
      borderRadius: BorderRadius.circular(12),
    ),
    child: Text(
      ativo ? 'Ativo' : 'Inativo',
      style: TextStyle(
        color: ativo ? AppColors.success : AppColors.textLight,
        fontSize: 10,
        fontWeight: FontWeight.w700,
      ),
    ),
  );
}

class _Paginacao extends StatelessWidget {
  const _Paginacao({
    required this.pagina,
    required this.total,
    this.onAnterior,
    this.onProxima,
  });
  final int pagina;
  final int total;
  final VoidCallback? onAnterior;
  final VoidCallback? onProxima;

  @override
  Widget build(BuildContext context) => Row(
    mainAxisAlignment: MainAxisAlignment.center,
    children: [
      IconButton(onPressed: onAnterior, icon: const Icon(Icons.chevron_left)),
      Text('$pagina de $total'),
      IconButton(onPressed: onProxima, icon: const Icon(Icons.chevron_right)),
    ],
  );
}

class _CadastroUsuarioDialog extends StatefulWidget {
  const _CadastroUsuarioDialog();
  @override
  State<_CadastroUsuarioDialog> createState() => _CadastroUsuarioDialogState();
}

class _CadastroUsuarioDialogState extends State<_CadastroUsuarioDialog> {
  final _form = GlobalKey<FormState>();
  final _nome = TextEditingController();
  final _email = TextEditingController();
  final _documento = TextEditingController();
  final _razao = TextEditingController();
  final _senha = TextEditingController();
  String _tipo = 'cidadao';

  @override
  void dispose() {
    _nome.dispose();
    _email.dispose();
    _documento.dispose();
    _razao.dispose();
    _senha.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
    title: const Text('Cadastrar usuário'),
    content: Form(
      key: _form,
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            SegmentedButton<String>(
              segments: const [
                ButtonSegment(value: 'cidadao', label: Text('Cidadão')),
                ButtonSegment(value: 'empresa', label: Text('Empresa')),
              ],
              selected: {_tipo},
              onSelectionChanged: (valor) => setState(() => _tipo = valor.first),
            ),
            const SizedBox(height: 12),
            TextFormField(controller: _nome, decoration: const InputDecoration(labelText: 'Nome'), validator: _obrigatorio),
            const SizedBox(height: 10),
            TextFormField(controller: _email, keyboardType: TextInputType.emailAddress, decoration: const InputDecoration(labelText: 'E-mail'), validator: _obrigatorio),
            const SizedBox(height: 10),
            TextFormField(
              controller: _documento,
              keyboardType: TextInputType.number,
              decoration: InputDecoration(labelText: _tipo == 'empresa' ? 'CNPJ' : 'CPF'),
              validator: _obrigatorio,
            ),
            if (_tipo == 'empresa') ...[
              const SizedBox(height: 10),
              TextFormField(controller: _razao, decoration: const InputDecoration(labelText: 'Razão social'), validator: _obrigatorio),
            ],
            const SizedBox(height: 10),
            TextFormField(
              controller: _senha,
              obscureText: true,
              decoration: const InputDecoration(labelText: 'Senha inicial'),
              validator: (value) => (value?.length ?? 0) < 6 ? 'Use pelo menos 6 caracteres.' : null,
            ),
          ],
        ),
      ),
    ),
    actions: [
      TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancelar')),
      ElevatedButton(onPressed: _salvar, child: const Text('Cadastrar')),
    ],
  );

  String? _obrigatorio(String? valor) =>
      (valor?.trim().isEmpty ?? true) ? 'Campo obrigatório.' : null;

  void _salvar() {
    if (!_form.currentState!.validate()) return;
    Navigator.pop(context, {
      'tipo': _tipo,
      'nome': _nome.text.trim(),
      'email': _email.text.trim(),
      'senha': _senha.text,
      if (_tipo == 'cidadao') 'cpf': _documento.text.trim(),
      if (_tipo == 'empresa') 'cnpj': _documento.text.trim(),
      if (_tipo == 'empresa') 'razao_social': _razao.text.trim(),
    });
  }
}
