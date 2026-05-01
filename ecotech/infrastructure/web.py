"""
Aplicação web Flask - Interface do sistema EcoTech.

Este módulo implementa a interface web usando Flask,
baseada no design mobile fornecido.
"""

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
    
    # carrega solicitacoes do banco de dados
    servico_descarte._carregar_solicitacoes_do_banco()
    
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
        """Tela de login."""
        if usuario_logado():
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            tipo      = request.form.get('tipo', 'cidadao')
            credencial = request.form.get('credencial', '').strip()
            senha      = request.form.get('senha', '')

            # normaliza CPF/CNPJ removendo pontuação — aceita "123.456.789-09" ou "12345678909"
            if tipo in ('cidadao', 'empresa'):
                credencial = credencial.replace('.', '').replace('-', '').replace('/', '').replace(' ', '')

            usuario_obj = servico_usuario.autenticar(tipo, credencial, senha)

            if usuario_obj is None:
                flash('Credencial ou senha inválidos.', 'error')
                return render_template('login.html', tipo_selecionado=tipo)

            session['user_id']   = usuario_obj.id
            session['user_nome'] = usuario_obj.nome
            session['user_tipo'] = usuario_obj.obter_tipo().split()[0].lower()

            # normaliza o tipo antes de salvar na sessão
            _tipo_map = {
                'cidadão': 'cidadao',
                'empresa': 'empresa',
                'administrador': 'administrador',
            }
            session['user_tipo'] = _tipo_map.get(session['user_tipo'], session['user_tipo'])

            return redirect(url_for('dashboard'))

        return render_template('login.html', tipo_selecionado='cidadao')
    
    @app.route('/criar-conta', methods=['GET', 'POST'])
    def criar_conta():
        """Página de cadastro de nova conta."""
        if usuario_logado():
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            tipo  = request.form.get('tipo', 'cidadao')
            nome  = request.form.get('nome', '').strip()
            email = request.form.get('email', '').strip()
            senha = request.form.get('senha', '')
            senha_confirmacao = request.form.get('senha_confirmacao', '')

            # validações básicas
            if not nome or not email or not senha:
                flash('Preencha todos os campos obrigatórios.', 'error')
                return render_template('criar_conta.html', tipo_selecionado=tipo)

            if senha != senha_confirmacao:
                flash('As senhas não coincidem.', 'error')
                return render_template('criar_conta.html', tipo_selecionado=tipo)

            if len(senha) < 6:
                flash('A senha deve ter pelo menos 6 caracteres.', 'error')
                return render_template('criar_conta.html', tipo_selecionado=tipo)

            try:
                dados_novo = {'nome': nome, 'email': email}

                if tipo == 'cidadao':
                    dados_novo['cpf'] = request.form.get('cpf', '').strip()
                elif tipo == 'empresa':
                    dados_novo['cnpj']         = request.form.get('cnpj', '').strip()
                    dados_novo['razao_social']  = request.form.get('razao_social', '').strip()

                usuario_obj = servico_usuario.criar_usuario(tipo, dados_novo, senha)

            except (ValueError, Exception) as e:
                flash(str(e), 'error')
                return render_template('criar_conta.html', tipo_selecionado=tipo)

            # login automático após cadastro
            session['user_id']   = usuario_obj.id
            session['user_nome'] = usuario_obj.nome

            _tipo_map = {
                'cidadão': 'cidadao',
                'empresa': 'empresa',
                'administrador': 'administrador',
            }
            tipo_sessao = usuario_obj.obter_tipo().split()[0].lower()
            session['user_tipo'] = _tipo_map.get(tipo_sessao, tipo_sessao)

            flash(f'Conta criada com sucesso! Bem-vindo(a), {usuario_obj.nome}.', 'success')
            return redirect(url_for('dashboard'))

        return render_template('criar_conta.html', tipo_selecionado='cidadao')
    
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
        
        # calcula tier com base nos pontos
        if pontos_acumulados >= 1200:
            tier_nome = 'Tier Ouro'
        elif pontos_acumulados >= 400:
            tier_nome = 'Tier Prata'
        else:
            tier_nome = 'Tier Bronze'
        
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
                tier_nome=tier_nome,
                is_empresa=True,
                is_admin=False
            )
        
        # dashboard para cidadão - busca entregas do histórico
        entregas_db = dados.buscar_entregas_usuario(usuario['id'])
        
        # converte e ordena entregas por data
        entregas = []
        for e in entregas_db:
            # substitui abreviações de mês
            data_str = e['data'].replace('Jan', '01').replace('Fev', '02').replace('Feb', '02')
            data_str = data_str.replace('Mar', '03').replace('Abr', '04').replace('Apr', '04')
            data_str = data_str.replace('Mai', '05').replace('May', '05').replace('Jun', '06')
            data_str = data_str.replace('Jul', '07').replace('Ago', '08').replace('Aug', '08')
            data_str = data_str.replace('Set', '09').replace('Sep', '09').replace('Out', '10')
            data_str = data_str.replace('Oct', '10').replace('Nov', '11').replace('Dez', '12')
            data_str = data_str.replace('Dec', '12')
            
            partes = data_str.split()
            if len(partes) == 3:
                data_ordenavel = f"{partes[2]}-{partes[1]}-{partes[0]} {e['hora']}"
                data_formatada = f"{partes[0]}/{partes[1]}"  # dd/mm
            else:
                data_ordenavel = e['data'] + ' ' + e['hora']
                data_formatada = e['data']
            
            entregas.append({
                'valor': e['valor'],
                'empresa': e['empresa'],
                'id': e['id'],
                'data': e['data'],
                'data_formatada': data_formatada,
                'hora': e['hora'],
                'status': e['status'],
                '_data_ordenavel': data_ordenavel
            })
        
        # ordena por data (mais recente primeiro)
        entregas.sort(key=lambda x: x['_data_ordenavel'], reverse=True)
        
        # calcula porcentagens para barras de progresso
        progresso_missao = min(round((len(solicitacoes_usuario) / 15) * 100), 100)
        progresso_tier = min(round((pontos_acumulados / 1200) * 100), 100)
        
        return render_template(
            'dashboard.html',
            usuario=usuario,
            solicitacoes=solicitacoes_usuario,
            entregas=entregas[:10],  # apenas 10 mais recentes
            total_descartado=total_descartado,
            impacto_evitado=impacto_evitado,
            pontos_acumulados=pontos_acumulados,
            progresso_missao=progresso_missao,
            progresso_tier=progresso_tier,
            tier_nome=tier_nome,
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
        
        # data minima para agendamento eh hoje
        from datetime import date
        hoje = date.today().strftime('%Y-%m-%d')
        
        return render_template('nova_solicitacao.html', usuario=usuario, today=hoje)
    
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
        from datetime import datetime
        import locale
        
        entregas = []
        for e in entregas_db:
            # substitui abreviacoes pt e ing
            data_str = e['data'].replace('Jan', '01').replace('Fev', '02').replace('Feb', '02')
            data_str = data_str.replace('Mar', '03').replace('Abr', '04').replace('Apr', '04')
            data_str = data_str.replace('Mai', '05').replace('May', '05').replace('Jun', '06')
            data_str = data_str.replace('Jul', '07').replace('Ago', '08').replace('Aug', '08')
            data_str = data_str.replace('Set', '09').replace('Sep', '09').replace('Out', '10')
            data_str = data_str.replace('Oct', '10').replace('Nov', '11').replace('Dez', '12')
            data_str = data_str.replace('Dec', '12')
            
            partes = data_str.split()
            if len(partes) == 3:
                data_ordenavel = f"{partes[2]}-{partes[1]}-{partes[0]} {e['hora']}"
                data_formatada = f"{partes[0]}/{partes[1]}"  # dd/mm
            else:
                data_ordenavel = e['data'] + ' ' + e['hora']
                data_formatada = e['data']
            
            entregas.append({
                'valor': e['valor'],
                'empresa': e['empresa'],
                'id': e['id'],
                'data': e['data'],
                'data_formatada': data_formatada,
                'hora': e['hora'],
                'status': e['status'],
                '_data_ordenavel': data_ordenavel
            })
        
        # ordena por data (mais recente primeiro)
        entregas.sort(key=lambda x: x['_data_ordenavel'], reverse=True)
        
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
        
        todas_solicitacoes = servico_descarte.listar_solicitacoes()
        solicitacoes_usuario = [s for s in todas_solicitacoes if s.usuario.id == usuario['id']]
        total_peso = sum(s.calcular_peso_total() for s in solicitacoes_usuario)
        pontos_reais = int(total_peso * 10)
        
        return render_template(
            'perfil.html',
            usuario=usuario,
            total_solicitacoes=len(solicitacoes_usuario),
            pontos=pontos_reais
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
        """Página de usuários (apenas admin)."""
        if not usuario_logado():
            return redirect(url_for('login'))
        
        usuario = dados_usuario()
        
        # Apenas admin pode acessar
        if usuario['tipo'] != 'administrador':
            flash('Acesso negado. Apenas administradores podem acessar esta página.', 'error')
            return redirect(url_for('dashboard'))
        
        # Buscar todos os usuários
        dados = Dados()
        
        # buscar cidadaos com dados completos
        c = dados.conn.cursor()
        c.execute("""
            SELECT u.id, u.nome, u.email, u.data_cadastro, c.cpf, c.pontos
            FROM usuario u
            JOIN cidadao c ON u.id = c.id_usuario
            WHERE u.tipo = 'cidadao'
        """)
        cidadaos_raw = c.fetchall()
        
        # buscar empresas com dados completos
        c.execute("""
            SELECT u.id, u.nome, u.email, u.data_cadastro, e.cnpj, e.descartado_mes
            FROM usuario u
            JOIN empresa e ON u.id = e.id_usuario
            WHERE u.tipo = 'empresa'
        """)
        empresas_raw = c.fetchall()
        
        #formatar datas
        from datetime import datetime
        
        def formatar_data(data_str):
            if not data_str:
                return '-'
            try:
                dt = datetime.strptime(data_str, '%Y-%m-%d %H:%M:%S')
                return dt.strftime('%d/%m/%Y %H:%M:%S')
            except:
                return data_str
        
        cidadaos = []
        for c in cidadaos_raw:
            cidadaos.append({
                'id': c['id'],
                'nome': c['nome'],
                'email': c['email'],
                'data_cadastro': formatar_data(c['data_cadastro']),
                'cpf': c['cpf'],
                'pontos': c['pontos']
            })
        
        empresas = []
        for e in empresas_raw:
            empresas.append({
                'id': e['id'],
                'nome': e['nome'],
                'email': e['email'],
                'data_cadastro': formatar_data(e['data_cadastro']),
                'cnpj': e['cnpj'],
                'descartado_mes': e['descartado_mes']
            })
        
        return render_template('usuarios.html',
                             usuario=usuario,
                             cidadaos=cidadaos,
                             empresas=empresas,
                             total_cidadaos=len(cidadaos),
                             total_empresas=len(empresas))
    
    @app.route('/api/solicitacoes')
    def api_solicitacoes():
        """API para listar solicitações."""
        if not usuario_logado():
            return jsonify({'error': 'Not authenticated'}), 401
        
        return jsonify([])
    
    return app


def _inicializar_dados_exemplo(servico_usuario, servico_ponto, servico_descarte, dados):
    """Cria os perfis base e dados de demonstração para o sistema."""

    if dados.contar_usuarios() > 0:
        return  # banco já populado, não sobrescrever

    # ---- usuários base ----
    cidadao1    cidadao1 = servico_usuario.criar_usuario('cidadao', {
        'id': 'user-1',
        'nome': 'João Silva',
        'email': 'joao@ecotech.com',
        'cpf': '12345678909'
    }, senha='cidadao123')

    empresa = servico_usuario.criar_usuario('empresa', {
        'id': 'user-2',
        'nome': 'Recicla Kariri',
        'email': 'contato@recilakariri.com',
        'cnpj': '11222333000181',
        'razao_social': 'Recicla Kariri Reciclagem LTDA'
    }, senha='empresa123')

    servico_usuario.criar_usuario('administrador', {
        'id': 'USR-ADM-001',
        'nome': 'Admin Ecotech',
        'email': 'admin@ecotech.com',
        'nivel_acesso': 3
    }, senha='admin123')

    cidadao2 = servico_usuario.criar_usuario('cidadao', {
        'id': 'user-3',
        'nome': 'Maria Santos',
        'email': 'maria@example.com',
        'cpf': '98765432100'
    })

    # ---- pontos de coleta ----
    ponto1 = servico_ponto.criar_ponto_coleta(
        'Centro de Coleta Lagoa Seca',
        'R. Dr. Morato Saraiva, 1100 - Lagoa Seca',
        -7.2138,
        -39.3089,
        5000.0
    )

    ponto2 = servico_ponto.criar_ponto_coleta(
        'Centro de Coleta Cariri',
        'Av. Padre Cícero, 500 - Centro',
        -7.2123,
        -39.3145,
        5000.0
    )

    ponto3 = servico_ponto.criar_ponto_coleta(
        'EcoPonto Sul',
        'Av. Leão Sampaio, 200 - Juazeiro do Norte',
        -7.2190,
        -39.3200,
        3000.0
    )

    # ── ESTADO: SOLICITADO (5 solicitações) ────────────────────────
    sol_s1 = servico_descarte.criar_solicitacao(cidadao1, ponto1)
    servico_descarte.adicionar_item_solicitacao(sol_s1, DispositivoFactory.criar_celular('cel-001', 'iPhone 11', 0.194), 1, 'tela quebrada')
    servico_descarte.adicionar_item_solicitacao(sol_s1, DispositivoFactory.criar_computador('comp-001', 'Dell Inspiron 15', 2.1), 1, 'não liga mais')

    sol_s2 = servico_descarte.criar_solicitacao(cidadao2, ponto3)
    servico_descarte.adicionar_item_solicitacao(sol_s2, DispositivoFactory.criar_celular('cel-010', 'Motorola Moto G', 0.180), 2, 'bateria inchada')

    sol_s3 = servico_descarte.criar_solicitacao(cidadao1, ponto2)
    servico_descarte.adicionar_item_solicitacao(sol_s3, DispositivoFactory.criar_eletrodomestico('elet-020', 'Impressora HP', 4.5), 1, 'sem uso')
    servico_descarte.adicionar_item_solicitacao(sol_s3, DispositivoFactory.criar_computador('comp-020', 'Mouse Logitech', 0.1), 3)

    sol_s4 = servico_descarte.criar_solicitacao(empresa, ponto3)
    servico_descarte.adicionar_item_solicitacao(sol_s4, DispositivoFactory.criar_computador('comp-021', 'Servidor Dell PowerEdge', 12.0), 2, 'lote servidores obsoletos')

    sol_s5 = servico_descarte.criar_solicitacao(cidadao2, ponto1)
    servico_descarte.adicionar_item_solicitacao(sol_s5, DispositivoFactory.criar_celular('cel-022', 'Samsung Galaxy A20', 0.168), 1, 'display danificado')

    # ── ESTADO: COLETADO (4 solicitações) ──────────────────────────
    sol_c1 = servico_descarte.criar_solicitacao(cidadao2, ponto2)
    servico_descarte.adicionar_item_solicitacao(sol_c1, DispositivoFactory.criar_eletrodomestico('elet-001', 'TV Samsung 32"', 5.5), 1)
    servico_descarte.avancar_estado_solicitacao(sol_c1)

    sol_c2 = servico_descarte.criar_solicitacao(cidadao1, ponto3)
    servico_descarte.adicionar_item_solicitacao(sol_c2, DispositivoFactory.criar_computador('comp-010', 'MacBook Air 2019', 1.29), 1, 'placa mãe queimada')
    servico_descarte.avancar_estado_solicitacao(sol_c2)

    sol_c3 = servico_descarte.criar_solicitacao(empresa, ponto1)
    servico_descarte.adicionar_item_solicitacao(sol_c3, DispositivoFactory.criar_celular('cel-030', 'Xiaomi Redmi Note 10', 0.178), 8, 'lote corporativo')
    servico_descarte.avancar_estado_solicitacao(sol_c3)

    sol_c4 = servico_descarte.criar_solicitacao(cidadao2, ponto3)
    servico_descarte.adicionar_item_solicitacao(sol_c4, DispositivoFactory.criar_eletrodomestico('elet-030', 'Ar-condicionado LG 9000', 28.0), 1, 'defeito no compressor')
    servico_descarte.avancar_estado_solicitacao(sol_c4)

    # ── ESTADO: EM PROCESSAMENTO (4 solicitações) ──────────────────
    sol_ep1 = servico_descarte.criar_solicitacao(empresa, ponto1)
    servico_descarte.adicionar_item_solicitacao(sol_ep1, DispositivoFactory.criar_celular('cel-002', 'Samsung Galaxy S10', 0.175), 3)
    servico_descarte.adicionar_item_solicitacao(sol_ep1, DispositivoFactory.criar_celular('cel-003', 'iPad Air', 0.460), 2)
    servico_descarte.definir_metodo_tratamento(sol_ep1, MetodoTratamentoFactory.criar_reciclagem())
    servico_descarte.avancar_estado_solicitacao(sol_ep1)
    servico_descarte.avancar_estado_solicitacao(sol_ep1)

    sol_ep2 = servico_descarte.criar_solicitacao(cidadao2, ponto2)
    servico_descarte.adicionar_item_solicitacao(sol_ep2, DispositivoFactory.criar_eletrodomestico('elet-010', 'Micro-ondas Consul', 11.0), 1)
    servico_descarte.definir_metodo_tratamento(sol_ep2, MetodoTratamentoFactory.criar_descarte_controlado())
    servico_descarte.avancar_estado_solicitacao(sol_ep2)
    servico_descarte.avancar_estado_solicitacao(sol_ep2)

    sol_ep3 = servico_descarte.criar_solicitacao(cidadao1, ponto3)
    servico_descarte.adicionar_item_solicitacao(sol_ep3, DispositivoFactory.criar_computador('comp-040', 'Notebook Acer Aspire', 2.2), 2)
    servico_descarte.adicionar_item_solicitacao(sol_ep3, DispositivoFactory.criar_computador('comp-041', 'HD Externo 1TB', 0.26), 4)
    servico_descarte.definir_metodo_tratamento(sol_ep3, MetodoTratamentoFactory.criar_reuso())
    servico_descarte.avancar_estado_solicitacao(sol_ep3)
    servico_descarte.avancar_estado_solicitacao(sol_ep3)

    sol_ep4 = servico_descarte.criar_solicitacao(empresa, ponto2)
    servico_descarte.adicionar_item_solicitacao(sol_ep4, DispositivoFactory.criar_eletrodomestico('elet-040', 'Lavadora Electrolux', 52.0), 1, 'placa queimada')
    servico_descarte.definir_metodo_tratamento(sol_ep4, MetodoTratamentoFactory.criar_descarte_controlado())
    servico_descarte.avancar_estado_solicitacao(sol_ep4)
    servico_descarte.avancar_estado_solicitacao(sol_ep4)

    # ── ESTADO: RECICLADO (5 solicitações) ─────────────────────────
    sol_r1 = servico_descarte.criar_solicitacao(cidadao1, ponto2)
    servico_descarte.adicionar_item_solicitacao(sol_r1, DispositivoFactory.criar_computador('comp-002', 'Monitor LG 24"', 3.2), 1)
    servico_descarte.adicionar_item_solicitacao(sol_r1, DispositivoFactory.criar_computador('comp-003', 'Teclado Mecânico', 0.8), 1)
    servico_descarte.definir_metodo_tratamento(sol_r1, MetodoTratamentoFactory.criar_reciclagem())
    servico_descarte.avancar_estado_solicitacao(sol_r1)
    servico_descarte.avancar_estado_solicitacao(sol_r1)
    servico_descarte.avancar_estado_solicitacao(sol_r1)

    sol_r2 = servico_descarte.criar_solicitacao(empresa, ponto1)
    servico_descarte.adicionar_item_solicitacao(sol_r2, DispositivoFactory.criar_celular('cel-011', 'iPhone XR', 0.194), 5)
    servico_descarte.adicionar_item_solicitacao(sol_r2, DispositivoFactory.criar_celular('cel-012', 'Galaxy A51', 0.172), 4)
    servico_descarte.definir_metodo_tratamento(sol_r2, MetodoTratamentoFactory.criar_reciclagem())
    servico_descarte.avancar_estado_solicitacao(sol_r2)
    servico_descarte.avancar_estado_solicitacao(sol_r2)
    servico_descarte.avancar_estado_solicitacao(sol_r2)

    sol_r3 = servico_descarte.criar_solicitacao(cidadao2, ponto3)
    servico_descarte.adicionar_item_solicitacao(sol_r3, DispositivoFactory.criar_eletrodomestico('elet-050', 'TV LG 42"', 8.9), 1)
    servico_descarte.adicionar_item_solicitacao(sol_r3, DispositivoFactory.criar_eletrodomestico('elet-051', 'DVD Player Sony', 1.4), 2)
    servico_descarte.definir_metodo_tratamento(sol_r3, MetodoTratamentoFactory.criar_reciclagem())
    servico_descarte.avancar_estado_solicitacao(sol_r3)
    servico_descarte.avancar_estado_solicitacao(sol_r3)
    servico_descarte.avancar_estado_solicitacao(sol_r3)

    sol_r4 = servico_descarte.criar_solicitacao(cidadao1, ponto1)
    servico_descarte.adicionar_item_solicitacao(sol_r4, DispositivoFactory.criar_celular('cel-050', 'iPhone 7', 0.138), 3, 'bateria inchada')
    servico_descarte.definir_metodo_tratamento(sol_r4, MetodoTratamentoFactory.criar_reciclagem())
    servico_descarte.avancar_estado_solicitacao(sol_r4)
    servico_descarte.avancar_estado_solicitacao(sol_r4)
    servico_descarte.avancar_estado_solicitacao(sol_r4)

    sol_r5 = servico_descarte.criar_solicitacao(empresa, ponto3)
    servico_descarte.adicionar_item_solicitacao(sol_r5, DispositivoFactory.criar_computador('comp-050', 'Roteador TP-Link', 0.3), 10, 'lote equipamentos rede')
    servico_descarte.adicionar_item_solicitacao(sol_r5, DispositivoFactory.criar_computador('comp-051', 'Switch 24 portas', 2.1), 3)
    servico_descarte.definir_metodo_tratamento(sol_r5, MetodoTratamentoFactory.criar_reciclagem())
    servico_descarte.avancar_estado_solicitacao(sol_r5)
    servico_descarte.avancar_estado_solicitacao(sol_r5)
    servico_descarte.avancar_estado_solicitacao(sol_r5)

    # ── ESTADO: REUTILIZADO (4 solicitações) ───────────────────────
    sol_ru1 = servico_descarte.criar_solicitacao(cidadao1, ponto3)
    servico_descarte.adicionar_item_solicitacao(sol_ru1, DispositivoFactory.criar_computador('comp-005', 'Desktop HP EliteDesk', 6.8), 2)
    servico_descarte.definir_metodo_tratamento(sol_ru1, MetodoTratamentoFactory.criar_reuso())
    servico_descarte.avancar_estado_solicitacao(sol_ru1)
    servico_descarte.avancar_estado_solicitacao(sol_ru1)
    servico_descarte.avancar_estado_solicitacao(sol_ru1)

    sol_ru2 = servico_descarte.criar_solicitacao(empresa, ponto2)
    servico_descarte.adicionar_item_solicitacao(sol_ru2, DispositivoFactory.criar_computador('comp-006', 'Notebook Lenovo ThinkPad', 1.95), 3)
    servico_descarte.adicionar_item_solicitacao(sol_ru2, DispositivoFactory.criar_celular('cel-006', 'iPhone 8', 0.148), 6)
    servico_descarte.definir_metodo_tratamento(sol_ru2, MetodoTratamentoFactory.criar_reuso())
    servico_descarte.avancar_estado_solicitacao(sol_ru2)
    servico_descarte.avancar_estado_solicitacao(sol_ru2)
    servico_descarte.avancar_estado_solicitacao(sol_ru2)

    sol_ru3 = servico_descarte.criar_solicitacao(cidadao2, ponto1)
    servico_descarte.adicionar_item_solicitacao(sol_ru3, DispositivoFactory.criar_computador('comp-060', 'iMac 21.5" 2017', 5.55), 1, 'tela riscada')
    servico_descarte.definir_metodo_tratamento(sol_ru3, MetodoTratamentoFactory.criar_reuso())
    servico_descarte.avancar_estado_solicitacao(sol_ru3)
    servico_descarte.avancar_estado_solicitacao(sol_ru3)
    servico_descarte.avancar_estado_solicitacao(sol_ru3)

    sol_ru4 = servico_descarte.criar_solicitacao(empresa, ponto3)
    servico_descarte.adicionar_item_solicitacao(sol_ru4, DispositivoFactory.criar_celular('cel-060', 'iPad Pro 11"', 0.471), 4)
    servico_descarte.adicionar_item_solicitacao(sol_ru4, DispositivoFactory.criar_celular('cel-061', 'Samsung Tab A7', 0.476), 3)
    servico_descarte.definir_metodo_tratamento(sol_ru4, MetodoTratamentoFactory.criar_reuso())
    servico_descarte.avancar_estado_solicitacao(sol_ru4)
    servico_descarte.avancar_estado_solicitacao(sol_ru4)
    servico_descarte.avancar_estado_solicitacao(sol_ru4)

    # ── ESTADO: DESCARTADO (4 solicitações) ────────────────────────
    sol_d1 = servico_descarte.criar_solicitacao(cidadao2, ponto1)
    servico_descarte.adicionar_item_solicitacao(sol_d1, DispositivoFactory.criar_eletrodomestico('elet-002', 'Geladeira Brastemp', 45.0), 1, 'compressor queimado')
    servico_descarte.definir_metodo_tratamento(sol_d1, MetodoTratamentoFactory.criar_descarte_controlado())
    servico_descarte.avancar_estado_solicitacao(sol_d1)
    servico_descarte.avancar_estado_solicitacao(sol_d1)
    servico_descarte.avancar_estado_solicitacao(sol_d1)

    sol_d2 = servico_descarte.criar_solicitacao(empresa, ponto2)
    servico_descarte.adicionar_item_solicitacao(sol_d2, DispositivoFactory.criar_computador('comp-004', 'Desktop HP Compaq', 8.5), 5, 'lote de computadores antigos')
    servico_descarte.definir_metodo_tratamento(sol_d2, MetodoTratamentoFactory.criar_descarte_controlado())
    servico_descarte.avancar_estado_solicitacao(sol_d2)
    servico_descarte.avancar_estado_solicitacao(sol_d2)
    servico_descarte.avancar_estado_solicitacao(sol_d2)

    sol_d3 = servico_descarte.criar_solicitacao(cidadao1, ponto3)
    servico_descarte.adicionar_item_solicitacao(sol_d3, DispositivoFactory.criar_eletrodomestico('elet-070', 'Fogão Brastemp 4 bocas', 22.0), 1, 'sem condições de reparo')
    servico_descarte.definir_metodo_tratamento(sol_d3, MetodoTratamentoFactory.criar_descarte_controlado())
    servico_descarte.avancar_estado_solicitacao(sol_d3)
    servico_descarte.avancar_estado_solicitacao(sol_d3)
    servico_descarte.avancar_estado_solicitacao(sol_d3)

    sol_d4 = servico_descarte.criar_solicitacao(empresa, ponto1)
    servico_descarte.adicionar_item_solicitacao(sol_d4, DispositivoFactory.criar_eletrodomestico('elet-071', 'No-break APC 1500VA', 9.8), 4, 'baterias viciadas')
    servico_descarte.definir_metodo_tratamento(sol_d4, MetodoTratamentoFactory.criar_descarte_controlado())
    servico_descarte.avancar_estado_solicitacao(sol_d4)
    servico_descarte.avancar_estado_solicitacao(sol_d4)
    servico_descarte.avancar_estado_solicitacao(sol_d4)

    # ── ESTADO: CANCELADO (4 solicitações) ─────────────────────────
    sol_can1 = servico_descarte.criar_solicitacao(cidadao1, ponto1)
    servico_descarte.adicionar_item_solicitacao(sol_can1, DispositivoFactory.criar_celular('cel-007', 'Xiaomi Redmi 9', 0.198), 1)
    servico_descarte.cancelar_solicitacao(sol_can1, 'Usuário desistiu da entrega')

    sol_can2 = servico_descarte.criar_solicitacao(cidadao2, ponto3)
    servico_descarte.adicionar_item_solicitacao(sol_can2, DispositivoFactory.criar_eletrodomestico('elet-007', 'Ventilador Arno', 2.3), 2)
    servico_descarte.cancelar_solicitacao(sol_can2, 'Ponto de coleta indisponível')

    sol_can3 = servico_descarte.criar_solicitacao(cidadao1, ponto2)
    servico_descarte.adicionar_item_solicitacao(sol_can3, DispositivoFactory.criar_computador('comp-070', 'Webcam Logitech C920', 0.162), 1)
    servico_descarte.cancelar_solicitacao(sol_can3, 'Endereço incorreto informado')

    sol_can4 = servico_descarte.criar_solicitacao(empresa, ponto3)
    servico_descarte.adicionar_item_solicitacao(sol_can4, DispositivoFactory.criar_celular('cel-070', 'iPhone 6S', 0.143), 10, 'lote para descarte')
    servico_descarte.cancelar_solicitacao(sol_can4, 'Lote redirecionado para outra unidade')

    # ── HISTÓRICO DE ENTREGAS (João Silva) ──────────────────────────
    dados.salvar_entrega('56492574920', 'user-1', 13.95, 'Ecotech', '13 Set 2025', '13:02', 'finalizado')
    dados.salvar_entrega('58293049159', 'user-1', 8.19,  'Ecotech', '10 Set 2025', '08:55', 'finalizado')
    dados.salvar_entrega('98358259431', 'user-1', 6.41,  'Ecotech', '08 Set 2025', '15:31', 'cancelado')
    dados.salvar_entrega('47389088043', 'user-1', 27.65, 'Ecotech', '03 Set 2025', '16:44', 'finalizado')
    dados.salvar_entrega('57463968973', 'user-1', 12.53, 'Ecotech', '02 Set 2025', '08:21', 'finalizado')
    dados.salvar_entrega('61927384019', 'user-1', 19.80, 'Ecotech', '20 Ago 2025', '10:15', 'finalizado')
    dados.salvar_entrega('73849201938', 'user-1', 4.50,  'Ecotech', '15 Ago 2025', '14:30', 'reciclado')
    dados.salvar_entrega('84920173641', 'user-1', 31.20, 'Ecotech', '05 Ago 2025', '09:00', 'finalizado')
    dados.salvar_entrega('92837461029', 'user-1', 9.75,  'Ecotech', '28 Jul 2025', '11:45', 'finalizado')


if __name__ == '__main__':
    app = criar_app()
    app.run(debug=True, port=5000)
