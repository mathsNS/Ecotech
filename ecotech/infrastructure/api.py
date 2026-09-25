"""Camada de API JSON do EcoTech, usada pelo app mobile (prefixo /api/v1).

As rotas aqui apenas traduzem HTTP <-> services existentes em
`ecotech/application/`. Nenhuma regra de negocio deve ser reimplementada
neste modulo, ela ja existe nos services e no dominio.
"""

import csv
import io
import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import Blueprint, Response, current_app, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from ..application.authorization import (
    listar_solicitacoes_visiveis_empresa,
    usuario_pode_operar_solicitacao,
    usuario_pode_visualizar_solicitacao,
)
from ..application.elegibilidade import DemandaColeta
from ..application.factories import DispositivoFactory, MetodoTratamentoFactory
from ..application.planos import buscar_plano, listar_planos, recursos_do_plano
from ..application.services import (
    ServicoAutenticacao,
    ServicoDescarte,
    ServicoRelatorio,
    ServicoSaque,
    ServicoUsuario,
)
from ..domain.dispositivos import EstadoProduto
from ..domain.estados import BuscandoEmpresa, Solicitado
from ..domain.logistica import Coordenadas
from .pdf import gerar_mtr

ALGORITMO_JWT = "HS256"
EXPIRACAO_TOKEN_HORAS = 8


def _expiracao_token_horas() -> int:
    try:
        configurada = int(current_app.config.get("JWT_EXPIRACAO_HORAS", EXPIRACAO_TOKEN_HORAS))
    except (TypeError, ValueError):
        configurada = EXPIRACAO_TOKEN_HORAS
    return min(168, max(1, configurada))


def _chave_jwt() -> str:
    """Chave usada para assinar o token, propria para nao acoplar ao cookie de sessao."""
    return os.environ.get("ECOTECH_JWT_SECRET") or current_app.secret_key


