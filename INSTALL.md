# Guia de Instalação e Execução - EcoTech

## Pré-requisitos

- Python 3.10 ou superior
- pip (gerenciador de pacotes do Python)
- Poetry (opcional, mas recomendado)

## Método 1: Instalação com Poetry (Recomendado)

### 1. Instalar o Poetry

```powershell
# Windows (PowerShell)
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

# Ou via pip
pip install poetry
```

### 2. Instalar Dependências

```powershell
# Na raiz do projeto
cd C:\Users\T-Gamer\Desktop\Ecotech
poetry install
```

### 3. Ativar Ambiente Virtual

```powershell
poetry shell
```

### 4. Executar a Aplicação

```powershell
python run.py
```

## Método 2: Instalação com pip

### 1. Criar Ambiente Virtual

```powershell
cd C:\Users\T-Gamer\Desktop\Ecotech
python -m venv venv
```

### 2. Ativar Ambiente Virtual

```powershell
.\venv\Scripts\Activate.ps1
```

### 3. Instalar Dependências

```powershell
pip install flask python-dotenv
pip install pytest pytest-cov pytest-mock  # Para testes
```

### 4. Executar a Aplicação

```powershell
python run.py
```

## Executar Testes

### Com Poetry

```powershell
poetry run pytest
poetry run pytest --cov=ecotech  # Com cobertura
```

### Com pip

```powershell
pytest
pytest --cov=ecotech  # Com cobertura
```

## Acessar a Aplicação

Após executar, abra o navegador em:
- **URL**: http://localhost:5000
- **Email de teste**: joao@example.com ou contato@ecotech.com

## Usuários Pré-cadastrados

### Cidadão
- **Nome**: João Silva
- **Email**: joao@example.com
- **Tipo**: Cidadão

### Empresa
- **Nome**: EcoTech Recicláveis
- **Email**: contato@ecotech.com
- **Tipo**: Empresa

## Pontos de Coleta Pré-cadastrados

1. **R. Dr. Morato Saraiva, 1100 - Lagoa Seca**
   - Juazeiro do Norte, CE
   - Capacidade: 1000kg

2. **Centro de Reciclagem Cariri**
   - Av. Padre Cícero, 500 - Centro
   - Capacidade: 2000kg

## Estrutura de Pastas

```
Ecotech/
├── ecotech/                 # Código fonte
│   ├── domain/              # Camada de domínio
│   ├── application/         # Camada de aplicação
│   └── infrastructure/      # Camada de infraestrutura
├── tests/                   # Testes automatizados
├── run.py                   # Script principal
├── pyproject.toml           # Configuração Poetry
└── README.md                # Documentação
```

## Solução de Problemas

### Erro: "poetry: command not found"
Reinstale o Poetry ou use o método com pip.

### Erro: "ModuleNotFoundError"
Certifique-se de que está no ambiente virtual ativado.

### Porta 5000 em uso
Edite `run.py` e altere o parâmetro `port=5000` para outra porta.

## Comandos Úteis

```powershell
# Ver versão do Python
python --version

# Listar pacotes instalados
poetry show  # ou pip list

# Limpar cache
poetry cache clear . --all

# Desativar ambiente virtual
deactivate
```

## Suporte

Para problemas ou dúvidas, entre em contato com a equipe:
- Abner Levi (@abnerlevi)
- Maria Antônia (@mariastrajano)
- Matheus Nogueira (@mathNS)
