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

from ..application.services import ServicoAutenticacao, ServicoUsuario

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
) -> Blueprint:
    """Monta o blueprint /api/v1 reaproveitando os services ja existentes."""
    bp = Blueprint('api_v1', __name__, url_prefix='/api/v1')

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

    return bp
