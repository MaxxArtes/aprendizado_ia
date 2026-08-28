@../AI_CONTEXT.md

# Gerador de Documentos IA - Diretrizes e Mandatos

## Seleção de Modelos (LLMs)

### Criação de Documentos e Textos Longos
- **Llama 3.3 70B Instruct**: Melhor equilíbrio geral. Excelente em português, ideal para relatórios, contratos e artigos.
- **Hermes 3 405B Instruct**: Redações complexas, análises profundas e escrita criativa avançada.
- **GLM 4.5 Air**: Escrita corporativa, resumos e tradução.

### Dados, Lógica e Programação
- **Qwen3 Coder 480B**: Programação, refatoração e documentação de código.
- **Qwen3 Next 80B**: Processar dados brutos, JSON e automações.
- **Nemotron-3-nano (Reasoning)**: Problemas passo a passo e lógica pura.

### Velocidade e Chats Rápidos
- **Gemma 4 31B**: Ultra-rápido para brainstorming e assistentes do dia a dia.
- **Llama 3.2 3B**: Extremamente leve para tarefas simples de gramática ou extração.

---

## Geração de Imagens

### Pollinations.ai (Principal)
- Totalmente gratuito, sem login, velocidade instantânea.
- Prompt padrão: `flat vector illustration, corporate minimalist, high resolution --no text`
- Formato 16:9: `width=1920&height=1080`

### Fallback de Imagens
1. Pollinations.ai (ilimitado)
2. Hugging Face Inference API (requer token)
3. Dezgo / Prodia (1.000 gerações grátis)
4. Lorem Flickr (último recurso)

### Ícones e Avatares
- **Dicebear**: Avatares via URL.
- **Lucide Icons**: Ícones de interface.
- **LottieFiles**: Animações `.json` fluidas.

---

## Padrões de Engenharia de Prompt

- **Markdown**: Títulos (`#`, `##`), listas e negritos.
- **Gatilho de geração**: `[GENERATE_DOC:tipo:prompt_detalhado]`
- **CSV**: Separado por vírgula, sem blocos de código markdown.
- **Slides**: JSON puro com array de objetos `{ title, content, imagePrompt }`.

---

## Estabilidade de API

- **Delay**: 1-2 segundos entre requisições em massa.
- **Retry**: 3-5 tentativas para falhas temporárias.

---

## Economia de Tokens

- Lançar subagente para leituras massivas de logs ou arquivos grandes.
- Usar `read_url_content` para páginas web em Markdown limpo.
- `.antigravityignore` bloqueia `package-lock.json`, builds e mídias.

---

## Erros Conhecidos no Build

### Next.js Dynamic Server Usage
Aviso normal, não fatal. Adicionar `export const dynamic = 'force-dynamic'` só se quiser silenciar.

### ESLint Strict (Vercel)
Limpar imports e variáveis não usadas após refatorar. Usar `const` ao invés de `let` quando a referência não é reatribuída.

### jsPDF - getNumberOfPages
Usar `doc.getNumberOfPages()` diretamente, não `doc.internal.getNumberOfPages()`.

### node-pty (Terminal Web)
Servidor/Dockerfile precisa de compiladores C++, `make` e `Python` antes do `npm install`.

### Gráficos com Dados do Docker
`docker stats` retorna strings com `%`, `MB`, `GB`. Converter para `Float` na API antes de passar para bibliotecas de gráficos.

### Tamanho em Disco por Container
`docker stats` não expõe uso de disco. Usar `docker ps -s` paralelamente para capturar "Virtual Size".
