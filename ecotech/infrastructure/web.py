"""
Aplicação web Flask - Interface do sistema EcoTech.

Este módulo implementa a interface web usando Flask,
baseada no design mobile fornecido.
"""

import csv
import io
import hmac
import os
import secrets
import click
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, Response
from .pdf import gerar_mtr
from datetime import datetime
from typing import Optional
from werkzeug.security import generate_password_hash, check_password_hash

from ..application.services import (
    ServicoDescarte,
    ServicoRelatorio,
    ServicoPontoColeta,
    ServicoUsuario,
    ServicoSaque,
    ServicoAutenticacao,
    ServicoBaseOperacional,
)
from ..application.geolocalizacao import GeolocalizadorCoordenadasInformadas
from ..application.despacho import ConfiguracaoDespacho, ServicoDespacho
from ..application.elegibilidade import DemandaColeta
from ..application.agendamento import ServicoAgendamento
from ..application.chat import ServicoChat
from ..application.factories import (
    DispositivoFactory,
    MetodoTratamentoFactory
)
from ..application.authorization import (
    listar_solicitacoes_visiveis_empresa,
    usuario_pode_operar_solicitacao,
)
from ..domain.usuarios import Usuario
from ..domain.estados import BuscandoEmpresa, Solicitado
from ..domain.logistica import Coordenadas
from ..domain.dispositivos import EstadoProduto
from ..infrastructure.persistence.dados import Dados


