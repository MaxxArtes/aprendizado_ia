# OmniGen IA

O OmniGen IA é uma plataforma completa e instantânea alimentada por Inteligência Artificial. Ele evoluiu de um simples gerador de documentos para um ecossistema capaz de gerar e hospedar **Sites Inteiros**, além de criar PDFs, DOCX, XLSX, PPTX e imagens em tempo real.

## Principais Funcionalidades
- **Geração de Sites:** Crie sites complexos com Tailwind CSS. O código é exibido em um iframe interativo em tempo real e pode ser hospedado instantaneamente via Vercel Blob / Prisma, com um link definitivo compartilhável.
- **Documentos Ricos:** Geração nativa de PDFs formatados, planilhas estruturadas e apresentações profissionais.
- **Criação de Imagens:** Integração nativa para elaboração de recursos visuais sem sair do chat.
- **Preview em Tempo Real:** Todo o conteúdo gerado (texto, código e imagem) possui pré-visualização garantida antes da publicação ou do download.

## Stack Tecnológico
- **Next.js (App Router)** para a estrutura full-stack
- **Prisma + PostgreSQL (Neon)** para persistência de contas, histórico de chats e hospedagem de sites
- **Vercel** para deploy e edge-functions
- **Auth.js (NextAuth)** para segurança e controle de sessões
- Integrações flexíveis com **OpenRouter** para LLMs customizáveis (ex: Llama 3.3, Qwen)

## Como Executar Localmente

```bash
npm install
npm run dev
```

Abra [http://localhost:3000](http://localhost:3000) no seu navegador.
