# EcoTech — análise de prontidão operacional

Data: 25/09/2026. Base: commit `e894b2a`, branch `main`.

**Escopo confirmado:** a entrega atual é demonstrativa. Seleção automática de planos, cobrança simulada e ausência de pagamento real são aceitáveis e **não são pendências da apresentação**. Os requisitos financeiros reais abaixo ficam registrados somente para uma futura operação de mercado.

## Parecer

O EcoTech tem um núcleo funcional expressivo e pode sustentar uma demonstração técnica controlada. Para a entrega atual, o principal trabalho é garantir jornadas completas, sessão correta entre perfis, dados coerentes e recuperação de erros. A futura abertura pública com coleta e remuneração exige uma etapa adicional de preparação operacional.

Não é necessário terminar toda a visão de economia circular para iniciar. É necessário delimitar o serviço, homologar os parceiros e fechar as lacunas de segurança, execução logística, dinheiro e comprovação da destinação.

| Marco | Avaliação | Condição para liberar |
|---|---|---|
| Apresentação acadêmica ou demonstração a parceiros | Viável em ambiente controlado | Roteiro ensaiado, dados fictícios, limitações explícitas e sessão mobile confiável |
| Piloto com usuários e parceiros reais | Ainda bloqueado | Segurança corrigida, operação assistida, parceiros homologados, comprovantes, suporte e infraestrutura recuperável |
| Oferta comercial aberta | Ainda bloqueada | Acrescentar cobrança/conciliação, contratos, gestão de equipes, aquisição e economia por coleta validada |

## Método e limites

Foram revisados domínio, serviços, persistência/migrações, rotas web e API, configuração de execução, telas/controllers/repositórios Flutter e testes. A documentação anterior foi usada como contexto, não como prova do estado atual.

Validação executada:

- Backend: **397 testes aprovados**, em 127,69 segundos.
- Flutter: **30 testes aprovados**.
- `flutter analyze --no-pub`: **nenhum problema encontrado**.
- Provas adicionais em banco temporário independente, descritas abaixo.

A análise mobile combina código e testes de widgets. Não foi realizada navegação exploratória completa em aparelho físico, homologação iOS, teste de acessibilidade com leitor de tela, ensaio de carga ou inspeção de infraestrutura remota. As imagens locais de referência não comprovam a renderização atual do aplicativo. Não foram movimentados valores, alterados dados do banco operacional nem modificadas funcionalidades.

Os itens marcados como risco de implementação decorrem da inspeção; não devem ser confundidos com incidentes observados em produção. Não foi verificada a existência de contratos, licenças ou procedimentos externos ao repositório.

## O que já existe e deve ser preservado

| Área | Implementação encontrada | Limite operacional |
|---|---|---|
| Identidade | Cadastro, login, hash de senha, JWT, sessão web, perfis | Ciclo de vida de acesso incompleto |
| Segurança básica | CSRF web, cookies configuráveis, segredos externos, autorização por solicitação | Desativação não revoga token já emitido |
| Solicitações | Entrega em ponto, coleta domiciliar, fotos, estimativa e aferição de peso | Recuperação de erros e cancelamento não expostos como jornada completa |
| Despacho | Bases, raio, categorias, capacidade, ranking, ofertas persistidas e aceite atômico | Agendador não provisionado no Compose; notificações externas ausentes |
| Comunicação | Chat privado, agenda negociada, notificações persistentes e leitura | Atualização por consulta periódica enquanto o app está aberto |
| Operação | Estados, avaliação, tratamento, histórico e finalização | Falta comprovação operacional e tratamento de exceções |
| Financeiro | Incentivo, pontos, saldo, pedido de saque e unicidade de alguns registros | Sem liquidação real e sem transação abrangente |
| B2B | Planos, relatórios, exportação CSV e PDF denominado MTR | Cobrança demonstrativa e comprovação regulatória não estabelecida |
| Administração | Usuários, preços, overrides e diagnóstico do despacho | Falta central de resolução operacional e financeira |
| Mobile | Jornadas cidadão/empresa/admin, navegação, estados de erro/vazio, fotos e compartilhamento | Sessão, publicação e uso em campo precisam de homologação |

