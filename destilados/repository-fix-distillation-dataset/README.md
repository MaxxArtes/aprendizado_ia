# Repository fix distillation dataset

Corpus SFT anonimizado e independente de modelo, derivado de correcoes humanas
observadas no historico de um grupo Git privado. Nenhum treino foi executado e
nenhum dado foi enviado a um provedor de modelos.

## Arquivos

- `dataset/train.jsonl`: 1.816 exemplos.
- `dataset/validation.jsonl`: 173 exemplos.
- `dataset/test.jsonl`: 172 exemplos.
- `dataset/manifest.json`: proveniencia, politica de split e hashes SHA-256.

Total: 2.161 exemplos unicos de 148 repositorios. Os splits sao agrupados por
repositorio e nao se sobrepoem.

Cada linha contem as mensagens `system`, `user` e `assistant` no formato
`entrada -> raciocinio verificavel -> resposta final`, alem de metadados
pseudonimizados. O raciocinio e um resumo sustentado pelas evidencias do diff,
nao uma cadeia de pensamento privada.

Repositorios, commits, caminhos, organizacoes, clientes, pessoas, e-mails,
URLs, hostnames, IPs e identificadores estruturados foram substituidos. O mapa
reversivel de aliases permanece fora deste repositorio, protegido localmente.

O corpus pode ser usado depois em SFT, LoRA ou QLoRA com o modelo e a plataforma
escolhidos pelo responsavel pelos dados. Mesmo anonimizado, deve permanecer
privado porque conserva logica tecnica necessaria para ensinar as correcoes.
