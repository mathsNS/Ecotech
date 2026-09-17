"""Catalogo unico de planos e recursos comerciais do EcoTech."""

from copy import deepcopy


PLANOS = (
    {
        'id': 'free',
        'nome': 'Free',
        'preco_mensal': 0.0,
        'destaque': False,
        'limite_solicitacoes_mes': 30,
        'recursos': (
            'Até 30 solicitações por mês',
            'Notificações básicas',
            'Histórico de coletas',
        ),
        'feature_flags': {
            'solicitacoes_ilimitadas': False,
            'notificacoes_avancadas': False,
            'historico_completo': False,
            'relatorio_pnrs': False,
            'exportacao_dados': False,
            'mtr': False,
            'dashboard_esg': False,
            'api_integracao': False,
            'multiplos_pontos': False,
            'relatorios_automaticos': False,
            'analytics_regional': False,
            'suporte_dedicado': False,
        },
    },
    {
        'id': 'professional',
        'nome': 'Professional',
        'preco_mensal': 249.0,
        'destaque': True,
        'limite_solicitacoes_mes': None,
        'recursos': (
            'Solicitações ilimitadas',
            'Notificações avançadas',
            'Histórico completo',
            'Relatório PNRS e Compliance',
            'Exportação CSV',
            'MTR profissional',
            'Dashboard ESG',
        ),
        'feature_flags': {
            'solicitacoes_ilimitadas': True,
            'notificacoes_avancadas': True,
            'historico_completo': True,
            'relatorio_pnrs': True,
            'exportacao_dados': True,
            'mtr': True,
            'dashboard_esg': True,
            'api_integracao': False,
            'multiplos_pontos': False,
            'relatorios_automaticos': False,
            'analytics_regional': False,
            'suporte_dedicado': False,
        },
    },
    {
        'id': 'enterprise',
        'nome': 'Enterprise',
        'preco_mensal': 599.0,
        'destaque': False,
        'limite_solicitacoes_mes': None,
        'recursos': (
            'Tudo do Professional',
            'API de integração',
            'Múltiplos pontos de coleta',
            'Relatórios automáticos mensais',
            'Analytics regional',
            'Suporte dedicado com SLA',
        ),
        'feature_flags': {
            'solicitacoes_ilimitadas': True,
            'notificacoes_avancadas': True,
            'historico_completo': True,
            'relatorio_pnrs': True,
            'exportacao_dados': True,
            'mtr': True,
            'dashboard_esg': True,
            'api_integracao': True,
            'multiplos_pontos': True,
            'relatorios_automaticos': True,
            'analytics_regional': True,
            'suporte_dedicado': True,
        },
    },
)


def listar_planos():
    """Devolve uma copia serializavel do catalogo comercial."""
    return deepcopy(PLANOS)


def buscar_plano(plano_id):
    """Localiza um plano pelo identificador canonico."""
    return next(
        (plano for plano in listar_planos() if plano['id'] == plano_id),
        None,
    )


def recursos_do_plano(plano_id):
    """Retorna somente as flags efetivas do plano informado."""
    plano = buscar_plano(plano_id) or buscar_plano('free')
    return deepcopy(plano['feature_flags'])