Vários problemas do documento histórico já têm implementação: autorização por solicitação, despacho, aceite, agenda, chat, CSRF e leitura de notificações. Não devem ser recolocados no backlog como se estivessem totalmente ausentes.

## Prioridades da demonstração e requisitos futuros

Para a apresentação: priorizar P0-03 (sessão/cache), execução automática do despacho em P0-08, o roteiro ponta a ponta e a coerência dos relatórios. P0-02 merece correção se a gestão/desativação de usuários for demonstrada ou o ambiente for compartilhado. P0-09 se aplica ao artefato efetivamente distribuído; publicação em loja pode esperar.

Os demais itens de produção são exigências para abertura real, não impedimentos para uma demonstração isolada. O seed de exemplo é desejável na demo. Gateway, cobrança, pagamento e conciliação bancária ficam fora da prioridade atual por decisão do usuário.

### Mercado-01 — Separação entre contas de demonstração e produção

Evidência: `ecotech/infrastructure/web.py:160` chama `_inicializar_dados_exemplo`; a função em `:2013` verifica se existem usuários, mas não exige ambiente de demonstração.

**Reproduzido:** iniciar um banco vazio com `ECOTECH_ENV=production` e segredos próprios cria o seed; o login da conta administrativa de demonstração retorna HTTP 200.

Implantar comando explícito de seed restrito à demonstração, criação segura do primeiro administrador e verificação de que produção inicia sem usuários fictícios. Remover contas demo de qualquer implantação real existente, se houver.

### P0-02 — Desativação não encerra o acesso

Evidência: `ecotech/infrastructure/api.py:89` valida assinatura/expiração do JWT, sem consultar o estado atual do usuário. O logout mobile apenas apaga o token local.

**Reproduzido:** após desativação administrativa bem-sucedida, o token anterior do cidadão continuou recebendo HTTP 200 em dashboard, carteira e solicitações.

Implantar checagem de usuário ativo, mecanismo de revogação/versionamento de sessão, invalidação após troca de senha e tratamento central de 401 no app. Complementar com recuperação de senha, proteção contra tentativas repetidas e verificação de contato. MFA administrativo é recomendável antes de operação comercial.

### P0-03 — Troca de conta pode manter dados anteriores no app

Evidência: `mobile/lib/features/auth/auth_controller.dart:62` encerra autenticação sem invalidar os providers de dados. Carteira, solicitações e dashboard usam providers persistentes sem dependência da identidade autenticada; `main.dart` mantém um único `ProviderScope`.

**Risco identificado no código, não reproduzido em aparelho:** a conta B pode receber visualmente dados em cache da conta A após logout/login no mesmo processo. A autorização do servidor não elimina esse risco de exibição local.

Escopar o estado por sessão, limpar caches privados e proteger rotas por autenticação/perfil. Critério: alternar cidadão A → cidadão B → empresa no mesmo aparelho sem exibir nenhum dado da sessão anterior.

### Futuro financeiro — Plano pago é ativado sem pagamento (aceito na demonstração)

Evidência: `ecotech/infrastructure/api.py:2485`; catálogo em `ecotech/application/planos.py`.

**Reproduzido em modo produção:** `POST /api/v1/planos/alterar` aceita Enterprise diretamente, retornando HTTP 200 e o novo plano. O modo demonstrativo é informado no retorno, mas não restringe a operação a ambiente de demonstração.

**Nenhuma alteração de pagamento é necessária agora.** Manter a seleção automática para demonstrar os recursos dos planos. Quando houver piloto comercial, liberar planos por administrador mediante contrato/manual auditável ou implementar cobrança automática com assinatura, checkout, webhook autenticado, idempotência, renovação, inadimplência, cancelamento e conciliação. Rever benefícios comerciais prometidos: flags de recursos não comprovam entrega de relatórios automáticos, API B2B documentada ou suporte com SLA.

### Futuro financeiro — Saque e reserva de saldo para dinheiro real

Evidências: `ecotech/application/services.py:428`, `ecotech/infrastructure/persistence/dados.py:392` e `ecotech/infrastructure/api.py:2036`.

O saque salva valor/método/status pendente. Não há fluxo completo encontrado para destino Pix/conta, pagamento, falha, estorno e conciliação. O titular recebido na API é devolvido na resposta, mas não é persistido por `salvar_saque`.

