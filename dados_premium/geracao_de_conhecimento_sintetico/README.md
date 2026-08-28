# Geração de conhecimento sintético

Corpus premium fundamentado em Markdown técnico limpo e licenciado. A geração é local,
determinística e extrativa: os textos de resposta vêm dos campos estruturados da fonte;
nenhum modelo externo ou fato adicional é usado.

## Conteúdo

- `dataset/premium_grounded.jsonl`: 387 registros com ID, tarefa e proveniência.
- `dataset/premium_sft.jsonl`: os mesmos 387 pares no schema exato `instruction/output`.
- `source_inventory.json`: lista positiva de fontes e exclusões justificadas.
- `quality_report.json`: métricas e validações.
- `manifest.json`: hashes SHA-256, tamanhos e contagens.
- `SECURITY_NOTICE.md`: risco encontrado nas fontes que ficaram fora do corpus.

Não concatene os dois JSONL: eles representam os mesmos pares em schemas diferentes.

## Distribuição

| tarefa | registros |
|---|---:|
| diagnóstico operacional | 134 |
| diretriz de execução | 124 |
| conceito técnico | 129 |
| **total** | **387** |

## Critérios aplicados

- Proveniência por arquivo, seção, licença e hash.
- Localizadores usam linhas inicial e final inclusivas; o hash de evidência cobre exatamente esse intervalo.
- Grounding por composição de `Sintoma`, `Causa`, `Regra` e `Como verificar`.
- Unicode NFC, UTF-8 sem BOM e finais de linha LF.
- IDs, instruções e pares únicos.
- Lista positiva de fontes; notas pessoais e manuais pendentes foram excluídos.
- Bloqueio de segredos, credenciais em URL, e-mails e raciocínio oculto.
- Bloqueio de aberturas formulaicas como “Claro!”, “Certamente!” e “Ótima pergunta”.
- Variação determinística de prompts e estruturas de resposta.
- Piso de cobertura do parser e snapshot de 308 seções/129 verbetes para detectar regressões.

## Limites conhecidos

- A auditoria comprova correspondência com as fontes, não atualização factual externa.
- Comandos e afirmações dependentes de versão herdam a data e o contexto do material original.
- Termos categóricos presentes nas regras técnicas foram preservados como evidência de origem;
  o gerador não acrescenta bordões nem intensificadores.
- Uma divisão treino/validação/teste deve ser feita por arquivo-fonte ou cluster semântico,
  nunca sorteando linhas isoladas.

## Reprodução

```powershell
python scripts/generate_dataset.py
python scripts/audit_dataset.py
```

Os scripts não fazem chamadas de rede e não escrevem fora desta pasta.
