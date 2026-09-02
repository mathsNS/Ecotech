import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_colors.dart';
import 'auth_controller.dart';

enum _TipoConta { cidadao, empresa, administrador }

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _credencialController = TextEditingController();
  final _senhaController = TextEditingController();
  _TipoConta _tipo = _TipoConta.cidadao;
  bool _carregando = false;

  static const _configPorTipo = {
    _TipoConta.cidadao: (label: 'CPF', hint: '000.000.000-00'),
    _TipoConta.empresa: (label: 'CNPJ', hint: '00.000.000/0000-00'),
    _TipoConta.administrador: (label: 'E-mail', hint: 'admin@ecotech.com'),
  };

  @override
  void dispose() {
    _credencialController.dispose();
    _senhaController.dispose();
    super.dispose();
  }

  Future<void> _entrar() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _carregando = true);
    await ref.read(authControllerProvider.notifier).login(
          tipo: _tipo.name,
          credencial: _credencialController.text.trim(),
          senha: _senhaController.text,
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
    final config = _configPorTipo[_tipo]!;

    return Scaffold(
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
                    Image.asset(
                      'assets/images/Ecotech logo completa.png',
                      height: 72,
                    ),
                    const SizedBox(height: 32),
                    Text('Entrar no sistema', style: Theme.of(context).textTheme.titleLarge),
                    const SizedBox(height: 4),
                    Text(
                      'Selecione o tipo de conta para acessar',
                      style: Theme.of(context).textTheme.bodyMedium,
                    ),
                    const SizedBox(height: 24),
                    _seletorDeTipo(),
                    const SizedBox(height: 16),
                    TextFormField(
                      controller: _credencialController,
                      decoration: InputDecoration(
                        labelText: config.label,
                        hintText: config.hint,
                      ),
                      keyboardType: _tipo == _TipoConta.administrador
                          ? TextInputType.emailAddress
                          : TextInputType.text,
                      validator: (valor) =>
                          (valor == null || valor.trim().isEmpty) ? 'Campo obrigatorio' : null,
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: _senhaController,
                      decoration: const InputDecoration(labelText: 'Senha'),
                      obscureText: true,
                      validator: (valor) =>
                          (valor == null || valor.isEmpty) ? 'Campo obrigatorio' : null,
                    ),
                    const SizedBox(height: 24),
                    ElevatedButton(
                      onPressed: _carregando ? null : _entrar,
                      child: _carregando
                          ? const SizedBox(
                              height: 20,
                              width: 20,
                              child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                            )
                          : const Text('Entrar'),
                    ),
                    const SizedBox(height: 16),
                    Center(
                      child: TextButton(
                        onPressed: () => context.go('/cadastro'),
                        child: const Text('Não tem uma conta? Criar conta'),
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
    return Wrap(
      spacing: 8,
      children: _TipoConta.values.map((tipo) {
        final selecionado = tipo == _tipo;
        return ChoiceChip(
          label: Text(_rotulo(tipo)),
          selected: selecionado,
          selectedColor: AppColors.secondary,
          labelStyle: TextStyle(
            color: selecionado ? AppColors.primaryDark : AppColors.textLight,
            fontWeight: selecionado ? FontWeight.w600 : FontWeight.normal,
          ),
          onSelected: (_) => setState(() => _tipo = tipo),
        );
      }).toList(),
    );
  }

  String _rotulo(_TipoConta tipo) => switch (tipo) {
        _TipoConta.cidadao => 'Cidadão',
        _TipoConta.empresa => 'Empresa',
        _TipoConta.administrador => 'Administrador',
      };
}
