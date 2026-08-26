# aprendizado_ia

Centraliza o que um modelo de IA precisa: dados limpos, corpora SFT, LoRAs,
adapters, receitas de treino e os documentos de origem.

## Estrutura

| pasta | o que guarda |
|---|---|
| `dados_premium/` | fonte limpa e curada: PDFs, markdown, planilhas, corpora brutos já tratados |
| `destilados/` | o que saiu do dado: corpora SFT, receitas de treino, LoRAs e adapters |

Um workspace por assunto dentro de `destilados/`, cada um autocontido:

```
destilados/<assunto>-lora-distillation/
  README.md      o que e, de onde veio, qual a receita
  scripts/       preparo do corpus e inspecao do adapter
  dataset/       train/validation/test.jsonl + manifest.json com sha256
  training/      receita reproduzivel
  artifacts/     adapter treinado + checksums
```

### Já aqui

- `destilados/aprendizados-tecnicos-lora-distillation` - 437 lições do repo
  público [`MaxxArtes/aprendizados-tecnicos`](https://github.com/MaxxArtes/aprendizados-tecnicos)
  destiladas em 811 exemplos SFT, prontas para QLoRA sobre Llama-3.2-3B.

## Arquivos grandes: Git LFS

Peso de modelo, adapter, PDF e parquet vão por **Git LFS** - ver
`.gitattributes`. Sem isso o GitHub recusa qualquer arquivo acima de 100 MB, e
cada versão antiga do peso continuaria dentro do clone para sempre.

Antes do primeiro clone ou push nesta máquina:

```bash
git lfs install
```

Clonar depois:

```bash
git clone https://github.com/MaxxArtes/aprendizado_ia.git
git lfs pull
```

A conta gratuita do GitHub dá **1 GB de armazenamento LFS e 1 GB de tráfego por
mês**. Um adapter LoRA cabe folgado; um modelo base completo, não. Peso de base
não se versiona - se baixa.

## Convenções

- Todo dataset gerado por script vem com `manifest.json`: contagem por split,
  sha256 de cada arquivo e a semente usada. O script de treino confere o
  checksum e recusa rodar se não bater.
- Split de dataset agrupa pela unidade que gerou os exemplos, não por linha.
  Linhas derivadas da mesma fonte compartilham texto e vazariam a resposta do
  treino para o teste.
- Tokenizer é salvo junto do adapter. Separado, o checkpoint vira lixo ilegível.
- Segredos via Doppler. Nada de `.env` versionado.

## Licenciamento do conteúdo

Este repositório é **público**. Só entra em `dados_premium/` material que pode
ser redistribuído: obra própria, domínio público ou licença que permita.
Material licenciado para uso pessoal, corpus de cliente e dado proprietário não
entram - publicar aqui é redistribuir.
