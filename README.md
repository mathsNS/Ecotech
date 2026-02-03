# EcoTech - Sistema de Gerenciamento de Descarte de Lixo Eletrônico

## Sobre o Projeto

O EcoTech é um sistema de gerenciamento de descarte de lixo eletrônico que facilita a coleta, tratamento e reciclagem de dispositivos eletrônicos. A plataforma conecta cidadãos e empresas a pontos de coleta especializados, garantindo o descarte ambientalmente responsável.

### Equipe de Desenvolvimento

- Abner Levi - [@abnerlevi](https://github.com/abnerlevi)
- Maria Antônia - [@mariastrajano](https://github.com/mariastrajano)
- Matheus Nogueira - [@mathNS](https://github.com/mathNS)

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

O projeto utiliza uma arquitetura em camadas que separa responsabilidades:

```
ecotech/
├── domain/              # Regras de negócio e entidades
│   ├── usuarios.py
│   ├── dispositivos.py
│   ├── estados.py
│   ├── tratamento.py
│   ├── descarte.py
│   └── relatorio.py
├── application/         # Lógica de aplicação
│   ├── factories.py
│   └── services.py
└── infrastructure/      # Camada de infraestrutura
    ├── web.py
    ├── templates/
    └── static/
```

## Tecnologias e Conceitos

### Design Orientado a Objetos

**Encapsulamento:** Todos os atributos das classes são privados com acesso controlado através de properties, garantindo validação e integridade dos dados.

**Hierarquias Implementadas:**

Usuários:
- Usuario (classe abstrata base)
- Cidadao, Empresa, Administrador (implementações concretas)

Dispositivos Eletrônicos:
- DispositivoEletronico (classe abstrata)
- Celular, Computador, Eletrodomestico (tipos específicos)

Estados de Solicitação:
- EstadoDescarte (classe abstrata)
- Solicitado, Coletado, EmProcessamento, Reciclado, Reutilizado, Descartado, Cancelado

Métodos de Tratamento:
- MetodoTratamento (classe abstrata)
- Reciclagem, Reuso, DescarteControlado

### Padrões de Projeto

**Factory Pattern:** Criação centralizada de objetos através de factories específicas para dispositivos, usuários e métodos de tratamento.

**Strategy Pattern:** Diferentes estratégias de tratamento de resíduos eletrônicos com cálculos específicos de custo e impacto ambiental.

**State Pattern:** Gerenciamento do ciclo de vida de solicitações de descarte com transições controladas entre estados.

### Princípios SOLID

O sistema foi projetado seguindo os princípios SOLID:

- **SRP:** Cada classe possui uma única responsabilidade bem definida
- **OCP:** Extensível para novos tipos sem modificar código existente
- **LSP:** Subclasses substituíveis por suas classes base
- **DIP:** Dependência de abstrações, não de implementações concretas
- Qualquer `MetodoTratamento` é intercambiável

#### Dependency Inversion Principle (DIP)
- Camadas superiores dependem de abstrações
- Serviços dependem de interfaces, não de implementações concretas
- Uso de injeção de dependências

## Instalação e Execução

### Pré-requisitos

## Instalação

### Pré-requisitos

- Python 3.10 ou superior
- Poetry (gerenciador de dependências)

### Passos

```bash
git clone https://github.com/abnerlevi/ecotech.git
cd ecotech
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
pytest
pytest --cov=ecotech
```

## Tecnologias Utilizadas

- Python 3.10+
- Flask (framework web)
- Poetry (gerenciamento de dependências)
- Pytest (testes automatizados)
