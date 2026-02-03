# arquivo principal para rodar o sistema
from ecotech.infrastructure.web import criar_app

if __name__ == '__main__':
    app = criar_app()
    print("=" * 50)
    print("ecotech - sistema de descarte de lixo eletronico")
    print("=" * 50)
    print("servidor: http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)
