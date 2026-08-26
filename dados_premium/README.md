# dados_premium

Fonte limpa e curada, antes de virar corpus de treino: PDFs, markdown,
planilhas, transcrições, exports já tratados.

Um diretório por fonte. Cada um com um `FONTE.md` curto respondendo:

- **De onde veio** - URL, edição, data da coleta.
- **Licença** - o que permite redistribuir. Se não souber, não entra.
- **O que já foi feito** - OCR, deduplicação, remoção de cabeçalho e rodapé,
  normalização de encoding.
- **O que sabidamente ainda está sujo** - o que o próximo passo precisa tratar.

Arquivos binários e volumosos (`.pdf`, `.parquet`, `.xlsx`) vão por Git LFS
automaticamente - ver `.gitattributes` na raiz.

## Antes de colocar algo aqui

O repositório é público. Só entra material redistribuível: obra própria,
domínio público ou licença que permita. Livro comprado, curso pago, base de
cliente e dado proprietário ficam fora - commitar aqui é publicar, e o
histórico do git guarda o arquivo mesmo depois de removido.

Dado com pessoa identificável precisa de anonimização antes, não depois.
