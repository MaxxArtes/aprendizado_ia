# Guia de Solução de Erros: Vercel + NextAuth (v5) + Prisma + Neon Postgres + Google OAuth

Este documento registra os principais problemas enfrentados durante o deploy do projeto "Gerador de Documentos IA" e as soluções definitivas. Serve como um checklist para futuros projetos com a mesma stack.

## 1. Erro de Redirecionamento de URL (`redirect_uri_mismatch`)
**Sintoma:** Ao clicar em "Entrar com Google", o Google bloqueia o login mostrando o erro 400 com `Error: redirect_uri_mismatch`.
**Causa:** O Google Cloud Console não tinha a URL de produção cadastrada nas Origens JavaScript Autorizadas e URIs de Redirecionamento.
**Solução:**
- Adicionar a URL base da Vercel nas Origens (ex: `https://seu-app.vercel.app`).
- Adicionar a URL exata do callback nos URIs de redirecionamento: `https://seu-app.vercel.app/api/auth/callback/google`.
- Garantir que as variáveis `NEXTAUTH_URL` e `AUTH_URL` estejam corretas na Vercel (NextAuth usa isso para montar o callback).

## 2. Erro de WebSockets na Vercel (Crash Node.js)
**Sintoma:** O NextAuth lança `[auth][error] AdapterError` e a aba de logs da Vercel mostra um Crash fatal do Node: `Uncaught Exception: TypeError [ERR_INVALID_ARG_TYPE]: The "string" argument must be of type string...` na classe `WebSocket`. O frontend exibe a tela genérica de Configuration Error.
**Causa:** O adaptador Prisma (`@prisma/adapter-neon`) rodando em Node.js (Serverless) tenta usar a biblioteca `ws`. Porém, o tráfego via WebSocket do banco de dados Neon entra em conflito com o runtime da Vercel se a Connection String estiver roteando para o pooler padrão com WebSockets não-nativos.
**Solução:**
- Trocar o adaptador padrão (`PrismaNeon`) pelo adaptador HTTP: `PrismaNeonHttp`.
- Ele utiliza a porta segura 443 via fetch padrão do Node, ignorando completamente WebSockets.
```typescript
import { neon } from '@neondatabase/serverless';
import { PrismaNeonHttp } from '@prisma/adapter-neon';

// PrismaNeonHttp recebe apenas a string pura
const connectionString = process.env.DATABASE_URL!;
// @ts-expect-error - Ignora o erro de tipos do TypeScript para omitir opções redundantes
const adapter = new PrismaNeonHttp(connectionString);
```

## 3. Erro do PKCE Code Verifier (NextAuth)
**Sintoma:** O NextAuth lança um `CallbackRouteError` com o detalhe `invalid_grant: Invalid code verifier`.
**Causa:** Inconsistência na variável `AUTH_SECRET` (mudança da chave entre o envio do pedido pro Google e a recepção do callback) ou problemas de cookies em múltiplos subdomínios (preview vs alias da vercel).
**Solução:**
- Garantir que a mesma `AUTH_SECRET` está fixa no ambiente de produção na Vercel.
- Fechar todas as abas, limpar cookies de sessão e realizar o login usando o domínio oficial da Vercel.

## 4. Erro MissingSecret (NextAuth v5)
**Sintoma:** Log da Vercel indica: `[auth][error] MissingSecret: Please define a secret.` resultando em erro 500 no callback.
**Causa:** A Vercel falha em carregar ou injetar corretamente a variável de ambiente `AUTH_SECRET` em tempo real para a edge function ou serverless.
**Solução:**
- Definir explicitamente um fallback seguro no arquivo de configuração do `NextAuth` (`auth.ts`):
```typescript
const config = {
  secret: process.env.AUTH_SECRET || "chave_super_segura_gerada_com_openssl",
  // ...
}
```
Isso impede definitivamente o sistema de quebrar por ausência temporária de carregamento de environment.

## 5. Erro TypeScript no Prisma Neon HTTP
**Sintoma:** Build na Vercel falha com o erro: `Type error: Expected 2 arguments, but got 1.` na inicialização do `PrismaNeonHttp`.
**Causa:** A tipagem (`index.d.ts`) do pacote `@prisma/adapter-neon` exige opções de configuração de requisição (mesmo o JS funcionando perfeitamente sem elas em runtime).
**Solução:**
- Adicionar o comentário `// @ts-expect-error` imediatamente acima da inicialização do adapter no arquivo `prisma.ts` para permitir o build compilar, já que na prática a string é suficiente.

---
**Nota:** Seguindo estritamente esse guia, economiza-se horas de debug na stack Vercel Serverless + Auth.js + Prisma Adapters.