Existe idempotência para a mesma chave; isso não impede dois pedidos distintos consumindo o mesmo saldo. A API lê o saldo antes e o serviço grava posteriormente, sem reserva atômica no banco.

**Prova controlada no serviço:** duas solicitações de R$ 80 com chaves diferentes, ambas usando a mesma leitura prévia de R$ 100 disponíveis, geraram R$ 160 em pedidos. Essa prova simula o intervalo entre leitura e gravação de duas requisições; não foi um ensaio concorrente HTTP.

Implantar livro de lançamentos, saldo disponível/reservado/liquidado, dinheiro em centavos ou Decimal, reserva transacional, destino validado e estados auditáveis. Pagamento manual é aceitável para um piloto pequeno se houver responsável, comprovante, reconciliação e tratamento de falha. Sem isso, desabilitar a promessa de saque real.

### Integridade — Finalização financeira não é uma única transação

Evidência: `_creditar_finalizacao` em `ecotech/infrastructure/api.py:918` e avanço em `:2597` aproximadamente; persistência em `dados.py:1467–1592`. Há lógica equivalente em `web.py`.

A mudança de estado, entrega, pontos, saldo empresarial e receita são feitas em etapas com commits separados. Há índices únicos para entrega/receita por solicitação, mas atualização de pontos/saldo não é protegida por um único lançamento de finalização.

**Risco de implementação:** falha entre etapas pode deixar solicitação encerrada sem todos os créditos; repetição em condições concorrentes pode aplicar parte dos efeitos novamente. Não foi realizada injeção de falhas nesta análise.

Criar um caso de uso compartilhado entre web/API que finalize estado e efeitos financeiros atomicamente, com chave única de origem e recuperação segura. Identificar a empresa beneficiária pela responsabilidade da operação; hoje a API usa a identidade do operador e a finalização pelo administrador não segue a mesma distribuição empresarial.

### Mercado-02 — Execução e persistência ainda exigem preparação para produção

`run.py` usa `app.run(debug=True, host='0.0.0.0')`; Docker executa esse arquivo. Compose monta o projeto inteiro e não provisiona scheduler, healthcheck ou backup.

`Dados` mantém uma conexão SQLite compartilhada com `check_same_thread=False`. `ServicoDescarte` mantém solicitações em memória; `listar_solicitacoes` só recarrega quando o cache está vazio. Isso cria risco de estado divergente entre processos e de concorrência na conexão. Simplesmente aumentar workers não resolve.

Implantar servidor de produção, HTTPS, configuração de segredos, conexões/transações adequadas, consultas consistentes ao banco, backup com restauração ensaiada, monitoramento e deploy reversível. SQLite não é, sozinho, motivo para impedir um piloto pequeno; o modelo atual de conexão/cache precisa ser corrigido. Avaliar PostgreSQL conforme concorrência e crescimento.

Adicionar limites de requisição/upload: `_validar_fotos` lê o conteúdo inteiro antes de aplicar o limite por foto e não foi encontrado limite global de corpo configurado na aplicação. Revisar também `.dockerignore` antes de `COPY . .` para excluir arquivos de configuração e material local sensível.

### P0-08 — Despacho depende de execução periódica externa

Existe o comando `processar-ofertas`, com regra de expiração implementada. Não foi encontrado agendador no Compose. Sem execução periódica, uma oferta ignorada não avança sozinha.

Provisionar job, medir última execução, alertar sobre atraso e testar reinício. A notificação atual é gravada no sistema; implementar push ou outro canal autorizado confiável para avisar a empresa com o app fechado. Para piloto assistido, um operador pode cobrir esse papel com procedimento e prazo definidos.

### P0-09 — Publicação mobile ainda não homologada

O release Android usa chave debug em `mobile/android/app/build.gradle.kts:35`. A permissão INTERNET está explícita em debug/profile e ausente do manifesto principal. Verificar o manifesto final mesclado do release e declarar a permissão no lugar correto; dependências podem afetar o manifesto final, que não foi compilado nesta análise.

O app exige HTTPS em release, o que é positivo, mas a URL padrão aponta para ambiente local. Preparar configuração de homologação/produção, assinatura própria, distribuição controlada e ensaio do artefato instalado. Validar iOS separadamente se fizer parte do lançamento.