def criar_app() -> Flask:
    """
    Cria e configura a aplicação Flask.
    
    Returns:
        Aplicação Flask configurada
    """
    from datetime import timedelta
    app = Flask(__name__)
    app.secret_key = os.environ.get('ECOTECH_SECRET_KEY') or secrets.token_hex(32)
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)
    app.config.setdefault('CSRF_ENABLED', True)
    
    # instancia unica de dados compartilhada por todos os servicos
    dados = Dados()
    
    # servicos com persistencia
    servico_usuario = ServicoUsuario(dados)
    servico_ponto = ServicoPontoColeta(dados)
    servico_descarte = ServicoDescarte(dados)
    servico_relatorio = ServicoRelatorio()
    servico_saque = ServicoSaque(dados)
    servico_autenticacao = ServicoAutenticacao(servico_usuario)
    servico_base = ServicoBaseOperacional(dados)
    lotes = tuple(
        int(valor.strip())
        for valor in os.environ.get('ECOTECH_DESPACHO_LOTES', '1,2,3').split(',')
        if valor.strip()
    )
    servico_despacho = ServicoDespacho(
        dados, servico_base,
        configuracao=ConfiguracaoDespacho(
            tamanhos_lotes=lotes,
            prazo_resposta_minutos=int(
                os.environ.get('ECOTECH_DESPACHO_PRAZO_MINUTOS', '5')
            ),
        ),
    )
    servico_agendamento = ServicoAgendamento(dados)
    servico_chat = ServicoChat(dados)
    geolocalizador = GeolocalizadorCoordenadasInformadas()
    
    # configura dependencias entre servicos
    servico_descarte.set_servicos(servico_usuario, servico_ponto)
    
    # carrega solicitacoes do banco de dados
    servico_descarte._carregar_solicitacoes_do_banco()
    
    # dados exemplo, só roda no processo pai (não no filho do reloader)
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

    def csrf_token():
        """Cria ou devolve o token CSRF associado à sessão atual."""
        token = session.get('_csrf_token')
        if not token:
            token = secrets.token_urlsafe(32)
            session['_csrf_token'] = token
        return token

    app.jinja_env.globals['csrf_token'] = csrf_token

    @app.before_request
    def proteger_csrf():
        """Valida requisições mutáveis que utilizam a sessão Flask."""
        if request.method not in ('POST', 'PUT', 'PATCH', 'DELETE'):
            return None
        if not app.config.get('CSRF_ENABLED', True) or app.testing:
            return None

        esperado = session.get('_csrf_token')
        recebido = request.form.get('_csrf_token') or request.headers.get('X-CSRF-Token')
        if not esperado or not recebido or not hmac.compare_digest(esperado, recebido):
            if request.path.startswith(('/operacoes/', '/solicitacao/', '/solicitacoes/', '/ofertas/', '/usuarios/', '/admin/')):
                return jsonify({'erro': 'Token CSRF inválido ou ausente'}), 400
            return 'Token CSRF inválido ou ausente', 400
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
            receita_ecotech_total = dados.buscar_receita_total_ecotech()

            return render_template(
                'dashboard.html',
                usuario=usuario,
                solicitacoes=todas_solicitacoes[:10],
                total_descartado=metricas['peso_total'],
                impacto_evitado=metricas['impacto_total'],
                pontos_acumulados=0,
                total_sistema=metricas['peso_total'],
                total_processadas=metricas['total_processadas'],
                receita_ecotech_total=receita_ecotech_total,
                is_empresa=False,
                is_admin=True
            )
        
        # escopo único por papel
        if usuario['tipo'] == 'empresa':
            solicitacoes_usuario = listar_solicitacoes_visiveis_empresa(
                usuario['id'], todas_solicitacoes, dados
            )
        else:
            solicitacoes_usuario = [
                s for s in todas_solicitacoes
                if s.usuario.id == usuario['id']
            ]
        
        # calcula metricas do usuario
        metricas_usuario = servico_descarte.calcular_metricas(solicitacoes_usuario)

        # dashboard diferente para empresa
        if usuario['tipo'] == 'empresa':
            metricas_sistema = servico_descarte.calcular_metricas(todas_solicitacoes)

            # --- ESG ---
            _ESTADOS_FINAIS = {'Reciclado', 'Reutilizado', 'Descartado'}
            sols_finais = [s for s in solicitacoes_usuario if s.estado.obter_nome() in _ESTADOS_FINAIS]
            sols_reciclados = [s for s in solicitacoes_usuario if s.estado.obter_nome() == 'Reciclado']
            co2_evitado = round(metricas_usuario['peso_total'] * 3.0, 1)
            taxa_reciclagem = round((len(sols_reciclados) / len(sols_finais) * 100), 1) if sols_finais else 0.0

            # tonelagem por categoria de dispositivo
            _MAPA_CATEGORIA = {
                'Celular': 'Celulares', 'Computador': 'Computadores',
                'Eletrodomestico': 'Eletrodomésticos', 'Eletrodoméstico': 'Eletrodomésticos',
            }
            por_categoria: dict = {}
            for sol in solicitacoes_usuario:
                for item in sol.itens:
                    tipo = type(item.dispositivo).__name__
                    nome_cat = _MAPA_CATEGORIA.get(tipo, tipo)
                    por_categoria[nome_cat] = round(
                        por_categoria.get(nome_cat, 0.0) + item.calcular_peso_total(), 2
                    )

            saldo_empresa = dados.buscar_saldo_empresa(usuario['id'])

            return render_template(
                'dashboard.html',
                usuario=usuario,
                solicitacoes=solicitacoes_usuario,
                total_descartado=metricas_usuario['peso_total'],
                impacto_evitado=metricas_usuario['impacto_total'],
                pontos_acumulados=metricas_usuario['pontos'],
                total_sistema=metricas_sistema['peso_total'],
                total_processadas=metricas_sistema['total_processadas'],
                co2_evitado=co2_evitado,
                taxa_reciclagem=taxa_reciclagem,
                por_categoria=por_categoria,
                saldo_empresa=saldo_empresa,
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

        # pontos reais persistidos no banco (não recalculados)
        cidadao_row = dados.buscar_cidadao(usuario['id'])
        pontos_reais = int(cidadao_row['pontos']) if cidadao_row and cidadao_row['pontos'] else 0

        # calcula porcentagens para barras de progresso
        progresso = servico_descarte.calcular_progresso(solicitacoes_usuario)
        tier_info = servico_descarte.calcular_info_tier(pontos_reais)
        # saldo baseado nos pontos reais do banco, descontando saques já realizados
        saques_realizados = sum(
            s['valor'] for s in servico_saque.listar_saques(usuario['id'])
            if s.get('status') != 'cancelado'
        )
        saldo_acumulado = max(round(pontos_reais * servico_saque.TAXA_REAIS_POR_PONTO - saques_realizados, 2), 0.0)
        meta_missao = 15

        return render_template(
            'dashboard.html',
            usuario=usuario,
            solicitacoes=solicitacoes_usuario,
            entregas=entregas[:10],
            total_descartado=metricas_usuario['peso_total'],
            impacto_evitado=metricas_usuario['impacto_total'],
            pontos_acumulados=pontos_reais,
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

        # empresas gerenciam seus pontos, não criam solicitações
        if usuario['tipo'] == 'empresa':
            flash('Empresas gerenciam seus pontos de coleta na página dedicada.', 'info')
            return redirect(url_for('empresa_pontos'))
        
        if request.method == 'POST':
            try:
                tipo_dispositivo  = request.form.get('tipo_dispositivo', 'celular')
                subcategoria      = request.form.get('subcategoria', '').strip()
                nome_dispositivo  = request.form.get('nome', '').strip()
                peso_kg           = float(request.form.get('peso_kg', 1.0))
                quantidade        = int(request.form.get('quantidade', 1))
                observacoes       = request.form.get('observacoes_endereco', '').strip()
                ponto_id          = request.form.get('ponto_id', '').strip()
                tipo_coleta       = request.form.get('tipo_coleta', 'domiciliar').strip()
                endereco_coleta   = request.form.get('endereco_coleta', '').strip()
                latitude_coleta   = request.form.get('latitude_coleta', '').strip()
                longitude_coleta  = request.form.get('longitude_coleta', '').strip()
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

                coordenadas = None
                if tipo_coleta == 'domiciliar':
                    coordenadas = geolocalizador.localizar(
                        endereco_coleta, latitude_coleta, longitude_coleta
                    )

                solicitacao = servico_descarte.criar_solicitacao(usuario_obj, ponto)

                dispositivo = DispositivoFactory.criar_dispositivo(
                    tipo_dispositivo,
                    {'id': str(__import__('uuid').uuid4()), 'nome': nome_dispositivo, 'peso_kg': peso_kg, 'subcategoria': subcategoria}
                )
                servico_descarte.adicionar_item_solicitacao(solicitacao, dispositivo, quantidade, observacoes)

                dados.atualizar_detalhes_coleta(
                    solicitacao.id, tipo_coleta, endereco_coleta, nome_contato, data_agendamento
                )

                if tipo_coleta == 'domiciliar':
                    dados.atualizar_localizacao_coleta(
                        solicitacao.id, coordenadas.latitude,
                        coordenadas.longitude, 'navegador_ou_formulario'
                    )
                    agendada_para = datetime.strptime(
                        data_agendamento, '%Y-%m-%d %H:%M'
                    ) if data_agendamento else datetime.now()
                    fim_informado = request.form.get('horario_fim', '').strip()
                    janela_fim = (
                        datetime.strptime(f'{data_coleta} {fim_informado}', '%Y-%m-%d %H:%M')
                        if data_coleta and fim_informado else agendada_para + timedelta(hours=2)
                    )
                    servico_agendamento.solicitar(
                        solicitacao.id, usuario['id'], agendada_para, janela_fim
                    )
                    servico_despacho.criar_ofertas(
                        solicitacao.id,
                        DemandaColeta(
                            coordenadas=Coordenadas(
                                coordenadas.latitude, coordenadas.longitude
                            ),
                            categorias=frozenset({tipo_dispositivo.lower()}),
                            peso_kg=peso_kg * quantidade,
                            agendada_para=agendada_para,
                        ),
                    )
                    solicitacao._estado = BuscandoEmpresa()

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

    @app.route('/empresa/pontos')
    def empresa_pontos():
        """Painel de administração dos pontos de coleta da empresa."""
        if not usuario_logado():
            return redirect(url_for('login'))
        usuario = dados_usuario()
        if usuario['tipo'] not in ('empresa', 'administrador'):
            flash('Acesso não autorizado.', 'error')
            return redirect(url_for('dashboard'))

        pontos_raw = dados.buscar_pontos_empresa(usuario['id'])
        todas = servico_descarte.listar_solicitacoes()
        sol_map = {s.id: s for s in todas}

        pontos_com_sol = []
        for ponto in pontos_raw:
            rows_sol = dados.buscar_solicitacoes_ponto(ponto['id'])
            solicitacoes_ponto = []
            for row in rows_sol:
                sol = sol_map.get(row['id'])
                if sol is None:
                    continue
                confs = dados.buscar_confirmacoes_solicitacao(row['id'])
                # formata data_agendamento 
                raw_agenda = row.get('data_agendamento') or ''
                data_agendamento_fmt = ''
                if raw_agenda:
                    for fmt in ('%Y-%m-%d %H:%M', '%Y-%m-%d', '%d/%m/%Y %H:%M', '%d/%m/%Y'):
                        try:
                            dt_agenda = datetime.strptime(raw_agenda.strip(), fmt)
                            data_agendamento_fmt = dt_agenda.strftime('%d/%m %H:%M') if '%H' in fmt else dt_agenda.strftime('%d/%m')
                            break
                        except ValueError:
                            continue
                    if not data_agendamento_fmt:
                        data_agendamento_fmt = raw_agenda
                solicitacoes_ponto.append({
                    'id':               row['id'],
                    'nome_usuario':     row.get('nome_usuario', ''),
                    'estado':           row['estado'].replace('_', ' ').title(),
                    'data_agendamento': data_agendamento_fmt,
                    'peso_total':       sol.calcular_peso_total(),
                    'confirmado_empresa':  confs['confirmado_empresa'],
                    'pode_confirmar':   (
                        row['estado'] == 'SOLICITADO' and not confs['confirmado_empresa']
                    ),
                })
            pontos_com_sol.append({'ponto': ponto, 'solicitacoes': solicitacoes_ponto})

        plano_empresa = dados.buscar_plano_empresa(usuario['id'])
        return render_template(
            'empresa_pontos.html',
            usuario=usuario,
            pontos_com_sol=pontos_com_sol,
            plano_empresa=plano_empresa,
        )

    def _dados_form_base():
        return {
            'nome': request.form.get('nome', '').strip(),
            'endereco': request.form.get('endereco', '').strip(),
            'latitude': request.form.get('latitude', '').strip(),
            'longitude': request.form.get('longitude', '').strip(),
            'raio_atendimento_km': request.form.get(
                'raio_atendimento_km', ''
            ).strip(),
            'capacidade_kg': request.form.get('capacidade_kg', '').strip(),
            'realiza_coleta_domiciliar': (
                request.form.get('realiza_coleta_domiciliar') == 'on'
            ),
        }

    @app.route('/empresa/bases', methods=['GET', 'POST'])
    def empresa_bases():
        if not usuario_logado():
            return redirect(url_for('login'))
        usuario = dados_usuario()
        if usuario['tipo'] != 'empresa':
            flash('Apenas empresas podem gerenciar bases operacionais.', 'error')
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            try:
                servico_base.criar(usuario['id'], _dados_form_base())
                flash('Base operacional criada com sucesso.', 'success')
                return redirect(url_for('empresa_bases'))
            except (ValueError, TypeError) as exc:
                flash(str(exc), 'error')

        return render_template(
            'empresa_bases.html', usuario=usuario,
            bases=servico_base.listar_empresa(usuario['id'])
        )

    @app.route('/empresa/bases/<id_base>/editar', methods=['POST'])
    def editar_base(id_base):
        if not usuario_logado():
            return jsonify({'erro': 'Não autenticado'}), 401
        usuario = dados_usuario()
        if usuario['tipo'] != 'empresa':
            return jsonify({'erro': 'Acesso não autorizado'}), 403
        try:
            servico_base.atualizar(usuario['id'], id_base, _dados_form_base())
            flash('Base operacional atualizada.', 'success')
            return redirect(url_for('empresa_bases'))
        except PermissionError as exc:
            return jsonify({'erro': str(exc)}), 403
        except (ValueError, TypeError) as exc:
            flash(str(exc), 'error')
            return redirect(url_for('empresa_bases'))

    @app.route('/empresa/bases/<id_base>/atividade', methods=['POST'])
    def atividade_base(id_base):
        if not usuario_logado():
            return jsonify({'erro': 'Não autenticado'}), 401
        usuario = dados_usuario()
        if usuario['tipo'] != 'empresa':
            return jsonify({'erro': 'Acesso não autorizado'}), 403
        try:
            servico_base.definir_atividade(
                usuario['id'], id_base, request.form.get('ativa') == '1'
            )
            return redirect(url_for('empresa_bases'))
        except PermissionError as exc:
            return jsonify({'erro': str(exc)}), 403

    @app.route('/solicitacao/<id_sol>/confirmar', methods=['POST'])
    def confirmar_solicitacao(id_sol):
        """AJAX: empresa confirma o recebimento da entrega."""
        if not usuario_logado():
            return jsonify({'erro': 'Não autenticado'}), 401

        usuario = dados_usuario()
        if usuario['tipo'] not in ('empresa', 'administrador'):
            return jsonify({'erro': 'Apenas a empresa pode confirmar recebimento'}), 403

        todas = servico_descarte.listar_solicitacoes()
        sol = next((s for s in todas if s.id == id_sol), None)
        if sol is None:
            return jsonify({'erro': 'Solicitação não encontrada'}), 404

        if not usuario_pode_operar_solicitacao(usuario, sol, dados):
            return jsonify({'erro': 'Acesso não autorizado a esta solicitação'}), 403

        if sol.estado.obter_nome() != 'Solicitado':
            return jsonify({'erro': 'Esta solicitação não está mais aguardando confirmação'}), 400

        # avança para Coletado
        servico_descarte.avancar_estado_solicitacao(sol)

        # atualiza capacidade real do ponto de coleta
        if sol.ponto_coleta:
            peso = sol.calcular_peso_total()
            nova_ocp = sol.ponto_coleta.ocupacao_atual_kg + peso
            dados.atualizar_ocupacao_ponto(sol.ponto_coleta.id, nova_ocp)
            sol.ponto_coleta.ocupacao_atual_kg = nova_ocp

        # notifica o cidadão
        dados.salvar_notificacao(
            sol.usuario.id,
            f'O ponto de coleta "{usuario["nome"]}" confirmou o recebimento do seu descarte. '
            f'Aguarde enquanto a empresa define o destino do material - '
            f'seus créditos serão liberados assim que o processo for concluído.'
        )

        return jsonify({
            'ok': True,
            'novo_estado': sol.estado.obter_nome(),
            'msg': f'Recebimento confirmado! {sol.usuario.nome} foi notificado.',
        })
    
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

    @app.route('/api/empresa/ofertas')
    def ofertas_ativas_empresa():
        if not usuario_logado():
            return jsonify({'erro': 'Não autenticado'}), 401
        usuario = dados_usuario()
        if usuario['tipo'] != 'empresa':
            return jsonify({'erro': 'Acesso não autorizado'}), 403
        return jsonify({'ofertas': servico_despacho.listar_ofertas_ativas(usuario['id'])})

    def _instante_form(nome):
        return datetime.fromisoformat(request.form.get(nome, ''))

    @app.route('/agendamentos/<id_sol>/propor', methods=['POST'])
    def propor_agendamento(id_sol):
        if not usuario_logado(): return jsonify({'erro':'Não autenticado'}), 401
        try:
            row=servico_agendamento.propor(id_sol,session['user_id'],_instante_form('inicio'),_instante_form('fim'))
            servico_chat.evento(id_sol,'PROPOSTA_HORARIO',{'inicio':row['proposta_inicio'],'fim':row['proposta_fim'],'autor_id':session['user_id']})
            return jsonify({'ok':True,'status':row['status']})
        except PermissionError as exc: return jsonify({'erro':str(exc)}),403
        except (ValueError,LookupError) as exc: return jsonify({'erro':str(exc)}),400

    @app.route('/agendamentos/<id_sol>/aceitar', methods=['POST'])
    def aceitar_agendamento(id_sol):
        if not usuario_logado(): return jsonify({'erro':'Não autenticado'}), 401
        try:
            row=servico_agendamento.aceitar(id_sol,session['user_id'])
            servico_chat.evento(id_sol,'HORARIO_ACEITO',{'inicio':row['inicio_confirmado'],'fim':row['fim_confirmado']})
            return jsonify({'ok':True,'status':row['status'],'inicio':row['inicio_confirmado'],'fim':row['fim_confirmado']})
        except PermissionError as exc: return jsonify({'erro':str(exc)}),403
        except (ValueError,LookupError) as exc: return jsonify({'erro':str(exc)}),400

    @app.route('/agendamentos/<id_sol>/rejeitar', methods=['POST'])
    def rejeitar_agendamento(id_sol):
        if not usuario_logado(): return jsonify({'erro':'Não autenticado'}), 401
        try:
            row=servico_agendamento.rejeitar(id_sol,session['user_id'])
            servico_chat.evento(id_sol,'HORARIO_RECUSADO',{'autor_id':session['user_id']})
            return jsonify({'ok':True,'status':row['status']})
        except PermissionError as exc: return jsonify({'erro':str(exc)}),403
        except (ValueError,LookupError) as exc: return jsonify({'erro':str(exc)}),400

    @app.route('/ofertas/<oferta_id>/aceitar', methods=['POST'])
    def aceitar_oferta(oferta_id):
        if not usuario_logado():
            return jsonify({'erro': 'Não autenticado'}), 401
        usuario = dados_usuario()
        if usuario['tipo'] != 'empresa':
            return jsonify({'erro': 'Acesso não autorizado'}), 403
        try:
            aceita = servico_despacho.aceitar(oferta_id, usuario['id'])
        except LookupError as exc:
            return jsonify({'erro': str(exc)}), 404
        except TimeoutError as exc:
            return jsonify({'erro': str(exc)}), 410
        except (RuntimeError, ValueError) as exc:
            return jsonify({'erro': str(exc)}), 409

        sol = servico_descarte.obter_solicitacao(aceita['solicitacao_id'])
        if sol:
            sol._empresa_responsavel_id = usuario['id']
            sol._base_operacional_id = aceita['base_operacional_id']
            sol._atribuida_em = datetime.fromisoformat(aceita['respondida_em'])
            sol._estado = Solicitado()
            sol._endereco_coleta = aceita['endereco_coleta']
            sol._nome_contato = aceita['nome_contato']
        return jsonify({
            'ok': True,
            'solicitacao_id': aceita['solicitacao_id'],
            'endereco_coleta': aceita['endereco_coleta'],
            'nome_contato': aceita['nome_contato'],
            'data_agendamento': aceita['data_agendamento'],
        })

    @app.route('/solicitacoes/<id_sol>/chat', methods=['GET','POST'])
    def chat_solicitacao(id_sol):
        if not usuario_logado(): return redirect(url_for('login'))
        usuario=dados_usuario()
        try:
            if request.method=='POST':
                servico_chat.enviar(id_sol,usuario['id'],request.form.get('texto',''))
                return redirect(url_for('chat_solicitacao',id_sol=id_sol))
            pagina=request.args.get('pagina',1,type=int)
            mensagens=servico_chat.listar(id_sol,usuario['id'],pagina)
            servico_chat.marcar_lidas(id_sol,usuario['id'])
            return render_template('chat.html',usuario=usuario,mensagens=mensagens,id_sol=id_sol,pagina=pagina)
        except PermissionError: return jsonify({'erro':'Acesso não autorizado'}),403
        except LookupError: return jsonify({'erro':'Conversa não encontrada'}),404
        except ValueError as exc: return jsonify({'erro':str(exc)}),400
    
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

        # solicitações ativas do cidadão (acompanhamento de status)
        solicitacoes_ativas = []
        if usuario['tipo'] == 'cidadao':
            rows_ativas = dados.buscar_solicitacoes_ativas_cidadao(usuario['id'])
            for row in rows_ativas:
                confs = dados.buscar_confirmacoes_solicitacao(row['id'])
                solicitacoes_ativas.append({
                    'id':               row['id'],
                    'estado':           row['estado'].replace('_', ' ').title(),
                    'data_agendamento': row.get('data_agendamento') or '',
                    'nome_ponto':       row.get('nome_ponto') or 'Coleta domiciliar',
                    'confirmado_empresa': confs['confirmado_empresa'],
                })

        return render_template(
            'ultimas_entregas.html',
            usuario=usuario,
            entregas=entregas,
            solicitacoes_ativas=solicitacoes_ativas,
        )
    
    @app.route('/planos', methods=['GET', 'POST'])
    def planos():
        """Página de planos para empresas."""
        if not usuario_logado():
            return redirect(url_for('login'))
        usuario = dados_usuario()
        if usuario['tipo'] != 'empresa':
            flash('Apenas empresas podem acessar os planos.', 'error')
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            novo_plano = request.form.get('plano', 'free')
            dados.atualizar_plano_empresa(usuario['id'], novo_plano)
            flash('Plano atualizado com sucesso!', 'success')
            return redirect(url_for('planos'))

        plano_atual = dados.buscar_plano_empresa(usuario['id'])
        return render_template('planos.html', usuario=usuario, plano_atual=plano_atual)

    @app.route('/saque', methods=['GET', 'POST'])
    def saque():
        """Página de saque/carteira."""
        if not usuario_logado():
            return redirect(url_for('login'))

        usuario = dados_usuario()

        if usuario['tipo'] != 'cidadao':
            flash('A carteira e os saques estão disponíveis apenas para cidadãos.', 'error')
            return redirect(url_for('dashboard'))

        todas_solicitacoes = servico_descarte.listar_solicitacoes()
        # pontos reais do banco, não recalculados
        cidadao_row = dados.buscar_cidadao(usuario['id'])
        pontos = int(cidadao_row['pontos']) if cidadao_row and cidadao_row['pontos'] else 0
        saldo = round(pontos * servico_saque.TAXA_REAIS_POR_PONTO, 2) - sum(
            s['valor'] for s in servico_saque.listar_saques(usuario['id'])
            if s.get('status') != 'cancelado'
        )
        saldo = max(round(saldo, 2), 0.0)
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

        row_usuario = dados.buscar_usuario(usuario['id'])
        email_usuario = row_usuario['email'] if row_usuario else ''

        return render_template(
            'perfil.html',
            usuario=usuario,
            email_usuario=email_usuario,
            total_solicitacoes=len(solicitacoes_usuario),
            pontos=metricas['pontos'],
            tier_info=tier_info,
            rank=rank,
            conquistas=conquistas,
        )

    @app.route('/perfil/editar', methods=['POST'])
    def perfil_editar():
        """Atualiza nome, email e/ou senha do usuário logado."""
        if not usuario_logado():
            return redirect(url_for('login'))

        usuario = dados_usuario()
        nome  = request.form.get('nome',  '').strip()
        email = request.form.get('email', '').strip()
        senha_atual   = request.form.get('senha_atual',   '')
        nova_senha     = request.form.get('nova_senha',    '')
        confirma_senha = request.form.get('confirma_senha', '')

        if not nome or not email:
            flash('Nome e e-mail são obrigatórios.', 'error')
            return redirect(url_for('perfil'))

        # verifica se o e-mail já pertence a outro usuário
        row_email = dados.buscar_usuario_por_email(email)
        if row_email and row_email['id'] != usuario['id']:
            flash('Este e-mail já está em uso por outro usuário.', 'error')
            return redirect(url_for('perfil'))

        password_hash = None
        if nova_senha:
            # verifica senha atual antes de permitir troca
            row = dados.buscar_usuario(usuario['id'])
            if not row or not check_password_hash(row['password_hash'] or '', senha_atual):
                flash('Senha atual incorreta.', 'error')
                return redirect(url_for('perfil'))
            if nova_senha != confirma_senha:
                flash('A nova senha e a confirmação não coincidem.', 'error')
                return redirect(url_for('perfil'))
            if len(nova_senha) < 6:
                flash('A nova senha deve ter pelo menos 6 caracteres.', 'error')
                return redirect(url_for('perfil'))
            password_hash = generate_password_hash(nova_senha)

        dados.atualizar_usuario(usuario['id'], nome, email, password_hash)

        # atualiza a sessão com o novo nome
        session['user_nome'] = nome

        flash('Perfil atualizado com sucesso!', 'success')
        return redirect(url_for('perfil'))

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
        elif usuario['tipo'] == 'empresa':
            solicitacoes_usuario = listar_solicitacoes_visiveis_empresa(
                usuario['id'], todas_solicitacoes, dados
            )
        else:
            solicitacoes_usuario = [
                s for s in todas_solicitacoes
                if s.usuario.id == usuario['id']
            ]
        
        # ordena do mais recente para o mais antigo
        solicitacoes_usuario = sorted(solicitacoes_usuario, key=lambda s: s._data_criacao, reverse=True)

        # filtra por estado se tiver parametro
        filtro_estado = request.args.get('estado', '')
        solicitacoes_filtradas = servico_descarte.filtrar_por_estado(solicitacoes_usuario, filtro_estado)

        # calcula estatisticas baseadas nas solicitações que o usuário pode ver
        stats = servico_descarte.calcular_stats_estados(solicitacoes_usuario)

        plano_empresa = ''
        if usuario['tipo'] == 'empresa':
            plano_empresa = dados.buscar_plano_empresa(usuario['id'])

        per_page = 20
        page = request.args.get('page', 1, type=int)
        total_solicitacoes = len(solicitacoes_filtradas)
        total_pages = max(1, (total_solicitacoes + per_page - 1) // per_page)
        page = max(1, min(page, total_pages))
        solicitacoes_page = solicitacoes_filtradas[(page - 1) * per_page : page * per_page]

        return render_template(
            'operacoes.html', 
            usuario=usuario,
            solicitacoes=solicitacoes_page,
            stats=stats,
            filtro_atual=filtro_estado,
            is_admin=usuario['tipo'] == 'administrador',
            plano_empresa=plano_empresa,
            page=page,
            total_pages=total_pages,
            total_solicitacoes=total_solicitacoes,
        )

    @app.route('/operacoes/<id_sol>/avancar', methods=['POST'])
    def avancar_estado(id_sol):
        """Avança o estado de uma solicitação. Empresa/admin only."""
        if not usuario_logado():
            return jsonify({'erro': 'Não autenticado'}), 401

        usuario = dados_usuario()
        if usuario['tipo'] not in ('empresa', 'administrador'):
            return jsonify({'erro': 'Acesso não autorizado'}), 403

        # busca a solicitação
        todas = servico_descarte.listar_solicitacoes()
        sol = next((s for s in todas if s.id == id_sol), None)
        if sol is None:
            return jsonify({'erro': 'Solicitação não encontrada'}), 404

        if not usuario_pode_operar_solicitacao(usuario, sol, dados):
            return jsonify({'erro': 'Acesso não autorizado a esta solicitação'}), 403

        # verifica o limite mensal somente dentro do escopo da empresa atual
        if usuario['tipo'] == 'empresa':
            plano = dados.buscar_plano_empresa(usuario['id'])
            if plano == 'free':
                mes_atual = datetime.now().month
                ano_atual = datetime.now().year
                solicitacoes_empresa = listar_solicitacoes_visiveis_empresa(
                    usuario['id'], todas, dados
                )
                processadas_mes = sum(
                    1 for s in solicitacoes_empresa
                    if s.estado.obter_nome() not in ('Solicitado', 'Cancelado')
                    and s._data_criacao.month == mes_atual
                    and s._data_criacao.year == ano_atual
                )
                if processadas_mes >= 30:
                    return jsonify({
                        'erro': 'Limite de 30 solicitações/mês atingido. Faça upgrade para o plano Professional.',
                        'upgrade': True
                    }), 403

        if not sol.estado.pode_avancar():
            return jsonify({'erro': 'Esta solicitação já está em estado final'}), 400

        # se EmProcessamento, exige método de tratamento e avalia o produto
        estado_atual = sol.estado.obter_nome()
        if estado_atual == 'Em Processamento':
            metodo_str = request.form.get('metodo', '').strip()
            if not metodo_str:
                return jsonify({'erro': 'Informe o método de tratamento'}), 400
            metodo_map = {
                'reciclagem': MetodoTratamentoFactory.criar_reciclagem(),
                'reuso':      MetodoTratamentoFactory.criar_reuso(),
                'descarte':   MetodoTratamentoFactory.criar_descarte_controlado(),
            }
            metodo = metodo_map.get(metodo_str.lower())
            if metodo is None:
                return jsonify({'erro': f'Método inválido: {metodo_str}'}), 400
            servico_descarte.definir_metodo_tratamento(sol, metodo)

            # avaliação do produto
            estado_produto = request.form.get('estado_produto', 'funcionando').strip()
            valor_proposto_str = request.form.get('valor_proposto', '').strip()
            justificativa = request.form.get('justificativa', '').strip()
            valor_proposto = float(valor_proposto_str) if valor_proposto_str else None

            # calcula valor total avaliado somando todos os itens
            valor_total_avaliado = 0.0
            for item in sol.itens:
                subcategoria = item.dispositivo.subcategoria or 'smartphone_medio'
                preco_row = dados.buscar_preco_subcategoria(subcategoria)
                if preco_row:
                    vb = float(preco_row['valor_base_funcionando'])
                    vm = float(preco_row['valor_minimo_sucata'])
                else:
                    vb, vm = item.dispositivo.calcular_valor_revenda(), 0.0
                if valor_proposto is not None:
                    resultado_override = ServicoDescarte.validar_override(valor_proposto, vb, vm)
                    valor_item = resultado_override['valor_aplicado']
                    status_override = resultado_override['status']
                else:
                    valor_item = item.dispositivo.calcular_valor_avaliado(
                        EstadoProduto(estado_produto), vb, vm
                    )
                    status_override = 'nenhum'
                valor_total_avaliado += valor_item * item.quantidade

            dados.atualizar_avaliacao_solicitacao(
                sol.id, estado_produto, valor_total_avaliado, justificativa, status_override
            )

        servico_descarte.avancar_estado_solicitacao(sol)

        novo_estado = sol.estado.obter_nome()

        # feature flag Enterprise: cidadão recebe 50% de bônus nos pontos
        # quando uma empresa Enterprise finaliza a solicitação
        _estados_finais_set = {'Reciclado', 'Reutilizado', 'Descartado'}
        notificacao_msg = ''
        bonus_msg = ''
        if novo_estado in _estados_finais_set:
            if sol.usuario.obter_tipo() == 'Cidadão':
                # usa valor avaliado gravado no banco se disponível, senão fallback legacy
                avaliacao_row = dados.buscar_avaliacao_solicitacao(sol.id)
                if avaliacao_row and avaliacao_row['valor_proposto']:
                    valor_revenda_total = float(avaliacao_row['valor_proposto'])
                else:
                    valor_revenda_total = sum(
                        item.dispositivo.calcular_valor_revenda() * item.quantidade
                        for item in sol.itens
                    )
                credito = round(valor_revenda_total * 0.1, 2)
                nome_empresa = usuario['nome'] if usuario['tipo'] == 'empresa' else 'EcoTech'
                dados.salvar_entrega_para_solicitacao(sol.id, sol.usuario.id, credito, nome_empresa)
                # pontos = valor_final × 10% em R$ ÷ TAXA_REAIS_POR_PONTO
                pontos_credito = int(credito / servico_saque.TAXA_REAIS_POR_PONTO)
                dados.atualizar_pontos_cidadao(sol.usuario.id, pontos_credito)
                sol.usuario.adicionar_pontos(pontos_credito)
                notificacao_msg = f'+{pontos_credito} pontos creditados!'
                if credito > 0:
                    notificacao_msg += f' Crédito de R$ {credito:.2f} liberado na carteira!'

                # parcelas EcoTech e empresa
                plano_empresa = dados.buscar_plano_empresa(usuario['id']) if usuario['tipo'] == 'empresa' else 'free'
                taxa_ecotech = ServicoDescarte.TAXAS_ECOTECH.get(plano_empresa, 0.08)
                valor_ecotech = round(valor_revenda_total * taxa_ecotech, 2)
                valor_empresa = round(valor_revenda_total * (1.0 - 0.10 - taxa_ecotech), 2)
                if usuario['tipo'] == 'empresa':
                    dados.atualizar_saldo_empresa(usuario['id'], valor_empresa)
                dados.registrar_receita_ecotech(sol.id, valor_ecotech)

            # bônus Enterprise para o cidadão que submeteu
            if usuario['tipo'] == 'empresa':
                plano_atual = dados.buscar_plano_empresa(usuario['id'])
                if plano_atual == 'enterprise' and sol.usuario.obter_tipo() == 'Cidadão':
                    peso = sol.calcular_peso_total()
                    bonus = int(peso * 10 * 0.5)  # 50% extra
                    if bonus > 0:
                        dados.atualizar_pontos_cidadao(sol.usuario.id, bonus)
                        bonus_msg = f' Bônus Enterprise: +{bonus} pontos extras!'
                        notificacao_msg += bonus_msg

        dados.salvar_notificacao(
            sol.usuario.id,
            f'Sua solicitação foi atualizada para: {novo_estado}.{bonus_msg}'
        )

        return jsonify({
            'novo_estado': novo_estado,
            'pode_avancar': sol.estado.pode_avancar(),
            'notificacao': notificacao_msg,
        })

    @app.route('/relatorios')
    def relatorios():
        """Página de relatórios ambientais."""
        if not usuario_logado():
            return redirect(url_for('login'))

        usuario = dados_usuario()
        
        # busca todas as solicitacoes
        todas_solicitacoes = servico_descarte.listar_solicitacoes()
        
        """Administrador vê tudo; empresa usa o escopo operacional."""
        if usuario['tipo'] == 'administrador':
            solicitacoes_para_relatorio = todas_solicitacoes
            titulo_relatorio = "Relatório Geral do Sistema"
        elif usuario['tipo'] == 'empresa':
            solicitacoes_para_relatorio = listar_solicitacoes_visiveis_empresa(
                usuario['id'], todas_solicitacoes, dados
            )
            titulo_relatorio = f"Relatório de {usuario['nome']}"
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

        plano_empresa = dados.buscar_plano_empresa(usuario['id']) if usuario['tipo'] == 'empresa' else None

        return render_template(
            'relatorios.html',
            usuario=usuario,
            metricas=metricas,
            solicitacoes=solicitacoes_finalizadas,
            is_admin=usuario['tipo'] == 'administrador',
            data_inicio_str=data_inicio_str,
            data_fim_str=data_fim_str,
            plano_empresa=plano_empresa,
        )
    
    @app.route('/relatorios/exportar-csv')
    def exportar_csv():
        """Exporta solicitações finalizadas como CSV (Professional+ apenas)."""
        if not usuario_logado():
            return redirect(url_for('login'))
        usuario = dados_usuario()
        if usuario['tipo'] == 'empresa':
            plano = dados.buscar_plano_empresa(usuario['id'])
            if plano == 'free':
                flash('Exportação de dados disponível apenas nos planos Professional e Enterprise.', 'error')
                return redirect(url_for('relatorios'))
        elif usuario['tipo'] not in ('administrador',):
            flash('Acesso não autorizado.', 'error')
            return redirect(url_for('relatorios'))

        todas_solicitacoes = servico_descarte.listar_solicitacoes()
        if usuario['tipo'] == 'administrador':
            solicitacoes = todas_solicitacoes
        else:
            solicitacoes = listar_solicitacoes_visiveis_empresa(
                usuario['id'], todas_solicitacoes, dados
            )

        estados_finais = {'Reciclado', 'Reutilizado', 'Descartado'}
        finalizadas = [s for s in solicitacoes if s.estado.obter_nome() in estados_finais]

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Usuario', 'Peso (kg)', 'Impacto CO2 (kg)', 'Metodo', 'Estado', 'Data'])
        for s in finalizadas:
            writer.writerow([
                s.id,
                s.usuario.nome,
                round(s.calcular_peso_total(), 2),
                round(s.calcular_impacto_total(), 2),
                s.metodo_tratamento.obter_nome() if s.metodo_tratamento else '',
                s.estado.obter_nome(),
                s._data_criacao.strftime('%d/%m/%Y') if s._data_criacao else '',
            ])

        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=relatorio_ecotech.csv'}
        )

    @app.route('/solicitacao/<id_sol>/mtr')
    def gerar_mtr_pdf(id_sol):
        """Gera e retorna o PDF do MTR para a solicitação. Professional+ e admin apenas."""
        if not usuario_logado():
            return redirect(url_for('login'))

        usuario = dados_usuario()

        # Gate: apenas empresa Professional/Enterprise ou admin
        if usuario['tipo'] == 'empresa':
            plano = dados.buscar_plano_empresa(usuario['id'])
            if plano == 'free':
                flash('Geração de MTR disponível apenas nos planos Professional e Enterprise.', 'error')
                return redirect(url_for('operacoes'))
        elif usuario['tipo'] == 'cidadao':
            flash('Acesso não autorizado.', 'error')
            return redirect(url_for('dashboard'))

        # Busca a solicitação
        todas = servico_descarte.listar_solicitacoes()
        sol = next((s for s in todas if s.id == id_sol), None)
        if sol is None:
            flash('Solicitação não encontrada.', 'error')
            return redirect(url_for('operacoes'))

        if not usuario_pode_operar_solicitacao(usuario, sol, dados):
            flash('Acesso não autorizado a esta solicitação.', 'error')
            return redirect(url_for('operacoes'))

        pdf_bytes = gerar_mtr(sol)
        numero_mtr = f"MTR-{sol.id[:8].upper()}"
        return Response(
            pdf_bytes,
            mimetype='application/pdf',
            headers={'Content-Disposition': f'attachment; filename={numero_mtr}.pdf'}
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

        per_page = 20
        total_cidadaos = len(cidadaos)
        total_empresas = len(empresas)

        page_c = request.args.get('page_c', 1, type=int)
        total_pages_c = max(1, (total_cidadaos + per_page - 1) // per_page)
        page_c = max(1, min(page_c, total_pages_c))
        cidadaos_page = cidadaos[(page_c - 1) * per_page : page_c * per_page]

        page_e = request.args.get('page_e', 1, type=int)
        total_pages_e = max(1, (total_empresas + per_page - 1) // per_page)
        page_e = max(1, min(page_e, total_pages_e))
        empresas_page = empresas[(page_e - 1) * per_page : page_e * per_page]

        return render_template('usuarios.html',
                             usuario=usuario,
                             cidadaos=cidadaos_page,
                             empresas=empresas_page,
                             total_cidadaos=total_cidadaos,
                             total_empresas=total_empresas,
                             page_c=page_c,
                             total_pages_c=total_pages_c,
                             page_e=page_e,
                             total_pages_e=total_pages_e)
    
    @app.route('/api/solicitacoes')
    def api_solicitacoes():
        """API para listar solicitações do usuário logado."""
        if not usuario_logado():
            return jsonify({'error': 'Not authenticated'}), 401

        usuario = dados_usuario()
        todas = servico_descarte.listar_solicitacoes()

        if usuario['tipo'] == 'administrador':
            lista = todas
        elif usuario['tipo'] == 'empresa':
            lista = listar_solicitacoes_visiveis_empresa(
                usuario['id'], todas, dados
            )
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

    @app.route('/admin/overrides')
    def admin_overrides():
        """Fila de overrides de valor aguardando aprovação do admin."""
        if not usuario_logado():
            return redirect(url_for('login'))

        usuario = dados_usuario()
        if usuario['tipo'] != 'administrador':
            flash('Acesso negado.', 'error')
            return redirect(url_for('dashboard'))

        pendentes_raw = dados.buscar_overrides_pendentes()

        from datetime import datetime

        def _fmt(data_str):
            if not data_str:
                return '-'
            try:
                return datetime.strptime(data_str, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')
            except Exception:
                return data_str

        _estado_labels = {
            'funcionando': 'Funcionando',
            'defeito_leve': 'Defeito Leve',
            'defeito_grave': 'Defeito Grave',
            'sucata': 'Sucata',
        }

        pendentes = [
            {
                'id': row['id'],
                'data_criacao': _fmt(row['data_criacao']),
                'nome_usuario': row['nome_usuario'],
                'tipo_usuario': row['tipo_usuario'],
                'estado_produto': _estado_labels.get(row['estado_produto'], row['estado_produto'] or '-'),
                'valor_proposto': float(row['valor_proposto']) if row['valor_proposto'] else 0.0,
                'justificativa': row['justificativa_valor'] or '-',
            }
            for row in pendentes_raw
        ]

        return render_template(
            'admin_overrides.html',
            usuario=usuario,
            pendentes=pendentes,
            total=len(pendentes),
        )

    @app.route('/admin/overrides/<id_sol>/aprovar', methods=['POST'])
    def aprovar_override(id_sol):
        """Aprova o override de valor proposto para uma solicitação."""
        if not usuario_logado():
            return jsonify({'error': 'Not authenticated'}), 401

        usuario = dados_usuario()
        if usuario['tipo'] != 'administrador':
            return jsonify({'error': 'Acesso negado'}), 403

        dados.aprovar_override(id_sol)
        flash('Override aprovado com sucesso.', 'success')
        return redirect(url_for('admin_overrides'))

    @app.route('/admin/overrides/<id_sol>/rejeitar', methods=['POST'])
    def rejeitar_override(id_sol):
        """Rejeita o override, revertendo ao valor calculado automaticamente."""
        if not usuario_logado():
            return jsonify({'error': 'Not authenticated'}), 401

        usuario = dados_usuario()
        if usuario['tipo'] != 'administrador':
            return jsonify({'error': 'Acesso negado'}), 403

        # recalcula o valor correto baseado no estado_produto e tabela_precos
        avaliacao = dados.buscar_avaliacao_solicitacao(id_sol)
        estado_produto_str = avaliacao['estado_produto'] if avaliacao else 'funcionando'

        itens = dados.buscar_itens_solicitacao(id_sol)
        valor_recalculado = 0.0
        for item in itens:
            subcategoria = item['subcategoria'] or 'smartphone_medio'
            preco_row = dados.buscar_preco_subcategoria(subcategoria)
            if preco_row:
                vb = float(preco_row['valor_base_funcionando'])
                vm = float(preco_row['valor_minimo_sucata'])
            else:
                vb, vm = 0.0, 0.0
            try:
                estado_enum = EstadoProduto(estado_produto_str)
            except ValueError:
                estado_enum = EstadoProduto.FUNCIONANDO
            # cria dispositivo temporário para usar calcular_valor_avaliado
            from ..domain.dispositivos import Celular
            tmp = Celular(id='tmp', nome='tmp', peso_kg=0.0)
            valor_item = tmp.calcular_valor_avaliado(estado_enum, vb, vm)
            quantidade = item['quantidade'] if 'quantidade' in item.keys() else 1
            valor_recalculado += valor_item * quantidade

        dados.rejeitar_override(id_sol, valor_recalculado)
        flash('Override rejeitado. Valor revertido ao cálculo automático.', 'success')
        return redirect(url_for('admin_overrides'))

    @app.route('/admin/precos')
    def admin_precos():
        """Tabela de preços editável pelo admin."""
        if not usuario_logado():
            return redirect(url_for('login'))

        usuario = dados_usuario()
        if usuario['tipo'] != 'administrador':
            flash('Acesso negado.', 'error')
            return redirect(url_for('dashboard'))

        tabela = dados.buscar_tabela_precos()
        _cat_labels = {
            'celular': 'Celular',
            'computador': 'Computador',
            'eletrodomestico': 'Eletrodoméstico',
        }
        _sub_labels = {
            'smartphone_basico': 'Smartphone Básico',
            'smartphone_medio': 'Smartphone Médio',
            'smartphone_premium': 'Smartphone Premium',
            'iphone': 'iPhone',
            'notebook_basico': 'Notebook Básico',
            'notebook_gamer': 'Notebook Gamer',
            'desktop': 'Desktop',
            'geladeira': 'Geladeira',
            'lavadora': 'Lavadora',
            'ar_condicionado': 'Ar-condicionado',
            'micro_ondas': 'Micro-ondas',
            'tv': 'TV',
        }
        precos = [
            {
                'subcategoria': row['subcategoria'],
                'subcategoria_label': _sub_labels.get(row['subcategoria'], row['subcategoria']),
                'categoria': _cat_labels.get(row['categoria'], row['categoria']),
                'valor_base': float(row['valor_base_funcionando']),
                'valor_minimo': float(row['valor_minimo_sucata']),
            }
            for row in tabela
        ]
        return render_template('admin_precos.html', usuario=usuario, precos=precos)

    @app.route('/admin/precos/<subcategoria>', methods=['POST'])
    def atualizar_preco(subcategoria):
        """Atualiza valores de uma subcategoria (admin only)."""
        if not usuario_logado():
            return jsonify({'error': 'Not authenticated'}), 401

        usuario = dados_usuario()
        if usuario['tipo'] != 'administrador':
            return jsonify({'error': 'Acesso negado'}), 403

        try:
            valor_base = float(request.form.get('valor_base', '0').replace(',', '.'))
            valor_minimo = float(request.form.get('valor_minimo', '0').replace(',', '.'))
        except ValueError:
            flash('Valores inválidos.', 'error')
            return redirect(url_for('admin_precos'))

        if valor_base <= 0 or valor_minimo < 0:
            flash('Valor base deve ser positivo e valor mínimo não pode ser negativo.', 'error')
            return redirect(url_for('admin_precos'))

        if valor_minimo >= valor_base:
            flash('Valor mínimo de sucata deve ser menor que o valor base.', 'error')
            return redirect(url_for('admin_precos'))

        dados.atualizar_preco_subcategoria(subcategoria, valor_base, valor_minimo)
        flash(f'Preços de "{subcategoria}" atualizados com sucesso.', 'success')
        return redirect(url_for('admin_precos'))

    @app.cli.command('processar-ofertas')
    @click.option(
        '--agora', default=None,
        help='Instante ISO-8601 opcional para execução determinística.'
    )
    def processar_ofertas(agora):
        """Expira ofertas vencidas e ativa o próximo lote, sem espera ativa."""
        instante = datetime.fromisoformat(agora) if agora else datetime.now()
        ativadas = servico_despacho.processar_ofertas_expiradas(instante)
        click.echo(f'{len(ativadas)} oferta(s) ativada(s).')

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
