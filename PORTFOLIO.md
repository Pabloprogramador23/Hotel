# Hotel HMS – Sistema de Gestão Hoteleira de Alta Performance

> **Stack Tecnológico**: Django 5.2 • HTMX • Docker • PostgreSQL • TailwindCSS (via CDN/Custom)

![Dashboard do Sistema](hotel_media/screenshots/dashboard.png)

## 🚀 Sobre o Projeto
O **Hotel HMS** é uma solução robusta e moderna operando no setor de **Hotelaria**. Desenvolvida para simplificar a operação hoteleira, superando sistemas legados em **agilidade** e **experiência do usuário (UX)**.

A aplicação entrega uma sensação de SPA (Single Page Application) sem a complexidade de frameworks JavaScript pesados, graças ao uso estratégico de **HTMX/Hyperscript**.

## 💡 Diferenciais Técnicos
*   **Interatividade Real-Time**: Status dos quartos atualizado instantaneamente sem recarregar a página.
*   **Performance First**: Queries otimizadas com `select_related` e `prefetch_related` para evitar problemas de N+1.
*   **Segurança Enterprise**: Proteção CSRF, XSS e gestão de sessões robusta nativa do Django.
*   **Gestão Financeira**: Log de transações imutável (Ledger) para auditoria completa.

## 🛠️ Detalhes da Implementação

### 1. Core: Reservas & Recepção
O módulo de reservas gerencia o ciclo de vida completo: `Pendente -> Check-in -> Ocupado -> Checkout -> Financeiro`.
*   **Lógica de Negócio Robusta**: Validadores customizados em `models.py` impedem estados inválidos (ex: check-in em quarto sujo).
*   **Automação**: O status do quarto reflete automaticamente as ações da recepção.

### 2. Módulo Financeiro
![Financeiro](hotel_media/screenshots/finance.png)
Painel administrativo para visão clara do fluxo de caixa.
*   **Features**: Balanço Mensal, Gestão de Despesas Operacionais, Receitas Extras (Frigobar, Serviços).
*   **Tech**: Aggregation Functions do Django ORM para cálculos on-the-fly.

### 3. Qualidade de Código & Infraestrutura
*   **Docker Compose**: Setup de ambiente reprodutível em segundos.
*   **Type Hinting**: Aplicação 100% tipada para reduzir bugs em tempo de execução.
*   **CI/CD Ready**: Estrutura pronta para pipelines de integração contínua.

---

### 👨‍💻 Por que me contratar?
Este projeto demonstra minha capacidade de entregar **software de valor**: focado no problema do cliente, bem arquitetado e tecnicamente sólido.

[🔗 Link para o Repositório GitHub](#) • [🔗 Meu LinkedIn](#)
