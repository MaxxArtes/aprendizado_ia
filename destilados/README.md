# destilados

O que saiu do dado: corpora SFT, receitas de treino, LoRAs e adapters.

Um workspace por assunto, autocontido, no formato:

```
<assunto>-lora-distillation/
  README.md      o que e, de onde veio, a receita e os numeros
  scripts/       preparo do corpus e inspecao do adapter
  dataset/       train/validation/test.jsonl + manifest.json com sha256
  training/      receita reproduzivel
  artifacts/     adapter treinado + checksums
```

## Workspaces

| workspace | fonte | exemplos | estado |
|---|---|---|---|
| `aprendizados-tecnicos-lora-distillation` | [`MaxxArtes/aprendizados-tecnicos`](https://github.com/MaxxArtes/aprendizados-tecnicos) (público) | 811 | corpus pronto, treino ainda não rodado |

## Regras

- `manifest.json` é obrigatório: contagem por split, sha256 de cada arquivo e a
  semente. O script de treino confere o checksum e recusa rodar se não bater.
- O campo `method` do manifesto identifica o corpus. Dois workspaces montados na
  mesma sessão de treino precisam de `method` diferente, senão o job não sabe
  qual carregar.
- Split agrupa pela unidade que gerou os exemplos (lição, documento, commit),
  nunca por linha solta.
- Adapter entra via LFS. Checkpoint intermediário não entra - está no
  `.gitignore`.
