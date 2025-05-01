# Prompt para VSCode Copilot Agent

**Objetivo:**  
Melhorar performance, segurança, qualidade de código e cobertura de testes do projeto Django conforme recomendações de auditoria.

---

## 1. Performance

1. **List views e paginação**  
   - Identifique todas as views que fazem `Model.objects.all()` sem paginação.  
   - Substitua por uso de `django.core.paginator.Paginator` para limitar resultados a 20–50 itens por página.  
2. **Otimização de consultas ORM**  
   - Em cada view, aplique `select_related()` para campos ForeignKey e `prefetch_related()` para relações many-to-many ou reversas.  
   - Remova chamadas redundantes a `Room.objects.all()` nos contextos de listagem ou mova-as para cache em Redis.  
3. **Limpeza de arquivos gerados**  
   - Crie um comando customizado (`management/commands/cleanup_reports.py`) que delete relatórios em `media/reports/` com mais de 30 dias.

---

## 2. Segurança

1. **Proteção de acesso**  
   - Adicione `@login_required` (ou mixins de login) em todas as views de CRUD e dashboards.  
   - Para a API, garanta autenticação via tokens JWT ou DRF TokenAuthentication.  
2. **Validação de input**  
   - Substitua filtros diretos em views por uso de `Django Forms` ou `Serializers` (no caso de API) para validar `date`, `status`, `guest`.  
3. **Middlewares essenciais**  
   - Confirme que `CsrfViewMiddleware` e `XFrameOptionsMiddleware` estão ativos em `settings.py`.

---

## 3. Qualidade de Código

1. **Configuração de linters e formatadores**  
   - Adicione `.pre-commit-config.yaml` com hooks para:  
     - `black --line-length 88`  
     - `flake8`  
     - `isort`  
2. **Refatoração e organização**  
   - Extraia lógica complexa (cálculo de receita, filtros avançados) para módulos em `apps/<nome>/services.py`.  
   - Simplifique funções com alta complexidade ciclomática (>10) decompondo-as em helpers.  
3. **Type hints e docstrings**  
   - Insira type hints em todas as funções públicas e modele docstrings Google-style para classes e métodos de apps principais.

---

## 4. Testes e CI

1. **Aumentar cobertura de testes**  
   - Escreva testes unitários para fluxos críticos: geração de relatórios, filtros de reservas, endpoints da API.  
   - Configure no `pytest.ini` `--cov-fail-under=80`.  
2. **GitHub Actions**  
   - Crie `.github/workflows/ci.yml` com jobs:  
     - `Lint & Format` (black, flake8, isort)  
     - `Test & Coverage` (pytest + coverage)  
     - `Safety` (checagem de vulnerabilidades em dependências)

---

## 5. Monitoramento e Produção

1. **Sentry**  
   - Instale e configure `sentry-sdk` em `settings_prod.py` para capturar exceções e performance.  
2. **Static & Cache**  
   - Garanta `STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"`.  
   - Configure `django-redis` como backend de cache em produção (`CACHES` no settings).

---

### Critérios de Sucesso

- Todas as views paginadas passam nos testes de integração.  
- `flake8` e `isort --check` retornam status zero.  
- Cobertura de testes ≥ 80% e CI “green.”  
- Gestão de relatórios antigos acionada via comando Django.  
- Sentry ativo em ambiente de produção.

> **Ação do Agent:**  
> Siga cada item acima, commit a commit, validando em ambiente local e CI até atingir todos os critérios.  

