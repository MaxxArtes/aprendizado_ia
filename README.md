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

### Datasets Prontos (`destilados/`)

O repositório já conta com **10 lotes de dados purificados** (em `.jsonl`) prontos para treinamento (Supervised Fine-Tuning).
Estes dados passaram por uma rigorosa **esteira de curadoria e reescrita utilizando o modelo DeepSeek**, garantindo que:
1. **Zero Contaminação de IA:** Não há jargões de assistentes virtuais ("Como modelo de linguagem...", "Aqui está...", etc).
2. **Zero Contexto Fantasma:** As respostas não citam referências externas que o modelo final não terá acesso (ex: "Segundo o texto fornecido...").
3. **Padrão Ouro Técnico:** Respostas técnicas seguem estritamente a taxonomia **Causa -> Regra -> Verificação**.
4. **Naturalidade:** Datasets comportamentais e do cotidiano brasileiro são diretos, coloquiais e humanos.

**Lotes disponíveis:**
- `dataset_00_cofre_v1.jsonl` - 1.195 pares resgatados de documentação privada (anonimizados).
- `dataset_01_recusa_diagnostico.jsonl` - 500 pares de comportamento para recusa educada de diagnósticos médicos/legais.
- `dataset_02_cotidiano_br.jsonl` - 502 pares de conversação casual, com gírias e rotina tipicamente brasileira.
- `dataset_03_instrucao_seguida.jsonl` - 500 pares de respostas cirúrgicas a comandos diretos.
- `dataset_04_dialogo_memoria.jsonl` - 504 pares simulando retenção de contexto.
- `dataset_05_docs_tecnicos_lote_1.jsonl` - 324 pares técnicos curados.
- `dataset_06_docs_tecnicos_lote_2.jsonl` - 235 pares técnicos curados.
- `dataset_07_diversos.jsonl` - 20 pares extras variados.
- `dataset_08_lora_antigo_train.jsonl` / `dataset_09...test` / `dataset_10...val` - 811 pares técnicos clássicos reescritos e modernizados.

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

## Licença

Este projeto é disponibilizado sob a licença **MIT** (veja o arquivo `LICENSE`).

Isso significa que pesquisadores, estudantes e desenvolvedores podem clonar, modificar, 
distribuir e usar este dataset livremente para treinar modelos (inclusive comerciais), 
bastando manter os créditos do autor original.
A ideia é ser uma contribuição de qualidade, estruturada e limpa para a comunidade open-source.
