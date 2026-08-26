# Aprendizados-tecnicos LoRA

Destilacao supervisionada do repositorio publico
[`MaxxArtes/aprendizados-tecnicos`](https://github.com/MaxxArtes/aprendizados-tecnicos)
em um adaptador LoRA: 437 licoes viram 811 exemplos SFT e, depois do treino,
pares de matrizes `(lora_A, lora_B)` em `adapter_model.safetensors`.

Mesma receita do `etl-lora-distillation` (QLoRA sobre
`unsloth/Llama-3.2-3B-Instruct`, seed 42, Kaggle). O que muda e a fonte: la sao
correcoes humanas mineradas do historico Git; aqui sao licoes ja curadas, com
sintoma, causa, regra e verificacao.

## O que "converter em binario" quer dizer aqui

O adaptador nao guarda um peso novo. Para cada projecao alvo ele guarda duas
matrizes finas, e o peso base fica intacto:

    dW = (alpha / r) * B @ A         A e r x entrada,  B e saida x r

Com `r = 16` sobre `q,k,v,o,gate,up,down` das 28 camadas do Llama-3.2-3B, sao
196 pares de matrizes. `scripts/inspect_adapter.py` abre o `.safetensors` e
lista par a par, sem precisar de torch instalado.

## Limites de seguranca

- A fonte e publica, entao nao ha corpus privado a proteger aqui.
- Ainda assim o builder recusa escrever se encontrar string com forma de
  credencial real (`sk-`, `ghp_`, `AKIA`, JWT, `user:senha@host`). O corpus fala
  de segredos o tempo todo; o filtro procura formato, nao a palavra.
- `artifacts/` guarda o adaptador e os checksums. Pesos treinados nao entram em
  commit sem revisao.

## Estrutura

- `scripts/build_distillation_dataset.py`: markdown -> splits SFT + manifesto.
- `scripts/inspect_adapter.py`: leitor de `.safetensors` que mostra os pares.
- `dataset/`: `train/validation/test.jsonl` e `manifest.json` com sha256.
- `training/train_adapter.py`: job QLoRA reproduzivel para Kaggle.
- `artifacts/`: adaptador PEFT/LoRA validado e checksums.

## Corpus

| split | exemplos | licoes | fatia |
|---|---|---|---|
| train | 681 | 372 | 84.0% |
| validation | 64 | 29 | 7.9% |
| test | 66 | 36 | 8.1% |

Quatro tarefas, derivadas do formato fixo de cada licao:

| tarefa | exemplos | pergunta que treina |
|---|---|---|
| `licao` | 308 | "me explique isto, com exemplo concreto" |
| `diagnostico` | 281 | cola o sintoma, recebe causa + regra + verificacao |
| `glossario` | 129 | "o que quer dizer X" |
| `verificacao` | 93 | "como eu confirmo, na pratica" |

O split agrupa por licao. As tres linhas geradas de uma mesma licao compartilham
quase todo o texto: separa-las ao acaso vazaria a resposta do treino para o
teste e a perda de validacao nao significaria nada. Nenhuma licao aparece em
dois splits - `train ∩ test = 0`.

## Como rodar

Gerar o corpus a partir de um checkout da fonte:

```bash
git clone --depth 1 https://github.com/MaxxArtes/aprendizados-tecnicos.git /tmp/at
python scripts/build_distillation_dataset.py --source /tmp/at --out dataset
```

Treinar no Kaggle (GPU T4 ou P100): suba `dataset/` como um Dataset privado e
rode `training/train_adapter.py` como notebook/script. O job localiza o corpus
por `manifest.json`, confere o sha256 de cada split e recusa rodar se algum nao
bater. O campo `method` do manifesto e o que separa este corpus do da etl-company
quando os dois estao montados na mesma sessao.

Saida em `/kaggle/working/adapter/`: `adapter_model.safetensors`,
`adapter_config.json`, o tokenizer e `training_report.json` com perda base
versus perda do adaptador.

Inspecionar o resultado:

```bash
python scripts/inspect_adapter.py artifacts/adapter_model.safetensors --delta 5
```

## Receita

| parametro | valor | por que |
|---|---|---|
| base | `unsloth/Llama-3.2-3B-Instruct` | mesma do outro corpus |
| quantizacao | NF4 double-quant, compute fp16 | cabe na T4 do Kaggle |
| `r` / `alpha` | 16 / 32 | escala 2.0, igual a receita validada |
| dropout | 0.05 | |
| alvos | `q,k,v,o,gate,up,down` | |
| seq maxima | 2048 tokens | o maior exemplo tem ~900 |
| batch efetivo | 8 (1 x 8 acumulacao) | |
| lr / schedule | 1e-4, cosine, warmup 3% | |
| epocas | 3 | 681 exemplos, corpus 2.7x menor que o da etl-company. A licao "Dado raro repetido: aprende ate ~3 epocas, memoriza aos ~5" fixa o teto |

A perda so conta os tokens da resposta do assistente; system e pergunta entram
como contexto, nao como alvo. O tokenizer e salvo junto do adaptador - separado,
o checkpoint vira lixo ilegivel.
