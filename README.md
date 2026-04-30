# EcoTech - Sistema de Gerenciamento de Descarte de Lixo Eletrônico

## Sobre o Projeto

O EcoTech é um sistema de gerenciamento de descarte de lixo eletrônico que facilita a coleta, tratamento e reciclagem de dispositivos eletrônicos. A plataforma conecta cidadãos e empresas a pontos de coleta especializados, garantindo o descarte ambientalmente responsável.

### Equipe de Desenvolvimento

- Abner Levi - [@abnerlevi](https://github.com/abnerlevi)
- Maria Antônia - [@mariastrajano](https://github.com/mariastrajano)
- Matheus Nogueira - [@mathsNS](https://github.com/mathsNS)

### Divisão de Responsabilidades

- Abner: Implementação do módulo de dispositivos eletrônicos e testes
- Maria: Implementação do sistema de usuários e relatórios ambientais
- Matheus: Implementação do sistema de estados e métodos de tratamento

## Funcionalidades

- Cadastro de usuários (cidadãos, empresas e administradores)
- Registro de dispositivos eletrônicos para descarte
- Sistema de solicitação e rastreamento de coletas
- Cálculo automático de impacto ambiental
- Relatórios de reciclagem e sustentabilidade
- Gerenciamento de pontos de coleta

## Arquitetura

O projeto utiliza uma arquitetura em camadas que separa responsabilidades, com fluxo de dependência sempre de fora para dentro (**infrastructure → application → domain**):

```
ecotech/
├── domain/              # Regras de negócio e entidades
│   ├── usuarios.py      # Hierarquia Usuario → Cidadao, Empresa, Administrador
│   ├── dispositivos.py  # Hierarquia DispositivoEletronico → Celular, Computador, Eletrodomestico
│   ├── estados.py       # State Pattern — 7 estados de solicitação
│   ├── tratamento.py    # Strategy Pattern — Reciclagem, Reuso, DescarteControlado
│   ├── descarte.py      # PontoColeta, SolicitacaoDescarte, ItemDescarte, RastreamentoEntrega
│   ├── relatorio.py     # RelatorioAmbiental — métricas consolidadas
│   ├── mixins.py        # LoggableMixin, NotificavelMixin (herança múltipla)
│   └── repositorio.py   # RepositorioBase (interface abstrata — DIP)
├── application/         # Lógica de aplicação (serviços e factories)
│   ├── factories.py     # DispositivoFactory, UsuarioFactory, MetodoTratamentoFactory, PontoColetaFactory
│   └── services.py      # ServicoDescarte, ServicoPontoColeta, ServicoUsuario
└── infrastructure/      # Camada de infraestrutura (persistência e web)
    ├── web.py           # Rotas Flask
    ├── persistence/
    │   └── dados.py     # Dados(RepositorioBase) — implementação SQLite
    ├── templates/
    └── static/
```

## Tecnologias e Conceitos

### Design Orientado a Objetos

**Encapsulamento:** Todos os atributos das classes são privados com acesso controlado através de properties, garantindo validação e integridade dos dados. Docstrings estão presentes em todas as classes e métodos públicos.

**Hierarquias Implementadas (herança simples):**

Usuários:
- `Usuario` (classe abstrata base — ABC)
- `Cidadao`, `Empresa`, `Administrador` (implementações concretas)

Dispositivos Eletrônicos:
- `DispositivoEletronico` (classe abstrata — ABC)
- `Celular`, `Computador`, `Eletrodomestico` (tipos específicos com polimorfismo em `calcular_impacto_ambiental` e `calcular_valor_revenda`)

Estados de Solicitação (State Pattern):
- `EstadoDescarte` (classe abstrata — ABC)
- `Solicitado`, `Coletado`, `EmProcessamento`, `Reciclado`, `Reutilizado`, `Descartado`, `Cancelado`

Métodos de Tratamento (Strategy Pattern):
- `MetodoTratamento` (classe abstrata — ABC)
- `Reciclagem`, `Reuso`, `DescarteControlado`

Persistência (DIP):
- `RepositorioBase` (interface abstrata — ABC, definida no domínio)
- `Dados` (implementação concreta em infrastructure)

**Herança Múltipla — Mixins:**

O projeto utiliza herança múltipla através de Mixins para adicionar comportamentos transversais sem acoplamento:

- `LoggableMixin` — registra logs com timestamp em qualquer entidade. Utilizado por `PontoColeta` e `SolicitacaoDescarte`.
- `NotificavelMixin` — emite e gerencia notificações. Utilizado por `SolicitacaoDescarte`.

Exemplo: `SolicitacaoDescarte(LoggableMixin, NotificavelMixin)` herda de dois Mixins sem conflito de MRO, pois cada Mixin inicializa seus atributos através de métodos `__init_log__()` / `__init_notificacoes__()` chamados explicitamente.

### Padrões de Projeto

**Factory Pattern:** Criação centralizada de objetos através de 4 factories: `DispositivoFactory`, `UsuarioFactory`, `MetodoTratamentoFactory` e `PontoColetaFactory`.

**Strategy Pattern:** Diferentes estratégias de tratamento (`Reciclagem`, `Reuso`, `DescarteControlado`) com cálculos polimórficos de custo e impacto ambiental, qualquer `MetodoTratamento` é intercambiável.

**State Pattern:** Gerenciamento do ciclo de vida de solicitações com 7 estados e transições controladas que validam regras de negócio (ex.: não é possível avançar de `Cancelado`).

### Princípios SOLID

- **SRP:** Cada classe possui uma única responsabilidade bem definida.
- **OCP:** Novas subclasses (dispositivos, estados, tratamentos) podem ser adicionadas sem modificar código existente.
- **LSP:** Subclasses são substituíveis por suas classes base em todos os contextos (verificado por testes polimórficos).
- **DIP:** A camada de aplicação (`services.py`) depende da abstração `RepositorioBase` definida no domínio, ou seja, nunca importa diretamente a implementação `Dados` da infraestrutura. A classe `Dados(RepositorioBase)` na infraestrutura implementa o contrato.

### Testes

O projeto conta com **85 testes automatizados** cobrindo:

- Domínio: dispositivos, estados, tratamento, descarte, mixins
- Aplicação: factories, serviços
- Todos os testes passam com `pytest`

## Instalação e Execução

### Pré-requisitos

- Python 3.10 ou superior
- Poetry (gerenciador de dependências)

### Passos

```bash
git clone https://github.com/mathsNS/Ecotech.git
cd Ecotech
poetry install
poetry shell
```

### Executar a Aplicação

```bash
python run.py
```

A aplicação estará disponível em http://localhost:5000

### Executar Testes

```bash
pytest -v
```

## Tecnologias Utilizadas

- Python 3.10+
- Flask (framework web)
- Poetry (gerenciamento de dependências)
- Pytest (testes automatizados)