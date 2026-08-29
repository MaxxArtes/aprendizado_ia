# Fonte

- **De onde veio**: 1.111 passagens de 21 publicações oficiais brasileiras — Presidência da
  República (CDC, SNDC, SAC, comércio eletrônico), Fundação Procon-SP (16 cartilhas) e
  Ministério da Saúde (3 guias alimentares). URL, órgão, edição e SHA-256 do snapshot de
  cada uma em `LICENSES.md`; inventário em `manifest.json`.
- **Data desta coleta**: 2026-08-28 (audit_report.json, 22:04 UTC).
- **Licença**: **MISTA — registrada por fonte, não há licença única.**
  - 4.777 pares (48%) de regime livre: textos oficiais de lei (Lei 9.610 art. 8º, IV — sem
    proteção autoral) e cartilhas Procon-SP (reprodução com atribuição).
  - **5.223 pares (52%) CC-BY-NC-SA-4.0** (guias do Ministério da Saúde). **NC = vedado uso
    comercial**; SA = obra derivada herda a licença. **Não podem entrar em modelo comercial
    sem decisão explícita do dono** — ver "Riscos" abaixo.
- **O que já foi feito**: extração determinística por trecho literal do documento fonte —
  `external_model_calls: 0` e `network_calls_during_generation: 0` (quality_report.json).
  Nenhum LLM escreveu resposta aqui, então **não há termo de gerador envolvido**.
  10.000 pares, 10.000 instruções únicas, 0 duplicatas, 0 respostas ambíguas,
  `literal_offset_matches: 10000` (toda resposta é trecho literal com offset conferido).
  Divisão treino/validação/teste por CLUSTER, com `cross_split_cluster_leaks: 0`.
  Auditoria independente: `audit_report.json` (18 checagens, APROVADO, auditor não importa
  o gerador). Aviso de domínio sensível em `MEDICAL_LEGAL_NOTICE.md`.
- **O que sabidamente ainda está sujo**: os HTML crus em `sources/raw/` estão em
  encoding legado (mojibake se lidos como UTF-8) — não afeta os `.jsonl` derivados, que
  estão limpos (0 ocorrências medidas em 10.000 linhas).
- **Riscos (decisão do dono antes de treinar)**: a fatia CC-BY-NC-SA é incompatível com
  modelo vendido. Opções: (a) treinar só com os 4.777 livres, (b) usar os 10k apenas em
  modelo publicado sob licença compatível, (c) obter permissão. Enquanto não houver
  decisão, este material NÃO entra em mistura de treino comercial.
