"""Camada de API JSON do EcoTech, usada pelo app mobile (prefixo /api/v1).

As rotas aqui apenas traduzem HTTP <-> services existentes em
`ecotech/application/`. Nenhuma regra de negocio deve ser reimplementada
neste modulo, ela ja existe nos services e no dominio.
"""

import os
import uuid
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import Blueprint, Response, current_app, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from ..application.authorization import (
    listar_solicitacoes_visiveis_empresa,
    usuario_pode_visualizar_solicitacao,
)
from ..application.elegibilidade import DemandaColeta
from ..application.factories import DispositivoFactory
from ..domain.estados import BuscandoEmpresa
from ..domain.logistica import Coordenadas
from ..application.services import (
    ServicoAutenticacao,
    ServicoDescarte,
    ServicoSaque,
    ServicoUsuario,
)

ALGORITMO_JWT = 'HS256'
EXPIRACAO_TOKEN_HORAS = 8


def _chave_jwt() -> str:
    """Chave usada para assinar o token, propria para nao acoplar ao cookie de sessao."""
    return os.environ.get('ECOTECH_JWT_SECRET') or current_app.secret_key


def gerar_token(usuario_id: str, nome: str, tipo: str) -> str:
    """Gera o token de acesso do usuario autenticado."""
    agora = datetime.now(timezone.utc)
    payload = {
        'sub': usuario_id,
        'nome': nome,
        'tipo': tipo,
        'iat': agora,
        'exp': agora + timedelta(hours=EXPIRACAO_TOKEN_HORAS),
    }
    return jwt.encode(payload, _chave_jwt(), algorithm=ALGORITMO_JWT)


def decodificar_token(token: str):
    """Retorna o payload do token ou None se invalido ou expirado."""
    try:
        return jwt.decode(token, _chave_jwt(), algorithms=[ALGORITMO_JWT])
    except jwt.PyJWTError:
        return None


def usuario_autenticado_por_token():
    """Le o header Authorization e devolve o payload do token, se houver."""
    cabecalho = request.headers.get('Authorization', '')
    if not cabecalho.startswith('Bearer '):
        return None
    token = cabecalho[len('Bearer '):].strip()
    return decodificar_token(token)


def requer_autenticacao_api(funcao):
    """Bloqueia a rota se nao vier um Bearer token valido."""
    @wraps(funcao)
    def wrapper(*args, **kwargs):
        payload = usuario_autenticado_por_token()
        if payload is None:
            return jsonify({'erro': 'Nao autenticado'}), 401
        request.usuario_token = payload
        return funcao(*args, **kwargs)
    return wrapper


