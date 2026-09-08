"""Camada de API JSON do EcoTech, usada pelo app mobile (prefixo /api/v1).

As rotas aqui apenas traduzem HTTP <-> services existentes em
`ecotech/application/`. Nenhuma regra de negocio deve ser reimplementada
neste modulo, ela ja existe nos services e no dominio.
"""

import os
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import Blueprint, current_app, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from ..application.authorization import listar_solicitacoes_visiveis_empresa
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

    return bp

