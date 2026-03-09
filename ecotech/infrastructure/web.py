"""
Aplicação web Flask - Interface do sistema EcoTech.

Este módulo implementa a interface web usando Flask,
baseada no design mobile fornecido.
"""

# sistema web ainda em desenvolvimento
# algumas rotas precisam de ajustes

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime
from typing import Optional

from ..application.services import (
    ServicoDescarte,
    ServicoRelatorio,
    ServicoPontoColeta,
    ServicoUsuario
)
from ..application.factories import (
    DispositivoFactory,
    MetodoTratamentoFactory
)
from ..domain.usuarios import Usuario
from ..infrastructure.persistence.dados import Dados


def criar_app() -> Flask:
    """
    Cria e configura a aplicação Flask.
    
    Returns:
        Aplicação Flask configurada
    """
    app = Flask(__name__)
    app.secret_key = "ecotech-secret-key-2026"
    
    # instancia unica de dados compartilhada por todos os servicos
    dados = Dados()
    
    # servicos com persistencia
    servico_usuario = ServicoUsuario(dados)
    servico_ponto = ServicoPontoColeta(dados)
    servico_descarte = ServicoDescarte(dados)
    servico_relatorio = ServicoRelatorio()
    
    # configura dependencias entre servicos
    servico_descarte.set_servicos(servico_usuario, servico_ponto)
    
    # dados exemplo
    _inicializar_dados_exemplo(servico_usuario, servico_ponto, servico_descarte, dados)
    
    # verifica login
    def usuario_logado():
        """Retorna True se tem usuário na sessão."""
        return 'user_id' in session
    
    def dados_usuario():
        """Retorna dados básicos do usuário da sessão."""
        if usuario_logado():
            return {
                'id': session.get('user_id'),
                'nome': session.get('user_nome'),
                'tipo': session.get('user_tipo')
            }
        return None
    
    # rotas
    
    @app.route('/')
    def index():
        """Página inicial / Hero visual."""
        usuario = dados_usuario()
        return render_template('index.html', usuario=usuario)
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Página de login."""
        if request.method == 'POST':
            tipo = request.form.get('tipo', 'cidadao')
            
            # 3 perfis fixos: João Silva (cidadão), Recicla Kariri (empresa) e Admin
            if tipo == 'cidadao':
                session['user_id'] = 'user-1'
                session['user_nome'] = 'João Silva'
                session['user_tipo'] = 'cidadao'
            elif tipo == 'empresa':
                session['user_id'] = 'user-3'
                session['user_nome'] = 'Recicla Kariri'
                session['user_tipo'] = 'empresa'
            elif tipo == 'admin':
                session['user_id'] = 'USR-ADM-001'
                session['user_nome'] = 'Admin Ecotech'
                session['user_tipo'] = 'administrador'
            
            return redirect(url_for('dashboard'))
        
        return render_template('login.html')
    
    @app.route('/criar-conta', methods=['GET', 'POST'])
    def criar_conta():
        """Página de criação de conta."""
        if request.method == 'POST':
            tipo = request.form.get('tipo', 'cidadao')
            
            # 3 perfis fixos: João Silva (cidadão), Recicla Kariri (empresa) e Admin
            if tipo == 'cidadao':
                session['user_id'] = 'user-1'
                session['user_nome'] = 'João Silva'
                session['user_tipo'] = 'cidadao'
            elif tipo == 'empresa':
                session['user_id'] = 'user-3'
                session['user_nome'] = 'Recicla Kariri'
                session['user_tipo'] = 'empresa'
            elif tipo == 'admin':
                session['user_id'] = 'USR-ADM-001'
                session['user_nome'] = 'Admin Ecotech'
                session['user_tipo'] = 'administrador'
            
            return redirect(url_for('dashboard'))
        
        return render_template('criar_conta.html')
    
    @app.route('/logout')
    def logout():
        """Logout do usuário."""
        session.clear()
        return redirect(url_for('index'))
    
    @app.route('/dashboard')
    def dashboard():
        """Dashboard principal - versões diferentes para cidadão, empresa e admin."""
        if not usuario_logado():
            return redirect(url_for('login'))
        
        usuario = dados_usuario()
        
        # busca solicitacoes
        todas_solicitacoes = servico_descarte.listar_solicitacoes()
        
        """" dashboard para administrador - visão geral do sistema """
        if usuario['tipo'] == 'administrador':
            total_sistema = sum(s.calcular_peso_total() for s in todas_solicitacoes)
            total_processadas = len([s for s in todas_solicitacoes if s.estado.obter_nome() in ['Reciclado', 'Reutilizado', 'Descartado']])
            impacto_total = sum(s.calcular_impacto_total() for s in todas_solicitacoes)
            
            return render_template(
                'dashboard.html',
                usuario=usuario,
                solicitacoes=todas_solicitacoes[:10],  # mostra últimas 10
                total_descartado=total_sistema,
                impacto_evitado=impacto_total,
                pontos_acumulados=0,
                total_sistema=total_sistema,
                total_processadas=total_processadas,
                is_empresa=False,
                is_admin=True
            )
        
        # solicitacoes do usuario
        solicitacoes_usuario = [
            s for s in todas_solicitacoes 
            if s.usuario.id == usuario['id']
        ]
        
        # calcula metricas do usuario
        total_descartado = sum(s.calcular_peso_total() for s in solicitacoes_usuario)
        impacto_evitado = sum(s.calcular_impacto_total() for s in solicitacoes_usuario)
        pontos_acumulados = int(total_descartado * 10)  # 10 pontos por kg
        
        # dashboard diferente para empresa
        if usuario['tipo'] == 'empresa':
            # metricas gerais do sistema para empresa
            total_sistema = sum(s.calcular_peso_total() for s in todas_solicitacoes)
            total_processadas = len([s for s in todas_solicitacoes if s.estado.obter_nome() in ['Reciclado', 'Reutilizado', 'Descartado']])
            
            return render_template(
                'dashboard.html',
                usuario=usuario,
                solicitacoes=solicitacoes_usuario,
                total_descartado=total_descartado,
                impacto_evitado=impacto_evitado,
                pontos_acumulados=pontos_acumulados,
                total_sistema=total_sistema,
                total_processadas=total_processadas,
                is_empresa=True,
                is_admin=False
            )
        
        # dashboard para cidadão
        return render_template(
            'dashboard.html',
            usuario=usuario,
            solicitacoes=solicitacoes_usuario,
            total_descartado=total_descartado,
            impacto_evitado=impacto_evitado,
            pontos_acumulados=pontos_acumulados,
            is_empresa=False,
            is_admin=False
        )
    
    @app.route('/nova-solicitacao', methods=['GET', 'POST'])
    def nova_solicitacao():
        """Criar nova solicitação de descarte."""
        if not usuario_logado():
            return redirect(url_for('login'))
        
        usuario = dados_usuario()
        
        if request.method == 'POST':
            # redireciona dashboard
            return redirect(url_for('dashboard'))
        
        pontos = servico_ponto.listar_pontos()
        return render_template('nova_solicitacao.html', usuario=usuario, pontos=pontos)
    
    @app.route('/pontos-coleta')
    def pontos_coleta():
        """Mapa de pontos de coleta."""
        usuario = dados_usuario()
        pontos = servico_ponto.listar_pontos()
        
        return render_template(
            'pontos_coleta.html',
            usuario=usuario,
            pontos=pontos
        )
    
    @app.route('/notificacoes')
    def notificacoes():
        """Página de notificações."""
        if not usuario_logado():
            return redirect(url_for('login'))
        
        usuario = dados_usuario()
        
        # busca notificacoes do usuario no banco de dados
        notificacoes_db = dados.buscar_notificacoes_usuario(usuario['id'])
        
        # converte para o formato esperado pelo template
        notificacoes = [
            {
                'titulo': 'Notificação do Sistema',
                'mensagem': n['mensagem'],
                'data': datetime.strptime(n['timestamp'], '%d/%m/%Y %H:%M:%S'),
                'lida': False
            }
            for n in notificacoes_db
        ]
        
        # se nao tiver notificacoes, adiciona uma de exemplo
        if not notificacoes:
            notificacoes = [
                {
                    'titulo': 'Seus valores foram finalizados',
                    'mensagem': 'Você recebeu R$ 13,95',
                    'data': datetime.now(),
                    'lida': False
                }
            ]
        
        return render_template(
            'notificacoes.html',
            usuario=usuario,
            notificacoes=notificacoes
        )
    
    @app.route('/ultimas-entregas')
    def ultimas_entregas():
        """Página de últimas entregas (histórico completo)."""
        if not usuario_logado():
            return redirect(url_for('login'))
        
        usuario = dados_usuario()
        
        # busca entregas do usuario no banco de dados
        entregas_db = dados.buscar_entregas_usuario(usuario['id'])
        
        # converte para o formato esperado pelo template
        entregas = [
            {
                'valor': e['valor'],
                'empresa': e['empresa'],
                'id': e['id'],
                'data': e['data'],
                'hora': e['hora'],
                'status': e['status']
            }
            for e in entregas_db
        ]
        
        return render_template(
            'ultimas_entregas.html',
            usuario=usuario,
            entregas=entregas
        )
    
    @app.route('/saque')
    def saque():
        """Página de saque/carteira."""
        if not usuario_logado():
            return redirect(url_for('login'))
        
        usuario = dados_usuario()
        
        return render_template(
            'saque.html',
            usuario=usuario
        )
    
    @app.route('/perfil')
    def perfil():
        """Página de perfil do usuário."""
        if not usuario_logado():
            return redirect(url_for('login'))
        
        usuario = dados_usuario()
        
        return render_template(
            'perfil.html',
            usuario=usuario,
            total_solicitacoes=5,
            pontos=1250
        )
    
    @app.route('/operacoes')
    def operacoes():
        """Página de operações para gerenciamento de solicitações."""
        if not usuario_logado():
            return redirect(url_for('login'))
        
        usuario = dados_usuario()
        
        # busca todas as solicitacoes
        todas_solicitacoes = servico_descarte.listar_solicitacoes()
        
        # administrador vê tudo, outros usuários veem apenas as suas
        if usuario['tipo'] == 'administrador':
            solicitacoes_usuario = todas_solicitacoes
        else:
            solicitacoes_usuario = [
                s for s in todas_solicitacoes 
                if s.usuario.id == usuario['id']
            ]
        
        # filtra por estado se tiver parametro
        filtro_estado = request.args.get('estado', '')
        if filtro_estado:
            solicitacoes_filtradas = [
                s for s in solicitacoes_usuario 
                if filtro_estado.lower() in s.estado.obter_nome().lower()
            ]
        else:
            solicitacoes_filtradas = solicitacoes_usuario
        
        # calcula estatisticas baseadas nas solicitações que o usuário pode ver
        stats = {
            'pendentes': len([s for s in solicitacoes_usuario if s.estado.obter_nome() == 'Solicitado']),
            'em_coleta': len([s for s in solicitacoes_usuario if s.estado.obter_nome() == 'Coletado']),
            'processando': len([s for s in solicitacoes_usuario if s.estado.obter_nome() == 'Em Processamento']),
            'finalizadas': len([s for s in solicitacoes_usuario if s.estado.obter_nome() in ['Reciclado', 'Reutilizado', 'Descartado']])
        }
        
        return render_template(
            'operacoes.html', 
            usuario=usuario,
            solicitacoes=solicitacoes_filtradas,
            stats=stats,
            filtro_atual=filtro_estado,
            is_admin=usuario['tipo'] == 'administrador'
        )
    
    @app.route('/relatorios')
    def relatorios():
        """Página de relatórios ambientais."""
        if not usuario_logado():
            return redirect(url_for('login'))
        
        usuario = dados_usuario()
        
        # busca todas as solicitacoes
        todas_solicitacoes = servico_descarte.listar_solicitacoes()
        
        """ administrador vê relatório geral, outros veem apenas suas solicitações """
        if usuario['tipo'] == 'administrador':
            solicitacoes_para_relatorio = todas_solicitacoes
            titulo_relatorio = "Relatório Geral do Sistema"
        else:
            solicitacoes_para_relatorio = [
                s for s in todas_solicitacoes 
                if s.usuario.id == usuario['id']
            ]
            titulo_relatorio = f"Relatório de {usuario['nome']}"
        
        # gera relatorio usando o servico
        relatorio = servico_relatorio.gerar_relatorio_periodo(
            titulo_relatorio,
            solicitacoes_para_relatorio
        )
        
        # pega metricas do relatorio
        metricas = relatorio.gerar_relatorio()
        
        # filtra solicitacoes finalizadas para mostrar na tabela
        solicitacoes_finalizadas = [
            s for s in solicitacoes_para_relatorio
            if s.estado.obter_nome() in ['Reciclado', 'Reutilizado', 'Descartado']
        ]
        
        return render_template(
            'relatorios.html',
            usuario=usuario,
            metricas=metricas,
            solicitacoes=solicitacoes_finalizadas,
            is_admin=usuario['tipo'] == 'administrador'
        )
    
    @app.route('/usuarios')
    def usuarios():
        """Página de usuários (placeholder)."""
        if not usuario_logado():
            return redirect(url_for('login'))
        
        usuario = dados_usuario()
        return render_template('usuarios.html', usuario=usuario)
    
    @app.route('/api/solicitacoes')
    def api_solicitacoes():
        """API para listar solicitações."""
        if not usuario_logado():
            return jsonify({'error': 'Not authenticated'}), 401
        
        return jsonify([])
    
    return app


