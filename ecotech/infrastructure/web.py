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


def criar_app() -> Flask:
    """
    Cria e configura a aplicação Flask.
    
    Returns:
        Aplicação Flask configurada
    """
    app = Flask(__name__)
    app.secret_key = "ecotech-secret-key-2026"
    
    # servicos
    servico_descarte = ServicoDescarte()
    servico_relatorio = ServicoRelatorio()
    servico_ponto = ServicoPontoColeta()
    servico_usuario = ServicoUsuario()
    
    # dados exemplo
    _inicializar_dados_exemplo(servico_usuario, servico_ponto)
    
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
            
            session['user_id'] = 'demo'
            session['user_tipo'] = tipo
            
            if tipo == 'cidadao':
                session['user_nome'] = 'João Silva'
            else:
                session['user_nome'] = 'EcoTech Reciclável'
            
            return redirect(url_for('dashboard'))
        
        return render_template('login.html')
    
    @app.route('/criar-conta', methods=['GET', 'POST'])
    def criar_conta():
        """Página de criação de conta."""
        if request.method == 'POST':
            tipo = request.form.get('tipo', 'cidadao')
            
            session['user_id'] = 'demo'
            session['user_tipo'] = tipo
            
            if tipo == 'cidadao':
                session['user_nome'] = 'João Silva'
            else:
                session['user_nome'] = 'EcoTech Reciclável'
            
            return redirect(url_for('dashboard'))
        
        return render_template('criar_conta.html')
    
    @app.route('/logout')
    def logout():
        """Logout do usuário."""
        session.clear()
        return redirect(url_for('index'))
    
    @app.route('/dashboard')
    def dashboard():
        """Dashboard principal."""
        if not usuario_logado():
            return redirect(url_for('login'))
        
        usuario = dados_usuario()
        
        return render_template(
            'dashboard.html',
            usuario=usuario,
            solicitacoes=[],
            total_descartado=45.8,
            impacto_evitado=125.3,
            pontos_acumulados=1250
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
        
        # dados de exemplo das entregas (talvez alterar dps)
        entregas = [
            {
                'valor': 13.95,
                'empresa': 'Ecotech - Reciclagem Cariri',
                'id': '56492574920',
                'data': '13 Set 2025',
                'hora': '13:02',
                'status': 'finalizado'
            },
            {
                'valor': 8.19,
                'empresa': 'Ecotech - Reciclagem Cariri',
                'id': '58293049159',
                'data': '10 Set 2025',
                'hora': '08:55',
                'status': 'finalizado'
            },
            {
                'valor': 6.41,
                'empresa': 'Ecotech - Reciclagem Cariri',
                'id': '98358259431',
                'data': '08 Set 2025',
                'hora': '15:31',
                'status': 'cancelado'
            },
            {
                'valor': 27.65,
                'empresa': 'Ecotech - Reciclagem Cariri',
                'id': '47389088043',
                'data': '03 Set 2025',
                'hora': '16:44',
                'status': 'finalizado'
            },
            {
                'valor': 12.53,
                'empresa': 'Ecotech - Reciclagem Cariri',
                'id': '57463968973',
                'data': '02 Set 2025',
                'hora': '08:21',
                'status': 'finalizado'
            }
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
        """Página de operações (placeholder)."""
        if not usuario_logado():
            return redirect(url_for('login'))
        
        usuario = dados_usuario()
        return render_template('operacoes.html', usuario=usuario)
    
    @app.route('/relatorios')
    def relatorios():
        """Página de relatórios (placeholder)."""
        if not usuario_logado():
            return redirect(url_for('login'))
        
        usuario = dados_usuario()
        return render_template('relatorios.html', usuario=usuario)
    
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


def _inicializar_dados_exemplo(servico_usuario, servico_ponto):
    """Inicializa dados de exemplo para demonstração."""
    # Usuários de exemplo
    servico_usuario.criar_usuario('cidadao', {
        'id': 'user-1',
        'nome': 'João Silva',
        'email': 'joao@example.com',
        'cpf': '123.456.789-00'
    })
    
    servico_usuario.criar_usuario('empresa', {
        'id': 'user-2',
        'nome': 'EcoTech Recicláveis',
        'email': 'contato@ecotech.com',
        'cnpj': '12.345.678/0001-99',
        'razao_social': 'EcoTech Recicláveis LTDA'
    })
    
    servico_ponto.criar_ponto_coleta(
        'R. Dr. Morato Saraiva, 1100 - Lagoa Seca',
        'Juazeiro do Norte, CE',
        -7.2138,
        -39.3089,
        1000.0
    )
    
    servico_ponto.criar_ponto_coleta(
        'Centro de Reciclagem Cariri',
        'Av. Padre Cícero, 500 - Centro',
        -7.2123,
        -39.3145,
        2000.0
    )


if __name__ == '__main__':
    app = criar_app()
    app.run(debug=True, port=5000)
