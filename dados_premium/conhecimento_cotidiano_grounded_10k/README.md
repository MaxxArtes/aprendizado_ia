# Conhecimento cotidiano grounded

Corpus local de QA extrativo em português do Brasil, criado apenas de snapshots
oficiais preservados em sources/raw. Não houve chamada a API nem uso de modelo
na geração.

## Conteúdo

- Pares: 10000
- Passagens processadas: 1111
- Consumidor: 4777
- Saúde: 5223
- Splits: train=9011, validation=513, test=476

premium_grounded_10k.jsonl mantém contexto, offsets e proveniência completos.
premium_sft_10k.jsonl e os três splits contêm somente instruction e output.
Cada output é uma substring literal contínua do contexto, confirmada pelos
offsets answer_start e answer_end. O agrupamento por fonte e localizador impede
que uma mesma unidade documental apareça em mais de um split.

## Reprodução

1. Execute scripts/fetch_sources.py somente para obter e registrar snapshots.
2. Execute scripts/generate_dataset.py para processar tudo offline.
3. Execute o auditor independente antes de treinar ou distribuir.

Consulte LICENSES.md e MEDICAL_LEGAL_NOTICE.md. O material não substitui
orientação médica ou jurídica e não deve ser apresentado como aconselhamento
individual.
