import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_colors.dart';
import 'auth_controller.dart';

class CadastroScreen extends ConsumerStatefulWidget {
  const CadastroScreen({super.key});

  @override
  ConsumerState<CadastroScreen> createState() => _CadastroScreenState();
}

class _CadastroScreenState extends ConsumerState<CadastroScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nomeController = TextEditingController();
  final _emailController = TextEditingController();
  final _cpfController = TextEditingController();
  final _cnpjController = TextEditingController();
  final _razaoSocialController = TextEditingController();
  final _senhaController = TextEditingController();
  final _senhaConfirmacaoController = TextEditingController();
  bool _isCidadao = true;
  bool _carregando = false;

  @override
  void dispose() {
    _nomeController.dispose();
    _emailController.dispose();
    _cpfController.dispose();
    _cnpjController.dispose();
    _razaoSocialController.dispose();
    _senhaController.dispose();
    _senhaConfirmacaoController.dispose();
    super.dispose();
  }

  Future<void> _criarConta() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _carregando = true);
    await ref.read(authControllerProvider.notifier).registrar(
          tipo: _isCidadao ? 'cidadao' : 'empresa',
          nome: _nomeController.text.trim(),
          email: _emailController.text.trim(),
          senha: _senhaController.text,
          senhaConfirmacao: _senhaConfirmacaoController.text,
          cpf: _isCidadao ? _cpfController.text.trim() : null,
          cnpj: _isCidadao ? null : _cnpjController.text.trim(),
          razaoSocial: _isCidadao ? null : _razaoSocialController.text.trim(),
        );
    if (!mounted) return;
    setState(() => _carregando = false);

    final estado = ref.read(authControllerProvider);
    estado.whenOrNull(
      data: (usuario) {
        if (usuario != null) context.go('/home');
      },
      error: (erro, _) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(erro.toString()), backgroundColor: AppColors.error),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Criar conta')),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 420),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Text(
                      'Selecione o tipo de conta para começar',
                      style: Theme.of(context).textTheme.bodyMedium,
                    ),
                    const SizedBox(height: 16),
                    _seletorDeTipo(),
                    const SizedBox(height: 16),
                    TextFormField(
                      controller: _nomeController,
                      decoration: const InputDecoration(labelText: 'Nome completo'),
                      validator: _obrigatorio,
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: _emailController,
                      decoration: const InputDecoration(labelText: 'E-mail'),
                      keyboardType: TextInputType.emailAddress,
                      validator: _obrigatorio,
                    ),
                    const SizedBox(height: 12),
                    if (_isCidadao)
                      TextFormField(
                        controller: _cpfController,
                        decoration: const InputDecoration(
                          labelText: 'CPF',
                          hintText: '000.000.000-00',
                        ),
                        validator: _obrigatorio,
                      )
                    else ...[
                      TextFormField(
                        controller: _cnpjController,
                        decoration: const InputDecoration(
                          labelText: 'CNPJ',
                          hintText: '00.000.000/0000-00',
                        ),
                        validator: _obrigatorio,
                      ),
                      const SizedBox(height: 12),
                      TextFormField(
                        controller: _razaoSocialController,
                        decoration: const InputDecoration(labelText: 'Razão social'),
                        validator: _obrigatorio,
                      ),
                    ],
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: _senhaController,
                      decoration: const InputDecoration(
                        labelText: 'Senha',
                        helperText: 'Mínimo de 6 caracteres',
                      ),
                      obscureText: true,
                      validator: _obrigatorio,
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: _senhaConfirmacaoController,
                      decoration: const InputDecoration(labelText: 'Confirmar senha'),
                      obscureText: true,
                      validator: _obrigatorio,
                    ),
                    const SizedBox(height: 24),
                    ElevatedButton(
                      onPressed: _carregando ? null : _criarConta,
                      child: _carregando
                          ? const SizedBox(
                              height: 20,
                              width: 20,
                              child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                            )
                          : const Text('Criar conta'),
                    ),
                    const SizedBox(height: 16),
                    Center(
                      child: TextButton(
                        onPressed: () => context.go('/login'),
                        child: const Text('Já tem uma conta? Entrar'),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _seletorDeTipo() {
    return Row(
      children: [
        Expanded(
          child: ChoiceChip(
            label: const Text('Cidadão'),
            selected: _isCidadao,
            selectedColor: AppColors.secondary,
            onSelected: (_) => setState(() => _isCidadao = true),
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: ChoiceChip(
            label: const Text('Empresa'),
            selected: !_isCidadao,
            selectedColor: AppColors.secondary,
            onSelected: (_) => setState(() => _isCidadao = false),
          ),
        ),
      ],
    );
  }

  String? _obrigatorio(String? valor) =>
      (valor == null || valor.trim().isEmpty) ? 'Campo obrigatorio' : null;
}