def _inicializar_dados_exemplo(servico_usuario, servico_ponto, servico_descarte, dados):
    """inicializa dados de exemplo para demonstracao."""
    
    # verifica se ja existem dados suficientes no banco
    if dados.contar_usuarios() > 3:
        return  # ja tem dados, nao precisa inicializar novamente
    
    # usuarios de exemplo
    cidadao1 = servico_usuario.criar_usuario('cidadao', {
        'id': 'user-1',
        'nome': 'João Silva',
        'email': 'joao@example.com',
        'cpf': '12345678900'
    })
    
    cidadao2 = servico_usuario.criar_usuario('cidadao', {
        'id': 'user-2',
        'nome': 'Maria Santos',
        'email': 'maria@example.com',
        'cpf': '98765432100'
    })
    
    empresa = servico_usuario.criar_usuario('empresa', {
        'id': 'user-3',
        'nome': 'Ecotech',
        'email': 'contato@ecotech.com',
        'cnpj': '12345678000199',
        'razao_social': 'Ecotech'
    })
    
    # pontos de coleta
    ponto1 = servico_ponto.criar_ponto_coleta(
        'Centro de Coleta Lagoa Seca',
        'R. Dr. Morato Saraiva, 1100 - Lagoa Seca',
        -7.2138,
        -39.3089,
        1000.0
    )
    
    ponto2 = servico_ponto.criar_ponto_coleta(
        'Centro de Coleta Cariri',
        'Av. Padre Cícero, 500 - Centro',
        -7.2123,
        -39.3145,
        2000.0
    )
    
    # cria algumas solicitacoes de exemplo com diferentes estados
    
    # solicitacao 1 - estado inicial (solicitado)
    sol1 = servico_descarte.criar_solicitacao(cidadao1, ponto1)
    celular1 = DispositivoFactory.criar_celular('cel-001', 'iPhone 11', 0.194)
    notebook1 = DispositivoFactory.criar_computador('comp-001', 'Dell Inspiron', 2.1)
    servico_descarte.adicionar_item_solicitacao(sol1, celular1, 1, 'tela quebrada')
    servico_descarte.adicionar_item_solicitacao(sol1, notebook1, 1, 'nao liga mais')
    
    # solicitacao 2 - ja foi coletada
    sol2 = servico_descarte.criar_solicitacao(cidadao2, ponto2)
    tv1 = DispositivoFactory.criar_eletrodomestico('elet-001', 'TV Samsung 32"', 5.5)
    servico_descarte.adicionar_item_solicitacao(sol2, tv1, 1)
    servico_descarte.avancar_estado_solicitacao(sol2)  # passa pra coletado
    
    # solicitacao 3 - em processamento
    sol3 = servico_descarte.criar_solicitacao(empresa, ponto1)
    celular2 = DispositivoFactory.criar_celular('cel-002', 'Samsung Galaxy S10', 0.175)
    tablet1 = DispositivoFactory.criar_celular('cel-003', 'iPad Air', 0.460)
    servico_descarte.adicionar_item_solicitacao(sol3, celular2, 3)
    servico_descarte.adicionar_item_solicitacao(sol3, tablet1, 2)
    metodo = MetodoTratamentoFactory.criar_reciclagem()
    servico_descarte.definir_metodo_tratamento(sol3, metodo)
    servico_descarte.avancar_estado_solicitacao(sol3)  # coletado
    servico_descarte.avancar_estado_solicitacao(sol3)  # em processamento
    
    # solicitacao 4 - finalizada (reciclada)
    sol4 = servico_descarte.criar_solicitacao(cidadao1, ponto2)
    monitor1 = DispositivoFactory.criar_computador('comp-002', 'Monitor LG 24"', 3.2)
    teclado1 = DispositivoFactory.criar_computador('comp-003', 'Teclado Mecanico', 0.8)
    servico_descarte.adicionar_item_solicitacao(sol4, monitor1, 1)
    servico_descarte.adicionar_item_solicitacao(sol4, teclado1, 1)
    metodo2 = MetodoTratamentoFactory.criar_reciclagem()
    servico_descarte.definir_metodo_tratamento(sol4, metodo2)
    servico_descarte.avancar_estado_solicitacao(sol4)  # coletado
    servico_descarte.avancar_estado_solicitacao(sol4)  # em processamento
    servico_descarte.avancar_estado_solicitacao(sol4)  # reciclado
    
    # solicitacao 5 - mais uma pendente
    sol5 = servico_descarte.criar_solicitacao(cidadao2, ponto1)
    geladeira = DispositivoFactory.criar_eletrodomestico('elet-002', 'Geladeira Brastemp', 45.0)
    servico_descarte.adicionar_item_solicitacao(sol5, geladeira, 1, 'compressor queimado')
    
    # solicitacao 6 - outra em processamento
    sol6 = servico_descarte.criar_solicitacao(empresa, ponto2)
    pc1 = DispositivoFactory.criar_computador('comp-004', 'Desktop HP', 8.5)
    servico_descarte.adicionar_item_solicitacao(sol6, pc1, 5, 'lote de computadores antigos')
    metodo3 = MetodoTratamentoFactory.criar_reuso()
    servico_descarte.definir_metodo_tratamento(sol6, metodo3)
    servico_descarte.avancar_estado_solicitacao(sol6)  # coletado
    servico_descarte.avancar_estado_solicitacao(sol6)  # em processamento
    
    # adiciona historico de entregas para o cidadao1 (joao silva)
    # isso é o que aparece na pagina de ultimas entregas
    dados.salvar_entrega(
        '56492574920',
        'user-1',
        13.95,
        'Ecotech',
        '13 Set 2025',
        '13:02',
        'finalizado'
    )
    
    dados.salvar_entrega(
        '58293049159',
        'user-1',
        8.19,
        'Ecotech',
        '10 Set 2025',
        '08:55',
        'finalizado'
    )
    
    dados.salvar_entrega(
        '98358259431',
        'user-1',
        6.41,
        'Ecotech',
        '08 Set 2025',
        '15:31',
        'cancelado'
    )
    
    dados.salvar_entrega(
        '47389088043',
        'user-1',
        27.65,
        'Ecotech',
        '03 Set 2025',
        '16:44',
        'finalizado'
    )
    
    dados.salvar_entrega(
        '57463968973',
        'user-1',
        12.53,
        'Ecotech',
        '02 Set 2025',
        '08:21',
        'finalizado'
    )


if __name__ == '__main__':
    app = criar_app()
    app.run(debug=True, port=5000)