## O que falta para o negócio operar

### 1. Delimitar cliente pagante e responsabilidades

O desenho atual combina cidadão que descarta, empresa operadora, assinatura B2B e comissão sobre valor avaliado. Ainda é necessário fechar em termos operacionais:

- Quem contrata e paga: coletor, reciclador, empresa geradora, entidade gestora ou patrocinador?
- A EcoTech intermedeia, opera transporte ou compra material?
- Quem recebe a propriedade do equipamento e assume responsabilidade pela guarda e pelos dados nele contidos?
- Quem paga a coleta quando o material tem pouco ou nenhum valor residual?
- Quais regiões, categorias e volumes mínimos são atendidos?
- Quando o cidadão passa a ter direito a crédito e como contesta uma avaliação?

Essas são decisões de negócio; o código não comprova que tenham sido definidas fora do repositório. A recomendação para o piloto é uma região delimitada, poucos parceiros homologados e um serviço claramente contratado.

### 2. Não confundir avaliação com dinheiro recebido

Na finalização, a API calcula crédito de 10% do valor avaliado para o cidadão, comissão de 8%/5%/2% conforme plano e o restante como saldo empresarial; Enterprise também pode gerar bônus em pontos. Não há ingresso financeiro externo encontrado que lastreie esses saldos.

Exemplo exclusivamente aritmético do código: em uma avaliação de R$ 100 no Free, R$ 10 viram incentivo, R$ 8 receita EcoTech e R$ 82 saldo da empresa. A operação ainda não comprova ter recebido R$ 100, nem deduz transporte, triagem, tratamento, taxas ou perdas.

Antes de ofertar remuneração, definir fonte de caixa, evento de liquidação, orçamento para incentivos e custo por coleta. Separar valor estimado, crédito aprovado, saldo pagável e receita recebida. Validar margem por categoria e distância; materiais com custo de destinação precisam de política própria.

### 3. Homologar parceiros e separar papéis

Validar dígitos de CNPJ não comprova capacidade operacional ou autorização ambiental. Criar onboarding de parceiro com documentos, responsável, escopo de atendimento, validade, aprovação e suspensão. A verificação pode começar manual, desde que registrada.

Distinguir gerador, ponto de recebimento, transportador e destinador. Hoje o papel empresa agrega atividades; no PDF transportador e destinador usam os mesmos dados empresariais. A cadeia real pode envolver organizações diferentes.

Empresas também precisam de usuários individuais e permissões para gestor, atendimento, coleta e triagem. Evitar senha compartilhada entre funcionários. No piloto muito pequeno, delimitar explicitamente um operador por parceiro.

### 4. Criar a jornada de exceções

O domínio possui cancelamento, mas não foi encontrada jornada completa correspondente nas rotas/telas revisadas. Falta tratar operacionalmente: nenhuma empresa aceita, empresa desiste após aceite, cidadão ausente, endereço errado, material recusado, peso divergente, equipamento diferente e disputa de avaliação.

Implantar cancelamento com motivo, reagendamento, reatribuição segura, liberação de capacidade, registro de tentativa e fila administrativa com responsável/prazo. O diagnóstico do despacho é útil, mas não substitui ações de recuperação.

Para a coleta real, registrar quem recebeu, quando, quantidade/peso e evidência simples de entrega. Pode ser confirmação bilateral ou comprovante; QR Code e GPS contínuo não são obrigatórios para o primeiro piloto.

### 5. Comprovar o destino, além de mudar o status

O sistema gera PDF próprio denominado MTR e calcula um percentual de destinação adequada a partir de estados/pesos. Isso não comprova emissão oficial de MTR, licença ou destinação efetiva.

