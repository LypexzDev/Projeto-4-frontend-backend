# Contribuindo com o LojaControl

Obrigado por contribuir.

## Fluxo recomendado

1. Faça um fork do repositório.
2. Crie uma branch com nome descritivo:
   - `feat/nome-da-feature`
   - `fix/nome-do-bug`
3. Rode os testes localmente:
   - `pytest`
4. Abra uma Pull Request usando o template.

## Padrões

- Python com tipagem e estilo PEP8.
- Mantenha rotas finas e regras de negócio em `services/`.
- Toda feature relevante deve incluir teste.
- Atualize README/docs quando mudar comportamento.

## Commits

Prefira mensagens objetivas:

- `feat: add refresh token rotation`
- `fix: validate product price range`
- `docs: update docker setup`