def gerar_token(usuario_id: str, nome: str, tipo: str) -> str:
    """Gera o token de acesso do usuario autenticado."""
    agora = datetime.now(timezone(timedelta(hours=-3)))
    payload = {
        "sub": usuario_id,
        "nome": nome,
        "tipo": tipo,
        "iat": agora,
        "exp": agora + timedelta(hours=_expiracao_token_horas()),
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
    cabecalho = request.headers.get("Authorization", "")
    if not cabecalho.startswith("Bearer "):
        return None
    token = cabecalho[len("Bearer ") :].strip()
    return decodificar_token(token)


def requer_autenticacao_api(funcao):
    """Bloqueia a rota se nao vier um Bearer token valido."""

    @wraps(funcao)
    def wrapper(*args, **kwargs):
        payload = usuario_autenticado_por_token()
        if payload is None:
            return jsonify({"erro": "Nao autenticado"}), 401
        request.usuario_token = payload
        return funcao(*args, **kwargs)

    return wrapper


def criar_blueprint_api_v1(
    servico_autenticacao: ServicoAutenticacao,
    servico_usuario: ServicoUsuario,
    servico_descarte: ServicoDescarte,
    servico_saque: ServicoSaque,
    servico_relatorio: ServicoRelatorio,
    dados,
    servico_ponto,
    geolocalizador,
    servico_agendamento,
    servico_chat,
    servico_despacho,
    servico_base,
) -> Blueprint:
    """Monta o blueprint /api/v1 reaproveitando os services ja existentes."""
    bp = Blueprint("api_v1", __name__, url_prefix="/api/v1")
    estados_finais = {"Reciclado", "Reutilizado", "Descartado"}

    def _solicitacoes_do_usuario(usuario_id: str, tipo: str):
        solicitacoes = servico_descarte.listar_solicitacoes()
        if tipo == "administrador":
            return solicitacoes
        if tipo == "empresa":
            return listar_solicitacoes_visiveis_empresa(usuario_id, solicitacoes, dados)
        return [s for s in solicitacoes if s.usuario.id == usuario_id]

    def _resumo_solicitacao(solicitacao):
        registro = dados.buscar_solicitacao(solicitacao.id)
        base = (
            dados.buscar_base_operacional(registro["base_operacional_id"])
            if registro and registro["base_operacional_id"]
            else None
        )
        return {
            "id": solicitacao.id,
            "cidadao": solicitacao.usuario.nome,
            "estado": solicitacao.estado.obter_nome(),
            "peso_kg": round(solicitacao.calcular_peso_total(), 3),
            "data_criacao": solicitacao.data_criacao.isoformat(),
            "ponto_coleta": (solicitacao.ponto_coleta.nome if solicitacao.ponto_coleta else None),
            "base_operacional": base["nome"] if base else None,
        }

    def _perfil_completo(usuario_id: str, tipo: str):
        usuario = dados.buscar_usuario(usuario_id)
        if usuario is None:
            return None
        perfil = {
            "id": usuario["id"],
            "nome": usuario["nome"],
            "email": usuario["email"],
            "tipo": tipo,
            "data_cadastro": usuario["data_cadastro"],
        }
        if tipo == "cidadao":
            cidadao = dados.buscar_cidadao(usuario_id)
            perfil["cpf"] = cidadao["cpf"] if cidadao else None
        elif tipo == "empresa":
            empresa = dados.buscar_empresa(usuario_id)
            perfil["cnpj"] = empresa["cnpj"] if empresa else None
            perfil["razao_social"] = empresa["razao_social"] if empresa else None
        return perfil

    def _dashboard_cidadao(usuario_id: str, solicitacoes):
        cidadao = dados.buscar_cidadao(usuario_id)
        pontos = int(cidadao["pontos"] or 0) if cidadao else 0
        total_sacado = sum(
            float(saque["valor"])
            for saque in servico_saque.listar_saques(usuario_id)
            if saque.get("status") != "cancelado"
        )
        saldo = max(
            round(pontos * servico_saque.TAXA_REAIS_POR_PONTO - total_sacado, 2),
            0.0,
        )
        tier = servico_descarte.calcular_info_tier(pontos)
        total_dispositivos = sum(
            item.quantidade for solicitacao in solicitacoes for item in solicitacao.itens
        )
        ativas = [
            s for s in solicitacoes if s.estado.obter_nome() not in estados_finais | {"Cancelado"}
        ]
        entregas = [
            {
                "id": entrega["id"],
                "valor": float(entrega["valor"]),
                "empresa": entrega["empresa"],
                "data": entrega["data"],
                "hora": entrega["hora"],
                "status": entrega["status"],
            }
            for entrega in dados.buscar_entregas_usuario(usuario_id)
        ]
        entregas.reverse()
        return {
            "metricas": {
                "saldo": saldo,
                "pontos": pontos,
                "tier": tier["nome"],
                "dispositivos": total_dispositivos,
            },
            "missao": {
                "titulo": "Recicle 15 aparelhos",
                "atual": min(total_dispositivos, 15),
                "meta": 15,
                "recompensa_pontos": 150,
            },
            "proximo_tier": {
                "nome": tier["proximo_nome"],
                "meta": tier["meta"],
                "progresso_percentual": tier["progresso_pct"],
            },
            "total_entregas_concluidas": sum(
                1 for entrega in entregas if str(entrega["status"]).lower() == "finalizado"
            ),
            "entregas_recentes": entregas[:6],
            "solicitacoes_ativas": [
                _resumo_solicitacao(s)
                for s in sorted(ativas, key=lambda s: s.data_criacao, reverse=True)[:5]
            ],
        }

    def _dashboard_empresa(usuario_id: str, solicitacoes):
        finais = [s for s in solicitacoes if s.estado.obter_nome() in estados_finais]
        recicladas = [s for s in finais if s.estado.obter_nome() == "Reciclado"]
        peso_processado = round(sum(s.calcular_peso_total() for s in finais), 2)
        ativas = [
            s for s in solicitacoes if s.estado.obter_nome() not in estados_finais | {"Cancelado"}
        ]
        em_processamento = [s for s in solicitacoes if s.estado.obter_nome() == "Em Processamento"]

        categorias = {}
        mapa_categoria = {
            "Celular": "Celulares",
            "Computador": "Computadores",
            "Eletrodomestico": "Eletrodomesticos",
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

        agora = datetime.now(timezone(timedelta(hours=-3)))
        meses = []
        ano, mes = agora.year, agora.month
        for _ in range(6):
            peso_mes = sum(
                s.calcular_peso_total()
                for s in finais
                if s.data_criacao.year == ano and s.data_criacao.month == mes
            )
            meses.append(
                {
                    "mes": f"{mes:02d}/{str(ano)[2:]}",
                    "peso_kg": round(peso_mes, 2),
                }
            )
            mes -= 1
            if mes == 0:
                mes, ano = 12, ano - 1
        meses.reverse()

        comparativo = None
        if meses[-1]["peso_kg"] and meses[-2]["peso_kg"]:
            comparativo = round(
                (meses[-1]["peso_kg"] - meses[-2]["peso_kg"]) / meses[-2]["peso_kg"] * 100,
                1,
            )
        return {
            "metricas": {
                "finalizadas": len(finais),
                "ativas": len(ativas),
                "peso_processado_kg": peso_processado,
                "saldo": round(dados.buscar_saldo_empresa(usuario_id), 2),
                "co2_evitado_kg": round(peso_processado * 3.0, 1),
                "taxa_reciclagem_percentual": (
                    round(len(recicladas) / len(finais) * 100, 1) if finais else 0.0
                ),
            },
            "comparativo_mensal_percentual": comparativo,
            "meses": meses,
            "categorias": [
                {"nome": nome, "peso_kg": peso} for nome, peso in sorted(categorias.items())
            ],
            "total_em_processamento": len(em_processamento),
            "em_processamento": [
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
            s for s in solicitacoes if s.estado.obter_nome() not in estados_finais | {"Cancelado"}
        ]
        return {
            "metricas": {
                "peso_total_kg": round(metricas["peso_total"], 2),
                "solicitacoes": len(solicitacoes),
                "ativas": len(ativas),
                "finalizadas": metricas["total_processadas"],
                "impacto_evitado_kg": round(metricas["impacto_total"], 2),
                "receita": round(dados.buscar_receita_total_ecotech(), 2),
            },
            "solicitacoes_recentes": [
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
        return {
            "id": payload["sub"],
            "tipo": payload["tipo"],
            "nome": payload.get("nome", ""),
        }

    def _exigir_cidadao():
        if request.usuario_token["tipo"] != "cidadao":
            return jsonify({"erro": "Recurso exclusivo para cidadaos"}), 403
        return None

    def _exigir_empresa():
        if request.usuario_token["tipo"] != "empresa":
            return jsonify({"erro": "Recurso exclusivo para empresas"}), 403
        return None

    def _exigir_operador():
        if request.usuario_token["tipo"] not in ("empresa", "administrador"):
            return jsonify({"erro": "Recurso exclusivo para operadores"}), 403
        return None

    def _exigir_admin():
        if request.usuario_token["tipo"] != "administrador":
            return jsonify({"erro": "Recurso exclusivo para administradores"}), 403
        return None

    def _endereco_operacional(payload):
        campos = {
            chave: str(payload.get(chave, "") or "")
            for chave in (
                "cep",
                "logradouro",
                "numero",
                "complemento",
                "bairro",
                "cidade",
                "uf",
                "referencia",
            )
        }
        endereco, cep = _montar_endereco(campos)
        localizado = geolocalizador.consultar_cep(cep)
        return endereco, localizado["latitude"], localizado["longitude"]

    def _base_json(base):
        return {
            "id": base.id,
            "nome": base.nome,
            "endereco": base.endereco,
            "raio_atendimento_km": base.raio_atendimento_km,
            "capacidade_kg": base.capacidade_kg,
            "ocupacao_kg": base.ocupacao_atual_kg,
            "capacidade_disponivel_kg": base.capacidade_disponivel_kg,
            "realiza_coleta_domiciliar": base.realiza_coleta_domiciliar,
            "ativa": base.ativa,
            "ponto_coleta_id": base.ponto_coleta_id,
        }

    def _nome_empresa_solicitacao(solicitacao, raw=None):
        raw = raw or dados.buscar_solicitacao(solicitacao.id)
        empresa_id = raw["empresa_responsavel_id"] if raw else None
        if not empresa_id and solicitacao.ponto_coleta:
            ponto = dados.buscar_ponto_coleta(solicitacao.ponto_coleta.id)
            empresa_id = ponto["id_empresa"] if ponto else None
        empresa = dados.buscar_usuario(empresa_id) if empresa_id else None
        return empresa["nome"] if empresa else None

    def _resumo_operacao(solicitacao):
        raw = dados.buscar_solicitacao(solicitacao.id)
        confirmado = raw["peso_confirmado_kg"] if raw else None
        estimado = raw["peso_estimado_kg"] if raw else None
        return {
            **_resumo_solicitacao(solicitacao),
            "empresa": _nome_empresa_solicitacao(solicitacao, raw),
            "tipo_coleta": raw["tipo_coleta"] if raw else None,
            "peso_estimado_kg": estimado,
            "peso_confirmado_kg": confirmado,
            "peso_origem": "aferido" if confirmado is not None else "estimado",
            "quantidade_itens": sum(item.quantidade for item in solicitacao.itens),
        }

    def _detalhes_operacao(solicitacao):
        raw = dados.buscar_solicitacao(solicitacao.id)
        itens = [dict(item) for item in dados.buscar_itens_solicitacao(solicitacao.id)]
        dispositivos = {item.dispositivo.id: item.dispositivo for item in solicitacao.itens}
        for item in itens:
            preco = dados.buscar_preco_subcategoria(item.get("subcategoria") or "smartphone_medio")
            dispositivo = dispositivos.get(item["id_dispositivo"])
            valor_base = (
                float(preco["valor_base_funcionando"])
                if preco
                else dispositivo.calcular_valor_revenda()
                if dispositivo
                else 0.0
            )
            valor_sucata = float(preco["valor_minimo_sucata"]) if preco else 0.0
            item["precos"] = {
                "funcionando": round(valor_base, 2),
                "defeito_leve": round(valor_base * 0.4, 2),
                "defeito_grave": round(valor_base * 0.15, 2),
                "sucata": round(valor_sucata, 2),
            }
        fotos = [
            {
                **dict(foto),
                "url": f"/api/v1/solicitacoes/{solicitacao.id}/fotos/{foto['id']}",
            }
            for foto in dados.listar_fotos_solicitacao(solicitacao.id)
        ]
        historico = [dict(item) for item in dados.buscar_historico_solicitacao(solicitacao.id)]
        agendamento = dados.buscar_agendamento(solicitacao.id)
        avaliacao = dados.buscar_avaliacao_solicitacao(solicitacao.id)
        base = (
            dados.buscar_base_operacional(raw["base_operacional_id"])
            if raw and raw["base_operacional_id"]
            else None
        )
        responsavel_peso = (
            dados.buscar_usuario(raw["peso_confirmado_por"])
            if raw and raw["peso_confirmado_por"]
            else None
        )
        estimado = float(raw["peso_estimado_kg"] or 0)
        confirmado = raw["peso_confirmado_kg"]
        diferenca = None
        if confirmado is not None and estimado > 0:
            diferenca = round((float(confirmado) - estimado) / estimado * 100, 1)
        return {
            **_resumo_operacao(solicitacao),
            "endereco_coleta": raw["endereco_coleta"],
            "nome_contato": raw["nome_contato"],
            "data_agendamento": raw["data_agendamento"],
            "metodo_tratamento": raw["metodo_tratamento"],
            "peso_informado_cidadao": bool(raw["peso_informado_cidadao"]),
            "peso_confirmado_em": raw["peso_confirmado_em"],
            "peso_confirmado_por": (responsavel_peso["nome"] if responsavel_peso else None),
            "diferenca_peso_percentual": diferenca,
            "diferenca_peso_relevante": (diferenca is not None and abs(diferenca) >= 20),
            "base": _base_json(servico_base.buscar(raw["base_operacional_id"])) if base else None,
            "atribuida_em": raw["atribuida_em"],
            "itens": itens,
            "fotos": fotos,
            "historico": historico,
            "agendamento": dict(agendamento) if agendamento else None,
            "avaliacao": dict(avaliacao) if avaliacao else None,
            "acoes": {
                "pode_avancar": solicitacao.estado.pode_avancar(),
                "exige_peso": (
                    solicitacao.estado.obter_nome() == "Solicitado" and confirmado is None
                ),
                "exige_avaliacao": (solicitacao.estado.obter_nome() == "Em Processamento"),
                "agenda": True,
                "chat": True,
            },
        }

    def _buscar_operacao_autorizada(solicitacao_id):
        solicitacao = servico_descarte.obter_solicitacao(solicitacao_id)
        if solicitacao is None:
            return None, (jsonify({"erro": "Operacao nao encontrada"}), 404)
        usuario = _usuario_token_dict()
        if not usuario_pode_operar_solicitacao(usuario, solicitacao, dados):
            return None, (jsonify({"erro": "Acesso nao autorizado a operacao"}), 403)
        return solicitacao, None

    def _buscar_solicitacao_visivel(solicitacao_id):
        solicitacao = servico_descarte.obter_solicitacao(solicitacao_id)
        if solicitacao is None:
            return None, (jsonify({"erro": "Solicitacao nao encontrada"}), 404)
        if not usuario_pode_visualizar_solicitacao(_usuario_token_dict(), solicitacao, dados):
            return None, (jsonify({"erro": "Acesso nao autorizado"}), 403)
        return solicitacao, None

    def _agenda_json(solicitacao, agenda=None):
        agenda = agenda or dados.buscar_agendamento(solicitacao.id)
        historico = [dict(item) for item in dados.buscar_historico_agendamento(solicitacao.id)]
        usuario_id = request.usuario_token["sub"]
        usuario_tipo = request.usuario_token["tipo"]
        proposta_por = agenda["proposta_por"] if agenda else None
        autor = dados.buscar_usuario(proposta_por) if proposta_por else None
        return {
            "solicitacao": _resumo_operacao(solicitacao),
            "agenda": dict(agenda) if agenda else None,
            "proposta_autor": {
                "id": autor["id"],
                "nome": autor["nome"],
                "tipo": autor["tipo"],
            }
            if autor
            else None,
            "historico": historico,
            "acoes": {
                "pode_propor": bool(
                    agenda and agenda["status"] != "AGENDADO" and usuario_tipo != "administrador"
                ),
                "pode_aceitar": bool(
                    agenda
                    and agenda["status"] != "AGENDADO"
                    and (
                        (agenda["status"] == "PROPOSTA_PENDENTE" and proposta_por != usuario_id)
                        or (
                            agenda["status"] == "AGUARDANDO_AGENDAMENTO"
                            and usuario_tipo == "empresa"
                        )
                    )
                ),
                "pode_rejeitar": bool(
                    agenda
                    and agenda["status"] == "PROPOSTA_PENDENTE"
                    and proposta_por != usuario_id
                    and usuario_tipo != "administrador"
                ),
            },
        }

    def _evento_chat_texto(tipo, payload):
        textos = {
            "SISTEMA": "Atualizacao do sistema",
            "PROPOSTA_HORARIO": "Novo horario proposto para a coleta",
            "HORARIO_ACEITO": "Horario da coleta confirmado",
            "HORARIO_RECUSADO": "Proposta de horario recusada",
            "COLETA_CONFIRMADA": "Coleta confirmada",
        }
        texto = textos.get(tipo, "Atualizacao da coleta")
        inicio = payload.get("inicio") if isinstance(payload, dict) else None
        return f"{texto}: {inicio}" if inicio else texto

    def _mensagem_json(row, usuario_id):
        item = dict(row)
        try:
            payload = json.loads(item.get("payload") or "{}")
        except (TypeError, json.JSONDecodeError):
            payload = {}
        tipo = item.get("tipo") or "MENSAGEM"
        return {
            "id": item["id"],
            "tipo": tipo,
            "texto": item.get("texto") or _evento_chat_texto(tipo, payload),
            "payload": payload,
            "criado_em": item["criado_em"],
            "lida_em": item.get("lida_em"),
            "propria": item.get("remetente_id") == usuario_id,
            "remetente": {
                "id": item.get("remetente_id"),
                "nome": item.get("remetente_nome") or "EcoTech",
                "tipo": item.get("remetente_tipo") or "sistema",
            },
        }

    def _destino_notificacao(notificacao, tipo):
        chave = notificacao["chave_idempotencia"] or ""
        usuario_tipo = request.usuario_token["tipo"]
        if chave.startswith("oferta:"):
            return "/empresa/oportunidades"
        if chave.startswith("agenda:"):
            solicitacao_id = chave.split(":", 2)[1]
            return f"/solicitacoes/{solicitacao_id}/agenda"
        if chave.startswith("estado:") or chave.startswith("mtr:"):
            solicitacao_id = chave.split(":", 2)[1]
            prefixo = "/empresa/operacoes" if usuario_tipo == "empresa" else "/solicitacoes"
            return f"{prefixo}/{solicitacao_id}"
        if chave.startswith("override:"):
            solicitacao_id = chave.split(":", 2)[1]
            return f"/empresa/operacoes/{solicitacao_id}"
        if chave.startswith("chat:"):
            mensagem_id = chave.split(":", 1)[1]
            row = dados.buscar_solicitacao_mensagem(mensagem_id)
            if row:
                return f"/conversas/{row['solicitacao_id']}"
        destinos = {
            "mensagem": "/conversas",
            "oportunidade": "/empresa/oportunidades",
            "pagamento": "/carteira",
            "agenda": "/conversas",
            "mtr": "/empresa/operacoes",
        }
        return destinos.get(tipo, "/notificacoes")

    def _notificacao_json(row):
        item = dict(row)
        mensagem = item["mensagem"]
        normalizada = mensagem.lower()
        chave = item.get("chave_idempotencia") or ""
        if chave.startswith("oferta:") or "oportunidade" in normalizada:
            tipo = "oportunidade"
        elif chave.startswith("chat:") or "mensagem" in normalizada:
            tipo = "mensagem"
        elif chave.startswith("agenda:") or any(
            termo in normalizada for termo in ("horario", "horário", "proposta")
        ):
            tipo = "agenda"
        elif chave.startswith("mtr:") or "mtr" in normalizada:
            tipo = "mtr"
        elif chave.startswith("override:"):
            tipo = "estado"
        elif any(
            termo in normalizada for termo in ("credito", "crédito", "pagamento", "saque", "r$")
        ):
            tipo = "pagamento"
        elif any(termo in normalizada for termo in ("estado", "atualizada", "processamento")):
            tipo = "estado"
        else:
            tipo = "coleta"
        return {
            "id": item["id"],
            "titulo": mensagem[:70] + ("..." if len(mensagem) > 70 else ""),
            "mensagem": mensagem,
            "tipo": tipo,
            "criada_em": item["timestamp"],
            "lida": bool(item.get("lida_em")),
            "lida_em": item.get("lida_em"),
            "destino": _destino_notificacao(item, tipo),
        }

    def _carteira_json(usuario_id):
        cidadao = dados.buscar_cidadao(usuario_id)
        usuario = dados.buscar_usuario(usuario_id)
        pontos = int(cidadao["pontos"] or 0) if cidadao else 0
        saques = [dict(item) for item in servico_saque.listar_saques(usuario_id)]
        total_reservado = sum(
            float(item["valor"]) for item in saques if item.get("status") != "cancelado"
        )
        saldo = max(
            round(pontos * servico_saque.TAXA_REAIS_POR_PONTO - total_reservado, 2),
            0.0,
        )

        def data_hora_iso(item):
            try:
                return datetime.strptime(
                    f"{item['data']} {item['hora']}", "%d %b %Y %H:%M"
                ).isoformat()
            except (TypeError, ValueError):
                return f"{item['data']} {item['hora']}".strip()

        return {
            "saldo": saldo,
            "pontos": pontos,
            "conversao": {
                "pontos_por_real": int(round(1 / servico_saque.TAXA_REAIS_POR_PONTO)),
                "reais_por_ponto": servico_saque.TAXA_REAIS_POR_PONTO,
            },
            "metodos": [
                {"id": "Pix", "nome": "Pix"},
                {"id": "Transferencia", "nome": "Transferencia bancaria"},
            ],
            "titular": {
                "nome": usuario["nome"] if usuario else "",
                "cpf": cidadao["cpf"] if cidadao else "",
                "email": usuario["email"] if usuario else "",
            },
            "saques": [
                {
                    "id": item["id"],
                    "valor": float(item["valor"]),
                    "metodo": item["metodo"],
                    "data": item["data"],
                    "hora": item["hora"],
                    "data_hora": data_hora_iso(item),
                    "status": item["status"],
                }
                for item in saques
            ],
        }

    def _periodo_relatorio():
        inicio_texto = str(request.args.get("data_inicio", "")).strip()
        fim_texto = str(request.args.get("data_fim", "")).strip()
        try:
            inicio = datetime.strptime(inicio_texto, "%Y-%m-%d") if inicio_texto else None
            fim = (
                datetime.strptime(fim_texto, "%Y-%m-%d").replace(
                    hour=23, minute=59, second=59, microsecond=999999
                )
                if fim_texto
                else None
            )
        except ValueError as exc:
            raise ValueError("Use datas validas no formato AAAA-MM-DD") from exc
        if inicio and fim and inicio > fim:
            raise ValueError("A data inicial deve ser anterior a data final")
        return inicio_texto, fim_texto, inicio, fim

    def _dados_relatorio():
        usuario = _usuario_token_dict()
        if usuario["tipo"] not in ("empresa", "administrador"):
            raise PermissionError("Relatorios estao disponiveis para empresas e administradores")
        inicio_texto, fim_texto, inicio, fim = _periodo_relatorio()
        solicitacoes = _solicitacoes_do_usuario(usuario["id"], usuario["tipo"])
        titulo = (
            "Relatorio Geral do Sistema"
            if usuario["tipo"] == "administrador"
            else f"Relatorio de {usuario['nome']}"
        )
        relatorio = servico_relatorio.gerar_relatorio_periodo(
            titulo, solicitacoes, data_inicio=inicio, data_fim=fim
        )
        metricas = relatorio.gerar_relatorio()
        filtradas = [
            item
            for item in solicitacoes
            if (inicio is None or item.data_criacao >= inicio)
            and (fim is None or item.data_criacao <= fim)
        ]
        finalizadas = [item for item in filtradas if item.estado.obter_nome() in estados_finais]
        plano = dados.buscar_plano_empresa(usuario["id"]) if usuario["tipo"] == "empresa" else None
        pode_exportar = usuario["tipo"] == "administrador" or plano in (
            "professional",
            "enterprise",
        )
        return {
            "usuario": usuario,
            "periodo": {
                "data_inicio": inicio_texto or None,
                "data_fim": fim_texto or None,
            },
            "metricas": metricas,
            "finalizadas": finalizadas,
            "plano": plano,
            "pode_exportar": pode_exportar,
        }

    def _mascarar_email(email):
        usuario, separador, dominio = str(email or "").partition("@")
        if not separador:
            return "-"
        visivel = usuario[:2] if len(usuario) > 1 else usuario[:1]
        return f"{visivel}***@{dominio}"

    def _mascarar_documento(documento, tipo):
        digitos = "".join(c for c in str(documento or "") if c.isdigit())
        if tipo == "cidadao" and len(digitos) == 11:
            return f"***.***.***-{digitos[-2:]}"
        if tipo == "empresa" and len(digitos) == 14:
            return f"**.***.***/****-{digitos[-2:]}"
        return "-"

    def _usuario_admin_json(item, tipo):
        documento = item.get("cpf") if tipo == "cidadao" else item.get("cnpj")
        return {
            "id": item["id"],
            "nome": item["nome"],
            "email": _mascarar_email(item.get("email")),
            "documento": _mascarar_documento(documento, tipo),
            "tipo": tipo,
            "ativo": bool(item.get("ativo")),
            "data_cadastro": item.get("data_cadastro"),
            "pontos": int(item.get("pontos") or 0) if tipo == "cidadao" else None,
            "descartado_mes_kg": (
                float(item.get("descartado_mes") or 0) if tipo == "empresa" else None
            ),
            "plano": item.get("plano") if tipo == "empresa" else None,
        }

    def _empresa_id_solicitacao(solicitacao_id):
        raw = dados.buscar_solicitacao(solicitacao_id)
        if not raw:
            return None
        empresa_id = raw["empresa_responsavel_id"]
        if not empresa_id and raw["id_ponto_coleta"]:
            ponto = dados.buscar_ponto_coleta(raw["id_ponto_coleta"])
            empresa_id = ponto["id_empresa"] if ponto else None
        return empresa_id

    def _valores_override(solicitacao_id, estado_produto=None):
        avaliacao = dados.buscar_avaliacao_solicitacao(solicitacao_id)
        if not avaliacao:
            raise LookupError("Avaliacao nao encontrada")
        estado = estado_produto or avaliacao["estado_produto"] or "funcionando"
        valor_base = 0.0
        valor_minimo = 0.0
        valor_recalculado = 0.0
        for item in dados.buscar_itens_solicitacao(solicitacao_id):
            preco = dados.buscar_preco_subcategoria(item["subcategoria"] or "smartphone_medio")
            if not preco:
                continue
            quantidade = int(item["quantidade"] or 1)
            base = float(preco["valor_base_funcionando"])
            minimo = float(preco["valor_minimo_sucata"])
            valor_base += base * quantidade
            valor_minimo += minimo * quantidade
            valor_recalculado += (
                ServicoDescarte.calcular_valor_avaliado(estado, base, minimo) * quantidade
            )
        return {
            "valor_base": round(valor_base, 2),
            "valor_minimo": round(valor_minimo, 2),
            "limite_override": round(valor_base * 1.5, 2),
            "valor_recalculado": round(valor_recalculado, 2),
        }

    def _registrar_avaliacao(solicitacao, payload):
        metodo_chave = str(payload.get("metodo", "")).strip().lower()
        metodos = {
            "reciclagem": MetodoTratamentoFactory.criar_reciclagem,
            "reuso": MetodoTratamentoFactory.criar_reuso,
            "descarte": MetodoTratamentoFactory.criar_descarte_controlado,
            "descarte_controlado": MetodoTratamentoFactory.criar_descarte_controlado,
        }
        if metodo_chave not in metodos:
            raise ValueError("Informe um metodo de tratamento valido")
        estado_chave = str(payload.get("estado_produto", "")).strip().lower()
        try:
            estado_produto = EstadoProduto(estado_chave)
        except ValueError as exc:
            raise ValueError("Informe o estado de conservacao do produto") from exc

        valor_informado = payload.get("valor_proposto")
        valor_proposto = None
        if valor_informado not in (None, ""):
            valor_proposto = float(str(valor_informado).replace(",", "."))
            if valor_proposto < 0:
                raise ValueError("O valor proposto nao pode ser negativo")
        justificativa = str(payload.get("justificativa", "")).strip()

        valor_total = 0.0
        status_override = "nenhum"
        prioridade_status = {
            "nenhum": 0,
            "aprovado": 1,
            "pendente_doc": 2,
            "invalido": 3,
        }
        for item in solicitacao.itens:
            preco = dados.buscar_preco_subcategoria(
                item.dispositivo.subcategoria or "smartphone_medio"
            )
            if preco:
                valor_base = float(preco["valor_base_funcionando"])
                valor_sucata = float(preco["valor_minimo_sucata"])
            else:
                valor_base = item.dispositivo.calcular_valor_revenda()
                valor_sucata = 0.0
            if valor_proposto is None:
                valor_item = item.dispositivo.calcular_valor_avaliado(
                    estado_produto, valor_base, valor_sucata
                )
                status_item = "nenhum"
            else:
                resultado = ServicoDescarte.validar_override(
                    valor_proposto, valor_base, valor_sucata
                )
                valor_item = resultado["valor_aplicado"]
                status_item = resultado["status"]
            valor_total += valor_item * item.quantidade
            if prioridade_status[status_item] > prioridade_status[status_override]:
                status_override = status_item

        if status_override in ("pendente_doc", "invalido") and not justificativa:
            raise ValueError("Informe a justificativa para o valor proposto")
        servico_descarte.definir_metodo_tratamento(solicitacao, metodos[metodo_chave]())
        dados.atualizar_avaliacao_solicitacao(
            solicitacao.id,
            estado_chave,
            round(valor_total, 2),
            justificativa,
            status_override,
        )

    def _creditar_finalizacao(solicitacao, operador):
        if "cidad" not in solicitacao.usuario.obter_tipo().lower():
            return
        avaliacao = dados.buscar_avaliacao_solicitacao(solicitacao.id)
        valor_total = (
            float(avaliacao["valor_proposto"])
            if avaliacao and avaliacao["valor_proposto"] is not None
            else sum(
                item.dispositivo.calcular_valor_revenda() * item.quantidade
                for item in solicitacao.itens
            )
        )
        credito = round(valor_total * 0.1, 2)
        nome_empresa = operador["nome"] if operador["tipo"] == "empresa" else "EcoTech"
        dados.salvar_entrega_para_solicitacao(
            solicitacao.id, solicitacao.usuario.id, credito, nome_empresa
        )
        pontos = int(credito / servico_saque.TAXA_REAIS_POR_PONTO)
        dados.atualizar_pontos_cidadao(solicitacao.usuario.id, pontos)
        solicitacao.usuario.adicionar_pontos(pontos)
        plano = (
            dados.buscar_plano_empresa(operador["id"]) if operador["tipo"] == "empresa" else "free"
        )
        taxa = ServicoDescarte.TAXAS_ECOTECH.get(plano, 0.08)
        if operador["tipo"] == "empresa":
            dados.atualizar_saldo_empresa(operador["id"], round(valor_total * (1 - 0.10 - taxa), 2))
            if plano == "enterprise":
                bonus = int(solicitacao.calcular_peso_total() * 10 * 0.5)
                if bonus:
                    dados.atualizar_pontos_cidadao(solicitacao.usuario.id, bonus)
        dados.registrar_receita_ecotech(solicitacao.id, round(valor_total * taxa, 2))

    def _validar_fotos(arquivos):
        fotos = []
        if len([a for a in arquivos if a and a.filename]) > 5:
            raise ValueError("Envie no maximo 5 fotos por solicitacao")
        for arquivo in arquivos:
            if not arquivo or not arquivo.filename:
                continue
            conteudo = arquivo.read()
            if conteudo.startswith(b"\xff\xd8\xff"):
                mime_type = "image/jpeg"
            elif conteudo.startswith(b"\x89PNG\r\n\x1a\n"):
                mime_type = "image/png"
            elif len(conteudo) > 12 and conteudo[:4] == b"RIFF" and conteudo[8:12] == b"WEBP":
                mime_type = "image/webp"
            else:
                raise ValueError("Envie somente fotos JPG, PNG ou WebP")
            if len(conteudo) > 5 * 1024 * 1024:
                raise ValueError("Cada foto pode ter no maximo 5 MB")
            fotos.append((arquivo.filename[:180], mime_type, conteudo))
        return fotos

    def _montar_endereco(formulario):
        obrigatorios = ("cep", "logradouro", "numero", "bairro", "cidade", "uf")
        ausentes = [campo for campo in obrigatorios if not formulario.get(campo, "").strip()]
        if ausentes:
            raise ValueError("Preencha todos os campos obrigatorios do endereco")
        cep = "".join(c for c in formulario["cep"] if c.isdigit())
        if len(cep) != 8:
            raise ValueError("Informe um CEP valido com 8 digitos")
        endereco = f"{formulario['logradouro'].strip()}, {formulario['numero'].strip()}"
        complemento = formulario.get("complemento", "").strip()
        if complemento:
            endereco += f", {complemento}"
        endereco += (
            f" - {formulario['bairro'].strip()}, {formulario['cidade'].strip()}"
            f" - {formulario['uf'].strip().upper()}, CEP {cep[:5]}-{cep[5:]}"
        )
        referencia = formulario.get("referencia", "").strip()
        if referencia:
            endereco += f". Referencia: {referencia}"
        return endereco, cep

    def _resposta_autenticada(usuario):
        dados_sessao = servico_autenticacao.criar_dados_sessao(usuario)
        token = gerar_token(
            dados_sessao["user_id"],
            dados_sessao["user_nome"],
            dados_sessao["user_tipo"],
        )
        return jsonify(
            {
                "access_token": token,
                "token_type": "Bearer",
                "expires_in": _expiracao_token_horas() * 3600,
                "usuario": {
                    "id": dados_sessao["user_id"],
                    "nome": dados_sessao["user_nome"],
                    "tipo": dados_sessao["user_tipo"],
                },
            }
        )

    @bp.route("/auth/login", methods=["POST"])
    def login_api():
        corpo = request.get_json(silent=True) or {}
        tipo = (corpo.get("tipo") or "").strip()
        credencial = (corpo.get("credencial") or "").strip()
        senha = corpo.get("senha") or ""

        if tipo in ("cidadao", "empresa"):
            credencial = (
                credencial.replace(".", "").replace("-", "").replace("/", "").replace(" ", "")
            )

        usuario = servico_autenticacao.autenticar(tipo, credencial, senha)
        if usuario is None:
            return jsonify({"erro": "Credencial ou senha invalidos"}), 401

        return _resposta_autenticada(usuario)

    @bp.route("/auth/registrar", methods=["POST"])
    def registrar_api():
        corpo = request.get_json(silent=True) or {}
        tipo = (corpo.get("tipo") or "cidadao").strip()
        nome = (corpo.get("nome") or "").strip()
        email = (corpo.get("email") or "").strip()
        senha = corpo.get("senha") or ""
        senha_confirmacao = corpo.get("senha_confirmacao") or ""

        if not nome or not email or not senha:
            return jsonify({"erro": "Preencha todos os campos obrigatorios"}), 400
        if senha != senha_confirmacao:
            return jsonify({"erro": "As senhas nao coincidem"}), 400
        if len(senha) < 6:
            return jsonify({"erro": "A senha deve ter pelo menos 6 caracteres"}), 400

        dados_novo = {"nome": nome, "email": email}
        if tipo == "cidadao":
            dados_novo["cpf"] = (corpo.get("cpf") or "").strip()
        elif tipo == "empresa":
            dados_novo["cnpj"] = (corpo.get("cnpj") or "").strip()
            dados_novo["razao_social"] = (corpo.get("razao_social") or "").strip()

        try:
            usuario = servico_usuario.criar_usuario(tipo, dados_novo, senha)
        except (ValueError, Exception) as exc:
            return jsonify({"erro": str(exc)}), 400

        return _resposta_autenticada(usuario)

    @bp.route("/auth/me", methods=["GET"])
    @requer_autenticacao_api
    def perfil_api():
        payload = request.usuario_token
        usuario = servico_usuario.buscar_usuario(payload["sub"])
        if usuario is None:
            return jsonify({"erro": "Usuario nao encontrado"}), 404

        return jsonify(
            {
                "id": usuario.id,
                "nome": usuario.nome,
                "email": usuario.email,
                "tipo": payload["tipo"],
            }
        )

    @bp.route("/dashboard", methods=["GET"])
    @requer_autenticacao_api
    def dashboard_api():
        payload = request.usuario_token
        usuario_id, tipo = payload["sub"], payload["tipo"]
        perfil = _perfil_completo(usuario_id, tipo)
        if perfil is None:
            return jsonify({"erro": "Usuario nao encontrado"}), 404

        solicitacoes = _solicitacoes_do_usuario(usuario_id, tipo)
        if tipo == "cidadao":
            dashboard = _dashboard_cidadao(usuario_id, solicitacoes)
        elif tipo == "empresa":
            dashboard = _dashboard_empresa(usuario_id, solicitacoes)
        elif tipo == "administrador":
            dashboard = _dashboard_admin(solicitacoes)
        else:
            return jsonify({"erro": "Tipo de usuario invalido"}), 403
        return jsonify({"tipo": tipo, "usuario": perfil, **dashboard})

    @bp.route("/perfil", methods=["GET", "PATCH"])
    @requer_autenticacao_api
    def perfil_detalhado_api():
        payload = request.usuario_token
        usuario_id, tipo = payload["sub"], payload["tipo"]
        perfil = _perfil_completo(usuario_id, tipo)
        if perfil is None:
            return jsonify({"erro": "Usuario nao encontrado"}), 404

        if request.method == "PATCH":
            corpo = request.get_json(silent=True) or {}
            nome = (corpo.get("nome") or perfil["nome"]).strip()
            email = (corpo.get("email") or perfil["email"]).strip().lower()
            senha_atual = corpo.get("senha_atual") or ""
            nova_senha = corpo.get("nova_senha") or ""
            confirma_senha = corpo.get("confirma_senha") or ""

            if len(nome) < 3 or not email:
                return jsonify({"erro": "Nome e e-mail sao obrigatorios"}), 400
            usuario_email = dados.buscar_usuario_por_email(email)
            if usuario_email and usuario_email["id"] != usuario_id:
                return jsonify({"erro": "Este e-mail ja esta em uso"}), 400

            password_hash = None
            if nova_senha:
                row = dados.buscar_usuario(usuario_id)
                if not check_password_hash(row["password_hash"] or "", senha_atual):
                    return jsonify({"erro": "Senha atual incorreta"}), 400
                if nova_senha != confirma_senha:
                    return jsonify({"erro": "As novas senhas nao coincidem"}), 400
                if len(nova_senha) < 6:
                    return jsonify({"erro": "A nova senha deve ter pelo menos 6 caracteres"}), 400
                password_hash = generate_password_hash(nova_senha)

            dados.atualizar_usuario(usuario_id, nome, email, password_hash)
            perfil = _perfil_completo(usuario_id, tipo)

        solicitacoes = _solicitacoes_do_usuario(usuario_id, tipo)
        metricas = servico_descarte.calcular_metricas(solicitacoes)
        resumo = {
            "total_solicitacoes": len(solicitacoes),
            "peso_total_kg": round(metricas["peso_total"], 2),
            "finalizadas": metricas["total_processadas"],
        }
        if tipo == "cidadao":
            cidadao = dados.buscar_cidadao(usuario_id)
            pontos = int(cidadao["pontos"] or 0) if cidadao else 0
            tier = servico_descarte.calcular_info_tier(pontos)
            rank = 1
            for outro in servico_usuario.listar_usuarios():
                if outro.id == usuario_id:
                    continue
                row = dados.buscar_cidadao(outro.id)
                if row and int(row["pontos"] or 0) > pontos:
                    rank += 1
            resumo.update(
                {
                    "pontos": pontos,
                    "rank": rank,
                    "tier": tier,
                    "conquistas": [
                        {
                            "meta": meta,
                            "titulo": titulo,
                            "conquistada": len(solicitacoes) >= meta,
                        }
                        for meta, titulo in (
                            (1, "Primeiro descarte"),
                            (5, "5 descartes"),
                            (10, "10 descartes"),
                            (20, "20 descartes"),
                        )
                    ],
                }
            )
        return jsonify({"usuario": perfil, "resumo": resumo})

    @bp.route("/pontos-coleta", methods=["GET"])
    @requer_autenticacao_api
    def pontos_coleta_api():
        pontos = []
        for ponto in servico_ponto.listar_pontos():
            if not ponto.ativo:
                continue
            raw = dados.buscar_ponto_coleta(ponto.id)
            empresa = dados.buscar_usuario(raw["id_empresa"]) if raw and raw["id_empresa"] else None
            pontos.append(
                {
                    "id": ponto.id,
                    "nome": ponto.nome,
                    "empresa": empresa["nome"] if empresa else "",
                    "endereco": ponto.endereco,
                    "capacidade_kg": ponto.capacidade_kg,
                    "ocupacao_kg": ponto.ocupacao_atual_kg,
                    "disponibilidade_percentual": ponto.calcular_disponibilidade_percentual(),
                }
            )
        return jsonify({"pontos": pontos})

    @bp.route("/cep/<cep>", methods=["GET"])
    @requer_autenticacao_api
    def consultar_cep_api(cep):
        try:
            resultado = geolocalizador.consultar_cep(cep)
        except ValueError as exc:
            return jsonify({"erro": str(exc)}), 400
        return jsonify(
            {
                "cep": "".join(c for c in cep if c.isdigit()),
                "logradouro": resultado.get("street", ""),
                "bairro": resultado.get("neighborhood", ""),
                "cidade": resultado.get("city", ""),
                "uf": resultado.get("state", ""),
            }
        )

    @bp.route("/solicitacoes", methods=["GET", "POST"])
    @requer_autenticacao_api
    def solicitacoes_api():
        payload = request.usuario_token
        if request.method == "GET":
            solicitacoes = _solicitacoes_do_usuario(payload["sub"], payload["tipo"])
            estatisticas = servico_descarte.calcular_stats_estados(solicitacoes)
            estado = request.args.get("estado", "").strip().lower()
            if estado:
                solicitacoes = [s for s in solicitacoes if estado in s.estado.obter_nome().lower()]
            solicitacoes.sort(key=lambda s: s.data_criacao, reverse=True)
            pagina = max(request.args.get("pagina", 1, type=int), 1)
            limite = min(max(request.args.get("limite", 20, type=int), 1), 100)
            inicio = (pagina - 1) * limite
            return jsonify(
                {
                    "itens": [_resumo_operacao(s) for s in solicitacoes[inicio : inicio + limite]],
                    "pagina": pagina,
                    "limite": limite,
                    "total": len(solicitacoes),
                    "total_paginas": max((len(solicitacoes) + limite - 1) // limite, 1),
                    "estatisticas": estatisticas,
                }
            )

        bloqueio = _exigir_cidadao()
        if bloqueio:
            return bloqueio
        try:
            form = request.form
            fotos = _validar_fotos(request.files.getlist("fotos"))
            tipo = form.get("tipo_dispositivo", "").strip().lower()
            if tipo not in {"celular", "computador", "eletrodomestico"}:
                raise ValueError("Selecione um tipo de dispositivo valido")
            nome = form.get("nome", "").strip()
            subcategoria = form.get("subcategoria", "").strip()
            if not nome or not subcategoria:
                raise ValueError("Informe a categoria e o modelo do produto")
            quantidade = int(form.get("quantidade", "1"))
            if quantidade < 1 or quantidade > 100:
                raise ValueError("A quantidade deve estar entre 1 e 100")
            ano = int(
                form.get("ano_fabricacao", str(datetime.now(timezone(timedelta(hours=-3))).year))
            )
            if ano < 1950 or ano > datetime.now(timezone(timedelta(hours=-3))).year:
                raise ValueError("Informe um ano de fabricacao valido")

            peso_texto = form.get("peso_kg", "").strip().replace(",", ".")
            peso_informado = bool(peso_texto)
            pesos_estimados = {
                "celular": 0.2,
                "computador": 5.0,
                "eletrodomestico": 15.0,
            }
            peso_unitario = float(peso_texto) if peso_informado else pesos_estimados[tipo]
            if peso_unitario <= 0:
                raise ValueError("O peso deve ser maior que zero")

            tipo_coleta = form.get("tipo_coleta", "domiciliar").strip()
            if tipo_coleta not in {"domiciliar", "entrega_ponto"}:
                raise ValueError("Selecione uma forma de entrega valida")
            ponto = None
            endereco = ""
            coordenadas = None
            if tipo_coleta == "entrega_ponto":
                ponto_id = form.get("ponto_id", "").strip()
                ponto = servico_ponto.buscar_ponto(ponto_id)
                if ponto is None:
                    raise ValueError("Selecione um ponto de coleta valido")
                if not ponto.pode_receber(peso_unitario * quantidade):
                    raise ValueError("O ponto selecionado nao possui capacidade disponivel")
            else:
                endereco, cep = _montar_endereco(form)
                dados_cep = geolocalizador.consultar_cep(cep)
                coordenadas = Coordenadas(dados_cep["latitude"], dados_cep["longitude"])

            data_coleta = form.get("data_coleta", "").strip()
            hora_inicio = form.get("horario_inicio", "").strip()
            hora_fim = form.get("horario_fim", "").strip()
            if not data_coleta or not hora_inicio or not hora_fim:
                raise ValueError("Informe a data e a janela de atendimento")
            inicio = datetime.strptime(f"{data_coleta} {hora_inicio}", "%Y-%m-%d %H:%M")
            fim = datetime.strptime(f"{data_coleta} {hora_fim}", "%Y-%m-%d %H:%M")
            servico_agendamento.validar(inicio, fim)

            usuario = servico_usuario.buscar_usuario(payload["sub"])
            if usuario is None:
                return jsonify({"erro": "Usuario nao encontrado"}), 404
            solicitacao = servico_descarte.criar_solicitacao(usuario, ponto)
            dispositivo = DispositivoFactory.criar_dispositivo(
                tipo,
                {
                    "id": str(uuid.uuid4()),
                    "nome": nome,
                    "peso_kg": peso_unitario,
                    "subcategoria": subcategoria,
                },
            )
            dispositivo._modelo = nome
            dispositivo.ano_fabricacao = ano
            servico_descarte.adicionar_item_solicitacao(
                solicitacao,
                dispositivo,
                quantidade,
                form.get("observacoes", "").strip(),
            )
            dados.atualizar_detalhes_coleta(
                solicitacao.id,
                tipo_coleta,
                endereco,
                form.get("nome_contato", "").strip() or usuario.nome,
                inicio.strftime("%Y-%m-%d %H:%M"),
            )
            dados.registrar_peso_estimado(
                solicitacao.id, peso_unitario * quantidade, peso_informado
            )
            dados.salvar_historico_rastreamento(solicitacao.id, "Solicitacao criada pelo cidadao")
            for nome_arquivo, mime_type, conteudo in fotos:
                dados.salvar_foto_solicitacao(
                    str(uuid.uuid4()),
                    solicitacao.id,
                    nome_arquivo,
                    mime_type,
                    conteudo,
                    datetime.now(timezone(timedelta(hours=-3))).isoformat(),
                )

            servico_agendamento.solicitar(solicitacao.id, payload["sub"], inicio, fim)

            if tipo_coleta == "domiciliar":
                dados.atualizar_localizacao_coleta(
                    solicitacao.id,
                    coordenadas.latitude,
                    coordenadas.longitude,
                    "cep",
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
                dados.atualizar_solicitacao(solicitacao.id, "BUSCANDO_EMPRESA")
            else:
                ponto_raw = dados.buscar_ponto_coleta(ponto.id)
                if ponto_raw and ponto_raw["id_empresa"]:
                    dados.salvar_notificacao(
                        ponto_raw["id_empresa"],
                        f"Nova entrega de {usuario.nome}: {nome}.",
                    )
            dados.salvar_notificacao(
                payload["sub"],
                f"Sua solicitacao de descarte do {nome} foi recebida.",
            )
            return jsonify(_detalhes_operacao(solicitacao)), 201
        except (ValueError, TypeError) as exc:
            return jsonify({"erro": str(exc)}), 400

    @bp.route("/solicitacoes/<solicitacao_id>", methods=["GET"])
    @requer_autenticacao_api
    def detalhes_solicitacao_api(solicitacao_id):
        solicitacao = servico_descarte.obter_solicitacao(solicitacao_id)
        if solicitacao is None:
            return jsonify({"erro": "Solicitacao nao encontrada"}), 404
        if not usuario_pode_visualizar_solicitacao(_usuario_token_dict(), solicitacao, dados):
            return jsonify({"erro": "Acesso nao autorizado"}), 403
        return jsonify(_detalhes_operacao(solicitacao))

    @bp.route("/solicitacoes/<solicitacao_id>/fotos/<foto_id>", methods=["GET"])
    @requer_autenticacao_api
    def foto_solicitacao_api(solicitacao_id, foto_id):
        solicitacao = servico_descarte.obter_solicitacao(solicitacao_id)
        foto = dados.buscar_foto_solicitacao(foto_id)
        if solicitacao is None or foto is None or foto["solicitacao_id"] != solicitacao_id:
            return jsonify({"erro": "Foto nao encontrada"}), 404
        if not usuario_pode_visualizar_solicitacao(_usuario_token_dict(), solicitacao, dados):
            return jsonify({"erro": "Acesso nao autorizado"}), 403
        return Response(
            foto["conteudo"],
            mimetype=foto["mime_type"],
            headers={"Content-Disposition": f'inline; filename="{foto["nome_arquivo"]}"'},
        )

    @bp.route("/entregas", methods=["GET"])
    @requer_autenticacao_api
    def entregas_api():
        bloqueio = _exigir_cidadao()
        if bloqueio:
            return bloqueio
        entregas = [
            dict(entrega) for entrega in dados.buscar_entregas_usuario(request.usuario_token["sub"])
        ]
        entregas.reverse()
        return jsonify({"entregas": entregas})

    def _ponto_empresa_json(row):
        solicitacoes = []
        for registro in dados.buscar_solicitacoes_ponto(row["id"]):
            solicitacao = servico_descarte.obter_solicitacao(registro["id"])
            if solicitacao is None:
                continue
            confirmacoes = dados.buscar_confirmacoes_solicitacao(registro["id"])
            peso = (
                registro["peso_confirmado_kg"]
                if registro["peso_confirmado_kg"] is not None
                else registro["peso_estimado_kg"]
            )
            if peso is None:
                peso = solicitacao.calcular_peso_total()
            solicitacoes.append(
                {
                    "id": registro["id"],
                    "cidadao": registro["nome_usuario"],
                    "estado": solicitacao.estado.obter_nome(),
                    "data_agendamento": registro["data_agendamento"],
                    "peso_kg": round(float(peso), 3),
                    "peso_informado_cidadao": bool(registro["peso_informado_cidadao"]),
                    "peso_confirmado_kg": registro["peso_confirmado_kg"],
                    "confirmado_empresa": bool(confirmacoes["confirmado_empresa"]),
                    "pode_confirmar": (
                        registro["estado"] == "SOLICITADO"
                        and not confirmacoes["confirmado_empresa"]
                    ),
                }
            )
        return {
            "id": row["id"],
            "nome": row["nome"],
            "endereco": row["endereco"],
            "capacidade_kg": row["capacidade_kg"],
            "ocupacao_kg": row["ocupacao_atual_kg"],
            "ativa": bool(row["ativo"]),
            "solicitacoes": solicitacoes,
        }

    @bp.route("/empresa/pontos", methods=["GET", "POST"])
    @requer_autenticacao_api
    def pontos_empresa_api():
        bloqueio = _exigir_empresa()
        if bloqueio:
            return bloqueio
        empresa_id = request.usuario_token["sub"]
        if request.method == "GET":
            return jsonify(
                {
                    "pontos": [
                        _ponto_empresa_json(row)
                        for row in dados.buscar_todos_pontos_empresa(empresa_id)
                    ]
                }
            )
        try:
            payload = request.get_json(silent=True) or {}
            endereco, latitude, longitude = _endereco_operacional(payload)
            ponto = servico_ponto.criar_para_empresa(
                empresa_id,
                str(payload.get("nome", "")),
                endereco,
                latitude,
                longitude,
                float(payload.get("capacidade_kg", 0)),
            )
            return jsonify(_ponto_empresa_json(dados.buscar_ponto_coleta(ponto.id))), 201
        except (ValueError, TypeError) as exc:
            return jsonify({"erro": str(exc)}), 400

    @bp.route("/empresa/pontos/<id_ponto>", methods=["PATCH", "DELETE"])
    @requer_autenticacao_api
    def ponto_empresa_api(id_ponto):
        bloqueio = _exigir_empresa()
        if bloqueio:
            return bloqueio
        empresa_id = request.usuario_token["sub"]
        try:
            if request.method == "DELETE":
                servico_ponto.definir_atividade_da_empresa(empresa_id, id_ponto, False)
            else:
                payload = request.get_json(silent=True) or {}
                if set(payload) == {"ativo"}:
                    servico_ponto.definir_atividade_da_empresa(
                        empresa_id, id_ponto, bool(payload["ativo"])
                    )
                else:
                    atual = dados.buscar_ponto_coleta(id_ponto)
                    if atual is None or atual["id_empresa"] != empresa_id:
                        raise PermissionError("ponto de coleta nao pertence a empresa")
                    if str(payload.get("cep", "")).strip():
                        endereco, latitude, longitude = _endereco_operacional(payload)
                    else:
                        endereco = atual["endereco"]
                        latitude = atual["latitude"]
                        longitude = atual["longitude"]
                    servico_ponto.atualizar_da_empresa(
                        empresa_id,
                        id_ponto,
                        str(payload.get("nome", "")),
                        endereco,
                        latitude,
                        longitude,
                        float(payload.get("capacidade_kg", 0)),
                    )
            return jsonify(_ponto_empresa_json(dados.buscar_ponto_coleta(id_ponto)))
        except PermissionError as exc:
            return jsonify({"erro": str(exc)}), 403
        except (ValueError, TypeError) as exc:
            return jsonify({"erro": str(exc)}), 400

    @bp.route(
        "/empresa/pontos/<id_ponto>/solicitacoes/<solicitacao_id>/confirmar",
        methods=["POST"],
    )
    @requer_autenticacao_api
    def confirmar_entrega_ponto_api(id_ponto, solicitacao_id):
        bloqueio = _exigir_empresa()
        if bloqueio:
            return bloqueio
        empresa_id = request.usuario_token["sub"]
        ponto_row = dados.buscar_ponto_coleta(id_ponto)
        solicitacao = servico_descarte.obter_solicitacao(solicitacao_id)
        if ponto_row is None or solicitacao is None:
            return jsonify({"erro": "Entrega nao encontrada"}), 404
        if ponto_row["id_empresa"] != empresa_id:
            return jsonify({"erro": "Ponto nao pertence a empresa"}), 403
        raw = dados.buscar_solicitacao(solicitacao_id)
        if raw["id_ponto_coleta"] != id_ponto or not usuario_pode_operar_solicitacao(
            _usuario_token_dict(), solicitacao, dados
        ):
            return jsonify({"erro": "Acesso nao autorizado a entrega"}), 403
        if solicitacao.estado.obter_nome() != "Solicitado":
            return jsonify({"erro": "Entrega nao aguarda recebimento"}), 409
        try:
            payload = request.get_json(silent=True) or {}
            peso = float(str(payload.get("peso_kg", "")).replace(",", "."))
            if peso <= 0:
                raise ValueError("Informe o peso aferido no recebimento")
            ponto = servico_ponto.buscar_ponto(id_ponto)
            if ponto is None or not ponto.pode_receber(peso):
                raise ValueError("O ponto nao possui capacidade para este peso")
            agora = datetime.now(timezone(timedelta(hours=-3))).isoformat(timespec="seconds")
            dados.confirmar_peso_solicitacao(solicitacao_id, peso, empresa_id, agora)
            solicitacao.confirmar_peso(peso)
            dados.confirmar_solicitacao(solicitacao_id, "empresa")
            servico_descarte.avancar_estado_solicitacao(solicitacao)
            ponto.adicionar_ocupacao(peso)
            dados.atualizar_ocupacao_ponto(id_ponto, ponto.ocupacao_atual_kg)
            dados.salvar_historico_rastreamento(
                solicitacao_id, "Recebimento e peso confirmados pela empresa"
            )
            dados.salvar_notificacao(
                solicitacao.usuario.id,
                f"O ponto de coleta confirmou o recebimento de {peso:g} kg.",
            )
            return jsonify(
                {
                    "ok": True,
                    "novo_estado": solicitacao.estado.obter_nome(),
                    "peso_confirmado_kg": peso,
                }
            )
        except (ValueError, TypeError) as exc:
            return jsonify({"erro": str(exc)}), 400

    @bp.route("/empresa/bases", methods=["GET", "POST"])
    @requer_autenticacao_api
    def bases_empresa_api():
        bloqueio = _exigir_empresa()
        if bloqueio:
            return bloqueio
        empresa_id = request.usuario_token["sub"]
        if request.method == "GET":
            return jsonify(
                {"bases": [_base_json(base) for base in servico_base.listar_empresa(empresa_id)]}
            )
        try:
            payload = request.get_json(silent=True) or {}
            endereco, latitude, longitude = _endereco_operacional(payload)
            base = servico_base.criar(
                empresa_id,
                {
                    "nome": str(payload.get("nome", "")),
                    "endereco": endereco,
                    "latitude": latitude,
                    "longitude": longitude,
                    "raio_atendimento_km": payload.get("raio_atendimento_km", 0),
                    "capacidade_kg": payload.get("capacidade_kg", 0),
                    "realiza_coleta_domiciliar": bool(
                        payload.get("realiza_coleta_domiciliar", True)
                    ),
                },
            )
            return jsonify(_base_json(base)), 201
        except (ValueError, TypeError) as exc:
            return jsonify({"erro": str(exc)}), 400

    @bp.route("/empresa/bases/<id_base>", methods=["PATCH", "DELETE"])
    @requer_autenticacao_api
    def base_empresa_api(id_base):
        bloqueio = _exigir_empresa()
        if bloqueio:
            return bloqueio
        empresa_id = request.usuario_token["sub"]
        try:
            if request.method == "DELETE":
                servico_base.definir_atividade(empresa_id, id_base, False)
                base = servico_base.buscar(id_base)
            else:
                payload = request.get_json(silent=True) or {}
                atual = servico_base.buscar(id_base)
                if atual is None or not atual.pertence_a(empresa_id):
                    raise PermissionError("base operacional nao pertence a empresa")
                if str(payload.get("cep", "")).strip():
                    endereco, latitude, longitude = _endereco_operacional(payload)
                else:
                    endereco = atual.endereco
                    latitude = atual.latitude
                    longitude = atual.longitude
                base = servico_base.atualizar(
                    empresa_id,
                    id_base,
                    {
                        "nome": str(payload.get("nome", "")),
                        "endereco": endereco,
                        "latitude": latitude,
                        "longitude": longitude,
                        "raio_atendimento_km": payload.get("raio_atendimento_km", 0),
                        "capacidade_kg": payload.get("capacidade_kg", 0),
                        "realiza_coleta_domiciliar": bool(
                            payload.get("realiza_coleta_domiciliar", False)
                        ),
                    },
                )
            return jsonify(_base_json(base))
        except PermissionError as exc:
            return jsonify({"erro": str(exc)}), 403
        except (ValueError, TypeError) as exc:
            return jsonify({"erro": str(exc)}), 400

    @bp.route("/empresa/bases/<id_base>/atividade", methods=["POST"])
    @requer_autenticacao_api
    def atividade_base_empresa_api(id_base):
        bloqueio = _exigir_empresa()
        if bloqueio:
            return bloqueio
        try:
            payload = request.get_json(silent=True) or {}
            servico_base.definir_atividade(
                request.usuario_token["sub"], id_base, bool(payload.get("ativa"))
            )
            return jsonify(_base_json(servico_base.buscar(id_base)))
        except PermissionError as exc:
            return jsonify({"erro": str(exc)}), 403
        except ValueError as exc:
            return jsonify({"erro": str(exc)}), 400

    @bp.route("/empresa/oportunidades", methods=["GET"])
    @requer_autenticacao_api
    def oportunidades_empresa_api():
        bloqueio = _exigir_empresa()
        if bloqueio:
            return bloqueio
        empresa_id = request.usuario_token["sub"]
        servico_despacho.processar_ofertas_expiradas()
        ofertas = servico_despacho.listar_ofertas_ativas(empresa_id)
        itens = []
        for oferta in ofertas:
            base = servico_base.buscar(oferta["base_operacional_id"])
            itens.append(
                {
                    **oferta,
                    "base_nome": base.nome if base else "",
                }
            )
        return jsonify({"oportunidades": itens, "total": len(itens)})

    @bp.route("/empresa/oportunidades/<oferta_id>/aceitar", methods=["POST"])
    @requer_autenticacao_api
    def aceitar_oportunidade_empresa_api(oferta_id):
        bloqueio = _exigir_empresa()
        if bloqueio:
            return bloqueio
        try:
            aceita = servico_despacho.aceitar(oferta_id, request.usuario_token["sub"])
            solicitacao = servico_descarte.obter_solicitacao(aceita["solicitacao_id"])
            if solicitacao:
                solicitacao._empresa_responsavel_id = request.usuario_token["sub"]
                solicitacao._base_operacional_id = aceita["base_operacional_id"]
                solicitacao._atribuida_em = datetime.fromisoformat(aceita["respondida_em"])
                solicitacao._estado = Solicitado()
                solicitacao._endereco_coleta = aceita["endereco_coleta"]
                solicitacao._nome_contato = aceita["nome_contato"]
            return jsonify(
                {
                    "ok": True,
                    "solicitacao_id": aceita["solicitacao_id"],
                    "endereco_coleta": aceita["endereco_coleta"],
                    "nome_contato": aceita["nome_contato"],
                    "data_agendamento": aceita["data_agendamento"],
                }
            )
        except LookupError as exc:
            return jsonify({"erro": str(exc)}), 404
        except TimeoutError as exc:
            return jsonify({"erro": str(exc)}), 410
        except (RuntimeError, ValueError) as exc:
            return jsonify({"erro": str(exc)}), 409

    @bp.route("/empresa/oportunidades/<oferta_id>/recusar", methods=["POST"])
    @requer_autenticacao_api
    def recusar_oportunidade_empresa_api(oferta_id):
        bloqueio = _exigir_empresa()
        if bloqueio:
            return bloqueio
        try:
            payload = request.get_json(silent=True) or {}
            servico_despacho.recusar(
                oferta_id,
                request.usuario_token["sub"],
                str(payload.get("motivo", "")),
            )
            return jsonify({"ok": True})
        except LookupError as exc:
            return jsonify({"erro": str(exc)}), 404
        except ValueError as exc:
            return jsonify({"erro": str(exc)}), 409

    @bp.route("/solicitacoes/<solicitacao_id>/agendamento", methods=["GET"])
    @requer_autenticacao_api
    def agendamento_api(solicitacao_id):
        solicitacao, erro = _buscar_solicitacao_visivel(solicitacao_id)
        if erro:
            return erro
        return jsonify(_agenda_json(solicitacao))

    def _instantes_agendamento():
        payload = request.get_json(silent=True) or {}
        try:
            inicio = datetime.fromisoformat(str(payload.get("inicio", "")))
            fim = datetime.fromisoformat(str(payload.get("fim", "")))
        except ValueError as exc:
            raise ValueError("Informe inicio e fim validos") from exc
        return inicio, fim

    @bp.route("/solicitacoes/<solicitacao_id>/agendamento/propor", methods=["POST"])
    @requer_autenticacao_api
    def propor_agendamento_api(solicitacao_id):
        solicitacao, erro = _buscar_solicitacao_visivel(solicitacao_id)
        if erro:
            return erro
        if request.usuario_token["tipo"] == "administrador":
            return jsonify({"erro": "Administrador nao participa da negociacao"}), 403
        try:
            inicio, fim = _instantes_agendamento()
            row = servico_agendamento.propor(
                solicitacao_id, request.usuario_token["sub"], inicio, fim
            )
            servico_chat.criar_para_atribuicao(solicitacao_id)
            servico_chat.evento(
                solicitacao_id,
                "PROPOSTA_HORARIO",
                {
                    "inicio": row["proposta_inicio"],
                    "fim": row["proposta_fim"],
                    "autor_id": request.usuario_token["sub"],
                },
            )
            return jsonify(_agenda_json(solicitacao, row))
        except PermissionError as exc:
            return jsonify({"erro": str(exc)}), 403
        except LookupError as exc:
            return jsonify({"erro": str(exc)}), 404
        except (TypeError, ValueError) as exc:
            return jsonify({"erro": str(exc)}), 400

    @bp.route("/solicitacoes/<solicitacao_id>/agendamento/aceitar", methods=["POST"])
    @requer_autenticacao_api
    def aceitar_agendamento_api(solicitacao_id):
        solicitacao, erro = _buscar_solicitacao_visivel(solicitacao_id)
        if erro:
            return erro
        if request.usuario_token["tipo"] == "administrador":
            return jsonify({"erro": "Administrador nao participa da negociacao"}), 403
        try:
            row = servico_agendamento.aceitar(solicitacao_id, request.usuario_token["sub"])
            servico_chat.criar_para_atribuicao(solicitacao_id)
            servico_chat.evento(
                solicitacao_id,
                "HORARIO_ACEITO",
                {
                    "inicio": row["inicio_confirmado"],
                    "fim": row["fim_confirmado"],
                },
            )
            return jsonify(_agenda_json(solicitacao, row))
        except PermissionError as exc:
            return jsonify({"erro": str(exc)}), 403
        except LookupError as exc:
            return jsonify({"erro": str(exc)}), 404
        except ValueError as exc:
            return jsonify({"erro": str(exc)}), 400

    @bp.route("/solicitacoes/<solicitacao_id>/agendamento/rejeitar", methods=["POST"])
    @requer_autenticacao_api
    def rejeitar_agendamento_api(solicitacao_id):
        solicitacao, erro = _buscar_solicitacao_visivel(solicitacao_id)
        if erro:
            return erro
        if request.usuario_token["tipo"] == "administrador":
            return jsonify({"erro": "Administrador nao participa da negociacao"}), 403
        try:
            row = servico_agendamento.rejeitar(solicitacao_id, request.usuario_token["sub"])
            servico_chat.criar_para_atribuicao(solicitacao_id)
            servico_chat.evento(
                solicitacao_id,
                "HORARIO_RECUSADO",
                {
                    "autor_id": request.usuario_token["sub"],
                },
            )
            return jsonify(_agenda_json(solicitacao, row))
        except PermissionError as exc:
            return jsonify({"erro": str(exc)}), 403
        except LookupError as exc:
            return jsonify({"erro": str(exc)}), 404
        except ValueError as exc:
            return jsonify({"erro": str(exc)}), 400

    @bp.route("/conversas", methods=["GET"])
    @requer_autenticacao_api
    def conversas_api():
        usuario = _usuario_token_dict()
        if usuario["tipo"] == "administrador":
            return jsonify({"conversas": [], "total_nao_lidas": 0})
        for solicitacao in _solicitacoes_do_usuario(usuario["id"], usuario["tipo"]):
            try:
                servico_chat.criar_para_atribuicao(solicitacao.id)
            except ValueError:
                pass
        conversas = []
        for row in dados.listar_conversas_usuario(usuario["id"]):
            item = dict(row)
            ultima = item.get("ultima_mensagem")
            if not ultima and item.get("ultima_mensagem_tipo"):
                ultima = _evento_chat_texto(item["ultima_mensagem_tipo"], {})
            conversas.append(
                {
                    "id": item["id"],
                    "solicitacao_id": item["solicitacao_id"],
                    "contato_nome": item["contato_nome"],
                    "contato_tipo": (
                        "cidadao" if item["empresa_id"] == usuario["id"] else "empresa"
                    ),
                    "estado": item["estado"].replace("_", " ").title(),
                    "criada_em": item["criada_em"],
                    "encerrada_em": item["encerrada_em"],
                    "ultima_mensagem": ultima or "Conversa iniciada",
                    "ultima_mensagem_em": (item["ultima_mensagem_em"] or item["criada_em"]),
                    "nao_lidas": int(item["nao_lidas"]),
                }
            )
        return jsonify(
            {
                "conversas": conversas,
                "total_nao_lidas": sum(item["nao_lidas"] for item in conversas),
            }
        )

    @bp.route("/conversas/<solicitacao_id>/mensagens", methods=["GET", "POST"])
    @requer_autenticacao_api
    def mensagens_conversa_api(solicitacao_id):
        solicitacao, erro = _buscar_solicitacao_visivel(solicitacao_id)
        if erro:
            return erro
        usuario = _usuario_token_dict()
        try:
            servico_chat.criar_para_atribuicao(solicitacao_id)
            if request.method == "POST":
                payload = request.get_json(silent=True) or {}
                row = servico_chat.enviar(
                    solicitacao_id,
                    usuario["id"],
                    payload.get("texto"),
                    chave_idempotencia=payload.get("id_cliente"),
                )
                row_completo = next(
                    item
                    for item in servico_chat.listar_recentes(solicitacao_id, usuario["id"], 1, 100)
                    if item["id"] == row["id"]
                )
                return jsonify(_mensagem_json(row_completo, usuario["id"])), 201
            try:
                pagina = max(1, int(request.args.get("pagina", 1)))
                limite = min(100, max(1, int(request.args.get("limite", 50))))
            except (TypeError, ValueError):
                return jsonify({"erro": "Paginacao invalida"}), 400
            mensagens = servico_chat.listar_recentes(solicitacao_id, usuario["id"], pagina, limite)
            return jsonify(
                {
                    "solicitacao": _resumo_operacao(solicitacao),
                    "mensagens": [_mensagem_json(item, usuario["id"]) for item in mensagens],
                    "pagina": pagina,
                    "limite": limite,
                    "tem_mais": len(mensagens) == limite,
                }
            )
        except PermissionError as exc:
            return jsonify({"erro": str(exc)}), 403
        except LookupError as exc:
            return jsonify({"erro": str(exc)}), 404
        except ValueError as exc:
            return jsonify({"erro": str(exc)}), 400

    @bp.route("/conversas/<solicitacao_id>/leitura", methods=["POST"])
    @requer_autenticacao_api
    def leitura_conversa_api(solicitacao_id):
        solicitacao, erro = _buscar_solicitacao_visivel(solicitacao_id)
        if erro:
            return erro
        try:
            total = servico_chat.marcar_lidas(solicitacao.id, request.usuario_token["sub"])
            return jsonify({"ok": True, "marcadas": total})
        except PermissionError as exc:
            return jsonify({"erro": str(exc)}), 403
        except LookupError as exc:
            return jsonify({"erro": str(exc)}), 404

    @bp.route("/notificacoes", methods=["GET"])
    @requer_autenticacao_api
    def notificacoes_api():
        try:
            pagina = max(1, int(request.args.get("pagina", 1)))
            limite = min(50, max(1, int(request.args.get("limite", 20))))
        except (TypeError, ValueError):
            return jsonify({"erro": "Paginacao invalida"}), 400
        todas = dados.buscar_notificacoes_usuario(request.usuario_token["sub"])
        inicio = (pagina - 1) * limite
        itens = todas[inicio : inicio + limite]
        return jsonify(
            {
                "notificacoes": [_notificacao_json(item) for item in itens],
                "pagina": pagina,
                "total": len(todas),
                "tem_mais": inicio + limite < len(todas),
                "nao_lidas": dados.contar_notificacoes_nao_lidas(request.usuario_token["sub"]),
            }
        )

    @bp.route("/notificacoes/leitura", methods=["POST"])
    @requer_autenticacao_api
    def leitura_notificacoes_api():
        payload = request.get_json(silent=True) or {}
        usuario_id = request.usuario_token["sub"]
        notificacao_id = payload.get("id")
        if notificacao_id is None:
            total = dados.marcar_notificacoes_lidas(usuario_id)
        else:
            try:
                total = dados.marcar_notificacao_lida(usuario_id, int(notificacao_id))
            except (TypeError, ValueError):
                return jsonify({"erro": "Notificacao invalida"}), 400
            if total == 0:
                return jsonify({"erro": "Notificacao nao encontrada"}), 404
        return jsonify({"ok": True, "marcadas": total})

    @bp.route("/badges", methods=["GET"])
    @requer_autenticacao_api
    def badges_api():
        usuario_id = request.usuario_token["sub"]
        oportunidades = (
            dados.contar_ofertas_ativas_empresa(usuario_id)
            if request.usuario_token["tipo"] == "empresa"
            else 0
        )
        mensagens = dados.contar_mensagens_nao_lidas(usuario_id)
        notificacoes = dados.contar_notificacoes_nao_lidas(usuario_id)
        return jsonify(
            {
                "notificacoes": notificacoes,
                "mensagens": mensagens,
                "oportunidades": oportunidades,
                "total": notificacoes + mensagens + oportunidades,
            }
        )

    @bp.route("/carteira", methods=["GET"])
    @requer_autenticacao_api
    def carteira_api():
        if request.usuario_token["tipo"] != "cidadao":
            return jsonify({"erro": "A carteira esta disponivel apenas para cidadaos"}), 403
        return jsonify(_carteira_json(request.usuario_token["sub"]))

    @bp.route("/saques", methods=["POST"])
    @requer_autenticacao_api
    def solicitar_saque_api():
        if request.usuario_token["tipo"] != "cidadao":
            return jsonify({"erro": "Saques estao disponiveis apenas para cidadaos"}), 403
        payload = request.get_json(silent=True) or {}
        metodo = str(payload.get("metodo", "")).strip()
        metodos = {"Pix", "Transferencia"}
        if metodo not in metodos:
            return jsonify({"erro": "Selecione um metodo de saque valido"}), 400
        titular = str(payload.get("titular", "")).strip()
        if len(titular) < 3:
            return jsonify({"erro": "Informe o nome completo do titular"}), 400
        try:
            valor = float(str(payload.get("valor", "")).replace(",", "."))
            carteira = _carteira_json(request.usuario_token["sub"])
            resultado = servico_saque.solicitar_saque(
                request.usuario_token["sub"],
                valor,
                metodo,
                carteira["saldo"],
                chave_idempotencia=payload.get("id_cliente"),
            )
            if not resultado.get("repetido"):
                dados.salvar_notificacao(
                    request.usuario_token["sub"],
                    f"Saque de R$ {valor:.2f} solicitado com sucesso.",
                    chave_idempotencia=f"saque:{resultado['id']}",
                )
            return jsonify(
                {
                    "saque": {
                        "id": resultado["id"],
                        "valor": float(resultado["valor"]),
                        "metodo": resultado["metodo"],
                        "data": resultado["data"],
                        "hora": resultado["hora"],
                        "data_hora": next(
                            item["data_hora"]
                            for item in _carteira_json(request.usuario_token["sub"])["saques"]
                            if item["id"] == resultado["id"]
                        ),
                        "status": resultado["status"],
                        "titular": titular,
                    },
                    "repetido": bool(resultado.get("repetido")),
                    "carteira": _carteira_json(request.usuario_token["sub"]),
                }
            ), 200 if resultado.get("repetido") else 201
        except (TypeError, ValueError) as exc:
            return jsonify({"erro": str(exc)}), 400

    @bp.route("/relatorios", methods=["GET"])
    @requer_autenticacao_api
    def relatorios_api():
        try:
            resultado = _dados_relatorio()
        except PermissionError as exc:
            return jsonify({"erro": str(exc)}), 403
        except ValueError as exc:
            return jsonify({"erro": str(exc)}), 400
        metricas = resultado["metricas"]
        total = round(
            metricas["peso_reciclado_kg"]
            + metricas["peso_reutilizado_kg"]
            + metricas["peso_descartado_kg"],
            2,
        )
        taxa_reciclagem = round(
            metricas["peso_reciclado_kg"] / total * 100 if total else 0.0,
            2,
        )
        destinacao_adequada = round(
            (metricas["peso_reciclado_kg"] + metricas["peso_reutilizado_kg"]) / total * 100
            if total
            else 0.0,
            2,
        )
        return jsonify(
            {
                "titulo": metricas["titulo"],
                "gerado_em": metricas["data_geracao"],
                "periodo": resultado["periodo"],
                "metricas": {
                    **metricas,
                    "peso_total_kg": total,
                    "taxa_reciclagem_pct": taxa_reciclagem,
                },
                "finalizadas": [
                    {
                        "id": item.id,
                        "cidadao": item.usuario.nome,
                        "peso_kg": round(item.calcular_peso_total(), 2),
                        "impacto_kg": round(item.calcular_impacto_total(), 2),
                        "metodo": (
                            item.metodo_tratamento.obter_nome() if item.metodo_tratamento else None
                        ),
                        "estado": item.estado.obter_nome(),
                        "data": item.data_criacao.isoformat(),
                    }
                    for item in sorted(
                        resultado["finalizadas"],
                        key=lambda item: item.data_criacao,
                        reverse=True,
                    )
                ],
                "pnrs": {
                    "disponivel": resultado["pode_exportar"],
                    "destinacao_adequada_pct": destinacao_adequada,
                    "peso_total_gerenciado_kg": total,
                    "solicitacoes_atendidas": len(resultado["finalizadas"]),
                },
                "plano": resultado["plano"],
                "pode_exportar": resultado["pode_exportar"],
            }
        )

    @bp.route("/relatorios/exportar.csv", methods=["GET"])
    @requer_autenticacao_api
    def exportar_relatorio_api():
        try:
            resultado = _dados_relatorio()
        except PermissionError as exc:
            return jsonify({"erro": str(exc)}), 403
        except ValueError as exc:
            return jsonify({"erro": str(exc)}), 400
        if not resultado["pode_exportar"]:
            return jsonify(
                {
                    "erro": "Exportacao disponivel nos planos Professional e Enterprise",
                    "upgrade": True,
                }
            ), 403
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "ID",
                "Cidadao",
                "Peso (kg)",
                "Impacto CO2 (kg)",
                "Metodo",
                "Estado",
                "Data",
            ]
        )
        for item in sorted(
            resultado["finalizadas"],
            key=lambda sol: sol.data_criacao,
            reverse=True,
        ):
            writer.writerow(
                [
                    item.id,
                    item.usuario.nome,
                    f"{item.calcular_peso_total():.2f}",
                    f"{item.calcular_impacto_total():.2f}",
                    item.metodo_tratamento.obter_nome() if item.metodo_tratamento else "",
                    item.estado.obter_nome(),
                    item.data_criacao.strftime("%d/%m/%Y"),
                ]
            )
        conteudo = "\ufeff" + output.getvalue()
        return Response(
            conteudo,
            mimetype="text/csv; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=relatorio_ecotech.csv"},
        )

    @bp.route("/admin/usuarios", methods=["GET", "POST"])
    @requer_autenticacao_api
    def usuarios_admin_api():
        bloqueio = _exigir_admin()
        if bloqueio:
            return bloqueio
        if request.method == "POST":
            payload = request.get_json(silent=True) or {}
            tipo = str(payload.get("tipo", "")).strip()
            nome = str(payload.get("nome", "")).strip()
            email = str(payload.get("email", "")).strip().lower()
            senha = str(payload.get("senha", ""))
            if tipo not in ("cidadao", "empresa"):
                return jsonify({"erro": "Selecione cidadao ou empresa"}), 400
            if len(nome) < 3 or "@" not in email:
                return jsonify({"erro": "Informe nome e e-mail validos"}), 400
            if len(senha) < 6:
                return jsonify({"erro": "A senha deve ter pelo menos 6 caracteres"}), 400
            if any(str(item["email"]).lower() == email for item in dados.buscar_todos_usuarios()):
                return jsonify({"erro": "Este e-mail ja esta em uso"}), 409
            novo = {"nome": nome, "email": email}
            if tipo == "cidadao":
                documento = str(payload.get("cpf", "")).strip()
                if any(
                    "".join(c for c in str(item.get("cpf") or "") if c.isdigit())
                    == "".join(c for c in documento if c.isdigit())
                    for item in dados.buscar_todos_cidadaos_admin()
                ):
                    return jsonify({"erro": "Este CPF ja esta cadastrado"}), 409
                novo["cpf"] = documento
            else:
                documento = str(payload.get("cnpj", "")).strip()
                if any(
                    "".join(c for c in str(item.get("cnpj") or "") if c.isdigit())
                    == "".join(c for c in documento if c.isdigit())
                    for item in dados.buscar_todos_empresas_admin()
                ):
                    return jsonify({"erro": "Este CNPJ ja esta cadastrado"}), 409
                novo["cnpj"] = documento
                novo["razao_social"] = str(payload.get("razao_social", "")).strip()
            try:
                usuario = servico_usuario.criar_usuario(tipo, novo, senha)
            except ValueError as exc:
                return jsonify({"erro": str(exc)}), 400
            except Exception:
                return jsonify({"erro": "Nao foi possivel cadastrar o usuario"}), 400
            row = (
                dados.buscar_cidadao(usuario.id)
                if tipo == "cidadao"
                else dados.buscar_empresa(usuario.id)
            )
            return jsonify(_usuario_admin_json(dict(row), tipo)), 201

        tipo = str(request.args.get("tipo", "todos")).strip().lower()
        busca = str(request.args.get("busca", "")).strip().lower()
        if tipo not in ("todos", "cidadao", "empresa"):
            return jsonify({"erro": "Tipo de usuario invalido"}), 400
        try:
            pagina = max(1, int(request.args.get("pagina", 1)))
            por_pagina = min(50, max(1, int(request.args.get("por_pagina", 20))))
        except (TypeError, ValueError):
            return jsonify({"erro": "Paginacao invalida"}), 400
        cidadaos = [dict(item) for item in dados.buscar_todos_cidadaos_admin()]
        empresas = [dict(item) for item in dados.buscar_todos_empresas_admin()]
        itens = []
        if tipo in ("todos", "cidadao"):
            itens.extend(_usuario_admin_json(item, "cidadao") for item in cidadaos)
        if tipo in ("todos", "empresa"):
            itens.extend(_usuario_admin_json(item, "empresa") for item in empresas)
        if busca:
            itens = [
                item
                for item in itens
                if busca in item["nome"].lower()
                or busca in item["email"].lower()
                or busca in item["documento"].lower()
            ]
        itens.sort(key=lambda item: (not item["ativo"], item["nome"].lower()))
        total = len(itens)
        inicio = (pagina - 1) * por_pagina
        return jsonify(
            {
                "usuarios": itens[inicio : inicio + por_pagina],
                "metricas": {
                    "total": len(cidadaos) + len(empresas),
                    "cidadaos": len(cidadaos),
                    "empresas": len(empresas),
                    "ativos": sum(bool(item.get("ativo")) for item in cidadaos + empresas),
                    "inativos": sum(not bool(item.get("ativo")) for item in cidadaos + empresas),
                },
                "paginacao": {
                    "pagina": pagina,
                    "por_pagina": por_pagina,
                    "total": total,
                    "total_paginas": max(1, (total + por_pagina - 1) // por_pagina),
                },
            }
        )

    @bp.route("/admin/usuarios/<usuario_id>/desativar", methods=["POST"])
    @requer_autenticacao_api
    def desativar_usuario_admin_api(usuario_id):
        bloqueio = _exigir_admin()
        if bloqueio:
            return bloqueio
        if usuario_id == request.usuario_token["sub"]:
            return jsonify({"erro": "Voce nao pode desativar a propria conta"}), 409
        usuario = dados.buscar_usuario(usuario_id)
        if not usuario:
            return jsonify({"erro": "Usuario nao encontrado"}), 404
        if usuario["tipo"] == "administrador":
            return jsonify({"erro": "Administradores nao podem ser desativados aqui"}), 403
        alterado = dados.desativar_usuario(usuario_id)
        return jsonify(
            {
                "ok": True,
                "ativo": False,
                "repetido": not alterado,
            }
        )

    @bp.route("/admin/despacho", methods=["GET"])
    @requer_autenticacao_api
    def despacho_admin_api():
        bloqueio = _exigir_admin()
        if bloqueio:
            return bloqueio
        diagnostico = dados.buscar_diagnostico_despacho()
        metricas = dict(diagnostico["metricas"] or {})
        eventos = dict(diagnostico["eventos"] or {})
        tempo = dict(diagnostico["tempo_agendamento"] or {})
        atribuicoes = []
        for row in diagnostico["atribuicoes"]:
            item = dict(row)
            empresa = dados.buscar_usuario(item["empresa_responsavel_id"])
            item["empresa_nome"] = empresa["nome"] if empresa else "Nao identificada"
            atribuicoes.append(item)
        return jsonify(
            {
                "somente_leitura": True,
                "metricas": {
                    **{chave: valor or 0 for chave, valor in metricas.items()},
                    "conflitos": eventos.get("conflitos") or 0,
                    "sem_empresa": eventos.get("sem_empresa") or 0,
                    "falhas_geocodificacao": eventos.get("falhas_geocodificacao") or 0,
                    "minutos_atribuicao_ate_agendamento": (
                        tempo.get("minutos_atribuicao_ate_agendamento") or 0
                    ),
                },
                "resumo": [dict(item) for item in diagnostico["resumo"]],
                "pendentes": [dict(item) for item in diagnostico["pendentes"]],
                "destinatarios": [dict(item) for item in diagnostico["destinatarios"]],
                "atribuicoes": atribuicoes,
            }
        )

    @bp.route("/admin/overrides", methods=["GET"])
    @requer_autenticacao_api
    def overrides_admin_api():
        bloqueio = _exigir_admin()
        if bloqueio:
            return bloqueio
        pendentes = []
        for row in dados.buscar_overrides_pendentes():
            item = dict(row)
            valores = _valores_override(item["id"], item["estado_produto"])
            empresa_id = _empresa_id_solicitacao(item["id"])
            empresa = dados.buscar_usuario(empresa_id) if empresa_id else None
            pendentes.append(
                {
                    "solicitacao_id": item["id"],
                    "data_criacao": item["data_criacao"],
                    "cidadao": item["nome_usuario"],
                    "empresa": empresa["nome"] if empresa else "Nao atribuida",
                    "estado_produto": item["estado_produto"],
                    "valor_proposto": float(item["valor_proposto"] or 0),
                    "justificativa": item["justificativa_valor"] or "",
                    **valores,
                }
            )
        return jsonify({"overrides": pendentes, "total": len(pendentes)})

    @bp.route("/admin/overrides/<solicitacao_id>/decisao", methods=["POST"])
    @requer_autenticacao_api
    def decidir_override_admin_api(solicitacao_id):
        bloqueio = _exigir_admin()
        if bloqueio:
            return bloqueio
        payload = request.get_json(silent=True) or {}
        decisao = str(payload.get("decisao", "")).strip().lower()
        if decisao not in ("aprovar", "rejeitar"):
            return jsonify({"erro": "Decisao deve ser aprovar ou rejeitar"}), 400
        avaliacao = dados.buscar_avaliacao_solicitacao(solicitacao_id)
        if not avaliacao:
            return jsonify({"erro": "Avaliacao nao encontrada"}), 404
        status_destino = "aprovado" if decisao == "aprovar" else "rejeitado"
        if avaliacao["status_override"] == status_destino:
            return jsonify(
                {
                    "ok": True,
                    "status": status_destino,
                    "repetido": True,
                    "valor": float(avaliacao["valor_proposto"] or 0),
                }
            )
        if avaliacao["status_override"] != "pendente_doc":
            return jsonify({"erro": "Override ja possui outra decisao"}), 409
        valores = _valores_override(solicitacao_id, avaliacao["estado_produto"])
        if decisao == "aprovar":
            alterado = dados.aprovar_override(solicitacao_id)
            valor = float(avaliacao["valor_proposto"] or 0)
        else:
            valor = valores["valor_recalculado"]
            alterado = dados.rejeitar_override(solicitacao_id, valor)
        if not alterado:
            return jsonify({"erro": "Override foi decidido por outro administrador"}), 409
        empresa_id = _empresa_id_solicitacao(solicitacao_id)
        if empresa_id:
            dados.salvar_notificacao(
                empresa_id,
                f"Override da operacao {solicitacao_id[:8]} foi {status_destino}.",
                chave_idempotencia=f"override:{solicitacao_id}:{status_destino}",
            )
        return jsonify(
            {
                "ok": True,
                "status": status_destino,
                "repetido": False,
                "valor": valor,
            }
        )

    @bp.route("/admin/precos", methods=["GET", "PATCH"])
    @requer_autenticacao_api
    def precos_admin_api():
        bloqueio = _exigir_admin()
        if bloqueio:
            return bloqueio
        if request.method == "PATCH":
            payload = request.get_json(silent=True) or {}
            subcategoria = str(payload.get("subcategoria", "")).strip()
            atual = dados.buscar_preco_subcategoria(subcategoria)
            if not atual:
                return jsonify({"erro": "Subcategoria nao encontrada"}), 404
            try:
                valor_base = float(str(payload.get("valor_base", "")).replace(",", "."))
                valor_minimo = float(str(payload.get("valor_minimo", "")).replace(",", "."))
            except (TypeError, ValueError):
                return jsonify({"erro": "Informe valores numericos validos"}), 400
            if valor_base <= 0 or valor_minimo < 0:
                return jsonify(
                    {"erro": "Valor base deve ser positivo e minimo nao pode ser negativo"}
                ), 400
            if valor_minimo >= valor_base:
                return jsonify({"erro": "Valor minimo deve ser menor que o valor base"}), 400
            dados.atualizar_preco_subcategoria(subcategoria, valor_base, valor_minimo)
        precos = []
        for row in dados.buscar_tabela_precos():
            item = dict(row)
            base = float(item["valor_base_funcionando"])
            precos.append(
                {
                    "subcategoria": item["subcategoria"],
                    "categoria": item["categoria"],
                    "valor_base": base,
                    "valor_minimo": float(item["valor_minimo_sucata"]),
                    "limite_override": round(base * 1.5, 2),
                }
            )
        return jsonify({"precos": precos})

    @bp.route("/planos", methods=["GET"])
    @requer_autenticacao_api
    def planos_api():
        payload = request.usuario_token
        if payload["tipo"] != "empresa":
            return jsonify({"erro": "Planos estao disponiveis apenas para empresas"}), 403
        plano_atual = dados.buscar_plano_empresa(payload["sub"])
        return jsonify(
            {
                "plano_atual": plano_atual,
                "feature_flags": recursos_do_plano(plano_atual),
                "planos": listar_planos(),
                "ambiente_demonstracao": True,
            }
        )

    @bp.route("/planos/alterar", methods=["POST"])
    @requer_autenticacao_api
    def alterar_plano_api():
        payload = request.usuario_token
        if payload["tipo"] != "empresa":
            return jsonify({"erro": "Planos estao disponiveis apenas para empresas"}), 403
        corpo = request.get_json(silent=True) or {}
        plano_id = str(corpo.get("plano", "")).strip().lower()
        if buscar_plano(plano_id) is None:
            return jsonify({"erro": "Plano invalido"}), 400
        plano_anterior = dados.buscar_plano_empresa(payload["sub"])
        repetido = plano_anterior == plano_id
        if not repetido:
            dados.atualizar_plano_empresa(payload["sub"], plano_id)
        return jsonify(
            {
                "ok": True,
                "plano_anterior": plano_anterior,
                "plano_atual": plano_id,
                "repetido": repetido,
                "feature_flags": recursos_do_plano(plano_id),
                "planos": listar_planos(),
                "ambiente_demonstracao": True,
            }
        )

    @bp.route("/operacoes", methods=["GET"])
    @requer_autenticacao_api
    def operacoes_api():
        bloqueio = _exigir_operador()
        if bloqueio:
            return bloqueio
        solicitacoes = _solicitacoes_do_usuario(
            request.usuario_token["sub"], request.usuario_token["tipo"]
        )
        estatisticas = servico_descarte.calcular_stats_estados(solicitacoes)
        estado = str(request.args.get("estado", "")).strip().lower()
        busca = str(request.args.get("busca", "")).strip().lower()
        if estado:
            solicitacoes = [
                item for item in solicitacoes if item.estado.obter_nome().lower() == estado
            ]
        if busca:
            solicitacoes = [
                item
                for item in solicitacoes
                if busca in item.id.lower()
                or busca in item.usuario.nome.lower()
                or busca in (_nome_empresa_solicitacao(item) or "").lower()
                or busca in (item.ponto_coleta.nome if item.ponto_coleta else "").lower()
            ]
        solicitacoes.sort(key=lambda item: item.data_criacao, reverse=True)
        try:
            pagina = max(1, int(request.args.get("pagina", 1)))
            por_pagina = min(50, max(1, int(request.args.get("por_pagina", 20))))
        except (TypeError, ValueError):
            return jsonify({"erro": "Paginacao invalida"}), 400
        total = len(solicitacoes)
        inicio = (pagina - 1) * por_pagina
        return jsonify(
            {
                "operacoes": [
                    _resumo_operacao(item) for item in solicitacoes[inicio : inicio + por_pagina]
                ],
                "estatisticas": estatisticas,
                "paginacao": {
                    "pagina": pagina,
                    "por_pagina": por_pagina,
                    "total": total,
                    "total_paginas": max(1, (total + por_pagina - 1) // por_pagina),
                },
            }
        )

    @bp.route("/operacoes/<solicitacao_id>", methods=["GET"])
    @requer_autenticacao_api
    def operacao_api(solicitacao_id):
        bloqueio = _exigir_operador()
        if bloqueio:
            return bloqueio
        solicitacao, erro = _buscar_operacao_autorizada(solicitacao_id)
        if erro:
            return erro
        return jsonify(_detalhes_operacao(solicitacao))

    @bp.route("/operacoes/<solicitacao_id>/peso", methods=["POST"])
    @requer_autenticacao_api
    def peso_operacao_api(solicitacao_id):
        bloqueio = _exigir_operador()
        if bloqueio:
            return bloqueio
        solicitacao, erro = _buscar_operacao_autorizada(solicitacao_id)
        if erro:
            return erro
        if solicitacao.estado.obter_nome() != "Solicitado":
            return jsonify({"erro": "O peso deve ser aferido no recebimento da solicitacao"}), 409
        try:
            payload = request.get_json(silent=True) or {}
            peso = dados.confirmar_peso_solicitacao(
                solicitacao.id,
                str(payload.get("peso_kg", "")).replace(",", "."),
                request.usuario_token["sub"],
                datetime.now().isoformat(timespec="seconds"),
            )
            solicitacao.confirmar_peso(peso)
            dados.salvar_historico_rastreamento(
                solicitacao.id, f"Peso aferido no recebimento: {peso:g} kg"
            )
            return jsonify(
                {
                    "peso_confirmado_kg": peso,
                    "peso_origem": "aferido",
                }
            )
        except (TypeError, ValueError) as exc:
            return jsonify({"erro": str(exc)}), 400

    @bp.route("/operacoes/<solicitacao_id>/avancar", methods=["POST"])
    @requer_autenticacao_api
    def avancar_operacao_api(solicitacao_id):
        bloqueio = _exigir_operador()
        if bloqueio:
            return bloqueio
        solicitacao, erro = _buscar_operacao_autorizada(solicitacao_id)
        if erro:
            return erro
        if not solicitacao.estado.pode_avancar():
            return jsonify({"erro": "A operacao ja esta em estado final"}), 409
        operador = _usuario_token_dict()
        if operador["tipo"] == "empresa" and dados.buscar_plano_empresa(operador["id"]) == "free":
            agora = datetime.now(timezone(timedelta(hours=-3)))
            processadas = sum(
                1
                for item in _solicitacoes_do_usuario(operador["id"], operador["tipo"])
                if item.estado.obter_nome() not in ("Solicitado", "Cancelado")
                and item.data_criacao.year == agora.year
                and item.data_criacao.month == agora.month
            )
            if processadas >= 30:
                return jsonify(
                    {
                        "erro": "Limite mensal do plano atingido",
                        "upgrade": True,
                    }
                ), 403
        payload = request.get_json(silent=True) or {}
        estado_anterior = solicitacao.estado.obter_nome()
        try:
            if estado_anterior == "Solicitado" and solicitacao.peso_confirmado_kg is None:
                peso = dados.confirmar_peso_solicitacao(
                    solicitacao.id,
                    str(payload.get("peso_kg", "")).replace(",", "."),
                    operador["id"],
                    datetime.now(timezone(timedelta(hours=-3))).isoformat(timespec="seconds"),
                )
                solicitacao.confirmar_peso(peso)
                dados.salvar_historico_rastreamento(
                    solicitacao.id, f"Peso aferido no recebimento: {peso:g} kg"
                )
            if estado_anterior == "Em Processamento":
                _registrar_avaliacao(solicitacao, payload)
            servico_descarte.avancar_estado_solicitacao(solicitacao)
        except (TypeError, ValueError) as exc:
            return jsonify({"erro": str(exc)}), 400

        novo_estado = solicitacao.estado.obter_nome()
        dados.salvar_historico_rastreamento(
            solicitacao.id,
            f"Operacao avancou de {estado_anterior} para {novo_estado}",
        )
        if novo_estado in estados_finais:
            _creditar_finalizacao(solicitacao, operador)
        dados.salvar_notificacao(
            solicitacao.usuario.id,
            f"Sua solicitacao foi atualizada para: {novo_estado}.",
            chave_idempotencia=f"estado:{solicitacao.id}:{novo_estado}",
        )
        if novo_estado in estados_finais and operador["tipo"] == "empresa":
            plano = dados.buscar_plano_empresa(operador["id"])
            if plano in ("professional", "enterprise"):
                dados.salvar_notificacao(
                    operador["id"],
                    f"MTR disponivel para a operacao {solicitacao.id[:8]}.",
                    chave_idempotencia=f"mtr:{solicitacao.id}:disponivel",
                )
        return jsonify(
            {
                "novo_estado": novo_estado,
                "pode_avancar": solicitacao.estado.pode_avancar(),
                "operacao": _detalhes_operacao(solicitacao),
            }
        )

    @bp.route("/operacoes/<solicitacao_id>/mtr", methods=["GET"])
    @requer_autenticacao_api
    def mtr_operacao_api(solicitacao_id):
        bloqueio = _exigir_operador()
        if bloqueio:
            return bloqueio
        operador = _usuario_token_dict()
        if operador["tipo"] == "empresa" and dados.buscar_plano_empresa(operador["id"]) == "free":
            return jsonify({"erro": "MTR disponivel nos planos Professional e Enterprise"}), 403
        solicitacao, erro = _buscar_operacao_autorizada(solicitacao_id)
        if erro:
            return erro
        raw = dados.buscar_solicitacao(solicitacao.id)
        empresa_id = raw["empresa_responsavel_id"]
        if not empresa_id and raw["id_ponto_coleta"]:
            ponto = dados.buscar_ponto_coleta(raw["id_ponto_coleta"])
            empresa_id = ponto["id_empresa"] if ponto else None
        empresa = dados.buscar_empresa(empresa_id) if empresa_id else None
        base = (
            dados.buscar_base_operacional(raw["base_operacional_id"])
            if raw["base_operacional_id"]
            else None
        )
        solicitacao._mtr_registro = dict(raw)
        solicitacao._mtr_empresa = dict(empresa) if empresa else {}
        solicitacao._mtr_base = dict(base) if base else {}
        numero = f"MTR-{solicitacao.id[:8].upper()}"
        return Response(
            gerar_mtr(solicitacao),
            mimetype="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={numero}.pdf"},
        )

    return bp
