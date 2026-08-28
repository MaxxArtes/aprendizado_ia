# Synthetic Evaluation Corpus v1

Corpus 100% fictício para avaliação de grounding documental e organização de execução.

## Conteúdo do pacote `evaluation-corpus-v1.zip`

- 5 empresas fictícias com a mesma arquitetura documental e fatos/números diferentes.
- 30 PDFs digitais nativos (6 por empresa; 150 páginas no total).
- 300 perguntas de teste com gabarito verificável.
- 1.000 pares executivos de treino ancorados nos documentos.
- 1.500 pares de organização: 30 intenções x 50 frases.
- Schema das 30 intenções e respectivos campos.
- Registro de documentos, CSVs auxiliares, manifest e checksums.

## Estrutura por empresa

1. Board Pack - Q3 2026, explicitamente sem dados de Q4.
2. Política de Alçadas e Aprovação com condicionais e exceções.
3. Procedimento Operacional de Recebimento em 7 etapas.
4. Especificações Técnicas de Equipamentos com códigos, tolerâncias e unidades.
5. Contrato Master de Serviços com vigência, prazos, SLA e renovação.
6. Relatório de Qualidade e Controles com contradições internas deliberadas.

## Distribuição das 300 perguntas

- 60: datas e prazos
- 60: condicionais e exceções
- 50: sequência de procedimentos
- 50: especificações técnicas e unidades
- 40: contradições internas
- 40: informação ausente no documento

## Organização de execução

O dataset possui 30 intenções genéricas com os campos esperados e 50 frases sintéticas por intenção, totalizando 1.500 pares. As frases variam entre formal, casual, abreviado, gíria e erro de digitação.

## Regras do corpus

- Todos os nomes de empresas, códigos, números, contratos, métricas e cenários são fictícios.
- Não há nomes de pessoas reais, credenciais, tokens, chaves ou segredos.
- Não há código-fonte dentro do pacote distribuído.
- PDFs com texto nativo e elementos vetoriais; 0 imagens raster detectadas no preflight.
- Nenhuma referência a OpenAI, ChatGPT, Claude, Gemini ou Anthropic foi encontrada no conteúdo ou metadados dos PDFs.
- Pergunta sem resposta deve retornar `Não informado no documento.`
- Contradição deve ser explicitada citando os dois valores; não escolher um sem evidência adicional.

## Arquivo

O corpus completo está em `evaluation-corpus-v1.zip` na raiz deste repositório.
