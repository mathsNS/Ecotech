import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../features/admin/admin_controller.dart';
import '../../features/citizen/citizen_controller.dart';
import '../../features/communication/communication_controller.dart';
import '../../features/company/company_controller.dart';
import '../../features/dashboard/dashboard_controller.dart';
import '../../features/finance/finance_controller.dart';
import '../../features/plans/plans_controller.dart';
import '../../features/profile/perfil_controller.dart';

/// Invalida todos os providers de dados vinculados a sessao do usuario atual.
/// Evita vazamento de cache entre contas ao sair, trocar de usuario ou expirar sessao.
void invalidarProvidersSessao(Ref ref) {
  // Painel e perfil
  ref.invalidate(dashboardControllerProvider);
  ref.invalidate(perfilControllerProvider);

  // Cidadao
  ref.invalidate(pontosColetaProvider);
  ref.invalidate(solicitacoesProvider);
  ref.invalidate(solicitacaoDetalhesProvider);
  ref.invalidate(entregasProvider);

  // Comunicacao
  ref.invalidate(agendaProvider);
  ref.invalidate(conversasProvider);
  ref.invalidate(notificacoesProvider);
  ref.invalidate(badgesProvider);

  // Empresa e operacoes
  ref.invalidate(pontosEmpresaProvider);
  ref.invalidate(basesEmpresaProvider);
  ref.invalidate(oportunidadesEmpresaProvider);
  ref.invalidate(operacoesEmpresaProvider);
  ref.invalidate(operacaoDetalhesProvider);

  // Financeiro e planos
  ref.invalidate(carteiraProvider);
  ref.invalidate(relatorioProvider);
  ref.invalidate(plansControllerProvider);

  // Administracao
  ref.invalidate(usuariosAdminProvider);
  ref.invalidate(despachoAdminProvider);
  ref.invalidate(overridesAdminProvider);
  ref.invalidate(precosAdminProvider);
}
