# Guia de Instalação e Execução - EcoTech

## Pré-requisitos

- Python 3.10 ou superior
- pip (gerenciador de pacotes do Python)

## Instalação

### 1. Clonar o repositório

```powershell
git clone https://github.com/mathsNS/Ecotech.git
cd Ecotech
```

### 2. Criar e ativar o ambiente virtual

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Instalar dependências

```powershell
pip install flask werkzeug fpdf2 pytest pytest-cov pytest-mock
```

### 4. Executar a aplicação

```powershell
python run.py
```

A aplicação estará disponível em **http://localhost:5000**.

---

## Executar Testes

```powershell
.\.venv\Scripts\python.exe -m pytest tests/ -q
.\.venv\Scripts\python.exe -m pytest tests/ --cov=ecotech   # com cobertura
```

## Configuração de segurança

Defina uma chave secreta própria antes de executar a aplicação em um ambiente
persistente ou compartilhado:

```powershell
$env:ECOTECH_SECRET_KEY = "uma-chave-longa-aleatoria-e-privada"
python run.py
```

Quando a variável não é informada, a aplicação gera uma chave efêmera aleatória.
Isso é adequado apenas para desenvolvimento local, pois invalida as sessões após
cada reinício do processo.

## Migrations do banco

O schema SQLite é atualizado automaticamente na inicialização por migrations
versionadas em `ecotech/infrastructure/persistence/migrations/`. As versões
aplicadas ficam registradas na tabela `schema_migration`.

Antes de atualizar um ambiente persistente, faça uma cópia de segurança de
`ecotech.db`. A migration interrompe a inicialização com uma mensagem explícita
se encontrar emails, CPFs, CNPJs ou lançamentos financeiros duplicados que
impeçam a aplicação das novas constraints; o banco não deve ser apagado para
contornar esse erro.

### Localização de coletas domiciliares

Coletas domiciliares exigem latitude e longitude válidas. A interface tenta
obtê-las pela API de geolocalização do navegador e permite correção manual. O
navegador normalmente exige HTTPS ou `localhost` para liberar essa API.

Empresas podem administrar suas bases em `/empresa/bases`. Os pontos
empresariais existentes são convertidos em bases iniciais pela migration v3,
com raio padrão de 25 km, sem remover ou alterar o ponto original.

---

## Contas de Acesso (pré-cadastradas no seed)

### Cidadãos
| Nome | CPF (login) | Senha |
|---|---|---|
| João Silva | `12345678909` | `cidadao123` |
| Ana Beatriz Ferreira | `98765432100` | `ana123` |
| Carlos Eduardo Mendes | `34945611840` | `carlos123` |
| Fernanda Lima | `47585901330` | `fernanda123` |
| Rafael Gonçalves | `70548478490` | `rafael123` |

### Empresas
| Nome | CNPJ (login) | Senha |
|---|---|---|
| Recicla Kariri | `11222333000181` | `empresa123` |
| TechLixo Soluções | `14380200000121` | `techlixo123` |
| GreenCycle Nordeste | `33000167000101` | `greencycle123` |

### Administrador
| Email | Senha |
|---|---|
| `admin@ecotech.com` | `admin123` |

> **Como fazer login:** acesse `/login`, selecione o tipo de conta e informe CPF/CNPJ (apenas dígitos, sem pontos ou traços) ou e-mail conforme o tipo.

---

## Estrutura de Pastas

```
Ecotech/
├── ecotech/
│   ├── domain/              # Entidades e regras de domínio
│   ├── application/         # Serviços e fábricas
│   └── infrastructure/      # Flask, SQLite, templates, static
├── tests/                   # Testes automatizados (271 testes)
├── run.py                   # Ponto de entrada
├── pyproject.toml           # Metadados do projeto
└── CREDENCIAIS.txt          # Referência completa de contas
```

---

## Solução de Problemas

### Erro: `ModuleNotFoundError`
Confirme que o ambiente virtual está ativado (`.venv`) e que as dependências foram instaladas.

### Porta 5000 em uso
Edite `run.py` e altere `port=5000` para outra porta disponível.

### Banco de dados corrompido
Delete o arquivo `ecotech.db` na raiz do projeto. Ele será recriado com os dados de seed na próxima execução.

---

## Suporte

- Abner Levi (@abnerlevi)
- Maria Antônia (@mariastrajano)
- Matheus Nogueira (@mathNS)


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
