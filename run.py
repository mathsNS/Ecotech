#arquivo principal pra rodar o app
from ecotech.infrastructure.web import criar_app

if __name__ == '__main__':
    app = criar_app()
    print("=" * 50)
    print("Ecotech - Sistema de descarte de lixo eletrônico")
    print("=" * 50)
    print("server: http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)