O SINIR descreve MTR, CDF e DMR como documentos com funções próprias de rastreabilidade. A aplicabilidade concreta deve ser validada por operação, resíduo e UF. Não assumir que um PDF interno substitui documento exigível. [SINIR — sobre o sistema](https://sinir.gov.br/informacoes/sobre/), [MTR Nacional](https://www.sinir.gov.br/sistemas/mtr/).

Para o piloto, permitir anexar documento externo e registrar número, emissor, datas, transportador, destinador e vínculo ao lote/solicitação, quando aplicável. Integração automática pode vir depois. Identificar o PDF interno como comprovante interno/demonstrativo até validação apropriada.

### 6. Corrigir o significado das métricas ambientais

`dispositivos.py:158/172/186` calcula impacto por fatores fixos 5/15/8 multiplicados pelo peso. Não foi encontrada metodologia documentada que sustente apresentar esses números como CO₂ evitado auditado.

Em `api.py:2109`, destinação adequada é reciclado + reutilizado dividido pelo total, excluindo descartado. O estado sozinho não demonstra conformidade, e descarte controlado precisa de classificação e evidência próprias.

Versionar fatores e fontes, distinguir estimativa de resultado comprovado, usar peso aferido conforme a metodologia e armazenar data efetiva de processamento/destinação. Hoje o filtro de relatórios usa data de criação da solicitação, que pode distorcer a produção do mês.

### 7. Privacidade e segurança do material

Não foram encontrados fluxos completos de política de privacidade, atendimento a direitos do titular, exportação/exclusão/anonymização, retenção ou gestão de incidentes. Definir finalidade e base aplicável por tratamento, acesso a endereço/fotos/chat e procedimentos de atendimento. Não usar um aceite genérico como solução para todo tratamento.

A ANPD ressalta que flexibilizações para agentes pequenos não afastam direitos dos titulares nem medidas essenciais de segurança. [Resolução CD/ANPD nº 2](https://www.gov.br/anpd/pt-br/acesso-a-informacao/institucional/atos-normativos/regulamentacoes_anpd/resolucao-cd-anpd-no-2-de-27-de-janeiro-de-2022).

Equipamentos podem conter dados pessoais: informar ao cidadão sobre preparação do dispositivo e combinar com o parceiro política de guarda, reutilização, sanitização/destruição de dados e evidências. Definir também quais materiais perigosos ou avariados são aceitos e como são encaminhados.

### 8. Adaptar CNPJ ao formato alfanumérico

`services.py:22` exige somente dígitos. O cadastro/login e normalização precisam suportar CNPJ alfanumérico preservando compatibilidade com os antigos.

É uma necessidade atual: a Receita Federal informou a emissão do primeiro CNPJ alfanumérico em 31/07/2026. [Comunicado oficial](https://www.gov.br/receitafederal/pt-br/assuntos/noticias/2026/julho/receita-federal-gera-o-primeiro-cnpj-em-formato-alfanumerico).

## Interface mobile: ajustes com impacto na operação

| Jornada | Avaliação | Implantar ou validar |
|---|---|---|
| Entrada e sessão | Login por perfil e armazenamento seguro presentes | Recuperar senha, expiração coerente, limpar dados entre contas, impedir acesso por rota incompatível |
| Cadastro de empresa | Cadastro básico presente | Homologação antes de receber coletas, documentos e contato verificado |
| Nova solicitação | Fluxo em etapas, fotos, endereço e agenda | Rascunho, recuperação de envio, idempotência na criação e mensagem clara de estimativa/aceitação |
| Localização | CEP resolve endereço/coordenadas | Confirmação do endereço exato, alternativa quando CEP não tem coordenadas e orientação ao coletor |
| Pontos de coleta | Lista, endereço e capacidade | Busca por região, horários/categorias e abrir rota em aplicativo de mapas; mapa embutido pode esperar |
| Acompanhamento | Estados e detalhes presentes | Próxima ação, prazo esperado, contato de suporte e saída para coleta sem parceiro |
| Oportunidades | Lista e aceite presentes | Aviso com app fechado, validade clara, prevenção de ação em oferta vencida |
| Agenda/chat | Negociação e polling implementados | Notificação externa, retentativa sem duplicar mensagem e tratamento de rede fraca |
| Coleta/processamento | Peso, avaliação e transições | Confirmação de ação irreversível, prova de recebimento e divergência de material/peso |
| Carteira | Saldo/pedido/recibo presentes; recibo informa pendência | Destino do pagamento, status real, falha/estorno, extrato explicável e canal de contestação |
| Relatórios | Filtros, métricas e exportações | Terminologia ambiental verificável; não apresentar percentual como certificação PNRS |
| Planos | Comparação e mudança presentes | Manter seleção automática na demo; identificar benefícios implementados e futuros |
| Administração | Gestão e diagnóstico presentes | Fila de pendências com ações, responsáveis, prazos e auditoria |

A arquitetura visual já dispõe de componentes compartilhados e tratamentos de carregamento/erro/vazio, mas a identidade ainda precisa ser padronizada. Por orientação do usuário, essa padronização faz parte das prioridades da apresentação, junto ao fechamento das jornadas.

### Padronização da identidade visual mobile — prioridade da apresentação

A inspeção confirmou três fontes de estilo que precisam convergir: tema global em `core/theme/app_theme.dart` e `app_colors.dart`, estilos próprios dos dashboards e estilos próprios de `features/operations/operations_widgets.dart`.

Exemplos concretos: o tema define cards com raio 12 e botões com raio 6, enquanto operações usa cards com raio 20 e ações com raio 11. Fundo, verde principal e texto secundário têm valores distintos entre dashboard, operações e tema. Há tamanhos de texto definidos diretamente nas telas, inclusive textos de 9–11 pontos a revisar quanto à legibilidade. Cidadão e empresa duplicam componentes de erro/vazio, com iconografia diferente. Diferenças podem ser intencionais, mas precisam virar variantes explícitas e coerentes.

Direção inicial: consolidar a linguagem das telas recentes de dashboard e operações — fonte Inter, verdes da marca, fundos claros, cards brancos, hierarquia legível e bordas arredondadas — em componentes compartilhados. Preservar distinções funcionais entre perfis usando a mesma linguagem visual.

| Frente | Padronização necessária | Critério de aceite |
|---|---|---|
| Cores | Marca, fundos, superfícies, bordas, texto e estados semânticos | Mesmo significado usa a mesma cor em todos os perfis |
| Tipografia | Título de página, seção, corpo, legenda e números | Hierarquia definida no tema; legibilidade com fonte ampliada |
| Espaçamento | Margens de página, distância entre seções e padding dos cards | Telas equivalentes seguem a mesma escala |
| Cards | Bordas, raios, sombras e variantes de métricas/listagem/destaque | Variações têm função definida, sem estilos independentes por tela |
| Botões e campos | Primário, secundário, destrutivo, desabilitado e carregando | Mesma ação tem aparência e comportamento equivalentes |
| Cabeçalhos e navegação | Logo, título, voltar, avatar, notificações e seleção inferior | Padrão consistente por nível de navegação, sem perder contexto |
| Ícones e status | Família visual, tamanho, espessura e badges | Estados têm texto e semântica consistente, sem depender só da cor |
| Feedback | Erro, vazio, carregamento, sucesso, diálogos e avisos | Componentes compartilhados e mensagens acionáveis |

Ordem de aplicação: tema e componentes → dashboards/operações de referência → solicitações/detalhes → agenda/chat/notificações → carteira/relatórios/planos → perfil/cadastro/login/administração. Incluir telas secundárias e diálogos; a identidade não pode terminar no dashboard.

Entrega esperada: catálogo visual dos componentes e estados, migração das telas para esses componentes e revisão comparativa em celular. Validar navegação e regras existentes após a migração. Este relatório define o trabalho; a interface ainda não foi alterada nesta análise.

Homologação visual ainda necessária: Android real, diferentes larguras, fonte ampliada, teclado aberto, listas longas, textos extensos, contraste, alvos de toque e leitor de tela. Ensaiar rede lenta, perda de conexão durante envio, token expirado, retorno do segundo plano e troca de conta. Testes de widgets aprovados não substituem essa validação.

## Sequência recomendada para a entrega atual

1. Corrigir isolamento entre sessões/contas e validar navegação por perfil.
2. Padronizar a identidade visual do mobile pelo tema e componentes compartilhados; ensaiar criação → oferta → aceite → agenda/chat → recebimento/peso → tratamento → histórico/relatório nos dois lados.
3. Garantir execução periódica do despacho na demonstração e dados suficientes para ilustrar expiração/recusa.
4. Tornar visíveis cancelamento, falta de parceiro, reagendamento e divergência, conforme o escopo apresentado; distinguir o que ainda é evolução planejada.
5. Revisar rótulos de impacto, PNRS, valor estimado e estado de saque; preservar a simulação de planos e pagamentos.
6. Validar o aplicativo no aparelho/build que será usado, incluindo teclado, rede, troca de conta e retorno às telas.
7. Preparar roteiro reproduzível e dataset fictício consistente.

## Sequência futura para operação real

| Ordem | Entrega | Critério de conclusão |
|---|---|---|
| 1 | Separar demo e produção; corrigir acesso e sessão | Banco de produção sem seed; conta desativada perde acesso; troca de conta sem dados antigos |
| 2 | Fechar escopo comercial e financeiro do piloto | Responsáveis, região, parceiros, categorias, preço/custo e fonte dos incentivos documentados |
| 3 | Garantir integridade | Dois saques não ultrapassam saldo; repetição/falha de finalização não duplica nem perde crédito; web/API convergem |
| 4 | Fechar execução e exceções | Oferta expira automaticamente; há aviso externo; coleta frustrada tem cancelamento/reagendamento/atendimento |
| 5 | Comprovar coleta e destinação | Recebimento com evidência; cadeia de responsáveis; documentos externos vinculados quando exigíveis |
| 6 | Preparar ambiente e app | HTTPS, release assinado/configurado, backup restaurado, monitoramento e procedimento de incidente |
| 7 | Operar piloto assistido | Todas as solicitações acompanhadas, diferenças conciliadas e indicadores revisados antes de expandir |
| 8 | Automatizar oferta comercial | Cobrança/pagamento integrados, equipes/permissões, contratos e suporte sustentáveis |

Esses marcos são dependências, não estimativas de prazo. Dimensionar esforço após decidir se o piloto terá dinheiro real, qual UF/região atenderá e qual parceiro executará cada etapa.

## Roteiro mínimo antes de apresentar

1. Criar cidadão e empresa em demonstração, com base/ponto e dados coerentes.
2. Criar solicitação pelo mobile e localizar a operação no painel da empresa.
3. Aceitar, negociar agenda e enviar mensagem entre as duas contas.
4. Registrar recebimento, aferir peso, avaliar e finalizar.
5. Mostrar histórico, relatório e incentivo como demonstração, distinguindo pedido de saque de pagamento.
6. Demonstrar falta de parceiro ou recusa, explicando o tratamento disponível e o que falta.
7. Alternar contas no mesmo aparelho; confirmar ausência de cache privado anterior.
8. Usar dados fictícios, ambiente isolado e documentação ambiental corretamente rotulada.

## Critérios para iniciar o piloto com dados reais

- [ ] Nenhum P0 aplicável ao escopo aberto permanece sem correção ou desativação efetiva da função.
- [ ] Parceiros, responsabilidades, região e categorias aprovados.
- [ ] Um responsável acompanha pendências e atende o cidadão.
- [ ] Regras de avaliação, crédito, cancelamento e reclamação informadas.
- [ ] Credenciais individuais; revogação e troca de conta testadas.
- [ ] Despacho periódico e aviso à empresa funcionando com app fechado.
- [ ] Recebimento e destino demonstráveis; documentos aplicáveis vinculados.
- [ ] Financeiro desabilitado ou integralmente conciliável, inclusive falhas e reservas.
- [ ] Termos, privacidade, retenção e canal de atendimento definidos.
- [ ] Backup restaurado com sucesso e indisponibilidade simulada.
- [ ] App instalado em aparelho real com HTTPS e build de distribuição.
- [ ] Métricas acompanhadas: aceite, coleta no prazo, ausência, cancelamento, custo/coleta, margem, destino comprovado e erro técnico.

## O que pode esperar

Marketplace nacional, GPS contínuo, roteirização otimizada, gamificação avançada, catálogo de recompensas, analytics sofisticado e integrações automáticas com todos os parceiros. A comprovação e o atendimento precisam existir; sua automação completa pode ser gradual.

Recomendação de posicionamento inicial: apresentar o EcoTech como plataforma de gestão e intermediação de descarte com rastreabilidade operacional em evolução. Abrir um piloto regional assistido após corrigir os bloqueios, e validar a economia real antes de prometer recompensa universal, conformidade automática ou atendimento amplo.