def criar_blueprint_api_v1(
    servico_autenticacao: ServicoAutenticacao,
    servico_usuario: ServicoUsuario,
    servico_descarte: ServicoDescarte,
    servico_saque: ServicoSaque,
    dados,
    servico_ponto,
    geolocalizador,
    servico_agendamento,
    servico_despacho,
) -> Blueprint:
    """Monta o blueprint /api/v1 reaproveitando os services ja existentes."""
    bp = Blueprint('api_v1', __name__, url_prefix='/api/v1')
    estados_finais = {'Reciclado', 'Reutilizado', 'Descartado'}

    def _solicitacoes_do_usuario(usuario_id: str, tipo: str):
        solicitacoes = servico_descarte.listar_solicitacoes()
        if tipo == 'administrador':
            return solicitacoes
        if tipo == 'empresa':
            return listar_solicitacoes_visiveis_empresa(
                usuario_id, solicitacoes, dados
            )
        return [s for s in solicitacoes if s.usuario.id == usuario_id]

    def _resumo_solicitacao(solicitacao):
        return {
            'id': solicitacao.id,
            'cidadao': solicitacao.usuario.nome,
            'estado': solicitacao.estado.obter_nome(),
            'peso_kg': round(solicitacao.calcular_peso_total(), 3),
            'data_criacao': solicitacao.data_criacao.isoformat(),
            'ponto_coleta': (
                solicitacao.ponto_coleta.nome
                if solicitacao.ponto_coleta else None
            ),
        }

    def _perfil_completo(usuario_id: str, tipo: str):
        usuario = dados.buscar_usuario(usuario_id)
        if usuario is None:
            return None
        perfil = {
            'id': usuario['id'],
            'nome': usuario['nome'],
            'email': usuario['email'],
            'tipo': tipo,
            'data_cadastro': usuario['data_cadastro'],
        }
        if tipo == 'cidadao':
            cidadao = dados.buscar_cidadao(usuario_id)
            perfil['cpf'] = cidadao['cpf'] if cidadao else None
        elif tipo == 'empresa':
            empresa = dados.buscar_empresa(usuario_id)
            perfil['cnpj'] = empresa['cnpj'] if empresa else None
            perfil['razao_social'] = empresa['razao_social'] if empresa else None
        return perfil

    def _dashboard_cidadao(usuario_id: str, solicitacoes):
        cidadao = dados.buscar_cidadao(usuario_id)
        pontos = int(cidadao['pontos'] or 0) if cidadao else 0
        total_sacado = sum(
            float(saque['valor'])
            for saque in servico_saque.listar_saques(usuario_id)
            if saque.get('status') != 'cancelado'
        )
        saldo = max(
            round(pontos * servico_saque.TAXA_REAIS_POR_PONTO - total_sacado, 2),
            0.0,
        )
        tier = servico_descarte.calcular_info_tier(pontos)
        total_dispositivos = sum(
            item.quantidade
            for solicitacao in solicitacoes
            for item in solicitacao.itens
        )
        ativas = [
            s for s in solicitacoes
            if s.estado.obter_nome() not in estados_finais | {'Cancelado'}
        ]
        entregas = [
            {
                'id': entrega['id'],
                'valor': float(entrega['valor']),
                'empresa': entrega['empresa'],
                'data': entrega['data'],
                'hora': entrega['hora'],
                'status': entrega['status'],
            }
            for entrega in dados.buscar_entregas_usuario(usuario_id)
        ]
        entregas.reverse()
        return {
            'metricas': {
                'saldo': saldo,
                'pontos': pontos,
                'tier': tier['nome'],
                'dispositivos': total_dispositivos,
            },
            'missao': {
                'titulo': 'Recicle 15 aparelhos',
                'atual': min(total_dispositivos, 15),
                'meta': 15,
                'recompensa_pontos': 150,
            },
            'proximo_tier': {
                'nome': tier['proximo_nome'],
                'meta': tier['meta'],
                'progresso_percentual': tier['progresso_pct'],
            },
            'entregas_recentes': entregas[:5],
            'solicitacoes_ativas': [
                _resumo_solicitacao(s)
                for s in sorted(ativas, key=lambda s: s.data_criacao, reverse=True)[:5]
            ],
        }

    def _dashboard_empresa(usuario_id: str, solicitacoes):
        finais = [s for s in solicitacoes if s.estado.obter_nome() in estados_finais]
        recicladas = [s for s in finais if s.estado.obter_nome() == 'Reciclado']
        peso_processado = round(sum(s.calcular_peso_total() for s in finais), 2)
        ativas = [
            s for s in solicitacoes
            if s.estado.obter_nome() not in estados_finais | {'Cancelado'}
        ]
        em_processamento = [
            s for s in solicitacoes
            if s.estado.obter_nome() == 'Em Processamento'
        ]

        categorias = {}
        mapa_categoria = {
            'Celular': 'Celulares',
            'Computador': 'Computadores',
            'Eletrodomestico': 'Eletrodomesticos',
        }
        for solicitacao in finais:
            for item in solicitacao.itens:
                categoria = mapa_categoria.get(
                    type(item.dispositivo).__name__,
                    type(item.dispositivo).__name__,
                )
                categorias[categoria] = round(
                    categorias.get(categoria, 0.0) + item.calcular_peso_total(), 2
                )

        agora = datetime.now()
        meses = []
        ano, mes = agora.year, agora.month
        for _ in range(6):
            peso_mes = sum(
                s.calcular_peso_total()
                for s in finais
                if s.data_criacao.year == ano and s.data_criacao.month == mes
            )
            meses.append({
                'mes': f'{mes:02d}/{str(ano)[2:]}',
                'peso_kg': round(peso_mes, 2),
            })
            mes -= 1
            if mes == 0:
                mes, ano = 12, ano - 1
        meses.reverse()

        comparativo = None
        if meses[-1]['peso_kg'] and meses[-2]['peso_kg']:
            comparativo = round(
                (meses[-1]['peso_kg'] - meses[-2]['peso_kg'])
                / meses[-2]['peso_kg'] * 100,
                1,
            )
        return {
            'metricas': {
                'finalizadas': len(finais),
                'ativas': len(ativas),
                'peso_processado_kg': peso_processado,
                'saldo': round(dados.buscar_saldo_empresa(usuario_id), 2),
                'co2_evitado_kg': round(peso_processado * 3.0, 1),
                'taxa_reciclagem_percentual': (
                    round(len(recicladas) / len(finais) * 100, 1)
                    if finais else 0.0
                ),
            },
            'comparativo_mensal_percentual': comparativo,
            'meses': meses,
            'categorias': [
                {'nome': nome, 'peso_kg': peso}
                for nome, peso in sorted(categorias.items())
            ],
            'total_em_processamento': len(em_processamento),
            'em_processamento': [
                _resumo_solicitacao(s)
                for s in sorted(
                    em_processamento,
                    key=lambda s: s.data_criacao,
                    reverse=True,
                )[:5]
            ],
        }

    def _dashboard_admin(solicitacoes):
        metricas = servico_descarte.calcular_metricas(solicitacoes)
        ativas = [
            s for s in solicitacoes
            if s.estado.obter_nome() not in estados_finais | {'Cancelado'}
        ]
        return {
            'metricas': {
                'peso_total_kg': round(metricas['peso_total'], 2),
                'solicitacoes': len(solicitacoes),
                'ativas': len(ativas),
                'finalizadas': metricas['total_processadas'],
                'impacto_evitado_kg': round(metricas['impacto_total'], 2),
                'receita': round(dados.buscar_receita_total_ecotech(), 2),
            },
            'solicitacoes_recentes': [
                _resumo_solicitacao(s)
                for s in sorted(
                    solicitacoes,
                    key=lambda s: s.data_criacao,
                    reverse=True,
                )[:10]
            ],
        }

    def _usuario_token_dict():
        payload = request.usuario_token
        return {'id': payload['sub'], 'tipo': payload['tipo']}

    def _exigir_cidadao():
        if request.usuario_token['tipo'] != 'cidadao':
            return jsonify({'erro': 'Recurso exclusivo para cidadaos'}), 403
        return None

    def _nome_empresa_solicitacao(solicitacao, raw=None):
        raw = raw or dados.buscar_solicitacao(solicitacao.id)
        empresa_id = raw['empresa_responsavel_id'] if raw else None
        if not empresa_id and solicitacao.ponto_coleta:
            ponto = dados.buscar_ponto_coleta(solicitacao.ponto_coleta.id)
            empresa_id = ponto['id_empresa'] if ponto else None
        empresa = dados.buscar_usuario(empresa_id) if empresa_id else None
        return empresa['nome'] if empresa else None

    def _resumo_operacao(solicitacao):
        raw = dados.buscar_solicitacao(solicitacao.id)
        confirmado = raw['peso_confirmado_kg'] if raw else None
        estimado = raw['peso_estimado_kg'] if raw else None
        return {
            **_resumo_solicitacao(solicitacao),
            'empresa': _nome_empresa_solicitacao(solicitacao, raw),
            'tipo_coleta': raw['tipo_coleta'] if raw else None,
            'peso_estimado_kg': estimado,
            'peso_confirmado_kg': confirmado,
            'peso_origem': 'aferido' if confirmado is not None else 'estimado',
            'quantidade_itens': sum(item.quantidade for item in solicitacao.itens),
        }

    def _detalhes_operacao(solicitacao):
        raw = dados.buscar_solicitacao(solicitacao.id)
        itens = [dict(item) for item in dados.buscar_itens_solicitacao(solicitacao.id)]
        fotos = [
            {
                **dict(foto),
                'url': f'/api/v1/solicitacoes/{solicitacao.id}/fotos/{foto["id"]}',
            }
            for foto in dados.listar_fotos_solicitacao(solicitacao.id)
        ]
        historico = [
            dict(item) for item in dados.buscar_historico_solicitacao(solicitacao.id)
        ]
        agendamento = dados.buscar_agendamento(solicitacao.id)
        avaliacao = dados.buscar_avaliacao_solicitacao(solicitacao.id)
        return {
            **_resumo_operacao(solicitacao),
            'endereco_coleta': raw['endereco_coleta'],
            'nome_contato': raw['nome_contato'],
            'data_agendamento': raw['data_agendamento'],
            'metodo_tratamento': raw['metodo_tratamento'],
            'peso_informado_cidadao': bool(raw['peso_informado_cidadao']),
            'peso_confirmado_em': raw['peso_confirmado_em'],
            'itens': itens,
            'fotos': fotos,
            'historico': historico,
            'agendamento': dict(agendamento) if agendamento else None,
            'avaliacao': dict(avaliacao) if avaliacao else None,
        }

    @staticmethod
    def _validar_fotos(arquivos):
        fotos = []
        if len([a for a in arquivos if a and a.filename]) > 5:
            raise ValueError('Envie no maximo 5 fotos por solicitacao')
        for arquivo in arquivos:
            if not arquivo or not arquivo.filename:
                continue
            conteudo = arquivo.read()
            if conteudo.startswith(b'\xff\xd8\xff'):
                mime_type = 'image/jpeg'
            elif conteudo.startswith(b'\x89PNG\r\n\x1a\n'):
                mime_type = 'image/png'
            elif len(conteudo) > 12 and conteudo[:4] == b'RIFF' and conteudo[8:12] == b'WEBP':
                mime_type = 'image/webp'
            else:
                raise ValueError('Envie somente fotos JPG, PNG ou WebP')
            if len(conteudo) > 5 * 1024 * 1024:
                raise ValueError('Cada foto pode ter no maximo 5 MB')
            fotos.append((arquivo.filename[:180], mime_type, conteudo))
        return fotos

    @staticmethod
    def _montar_endereco(formulario):
        obrigatorios = ('cep', 'logradouro', 'numero', 'bairro', 'cidade', 'uf')
        ausentes = [campo for campo in obrigatorios if not formulario.get(campo, '').strip()]
        if ausentes:
            raise ValueError('Preencha todos os campos obrigatorios do endereco')
        cep = ''.join(c for c in formulario['cep'] if c.isdigit())
        if len(cep) != 8:
            raise ValueError('Informe um CEP valido com 8 digitos')
        endereco = f'{formulario["logradouro"].strip()}, {formulario["numero"].strip()}'
        complemento = formulario.get('complemento', '').strip()
        if complemento:
            endereco += f', {complemento}'
        endereco += (
            f' - {formulario["bairro"].strip()}, {formulario["cidade"].strip()}'
            f' - {formulario["uf"].strip().upper()}, CEP {cep[:5]}-{cep[5:]}'
        )
        referencia = formulario.get('referencia', '').strip()
        if referencia:
            endereco += f'. Referencia: {referencia}'
        return endereco, cep

    def _resposta_autenticada(usuario):
        dados_sessao = servico_autenticacao.criar_dados_sessao(usuario)
        token = gerar_token(
            dados_sessao['user_id'], dados_sessao['user_nome'], dados_sessao['user_tipo']
        )
        return jsonify({
            'access_token': token,
            'token_type': 'Bearer',
            'expires_in': EXPIRACAO_TOKEN_HORAS * 3600,
            'usuario': {
                'id': dados_sessao['user_id'],
                'nome': dados_sessao['user_nome'],
                'tipo': dados_sessao['user_tipo'],
            },
        })

    @bp.route('/auth/login', methods=['POST'])
    def login_api():
        corpo = request.get_json(silent=True) or {}
        tipo = (corpo.get('tipo') or '').strip()
        credencial = (corpo.get('credencial') or '').strip()
        senha = corpo.get('senha') or ''

        if tipo in ('cidadao', 'empresa'):
            credencial = (
                credencial.replace('.', '').replace('-', '')
                .replace('/', '').replace(' ', '')
            )

        usuario = servico_autenticacao.autenticar(tipo, credencial, senha)
        if usuario is None:
            return jsonify({'erro': 'Credencial ou senha invalidos'}), 401

        return _resposta_autenticada(usuario)

    @bp.route('/auth/registrar', methods=['POST'])
    def registrar_api():
        corpo = request.get_json(silent=True) or {}
        tipo = (corpo.get('tipo') or 'cidadao').strip()
        nome = (corpo.get('nome') or '').strip()
        email = (corpo.get('email') or '').strip()
        senha = corpo.get('senha') or ''
        senha_confirmacao = corpo.get('senha_confirmacao') or ''

        if not nome or not email or not senha:
            return jsonify({'erro': 'Preencha todos os campos obrigatorios'}), 400
        if senha != senha_confirmacao:
            return jsonify({'erro': 'As senhas nao coincidem'}), 400
        if len(senha) < 6:
            return jsonify({'erro': 'A senha deve ter pelo menos 6 caracteres'}), 400

        dados_novo = {'nome': nome, 'email': email}
        if tipo == 'cidadao':
            dados_novo['cpf'] = (corpo.get('cpf') or '').strip()
        elif tipo == 'empresa':
            dados_novo['cnpj'] = (corpo.get('cnpj') or '').strip()
            dados_novo['razao_social'] = (corpo.get('razao_social') or '').strip()

        try:
            usuario = servico_usuario.criar_usuario(tipo, dados_novo, senha)
        except (ValueError, Exception) as exc:
            return jsonify({'erro': str(exc)}), 400

        return _resposta_autenticada(usuario)

    @bp.route('/auth/me', methods=['GET'])
    @requer_autenticacao_api
    def perfil_api():
        payload = request.usuario_token
        usuario = servico_usuario.buscar_usuario(payload['sub'])
        if usuario is None:
            return jsonify({'erro': 'Usuario nao encontrado'}), 404

        return jsonify({
            'id': usuario.id,
            'nome': usuario.nome,
            'email': usuario.email,
            'tipo': payload['tipo'],
        })

    @bp.route('/dashboard', methods=['GET'])
    @requer_autenticacao_api
    def dashboard_api():
        payload = request.usuario_token
        usuario_id, tipo = payload['sub'], payload['tipo']
        perfil = _perfil_completo(usuario_id, tipo)
        if perfil is None:
            return jsonify({'erro': 'Usuario nao encontrado'}), 404

        solicitacoes = _solicitacoes_do_usuario(usuario_id, tipo)
        if tipo == 'cidadao':
            dashboard = _dashboard_cidadao(usuario_id, solicitacoes)
        elif tipo == 'empresa':
            dashboard = _dashboard_empresa(usuario_id, solicitacoes)
        elif tipo == 'administrador':
            dashboard = _dashboard_admin(solicitacoes)
        else:
            return jsonify({'erro': 'Tipo de usuario invalido'}), 403
        return jsonify({'tipo': tipo, 'usuario': perfil, **dashboard})

    @bp.route('/perfil', methods=['GET', 'PATCH'])
    @requer_autenticacao_api
    def perfil_detalhado_api():
        payload = request.usuario_token
        usuario_id, tipo = payload['sub'], payload['tipo']
        perfil = _perfil_completo(usuario_id, tipo)
        if perfil is None:
            return jsonify({'erro': 'Usuario nao encontrado'}), 404

        if request.method == 'PATCH':
            corpo = request.get_json(silent=True) or {}
            nome = (corpo.get('nome') or perfil['nome']).strip()
            email = (corpo.get('email') or perfil['email']).strip().lower()
            senha_atual = corpo.get('senha_atual') or ''
            nova_senha = corpo.get('nova_senha') or ''
            confirma_senha = corpo.get('confirma_senha') or ''

            if len(nome) < 3 or not email:
                return jsonify({'erro': 'Nome e e-mail sao obrigatorios'}), 400
            usuario_email = dados.buscar_usuario_por_email(email)
            if usuario_email and usuario_email['id'] != usuario_id:
                return jsonify({'erro': 'Este e-mail ja esta em uso'}), 400

            password_hash = None
            if nova_senha:
                row = dados.buscar_usuario(usuario_id)
                if not check_password_hash(row['password_hash'] or '', senha_atual):
                    return jsonify({'erro': 'Senha atual incorreta'}), 400
                if nova_senha != confirma_senha:
                    return jsonify({'erro': 'As novas senhas nao coincidem'}), 400
                if len(nova_senha) < 6:
                    return jsonify({
                        'erro': 'A nova senha deve ter pelo menos 6 caracteres'
                    }), 400
                password_hash = generate_password_hash(nova_senha)

            dados.atualizar_usuario(usuario_id, nome, email, password_hash)
            perfil = _perfil_completo(usuario_id, tipo)

        solicitacoes = _solicitacoes_do_usuario(usuario_id, tipo)
        metricas = servico_descarte.calcular_metricas(solicitacoes)
        resumo = {
            'total_solicitacoes': len(solicitacoes),
            'peso_total_kg': round(metricas['peso_total'], 2),
            'finalizadas': metricas['total_processadas'],
        }
        if tipo == 'cidadao':
            cidadao = dados.buscar_cidadao(usuario_id)
            pontos = int(cidadao['pontos'] or 0) if cidadao else 0
            tier = servico_descarte.calcular_info_tier(pontos)
            rank = 1
            for outro in servico_usuario.listar_usuarios():
                if outro.id == usuario_id:
                    continue
                row = dados.buscar_cidadao(outro.id)
                if row and int(row['pontos'] or 0) > pontos:
                    rank += 1
            resumo.update({
                'pontos': pontos,
                'rank': rank,
                'tier': tier,
                'conquistas': [
                    {
                        'meta': meta,
                        'titulo': titulo,
                        'conquistada': len(solicitacoes) >= meta,
                    }
                    for meta, titulo in (
                        (1, 'Primeiro descarte'),
                        (5, '5 descartes'),
                        (10, '10 descartes'),
                        (20, '20 descartes'),
                    )
                ],
            })
        return jsonify({'usuario': perfil, 'resumo': resumo})

    @bp.route('/pontos-coleta', methods=['GET'])
    @requer_autenticacao_api
    def pontos_coleta_api():
        pontos = []
        for ponto in servico_ponto.listar_pontos():
            raw = dados.buscar_ponto_coleta(ponto.id)
            empresa = (
                dados.buscar_usuario(raw['id_empresa'])
                if raw and raw['id_empresa'] else None
            )
            pontos.append({
                'id': ponto.id,
                'nome': ponto.nome,
                'empresa': empresa['nome'] if empresa else '',
                'endereco': ponto.endereco,
                'capacidade_kg': ponto.capacidade_kg,
                'ocupacao_kg': ponto.ocupacao_atual_kg,
                'disponibilidade_percentual': ponto.calcular_disponibilidade_percentual(),
            })
        return jsonify({'pontos': pontos})

    @bp.route('/cep/<cep>', methods=['GET'])
    @requer_autenticacao_api
    def consultar_cep_api(cep):
        bloqueio = _exigir_cidadao()
        if bloqueio:
            return bloqueio
        try:
            resultado = geolocalizador.consultar_cep(cep)
        except ValueError as exc:
            return jsonify({'erro': str(exc)}), 400
        return jsonify({
            'cep': ''.join(c for c in cep if c.isdigit()),
            'logradouro': resultado.get('street', ''),
            'bairro': resultado.get('neighborhood', ''),
            'cidade': resultado.get('city', ''),
            'uf': resultado.get('state', ''),
        })

    @bp.route('/solicitacoes', methods=['GET', 'POST'])
    @requer_autenticacao_api
    def solicitacoes_api():
        payload = request.usuario_token
        if request.method == 'GET':
            solicitacoes = _solicitacoes_do_usuario(payload['sub'], payload['tipo'])
            estado = request.args.get('estado', '').strip().lower()
            if estado:
                solicitacoes = [
                    s for s in solicitacoes
                    if estado in s.estado.obter_nome().lower()
                ]
            solicitacoes.sort(key=lambda s: s.data_criacao, reverse=True)
            pagina = max(request.args.get('pagina', 1, type=int), 1)
            limite = min(max(request.args.get('limite', 20, type=int), 1), 100)
            inicio = (pagina - 1) * limite
            return jsonify({
                'itens': [
                    _resumo_operacao(s)
                    for s in solicitacoes[inicio:inicio + limite]
                ],
                'pagina': pagina,
                'limite': limite,
                'total': len(solicitacoes),
                'total_paginas': max((len(solicitacoes) + limite - 1) // limite, 1),
            })

        bloqueio = _exigir_cidadao()
        if bloqueio:
            return bloqueio
        try:
            form = request.form
            fotos = _validar_fotos(request.files.getlist('fotos'))
            tipo = form.get('tipo_dispositivo', '').strip().lower()
            if tipo not in {'celular', 'computador', 'eletrodomestico'}:
                raise ValueError('Selecione um tipo de dispositivo valido')
            nome = form.get('nome', '').strip()
            subcategoria = form.get('subcategoria', '').strip()
            if not nome or not subcategoria:
                raise ValueError('Informe a categoria e o modelo do produto')
            quantidade = int(form.get('quantidade', '1'))
            if quantidade < 1 or quantidade > 100:
                raise ValueError('A quantidade deve estar entre 1 e 100')
            ano = int(form.get('ano_fabricacao', str(datetime.now().year)))
            if ano < 1950 or ano > datetime.now().year:
                raise ValueError('Informe um ano de fabricacao valido')

            peso_texto = form.get('peso_kg', '').strip().replace(',', '.')
            peso_informado = bool(peso_texto)
            pesos_estimados = {
                'celular': 0.2,
                'computador': 5.0,
                'eletrodomestico': 15.0,
            }
            peso_unitario = float(peso_texto) if peso_informado else pesos_estimados[tipo]
            if peso_unitario <= 0:
                raise ValueError('O peso deve ser maior que zero')

            tipo_coleta = form.get('tipo_coleta', 'domiciliar').strip()
            if tipo_coleta not in {'domiciliar', 'entrega_ponto'}:
                raise ValueError('Selecione uma forma de entrega valida')
            ponto = None
            endereco = ''
            coordenadas = None
            if tipo_coleta == 'entrega_ponto':
                ponto_id = form.get('ponto_id', '').strip()
                ponto = servico_ponto.buscar_ponto(ponto_id)
                if ponto is None:
                    raise ValueError('Selecione um ponto de coleta valido')
                if not ponto.pode_receber(peso_unitario * quantidade):
                    raise ValueError('O ponto selecionado nao possui capacidade disponivel')
            else:
                endereco, cep = _montar_endereco(form)
                dados_cep = geolocalizador.consultar_cep(cep)
                coordenadas = Coordenadas(
                    dados_cep['latitude'], dados_cep['longitude']
                )

            data_coleta = form.get('data_coleta', '').strip()
            hora_inicio = form.get('horario_inicio', '').strip()
            hora_fim = form.get('horario_fim', '').strip()
            if not data_coleta or not hora_inicio or not hora_fim:
                raise ValueError('Informe a data e a janela de atendimento')
            inicio = datetime.strptime(
                f'{data_coleta} {hora_inicio}', '%Y-%m-%d %H:%M'
            )
            fim = datetime.strptime(
                f'{data_coleta} {hora_fim}', '%Y-%m-%d %H:%M'
            )
            servico_agendamento.validar(inicio, fim)

            usuario = servico_usuario.buscar_usuario(payload['sub'])
            if usuario is None:
                return jsonify({'erro': 'Usuario nao encontrado'}), 404
            solicitacao = servico_descarte.criar_solicitacao(usuario, ponto)
            dispositivo = DispositivoFactory.criar_dispositivo(tipo, {
                'id': str(uuid.uuid4()),
                'nome': nome,
                'peso_kg': peso_unitario,
                'subcategoria': subcategoria,
            })
            dispositivo._modelo = nome
            dispositivo.ano_fabricacao = ano
            servico_descarte.adicionar_item_solicitacao(
                solicitacao,
                dispositivo,
                quantidade,
                form.get('observacoes', '').strip(),
            )
            dados.atualizar_detalhes_coleta(
                solicitacao.id,
                tipo_coleta,
                endereco,
                form.get('nome_contato', '').strip() or usuario.nome,
                inicio.strftime('%Y-%m-%d %H:%M'),
            )
            dados.registrar_peso_estimado(
                solicitacao.id, peso_unitario * quantidade, peso_informado
            )
            dados.salvar_historico_rastreamento(
                solicitacao.id, 'Solicitacao criada pelo cidadao'
            )
            for nome_arquivo, mime_type, conteudo in fotos:
                dados.salvar_foto_solicitacao(
                    str(uuid.uuid4()), solicitacao.id, nome_arquivo,
                    mime_type, conteudo, datetime.now().isoformat(),
                )

            if tipo_coleta == 'domiciliar':
                dados.atualizar_localizacao_coleta(
                    solicitacao.id,
                    coordenadas.latitude,
                    coordenadas.longitude,
                    'cep',
                )
                servico_agendamento.solicitar(
                    solicitacao.id, payload['sub'], inicio, fim
                )
                servico_despacho.criar_ofertas(
                    solicitacao.id,
                    DemandaColeta(
                        coordenadas=coordenadas,
                        categorias=frozenset({tipo}),
                        peso_kg=peso_unitario * quantidade,
                        agendada_para=inicio,
                    ),
                )
                solicitacao._estado = BuscandoEmpresa()
                dados.atualizar_solicitacao(
                    solicitacao.id, 'BUSCANDO_EMPRESA'
                )
            else:
                ponto_raw = dados.buscar_ponto_coleta(ponto.id)
                if ponto_raw and ponto_raw['id_empresa']:
                    dados.salvar_notificacao(
                        ponto_raw['id_empresa'],
                        f'Nova entrega de {usuario.nome}: {nome}.',
                    )
            dados.salvar_notificacao(
                payload['sub'],
                f'Sua solicitacao de descarte do {nome} foi recebida.',
            )
            return jsonify(_detalhes_operacao(solicitacao)), 201
        except (ValueError, TypeError) as exc:
            return jsonify({'erro': str(exc)}), 400

    @bp.route('/solicitacoes/<solicitacao_id>', methods=['GET'])
    @requer_autenticacao_api
    def detalhes_solicitacao_api(solicitacao_id):
        solicitacao = servico_descarte.obter_solicitacao(solicitacao_id)
        if solicitacao is None:
            return jsonify({'erro': 'Solicitacao nao encontrada'}), 404
        if not usuario_pode_visualizar_solicitacao(
            _usuario_token_dict(), solicitacao, dados
        ):
            return jsonify({'erro': 'Acesso nao autorizado'}), 403
        return jsonify(_detalhes_operacao(solicitacao))

    @bp.route('/solicitacoes/<solicitacao_id>/fotos/<foto_id>', methods=['GET'])
    @requer_autenticacao_api
    def foto_solicitacao_api(solicitacao_id, foto_id):
        solicitacao = servico_descarte.obter_solicitacao(solicitacao_id)
        foto = dados.buscar_foto_solicitacao(foto_id)
        if solicitacao is None or foto is None or foto['solicitacao_id'] != solicitacao_id:
            return jsonify({'erro': 'Foto nao encontrada'}), 404
        if not usuario_pode_visualizar_solicitacao(
            _usuario_token_dict(), solicitacao, dados
        ):
            return jsonify({'erro': 'Acesso nao autorizado'}), 403
        return Response(
            foto['conteudo'], mimetype=foto['mime_type'],
            headers={
                'Content-Disposition': f'inline; filename="{foto["nome_arquivo"]}"'
            },
        )

    @bp.route('/entregas', methods=['GET'])
    @requer_autenticacao_api
    def entregas_api():
        bloqueio = _exigir_cidadao()
        if bloqueio:
            return bloqueio
        entregas = [
            dict(entrega)
            for entrega in dados.buscar_entregas_usuario(request.usuario_token['sub'])
        ]
        entregas.reverse()
        return jsonify({'entregas': entregas})

    return bp

