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
    ServicoUsuario,
    ServicoSaque,
    ServicoAutenticacao,
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
    from datetime import timedelta
    app = Flask(__name__)
    app.secret_key = "ecotech-secret-key-2026"
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)
    
    # instancia unica de dados compartilhada por todos os servicos
    dados = Dados()
    
    # servicos com persistencia
    servico_usuario = ServicoUsuario(dados)
    servico_ponto = ServicoPontoColeta(dados)
    servico_descarte = ServicoDescarte(dados)
    servico_relatorio = ServicoRelatorio()
    servico_saque = ServicoSaque(dados)
    servico_autenticacao = ServicoAutenticacao(servico_usuario)
    
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
        """Página de login com autenticação real por credencial e senha."""
        if usuario_logado():
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            tipo      = request.form.get('tipo', 'cidadao')
            credencial = request.form.get('credencial', '').strip()
            senha      = request.form.get('senha', '')

            # normaliza CPF/CNPJ removendo pontuação (aceita "123.456.789-09" ou "12345678909")
            if tipo in ('cidadao', 'empresa'):
                credencial = credencial.replace('.', '').replace('-', '').replace('/', '').replace(' ', '')

            usuario_obj = servico_autenticacao.autenticar(tipo, credencial, senha)

            if usuario_obj is None:
                flash('Credencial ou senha inválidos.', 'error')
                return render_template('login.html', tipo_selecionado=tipo)

            dados_sessao = servico_autenticacao.criar_dados_sessao(usuario_obj)
            session.permanent = True
            session['user_id']   = dados_sessao['user_id']
            session['user_nome'] = dados_sessao['user_nome']
            session['user_tipo'] = dados_sessao['user_tipo']

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

            # loga o usuário automaticamente após o cadastro
            dados_sessao = servico_autenticacao.criar_dados_sessao(usuario_obj)
            session.permanent = True
            session['user_id']   = dados_sessao['user_id']
            session['user_nome'] = dados_sessao['user_nome']
            session['user_tipo'] = dados_sessao['user_tipo']

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
        
        if usuario['tipo'] == 'administrador':
            metricas = servico_descarte.calcular_metricas(todas_solicitacoes)

            return render_template(
                'dashboard.html',
                usuario=usuario,
                solicitacoes=todas_solicitacoes[:10],
                total_descartado=metricas['peso_total'],
                impacto_evitado=metricas['impacto_total'],
                pontos_acumulados=0,
                total_sistema=metricas['peso_total'],
                total_processadas=metricas['total_processadas'],
                is_empresa=False,
                is_admin=True
            )
        
        # solicitacoes do usuario
        solicitacoes_usuario = [
            s for s in todas_solicitacoes 
            if s.usuario.id == usuario['id']
        ]
        
        # calcula metricas do usuario
        metricas_usuario = servico_descarte.calcular_metricas(solicitacoes_usuario)

        # dashboard diferente para empresa
        if usuario['tipo'] == 'empresa':
            metricas_sistema = servico_descarte.calcular_metricas(todas_solicitacoes)

            return render_template(
                'dashboard.html',
                usuario=usuario,
                solicitacoes=solicitacoes_usuario,
                total_descartado=metricas_usuario['peso_total'],
                impacto_evitado=metricas_usuario['impacto_total'],
                pontos_acumulados=metricas_usuario['pontos'],
                total_sistema=metricas_sistema['peso_total'],
                total_processadas=metricas_sistema['total_processadas'],
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
        progresso = servico_descarte.calcular_progresso(solicitacoes_usuario)
        tier_info = servico_descarte.calcular_info_tier(metricas_usuario['pontos'])
        saldo_acumulado = servico_saque.calcular_saldo_disponivel(todas_solicitacoes, usuario['id'])
        meta_missao = 15

        return render_template(
            'dashboard.html',
            usuario=usuario,
            solicitacoes=solicitacoes_usuario,
            entregas=entregas[:10],
            total_descartado=metricas_usuario['peso_total'],
            impacto_evitado=metricas_usuario['impacto_total'],
            pontos_acumulados=metricas_usuario['pontos'],
            saldo_acumulado=saldo_acumulado,
            tier_nome=tier_info['nome'],
            proximo_tier_nome=tier_info['proximo_nome'],
            meta_tier=tier_info['meta'] or 1200,
            meta_missao=meta_missao,
            progresso_missao=progresso['progresso_missao'],
            progresso_tier=tier_info['progresso_pct'],
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
            try:
                tipo_dispositivo = request.form.get('tipo_dispositivo', 'celular')
                nome_dispositivo  = request.form.get('nome', '').strip()
                peso_kg           = float(request.form.get('peso_kg', 1.0))
                quantidade        = int(request.form.get('quantidade', 1))
                observacoes       = request.form.get('observacoes_endereco', '').strip()

                usuario_obj = servico_usuario.buscar_usuario(usuario['id'])
                if not usuario_obj:
                    flash('Usuário não encontrado.', 'error')
                    return redirect(url_for('nova_solicitacao'))

                pontos_disponiveis = servico_ponto.listar_pontos()
                ponto = pontos_disponiveis[0] if pontos_disponiveis else None

                solicitacao = servico_descarte.criar_solicitacao(usuario_obj, ponto)

                dispositivo = DispositivoFactory.criar_dispositivo(
                    tipo_dispositivo,
                    {'id': str(__import__('uuid').uuid4()), 'nome': nome_dispositivo, 'peso_kg': peso_kg}
                )
                servico_descarte.adicionar_item_solicitacao(solicitacao, dispositivo, quantidade, observacoes)

                flash('Solicitação criada com sucesso!', 'success')
                return redirect(url_for('dashboard'))

            except ValueError as e:
                flash(str(e), 'error')
        
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

        def _tipo_notificacao(msg: str):
            m = msg.lower()
            if any(p in m for p in ['r$', 'receb', 'saque', 'crédito', 'incentivo']):
                return 'success', 'dinheiro'
            if any(p in m for p in ['coleta', 'ponto', 'solicitac']):
                return 'primary', 'coleta'
            if any(p in m for p in ['promo', 'bônus', 'bonus']):
                return 'warning', 'oferta'
            return 'info', 'mapa'

        notificacoes = []
        for n in notificacoes_db:
            tipo, icone = _tipo_notificacao(n['mensagem'])
            notificacoes.append({
                'titulo': n['mensagem'][:70] + ('…' if len(n['mensagem']) > 70 else ''),
                'mensagem': n['mensagem'],
                'data': datetime.strptime(n['timestamp'], '%d/%m/%Y %H:%M:%S'),
                'lida': False,
                'tipo': tipo,
                'icone': icone,
            })
        
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
    
    @app.route('/saque', methods=['GET', 'POST'])
    def saque():
        """Página de saque/carteira."""
        if not usuario_logado():
            return redirect(url_for('login'))

        usuario = dados_usuario()

        todas_solicitacoes = servico_descarte.listar_solicitacoes()
        saldo = servico_saque.calcular_saldo_disponivel(todas_solicitacoes, usuario['id'])
        pontos = servico_saque.calcular_pontos(todas_solicitacoes, usuario['id'])
        historico_saques = servico_saque.listar_saques(usuario['id'])

        if request.method == 'POST':
            try:
                valor_str = request.form.get('valor_saque', '0').replace('R$', '').replace(',', '.').strip()
                valor = float(valor_str)
                metodo = request.form.get('metodo', 'Pix')

                resultado = servico_saque.solicitar_saque(
                    usuario['id'], valor, metodo, saldo
                )

                flash(
                    f'Saque de R$ {resultado["valor"]:.2f} solicitado com sucesso via {resultado["metodo"]}!',
                    'success'
                )
                return redirect(url_for('saque'))

            except (ValueError, TypeError) as e:
                flash(str(e), 'error')

        return render_template(
            'saque.html',
            usuario=usuario,
            saldo=saldo,
            pontos=pontos,
            historico_saques=historico_saques,
            cpf_usuario=getattr(servico_usuario.buscar_usuario(usuario['id']), 'cpf', ''),
            email_usuario=getattr(servico_usuario.buscar_usuario(usuario['id']), 'email', ''),
        )
    
    @app.route('/perfil')
    def perfil():
        """Página de perfil do usuário."""
        if not usuario_logado():
            return redirect(url_for('login'))
        
        usuario = dados_usuario()
        
        todas_solicitacoes = servico_descarte.listar_solicitacoes()
        solicitacoes_usuario = [
            s for s in todas_solicitacoes if s.usuario.id == usuario['id']
        ]
        metricas = servico_descarte.calcular_metricas(solicitacoes_usuario)
        tier_info = servico_descarte.calcular_info_tier(metricas['pontos'])

        # rank: quantos usuários têm mais pontos que o usuário atual
        rank = 1
        for u in servico_usuario.listar_usuarios():
            if u.id != usuario['id']:
                sols_u = [s for s in todas_solicitacoes if s.usuario.id == u.id]
                if servico_descarte.calcular_metricas(sols_u)['pontos'] > metricas['pontos']:
                    rank += 1

        # conquistas baseadas no total de solicitações do usuário
        _milestones = [(1, '1º descarte', 'medalha'), (5, '5 descartes', 'medalha'),
                       (10, '10 descartes', 'trofeu'), (20, '20 descartes', 'trofeu')]
        conquistas = [
            {'valor': m, 'label': lbl, 'icone': ico, 'ativa': len(solicitacoes_usuario) >= m}
            for m, lbl, ico in _milestones
        ]

        return render_template(
            'perfil.html',
            usuario=usuario,
            total_solicitacoes=len(solicitacoes_usuario),
            pontos=metricas['pontos'],
            tier_info=tier_info,
            rank=rank,
            conquistas=conquistas,
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
        solicitacoes_filtradas = servico_descarte.filtrar_por_estado(solicitacoes_usuario, filtro_estado)

        # calcula estatisticas baseadas nas solicitações que o usuário pode ver
        stats = servico_descarte.calcular_stats_estados(solicitacoes_usuario)
        
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

        cidadaos_raw = dados.buscar_todos_cidadaos_admin()
        empresas_raw = dados.buscar_todos_empresas_admin()

        from datetime import datetime

        def formatar_data(data_str):
            if not data_str:
                return '-'
            try:
                dt = datetime.strptime(data_str, '%Y-%m-%d %H:%M:%S')
                return dt.strftime('%d/%m/%Y %H:%M:%S')
            except Exception:
                return data_str

        cidadaos = [
            {**c, 'data_cadastro': formatar_data(c['data_cadastro'])}
            for c in cidadaos_raw
        ]
        empresas = [
            {**e, 'data_cadastro': formatar_data(e['data_cadastro'])}
            for e in empresas_raw
        ]
        
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
    """Cria os 3 perfis base e dados de demonstração para o sistema."""

    if dados.contar_usuarios() > 0:
        return  # banco já populado, não sobrescrever

    # ---- usuários base ----
    cidadao1 = servico_usuario.criar_usuario('cidadao', {
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
        1000.0
    )

    ponto2 = servico_ponto.criar_ponto_coleta(
        'Centro de Coleta Cariri',
        'Av. Padre Cícero, 500 - Centro',
        -7.2123,
        -39.3145,
        2000.0
    )

    # ---- solicitações de exemplo ----

    # solicitacao 1 - estado inicial (solicitado)
    sol1 = servico_descarte.criar_solicitacao(cidadao1, ponto1)
    celular1 = DispositivoFactory.criar_celular('cel-001', 'iPhone 11', 0.194)
    notebook1 = DispositivoFactory.criar_computador('comp-001', 'Dell Inspiron', 2.1)
    servico_descarte.adicionar_item_solicitacao(sol1, celular1, 1, 'tela quebrada')
    servico_descarte.adicionar_item_solicitacao(sol1, notebook1, 1, 'nao liga mais')

    # solicitacao 2 - ja foi coletada (cidadao)
    sol2 = servico_descarte.criar_solicitacao(cidadao1, ponto2)
    tv1 = DispositivoFactory.criar_eletrodomestico('elet-001', 'TV Samsung 32"', 5.5)
    servico_descarte.adicionar_item_solicitacao(sol2, tv1, 1)
    servico_descarte.avancar_estado_solicitacao(sol2)  # coletado

    # solicitacao 3 - em processamento (empresa)
    sol3 = servico_descarte.criar_solicitacao(empresa, ponto1)
    celular2 = DispositivoFactory.criar_celular('cel-002', 'Samsung Galaxy S10', 0.175)
    tablet1 = DispositivoFactory.criar_celular('cel-003', 'iPad Air', 0.460)
    servico_descarte.adicionar_item_solicitacao(sol3, celular2, 3)
    servico_descarte.adicionar_item_solicitacao(sol3, tablet1, 2)
    metodo = MetodoTratamentoFactory.criar_reciclagem()
    servico_descarte.definir_metodo_tratamento(sol3, metodo)
    servico_descarte.avancar_estado_solicitacao(sol3)  # coletado
    servico_descarte.avancar_estado_solicitacao(sol3)  # em processamento

    # solicitacao 4 - finalizada / reciclada (cidadao)
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

    # solicitacao 5 - pendente com eletrodoméstico (cidadao)
    sol5 = servico_descarte.criar_solicitacao(cidadao1, ponto1)
    geladeira = DispositivoFactory.criar_eletrodomestico('elet-002', 'Geladeira Brastemp', 45.0)
    servico_descarte.adicionar_item_solicitacao(sol5, geladeira, 1, 'compressor queimado')

    # solicitacao 6 - em processamento / reuso (empresa)
    sol6 = servico_descarte.criar_solicitacao(empresa, ponto2)
    pc1 = DispositivoFactory.criar_computador('comp-004', 'Desktop HP', 8.5)
    servico_descarte.adicionar_item_solicitacao(sol6, pc1, 5, 'lote de computadores antigos')
    metodo3 = MetodoTratamentoFactory.criar_reuso()
    servico_descarte.definir_metodo_tratamento(sol6, metodo3)
    servico_descarte.avancar_estado_solicitacao(sol6)  # coletado
    servico_descarte.avancar_estado_solicitacao(sol6)  # em processamento

    # ---- histórico de entregas (João Silva) ----
    dados.salvar_entrega(
        '56492574920',
        'user-1',
        13.95,
        'Recicla Kariri',
        '13 Set 2025',
        '13:02',
        'finalizado'
    )

    dados.salvar_entrega(
        '58293049159',
        'user-1',
        8.19,
        'Recicla Kariri',
        '10 Set 2025',
        '08:55',
        'finalizado'
    )

    dados.salvar_entrega(
        '98358259431',
        'user-1',
        6.41,
        'Recicla Kariri',
        '08 Set 2025',
        '15:31',
        'cancelado'
    )

    dados.salvar_entrega(
        '47389088043',
        'user-1',
        27.65,
        'Recicla Kariri',
        '03 Set 2025',
        '16:44',
        'finalizado'
    )

    dados.salvar_entrega(
        '57463968973',
        'user-1',
        12.53,
        'Recicla Kariri',
        '02 Set 2025',
        '08:21',
        'finalizado'
    )


if __name__ == '__main__':
    app = criar_app()
    app.run(debug=True, port=5000)
