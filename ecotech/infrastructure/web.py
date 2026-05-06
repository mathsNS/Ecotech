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
    
    # dados exemplo, só roda no processo pai (não no filho do reloader)
    import os
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
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

        entregas = []
        for e in entregas_db:
            try:
                dt = datetime.strptime(e['data'], '%Y-%m-%d')
                data_formatada = dt.strftime('%d/%m/%Y')
            except (ValueError, TypeError):
                data_formatada = e['data']
                dt = datetime.min
            entregas.append({
                'valor': e['valor'],
                'empresa': e['empresa'],
                'id': e['id'],
                'data': e['data'],
                'data_formatada': data_formatada,
                'hora': e['hora'],
                'status': e['status'],
                '_dt': dt,
            })

        entregas.sort(key=lambda x: x['_dt'], reverse=True)
        
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
                tipo_dispositivo  = request.form.get('tipo_dispositivo', 'celular')
                nome_dispositivo  = request.form.get('nome', '').strip()
                peso_kg           = float(request.form.get('peso_kg', 1.0))
                quantidade        = int(request.form.get('quantidade', 1))
                observacoes       = request.form.get('observacoes_endereco', '').strip()
                ponto_id          = request.form.get('ponto_id', '').strip()
                tipo_coleta       = request.form.get('tipo_coleta', 'domiciliar').strip()
                endereco_coleta   = request.form.get('endereco_coleta', '').strip()
                nome_contato      = request.form.get('nome_contato', '').strip()
                data_coleta       = request.form.get('data_coleta', '').strip()
                horario_coleta    = request.form.get('horario_coleta', '').strip()
                data_agendamento  = f"{data_coleta} {horario_coleta}".strip() if data_coleta else None

                usuario_obj = servico_usuario.buscar_usuario(usuario['id'])
                if not usuario_obj:
                    flash('Usuário não encontrado.', 'error')
                    return redirect(url_for('nova_solicitacao'))

                ponto = servico_ponto.buscar_ponto(ponto_id) if ponto_id else None
                if ponto is None and tipo_coleta == 'entrega_ponto':
                    # sem ponto válido para entrega, usa o primeiro disponível
                    pontos_disponiveis = servico_ponto.listar_pontos()
                    ponto = pontos_disponiveis[0] if pontos_disponiveis else None
                # para domiciliar, ponto fica None (empresa é atribuída depois)

                solicitacao = servico_descarte.criar_solicitacao(usuario_obj, ponto)

                dispositivo = DispositivoFactory.criar_dispositivo(
                    tipo_dispositivo,
                    {'id': str(__import__('uuid').uuid4()), 'nome': nome_dispositivo, 'peso_kg': peso_kg}
                )
                servico_descarte.adicionar_item_solicitacao(solicitacao, dispositivo, quantidade, observacoes)

                dados.atualizar_detalhes_coleta(
                    solicitacao.id, tipo_coleta, endereco_coleta, nome_contato, data_agendamento
                )

                dados.salvar_notificacao(
                    usuario['id'],
                    f'Sua solicitação de descarte do {nome_dispositivo} foi recebida e aguarda coleta.'
                )

                # notificar empresa(s)
                if tipo_coleta == 'entrega_ponto' and ponto_id:
                    ponto_raw = dados.buscar_ponto_coleta(ponto_id)
                    if ponto_raw and ponto_raw['id_empresa']:
                        dados.salvar_notificacao(
                            ponto_raw['id_empresa'],
                            f'Nova solicitação de entrega recebida de {usuario["nome"]} para {nome_dispositivo}. Acesse o sistema para confirmar.'
                        )
                else:
                    # domiciliar: notifica todas as empresas
                    for p in dados.buscar_pontos_para_selecao():
                        if p['id_empresa']:
                            dados.salvar_notificacao(
                                p['id_empresa'],
                                f'Nova solicitação de coleta domiciliar de {usuario["nome"]} para {nome_dispositivo}. Acesse o sistema para aceitar.'
                            )

                flash('Solicitação criada com sucesso!', 'success')
                return redirect(url_for('dashboard'))

            except ValueError as e:
                flash(str(e), 'error')
        
        from datetime import date
        hoje = date.today().strftime('%Y-%m-%d')
        tipo_coleta_param = request.args.get('tipo', 'domiciliar')
        ponto_id_param    = request.args.get('ponto_id', '')
        # para entrega_ponto, busca dados do ponto selecionado
        ponto_selecionado = None
        if tipo_coleta_param == 'entrega_ponto' and ponto_id_param:
            ponto_selecionado = dados.buscar_ponto_coleta(ponto_id_param)
        return render_template(
            'nova_solicitacao.html',
            usuario=usuario,
            today=hoje,
            tipo_coleta=tipo_coleta_param,
            ponto_selecionado=ponto_selecionado,
        )
    
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

        entregas = []
        for e in entregas_db:
            try:
                dt = datetime.strptime(e['data'], '%Y-%m-%d')
                data_formatada = dt.strftime('%d/%m/%Y')
            except (ValueError, TypeError):
                data_formatada = e['data']
                dt = datetime.min
            entregas.append({
                'valor': e['valor'],
                'empresa': e['empresa'],
                'id': e['id'],
                'data': e['data'],
                'data_formatada': data_formatada,
                'hora': e['hora'],
                'status': e['status'],
                '_dt': dt,
            })

        entregas.sort(key=lambda x: x['_dt'], reverse=True)

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
        
        # lê filtro de período (GET params)
        data_inicio_str = request.args.get('data_inicio', '').strip()
        data_fim_str    = request.args.get('data_fim', '').strip()
        data_inicio_dt  = None
        data_fim_dt     = None
        try:
            if data_inicio_str:
                data_inicio_dt = datetime.strptime(data_inicio_str, '%Y-%m-%d')
            if data_fim_str:
                data_fim_dt = datetime.strptime(data_fim_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        except ValueError:
            pass

        relatorio = servico_relatorio.gerar_relatorio_periodo(
            titulo_relatorio,
            solicitacoes_para_relatorio,
            data_inicio=data_inicio_dt,
            data_fim=data_fim_dt
        )

        metricas = relatorio.gerar_relatorio()

        # filtra solicitacoes finalizadas para mostrar na tabela (respeitando o filtro de data)
        estados_finais = {'Reciclado', 'Reutilizado', 'Descartado'}
        solicitacoes_finalizadas = [
            s for s in solicitacoes_para_relatorio
            if s.estado.obter_nome() in estados_finais
            and (data_inicio_dt is None or s._data_criacao >= data_inicio_dt)
            and (data_fim_dt    is None or s._data_criacao <= data_fim_dt)
        ]

        return render_template(
            'relatorios.html',
            usuario=usuario,
            metricas=metricas,
            solicitacoes=solicitacoes_finalizadas,
            is_admin=usuario['tipo'] == 'administrador',
            data_inicio_str=data_inicio_str,
            data_fim_str=data_fim_str,
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
        """API para listar solicitações do usuário logado."""
        if not usuario_logado():
            return jsonify({'error': 'Not authenticated'}), 401

        usuario = dados_usuario()
        todas = servico_descarte.listar_solicitacoes()

        if usuario['tipo'] == 'administrador':
            lista = todas
        else:
            lista = [s for s in todas if s.usuario.id == usuario['id']]

        resultado = []
        for s in lista:
            resultado.append({
                'id': s.id,
                'usuario': s.usuario.nome,
                'ponto': s.ponto_coleta.nome if s.ponto_coleta else None,
                'estado': s.estado.obter_nome(),
                'peso_kg': s.calcular_peso_total(),
                'itens': len(s.itens),
            })

        return jsonify(resultado)
    
    @app.route('/usuarios/<id_usuario>/desativar', methods=['POST'])
    def desativar_usuario(id_usuario):
        """Desativar usuário (apenas admin)."""
        if not usuario_logado():
            return jsonify({'error': 'Not authenticated'}), 401

        usuario = dados_usuario()
        if usuario['tipo'] != 'administrador':
            return jsonify({'error': 'Acesso negado'}), 403

        dados.desativar_usuario(id_usuario)
        return jsonify({'ok': True})

    return app


def _inicializar_dados_exemplo(servico_usuario, servico_ponto, servico_descarte, dados):
    """Cria perfis base e dados de demonstração para o sistema."""

    if dados.contar_usuarios() > 0:
        return

    # ---- contas credenciadas (login documentado) ----
    cidadao1 = servico_usuario.criar_usuario('cidadao', {
        'id': 'user-1', 'nome': 'João Silva',
        'email': 'joao@ecotech.com', 'cpf': '12345678909'
    }, senha='cidadao123')

    empresa1 = servico_usuario.criar_usuario('empresa', {
        'id': 'user-2', 'nome': 'Recicla Kariri',
        'email': 'contato@recilakariri.com', 'cnpj': '11222333000181',
        'razao_social': 'Recicla Kariri Reciclagem LTDA'
    }, senha='empresa123')

    servico_usuario.criar_usuario('administrador', {
        'id': 'USR-ADM-001', 'nome': 'Admin Ecotech',
        'email': 'admin@ecotech.com', 'nivel_acesso': 3
    }, senha='admin123')

    # ---- cidadãos adicionais ----
    cidadao2 = servico_usuario.criar_usuario('cidadao', {
        'id': 'user-3', 'nome': 'Ana Beatriz Ferreira',
        'email': 'ana.ferreira@gmail.com', 'cpf': '98765432100'
    }, senha='ana123')
    cidadao3 = servico_usuario.criar_usuario('cidadao', {
        'id': 'user-4', 'nome': 'Carlos Eduardo Mendes',
        'email': 'carlos.mendes@outlook.com', 'cpf': '34945611840'
    }, senha='carlos123')
    cidadao4 = servico_usuario.criar_usuario('cidadao', {
        'id': 'user-5', 'nome': 'Fernanda Lima',
        'email': 'fernanda.lima@yahoo.com.br', 'cpf': '47585901330'
    }, senha='fernanda123')
    cidadao5 = servico_usuario.criar_usuario('cidadao', {
        'id': 'user-6', 'nome': 'Rafael Gonçalves',
        'email': 'rafael.goncalves@hotmail.com', 'cpf': '70548478490'
    }, senha='rafael123')

    # ---- empresas adicionais ----
    empresa2 = servico_usuario.criar_usuario('empresa', {
        'id': 'user-7', 'nome': 'TechLixo Soluções',
        'email': 'contato@techlixo.com.br', 'cnpj': '14380200000121',
        'razao_social': 'TechLixo Soluções Ambientais LTDA'
    }, senha='techlixo123')
    empresa3 = servico_usuario.criar_usuario('empresa', {
        'id': 'user-8', 'nome': 'GreenCycle Nordeste',
        'email': 'admin@greencycle.com.br', 'cnpj': '33000167000101',
        'razao_social': 'GreenCycle Nordeste Reciclagem S.A.'
    }, senha='greencycle123')

    # ---- pontos de coleta vinculados às empresas ----
    ponto_empresa1 = servico_ponto.criar_ponto_coleta(
        'Recicla Kariri - Centro de Triagem',
        'Av. Leão Sampaio, 600 - Triângulo, Juazeiro do Norte, CE',
        -7.2192, -39.3287, 3000.0
    )
    dados.vincular_empresa_a_ponto(ponto_empresa1.id, empresa1.id)

    ponto_empresa2 = servico_ponto.criar_ponto_coleta(
        'TechLixo Soluções - Unidade JDN',
        'R. São Pedro, 1250 - São José, Juazeiro do Norte, CE',
        -7.2071, -39.3152, 2500.0
    )
    dados.vincular_empresa_a_ponto(ponto_empresa2.id, empresa2.id)

    ponto_empresa3 = servico_ponto.criar_ponto_coleta(
        'GreenCycle Nordeste - Planta Crato',
        'Av. Contorno Norte, 850 - Vila Alta, Crato, CE',
        -7.2295, -39.4187, 4000.0
    )
    dados.vincular_empresa_a_ponto(ponto_empresa3.id, empresa3.id)

    # aliases para o seed (pontos distribuídos entre as 3 empresas)
    ponto1 = ponto_empresa1  # João Silva, Ana, Carlos → Recicla Kariri
    ponto2 = ponto_empresa1
    ponto3 = ponto_empresa2  # Rafael, Ana → TechLixo
    ponto4 = ponto_empresa3  # Fernanda, TechLixo → GreenCycle
    ponto5 = ponto_empresa2

    # ---- solicitações: João Silva ----
    sol1 = servico_descarte.criar_solicitacao(cidadao1, ponto1)
    servico_descarte.adicionar_item_solicitacao(sol1,
        DispositivoFactory.criar_celular('cel-001', 'iPhone 11', 0.194), 1, 'tela quebrada')
    servico_descarte.adicionar_item_solicitacao(sol1,
        DispositivoFactory.criar_computador('comp-001', 'Dell Inspiron 15 3000', 2.1), 1, 'não liga mais')

    sol2 = servico_descarte.criar_solicitacao(cidadao1, ponto2)
    servico_descarte.adicionar_item_solicitacao(sol2,
        DispositivoFactory.criar_eletrodomestico('elet-001', 'TV Samsung 32" Smart', 5.5), 1)
    servico_descarte.avancar_estado_solicitacao(sol2)

    sol3 = servico_descarte.criar_solicitacao(cidadao1, ponto2)
    servico_descarte.adicionar_item_solicitacao(sol3,
        DispositivoFactory.criar_computador('comp-002', 'Monitor LG 24" Full HD', 3.2), 1)
    servico_descarte.adicionar_item_solicitacao(sol3,
        DispositivoFactory.criar_computador('comp-003', 'Teclado Mecânico Redragon', 0.8), 1)
    m = MetodoTratamentoFactory.criar_reciclagem()
    servico_descarte.definir_metodo_tratamento(sol3, m)
    servico_descarte.avancar_estado_solicitacao(sol3)
    servico_descarte.avancar_estado_solicitacao(sol3)
    servico_descarte.avancar_estado_solicitacao(sol3)

    sol4 = servico_descarte.criar_solicitacao(cidadao1, ponto1)
    servico_descarte.adicionar_item_solicitacao(sol4,
        DispositivoFactory.criar_eletrodomestico('elet-002', 'Geladeira Brastemp Frost Free 360L', 45.0), 1, 'compressor queimado')

    sol5 = servico_descarte.criar_solicitacao(cidadao1, ponto3)
    servico_descarte.adicionar_item_solicitacao(sol5,
        DispositivoFactory.criar_computador('comp-004', 'Impressora HP LaserJet Pro M404n', 6.2), 2, 'cartucho vazando')
    m2 = MetodoTratamentoFactory.criar_reuso()
    servico_descarte.definir_metodo_tratamento(sol5, m2)
    servico_descarte.avancar_estado_solicitacao(sol5)
    servico_descarte.avancar_estado_solicitacao(sol5)
    servico_descarte.avancar_estado_solicitacao(sol5)

    sol6 = servico_descarte.criar_solicitacao(cidadao1, ponto5)
    servico_descarte.adicionar_item_solicitacao(sol6,
        DispositivoFactory.criar_celular('cel-002', 'Samsung Galaxy A52', 0.189), 1)
    servico_descarte.adicionar_item_solicitacao(sol6,
        DispositivoFactory.criar_celular('cel-003', 'Xiaomi Redmi Note 11', 0.179), 1, 'bateria inchada')
    m3 = MetodoTratamentoFactory.criar_reciclagem()
    servico_descarte.definir_metodo_tratamento(sol6, m3)
    servico_descarte.avancar_estado_solicitacao(sol6)
    servico_descarte.avancar_estado_solicitacao(sol6)
    servico_descarte.avancar_estado_solicitacao(sol6)

    sol7 = servico_descarte.criar_solicitacao(cidadao1, ponto2)
    servico_descarte.adicionar_item_solicitacao(sol7,
        DispositivoFactory.criar_eletrodomestico('elet-003', 'Air Fryer Mondial 4L', 3.8), 1, 'resistência queimada')
    servico_descarte.adicionar_item_solicitacao(sol7,
        DispositivoFactory.criar_eletrodomestico('elet-004', 'Liquidificador Arno Clic Pro', 1.6), 1)
    m4 = MetodoTratamentoFactory.criar_reciclagem()
    servico_descarte.definir_metodo_tratamento(sol7, m4)
    servico_descarte.avancar_estado_solicitacao(sol7)
    servico_descarte.avancar_estado_solicitacao(sol7)
    servico_descarte.avancar_estado_solicitacao(sol7)

    # ---- solicitações: Recicla Kariri ----
    sol_rk1 = servico_descarte.criar_solicitacao(empresa1, ponto1)
    servico_descarte.adicionar_item_solicitacao(sol_rk1,
        DispositivoFactory.criar_celular('cel-004', 'Samsung Galaxy S10', 0.175), 3)
    servico_descarte.adicionar_item_solicitacao(sol_rk1,
        DispositivoFactory.criar_celular('cel-005', 'iPad Air 3ª geração', 0.460), 2)
    m5 = MetodoTratamentoFactory.criar_reciclagem()
    servico_descarte.definir_metodo_tratamento(sol_rk1, m5)
    servico_descarte.avancar_estado_solicitacao(sol_rk1)
    servico_descarte.avancar_estado_solicitacao(sol_rk1)

    sol_rk2 = servico_descarte.criar_solicitacao(empresa1, ponto2)
    servico_descarte.adicionar_item_solicitacao(sol_rk2,
        DispositivoFactory.criar_computador('comp-005', 'Desktop HP EliteDesk 800 G5', 8.5), 5, 'lote corporativo')
    m6 = MetodoTratamentoFactory.criar_reuso()
    servico_descarte.definir_metodo_tratamento(sol_rk2, m6)
    servico_descarte.avancar_estado_solicitacao(sol_rk2)
    servico_descarte.avancar_estado_solicitacao(sol_rk2)

    sol_rk3 = servico_descarte.criar_solicitacao(empresa1, ponto4)
    servico_descarte.adicionar_item_solicitacao(sol_rk3,
        DispositivoFactory.criar_computador('comp-006', 'Servidor Dell PowerEdge R440', 12.0), 2, 'substituídos por novo modelo')
    m7 = MetodoTratamentoFactory.criar_reciclagem()
    servico_descarte.definir_metodo_tratamento(sol_rk3, m7)
    servico_descarte.avancar_estado_solicitacao(sol_rk3)
    servico_descarte.avancar_estado_solicitacao(sol_rk3)
    servico_descarte.avancar_estado_solicitacao(sol_rk3)

    sol_rk4 = servico_descarte.criar_solicitacao(empresa1, ponto3)
    servico_descarte.adicionar_item_solicitacao(sol_rk4,
        DispositivoFactory.criar_eletrodomestico('elet-005', 'Ar Condicionado Gree 12000BTU', 28.5), 4, 'gás refrigerante obsoleto')
    m8 = MetodoTratamentoFactory.criar_reciclagem()
    servico_descarte.definir_metodo_tratamento(sol_rk4, m8)
    servico_descarte.avancar_estado_solicitacao(sol_rk4)
    servico_descarte.avancar_estado_solicitacao(sol_rk4)
    servico_descarte.avancar_estado_solicitacao(sol_rk4)

    # ---- solicitações: Ana Beatriz ----
    sol_ana1 = servico_descarte.criar_solicitacao(cidadao2, ponto3)
    servico_descarte.adicionar_item_solicitacao(sol_ana1,
        DispositivoFactory.criar_celular('cel-006', 'Motorola Moto G82', 0.173), 1)
    servico_descarte.avancar_estado_solicitacao(sol_ana1)

    sol_ana2 = servico_descarte.criar_solicitacao(cidadao2, ponto2)
    servico_descarte.adicionar_item_solicitacao(sol_ana2,
        DispositivoFactory.criar_eletrodomestico('elet-006', 'Micro-ondas Electrolux MEF41', 11.0), 1, 'prato giratório quebrado')
    m9 = MetodoTratamentoFactory.criar_reciclagem()
    servico_descarte.definir_metodo_tratamento(sol_ana2, m9)
    servico_descarte.avancar_estado_solicitacao(sol_ana2)
    servico_descarte.avancar_estado_solicitacao(sol_ana2)
    servico_descarte.avancar_estado_solicitacao(sol_ana2)

    sol_ana3 = servico_descarte.criar_solicitacao(cidadao2, ponto1)
    servico_descarte.adicionar_item_solicitacao(sol_ana3,
        DispositivoFactory.criar_celular('cel-007', 'Notebook Samsung Book', 1.5), 1, 'tela com manchas')

    # ---- solicitações: Carlos Eduardo ----
    sol_car1 = servico_descarte.criar_solicitacao(cidadao3, ponto1)
    servico_descarte.adicionar_item_solicitacao(sol_car1,
        DispositivoFactory.criar_computador('comp-007', 'Notebook Lenovo ThinkPad E14', 1.85), 1)
    servico_descarte.adicionar_item_solicitacao(sol_car1,
        DispositivoFactory.criar_computador('comp-008', 'Mouse sem fio Logitech MX Master', 0.09), 2)

    sol_car2 = servico_descarte.criar_solicitacao(cidadao3, ponto5)
    servico_descarte.adicionar_item_solicitacao(sol_car2,
        DispositivoFactory.criar_eletrodomestico('elet-007', 'Micro System Philips BTB2595', 4.5), 1, 'caixa de som danificada')
    m10 = MetodoTratamentoFactory.criar_reciclagem()
    servico_descarte.definir_metodo_tratamento(sol_car2, m10)
    servico_descarte.avancar_estado_solicitacao(sol_car2)
    servico_descarte.avancar_estado_solicitacao(sol_car2)
    servico_descarte.avancar_estado_solicitacao(sol_car2)

    # ---- solicitações: Fernanda Lima ----
    sol_fer1 = servico_descarte.criar_solicitacao(cidadao4, ponto2)
    servico_descarte.adicionar_item_solicitacao(sol_fer1,
        DispositivoFactory.criar_celular('cel-008', 'Samsung Galaxy Tab A7', 0.476), 1)
    servico_descarte.adicionar_item_solicitacao(sol_fer1,
        DispositivoFactory.criar_celular('cel-009', 'AirPods Pro 2ª geração', 0.061), 2, 'bateria viciada')
    servico_descarte.avancar_estado_solicitacao(sol_fer1)

    sol_fer2 = servico_descarte.criar_solicitacao(cidadao4, ponto4)
    servico_descarte.adicionar_item_solicitacao(sol_fer2,
        DispositivoFactory.criar_eletrodomestico('elet-008', 'Cafeteira Nespresso Vertuo', 2.3), 1, 'bomba de pressão com defeito')
    m11 = MetodoTratamentoFactory.criar_reciclagem()
    servico_descarte.definir_metodo_tratamento(sol_fer2, m11)
    servico_descarte.avancar_estado_solicitacao(sol_fer2)
    servico_descarte.avancar_estado_solicitacao(sol_fer2)
    servico_descarte.avancar_estado_solicitacao(sol_fer2)

    # ---- solicitações: Rafael Gonçalves ----
    sol_raf1 = servico_descarte.criar_solicitacao(cidadao5, ponto3)
    servico_descarte.adicionar_item_solicitacao(sol_raf1,
        DispositivoFactory.criar_computador('comp-009', 'PC Gamer Pichau Orion', 9.2), 1, 'fonte queimada')
    servico_descarte.adicionar_item_solicitacao(sol_raf1,
        DispositivoFactory.criar_celular('cel-010', 'Monitor Gamer ASUS 27" 144Hz', 4.8), 1, 'pixels mortos')
    m12 = MetodoTratamentoFactory.criar_reuso()
    servico_descarte.definir_metodo_tratamento(sol_raf1, m12)
    servico_descarte.avancar_estado_solicitacao(sol_raf1)
    servico_descarte.avancar_estado_solicitacao(sol_raf1)
    servico_descarte.avancar_estado_solicitacao(sol_raf1)

    # ---- solicitações: TechLixo Soluções ----
    sol_tl1 = servico_descarte.criar_solicitacao(empresa2, ponto4)
    servico_descarte.adicionar_item_solicitacao(sol_tl1,
        DispositivoFactory.criar_computador('comp-010', 'Switch Cisco Catalyst 2960', 4.5), 4, 'fim de vida útil')
    servico_descarte.adicionar_item_solicitacao(sol_tl1,
        DispositivoFactory.criar_computador('comp-011', 'Roteador Mikrotik CCR1009', 1.2), 6, 'substituição de infraestrutura')
    m13 = MetodoTratamentoFactory.criar_reciclagem()
    servico_descarte.definir_metodo_tratamento(sol_tl1, m13)
    servico_descarte.avancar_estado_solicitacao(sol_tl1)
    servico_descarte.avancar_estado_solicitacao(sol_tl1)
    servico_descarte.avancar_estado_solicitacao(sol_tl1)

    sol_tl2 = servico_descarte.criar_solicitacao(empresa2, ponto3)
    servico_descarte.adicionar_item_solicitacao(sol_tl2,
        DispositivoFactory.criar_eletrodomestico('elet-009', 'Nobreak APC Smart-UPS 1500VA', 22.0), 8, 'baterias sulfatadas')
    m14 = MetodoTratamentoFactory.criar_reciclagem()
    servico_descarte.definir_metodo_tratamento(sol_tl2, m14)
    servico_descarte.avancar_estado_solicitacao(sol_tl2)
    servico_descarte.avancar_estado_solicitacao(sol_tl2)
    servico_descarte.avancar_estado_solicitacao(sol_tl2)

    sol_tl3 = servico_descarte.criar_solicitacao(empresa2, ponto2)
    servico_descarte.adicionar_item_solicitacao(sol_tl3,
        DispositivoFactory.criar_computador('comp-012', 'Workstation Dell Precision 5820', 18.0), 3, 'atualização de parque')
    servico_descarte.avancar_estado_solicitacao(sol_tl3)

    # ---- solicitações: GreenCycle Nordeste ----
    sol_gc1 = servico_descarte.criar_solicitacao(empresa3, ponto2)
    servico_descarte.adicionar_item_solicitacao(sol_gc1,
        DispositivoFactory.criar_eletrodomestico('elet-010', 'TV LG 55" OLED C1', 17.8), 3, 'telas com defeito de fábrica')
    servico_descarte.avancar_estado_solicitacao(sol_gc1)

    sol_gc2 = servico_descarte.criar_solicitacao(empresa3, ponto5)
    servico_descarte.adicionar_item_solicitacao(sol_gc2,
        DispositivoFactory.criar_eletrodomestico('elet-011', 'Ar Condicionado Daikin Inverter 18000BTU', 35.0), 2, 'gás R22 obsoleto')
    m15 = MetodoTratamentoFactory.criar_reuso()
    servico_descarte.definir_metodo_tratamento(sol_gc2, m15)
    servico_descarte.avancar_estado_solicitacao(sol_gc2)
    servico_descarte.avancar_estado_solicitacao(sol_gc2)
    servico_descarte.avancar_estado_solicitacao(sol_gc2)

    sol_gc3 = servico_descarte.criar_solicitacao(empresa3, ponto1)
    servico_descarte.adicionar_item_solicitacao(sol_gc3,
        DispositivoFactory.criar_computador('comp-013', 'Laptop Corporativo Lenovo ThinkPad T490', 1.6), 12, 'renovação de frota')
    m16 = MetodoTratamentoFactory.criar_reuso()
    servico_descarte.definir_metodo_tratamento(sol_gc3, m16)
    servico_descarte.avancar_estado_solicitacao(sol_gc3)
    servico_descarte.avancar_estado_solicitacao(sol_gc3)
    servico_descarte.avancar_estado_solicitacao(sol_gc3)

    # ---- histórico de entregas: João Silva ----
    _entregas_joao = [
        ('ENT-2026-0412', '2026-04-12', '09:14', 40.20, 'GreenCycle Nordeste', 'finalizado'),
        ('ENT-2026-0328', '2026-03-28', '14:32', 12.40, 'TechLixo Soluções',   'finalizado'),
        ('ENT-2026-0315', '2026-03-15', '11:05', 5.40,  'Recicla Kariri',       'finalizado'),
        ('ENT-2026-0228', '2026-02-28', '16:50', 3.68,  'Recicla Kariri',       'cancelado'),
        ('ENT-2026-0214', '2026-02-14', '08:22', 13.95, 'TechLixo Soluções',   'finalizado'),
        ('ENT-2026-0130', '2026-01-30', '13:47', 8.19,  'GreenCycle Nordeste', 'finalizado'),
        ('ENT-2026-0110', '2026-01-10', '10:03', 27.65, 'Recicla Kariri',       'finalizado'),
        ('ENT-2025-1218', '2025-12-18', '15:31', 6.41,  'TechLixo Soluções',   'finalizado'),
        ('ENT-2025-1205', '2025-12-05', '09:58', 12.53, 'Recicla Kariri',       'finalizado'),
        ('ENT-2025-1122', '2025-11-22', '17:20', 4.10,  'GreenCycle Nordeste', 'cancelado'),
        ('ENT-2025-1108', '2025-11-08', '08:45', 18.30, 'Recicla Kariri',       'finalizado'),
        ('ENT-2025-1025', '2025-10-25', '13:02', 9.75,  'TechLixo Soluções',   'finalizado'),
        ('ENT-2025-1010', '2025-10-10', '14:19', 22.80, 'GreenCycle Nordeste', 'finalizado'),
        ('ENT-2025-0928', '2025-09-28', '10:30', 7.60,  'Recicla Kariri',       'finalizado'),
        ('ENT-2025-0913', '2025-09-13', '13:02', 13.95, 'Recicla Kariri',       'finalizado'),
    ]
    for eid, data, hora, valor, empresa, status in _entregas_joao:
        dados.salvar_entrega(eid, 'user-1', valor, empresa, data, hora, status)

    # ---- notificações ----
    _notifs = [
        ('user-1', 'Sua solicitação foi recebida e aguarda coleta. Em breve entraremos em contato.'),
        ('user-1', 'Parabéns! Você ganhou R$ 40,20 de incentivo pela coleta ENT-2026-0412.'),
        ('user-1', 'Sua TV Samsung 32" foi coletada e está em processamento.'),
        ('user-1', 'Missão concluída: você atingiu 5 descartes realizados! Continue assim.'),
        ('user-1', 'Novo bônus disponível: ganhe 20% a mais neste fim de semana em coletas de eletrodomésticos.'),
        ('user-1', 'Sua solicitação de saque foi processada. Valor creditado em até 2 dias úteis.'),
        ('user-2', 'Lote de computadores Dell foi recebido no Ecoponto Centro. Processamento iniciado.'),
        ('user-2', 'Relatório mensal disponível: 114 kg reciclados em março de 2026.'),
        ('user-2', 'Seus servidores Dell PowerEdge foram reciclados com sucesso.'),
        ('user-3', 'Sua solicitação de coleta do Motorola Moto G82 foi recebida.'),
        ('user-3', 'Micro-ondas processado com sucesso. R$ 1,10 de incentivo creditado.'),
        ('user-4', 'Coleta do Micro System Philips agendada. Aguarde confirmação.'),
        ('user-4', 'Reciclagem concluída! Você evitou 0,5 kg de CO₂ com este descarte.'),
        ('user-5', 'Seus AirPods Pro foram coletados no Ecoponto Centro.'),
        ('user-5', 'Cafeteira Nespresso processada com sucesso via reciclagem.'),
        ('user-6', 'PC Gamer e monitor retirados para reutilização. Obrigado pelo descarte responsável!'),
        ('user-7', 'Lote de switches Cisco foi reciclado. Relatório de impacto disponível.'),
        ('user-7', 'Novo ponto de coleta disponível próximo à sua área de operação.'),
        ('user-8', 'Renovação de frota aprovada: 12 notebooks ThinkPad encaminhados para reuso.'),
        ('user-8', 'Ar condicionados coletados e em processo de reutilização de componentes.'),
    ]
    for uid, msg in _notifs:
        dados.salvar_notificacao(uid, msg)


if __name__ == '__main__':
    app = criar_app()
    app.run(debug=True, port=5000)
