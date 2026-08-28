# -*- coding: utf-8 -*-
"""Gera um corpus SFT fundamentado nas fontes curadas de dados_premium.

O gerador e deterministico, nao usa rede nem modelo externo e trabalha apenas
dentro de ``dados_premium``. As respostas sao compostas de trechos estruturados
das fontes; nenhum fato novo e acrescentado.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


VERSION = "1.0.0"
SEED = 20260828
METHOD = "deterministic-grounded-extractive"
EXPECTED_LESSON_SECTIONS = 308
MIN_PARSED_LESSONS = 250
MIN_LESSON_COVERAGE = 0.80
EXPECTED_GLOSSARY_ENTRIES = 129

TECHNICAL_FILES = (
    "apis-e-integracoes.md",
    "arquitetura-e-produto.md",
    "automacao-e-agendamento.md",
    "banco-de-dados.md",
    "deploy-e-build.md",
    "encoding-e-midia.md",
    "ferramentas-de-ia.md",
    "frontend-e-nextjs.md",
    "git.md",
    "infraestrutura-e-containers.md",
    "seguranca-e-segredos.md",
    "treino-de-modelos.md",
    "windows-e-powershell.md",
)
GLOSSARY_FILE = "GLOSSARIO.md"

SOURCE_LICENSE = "MIT License — Copyright (c) 2026 Maxuel Campos"
SENSITIVE_PATTERNS = {
    "private_key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "provider_token": re.compile(
        r"\b(?:ghp|github_pat|sk-proj|sk|xox[baprs])[-_A-Za-z0-9]{20,}\b"
    ),
    "jwt": re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
    "assigned_secret": re.compile(
        r"(?i)\b(?:api[_ -]?key|access[_ -]?token|edge[_ -]?token|secret|password|senha)"
        r"\s*[:=]\s*[\"']?[A-Za-z0-9_./+\-=]{24,}"
    ),
    "described_token": re.compile(
        r"(?i)\btoken\b[^\r\n]{0,80}?:\s*(?:\*{0,2}`?)?[A-Za-z0-9_-]{32,}"
    ),
    "credential_url": re.compile(r"(?i)\b[a-z][a-z0-9+.-]*://[^\s/@:]+:[^\s/@]+@"),
    "email": re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"),
}

BANNED_FILLER = (
    "claro!",
    "certamente!",
    "com certeza!",
    "sem dúvida!",
    "ótima pergunta",
    "espero que isso ajude",
    "vale ressaltar que",
    "é importante destacar que",
    "vamos lá!",
)

DIAGNOSTIC_PROMPTS = (
    "Analise o incidente técnico descrito a seguir. Identifique a causa e indique a conduta operacional adequada.{verification}\n\nTema: {title}\n\n{symptom}",
    "Um sistema apresenta este comportamento:\n\n{symptom}\n\nExplique o mecanismo que produz a falha e a regra que deve orientar a correção.{verification}\n\nAssunto: {title}",
    "Faça o diagnóstico do caso abaixo sem inventar contexto. A resposta deve separar causa e ação recomendada.{verification}\n\n{symptom}\n\nÁrea: {title}",
    "Considere o sintoma observado em produção:\n\n{symptom}\n\nQual é a causa documentada e qual prática evita a recorrência?{verification}\n\nTópico: {title}",
    "A partir apenas do relato abaixo, apresente um diagnóstico operacional: causa, regra de correção{verification_short}.\n\n{symptom}\n\nReferência: {title}",
    "Investigue este cenário técnico:\n\n{symptom}\n\nDescreva por que ele acontece e o procedimento recomendado.{verification}\n\nContexto temático: {title}",
    "Transforme o sintoma em uma orientação de engenharia fundamentada. Inclua a causa e a conduta segura.{verification}\n\nTítulo da lição: {title}\nSintoma: {symptom}",
    "Qual diagnóstico explica o comportamento a seguir e que regra prática deve ser aplicada?{verification}\n\n{symptom}\n\nDomínio: {title}",
    "Leia o caso e produza uma resposta técnica direta, sem suposições além do que foi informado.{verification}\n\nCaso: {symptom}\nTema: {title}",
    "Relacione o efeito observado à causa registrada e à medida corretiva apropriada.{verification}\n\nEfeito observado: {symptom}\nLição: {title}",
    "Este incidente precisa de uma análise causal e de uma recomendação executável.{verification}\n\n{symptom}\n\nReferência técnica: {title}",
    "Diagnostique o problema sem recorrer a explicações genéricas. Informe a causa e a regra operacional.{verification}\n\n{symptom}\n\nCategoria: {title}",
)

ACTION_PROMPTS = (
    "O diagnóstico já apontou o mecanismo abaixo. Converta-o em uma diretriz operacional{verification_short}.\n\nTema: {title}\nDiagnóstico: {cause}",
    "Com base na causa documentada, indique a ação recomendada{verification_short}. Não acrescente hipóteses.\n\n{cause}\n\nAssunto: {title}",
    "Que regra de engenharia deve ser adotada diante desta causa?{verification}\n\nCausa identificada: {cause}\nTópico: {title}",
    "Passe do diagnóstico para a execução: forneça a conduta aplicável{verification_short}.\n\n{cause}\n\nLição de origem: {title}",
    "A causa do incidente é a seguinte:\n\n{cause}\n\nQual prática reduz a chance de recorrência?{verification}\n\nTema: {title}",
    "Formule o próximo passo operacional usando somente a causa registrada abaixo.{verification}\n\n{cause}\n\nReferência: {title}",
    "Dado este diagnóstico, apresente uma regra acionável{verification_short}.\n\nDiagnóstico: {cause}\nÁrea: {title}",
    "Escolha a conduta compatível com a causa descrita e diga como avaliar o resultado quando houver evidência disponível.\n\n{cause}\n\nContexto: {title}",
)

GLOSSARY_PROMPTS = (
    "Explique o termo técnico “{term}” de forma objetiva, preservando o uso adotado em engenharia de software.",
    "O que significa “{term}” neste vocabulário técnico?",
    "Defina “{term}” para alguém que precisa reconhecer o conceito em documentação e diagnóstico.",
    "Forneça uma definição operacional de “{term}”.",
    "Em contexto técnico, como deve ser entendido o termo “{term}”?",
    "Descreva “{term}” sem substituir o termo por uma expressão imprecisa.",
    "Qual é o significado prático de “{term}”?",
    "Apresente uma definição concisa e tecnicamente fiel de “{term}”.",
)

OUTPUT_STYLES = (
    ("Causa", "Conduta", "Verificação"),
    ("Diagnóstico", "Regra operacional", "Como conferir"),
    ("Origem do problema", "Ação recomendada", "Validação"),
    ("Mecanismo", "Prática indicada", "Checagem"),
    ("Explicação causal", "Diretriz", "Evidência esperada"),
    ("Leitura do incidente", "Próximo passo", "Teste"),
)

ACTION_STYLES = (
    ("Diretriz", "Verificação"),
    ("Conduta recomendada", "Como conferir"),
    ("Regra operacional", "Validação"),
    ("Ação", "Checagem"),
    ("Prática indicada", "Teste"),
    ("Próximo passo", "Evidência"),
)


@dataclass(frozen=True)
class Lesson:
    source_path: Path
    relative_path: str
    source_sha256: str
    evidence_sha256: str
    title: str
    line_start: int
    line_end: int
    symptom: str
    cause: str
    rule: str
    verification: str


@dataclass(frozen=True)
class GlossaryEntry:
    source_path: Path
    relative_path: str
    source_sha256: str
    evidence_sha256: str
    section: str
    line_start: int
    line_end: int
    term: str
    definition: str


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def line_excerpt_sha256(text: str, line_start: int, line_end: int) -> str:
    """Hash de um intervalo de linhas inclusivo, apos leitura textual universal."""
    lines = text.splitlines()
    excerpt = "\n".join(lines[line_start - 1 : line_end])
    return sha256_bytes(excerpt.encode("utf-8"))


def clean_block(value: str) -> str:
    value = unicodedata.normalize("NFC", value.replace("\r\n", "\n").replace("\r", "\n"))
    lines = [line.rstrip() for line in value.strip().split("\n")]
    value = "\n".join(lines)
    value = re.sub(r"(?m)^\s*---\s*$", "", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    value = re.sub(r"(?m)^↳\s*\[[^\]]+\]\([^\)]+\)\s*$", "", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def normalized_key(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    return re.sub(r"\s+", " ", value).strip()


def normalized_label(value: str) -> str:
    value = normalized_key(value).rstrip(":")
    value = "".join(
        char for char in unicodedata.normalize("NFKD", value) if not unicodedata.combining(char)
    )
    return value


def is_structural_label(value: str) -> bool:
    """Distingue cabecalho editorial de enfase como ``**snapshot**:``."""
    normalized = normalized_label(value)
    if normalized in {
        "sintoma",
        "causa",
        "regra",
        "solucao",
        "como verificar",
        "verificacao",
        "como testar",
        "validacao",
    }:
        return True
    first_letter = next((char for char in value if char.isalpha()), "")
    return bool(first_letter and first_letter.isupper())


def stable_number(*parts: str) -> int:
    payload = "\x1f".join(parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def stable_id(*parts: str) -> str:
    payload = "\x1f".join(parts).encode("utf-8")
    return "gcs-" + hashlib.sha256(payload).hexdigest()[:20]


def sensitive_hits(text: str) -> list[str]:
    return [name for name, pattern in SENSITIVE_PATTERNS.items() if pattern.search(text)]


def filler_hits(text: str) -> list[str]:
    folded = normalized_key(text)
    return [phrase for phrase in BANNED_FILLER if normalized_key(phrase) in folded]


def validate_local_source(path: Path, premium_root: Path) -> Path:
    """Rejeita fonte ausente, link simbolico ou resolvida fora de dados_premium."""
    resolved_root = premium_root.resolve()
    resolved = path.resolve()
    if resolved_root not in resolved.parents or not resolved.is_file():
        raise ValueError(f"fonte ausente ou fora de dados_premium: {path}")
    if path.is_symlink():
        raise ValueError(f"link simbolico nao permitido como fonte: {path}")
    return resolved


def validate_source_license(premium_root: Path) -> None:
    license_path = validate_local_source(
        premium_root / "aprendizados_tecnicos" / "LICENSE", premium_root
    )
    license_text = license_path.read_text(encoding="utf-8")
    if not license_text.startswith(
        "MIT License\n\nCopyright (c) 2026 Maxuel Campos\n"
    ) or "Permission is hereby granted, free of charge" not in license_text:
        raise ValueError("a licenca das fontes nao corresponde ao metadado MIT esperado")


def parse_lesson_file(
    path: Path, premium_root: Path
) -> tuple[list[Lesson], list[str], list[str]]:
    raw = path.read_text(encoding="utf-8")
    source_hash = sha256_file(path)
    relative = path.relative_to(premium_root).as_posix()
    section_re = re.compile(r"(?ms)^##\s+(.+?)\s*$\n(.*?)(?=^##\s+|\Z)")
    # Aceita ``**Campo:**`` e ``**Campo**:``, mas nao trata qualquer negrito
    # no inicio da linha como delimitador. Isso preserva enfases dentro do campo.
    label_re = re.compile(
        r"(?m)^\*\*(?P<label>[^*\n:]+?)(?::\*\*|\*\*\s*:)\s*"
    )
    lessons: list[Lesson] = []
    rejected: list[str] = []
    ignored_label_candidates: list[str] = []

    for section_match in section_re.finditer(raw):
        title = clean_block(section_match.group(1))
        body = section_match.group(2)
        all_matches = list(label_re.finditer(body))
        matches = [
            match for match in all_matches if is_structural_label(match.group("label"))
        ]
        ignored_label_candidates.extend(
            clean_block(match.group("label"))
            for match in all_matches
            if not is_structural_label(match.group("label"))
        )
        fields: dict[str, str] = {}
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
            label = normalized_label(match.group("label"))
            value = clean_block(body[match.end() : end])
            if value and label not in fields:
                fields[label] = value

        symptom = fields.get("sintoma", "")
        cause = fields.get("causa", "")
        rule = fields.get("regra", fields.get("solucao", ""))
        verification = ""
        for candidate in ("como verificar", "verificacao", "como testar", "validacao"):
            if fields.get(candidate):
                verification = fields[candidate]
                break

        missing = [name for name, value in (("sintoma", symptom), ("causa", cause), ("regra", rule)) if not value]
        if missing:
            rejected.append(f"{title}: campos ausentes: {', '.join(missing)}")
            continue
        line_start = raw.count("\n", 0, section_match.start()) + 1
        section_text = section_match.group(0).rstrip()
        last_offset = section_match.start() + len(section_text) - 1
        line_end = raw.count("\n", 0, last_offset) + 1
        lessons.append(
            Lesson(
                source_path=path,
                relative_path=relative,
                source_sha256=source_hash,
                evidence_sha256=line_excerpt_sha256(raw, line_start, line_end),
                title=title,
                line_start=line_start,
                line_end=line_end,
                symptom=symptom,
                cause=cause,
                rule=rule,
                verification=verification,
            )
        )
    return lessons, rejected, sorted(set(ignored_label_candidates), key=normalized_key)


def parse_glossary(path: Path, premium_root: Path) -> list[GlossaryEntry]:
    raw = path.read_text(encoding="utf-8")
    source_hash = sha256_file(path)
    relative = path.relative_to(premium_root).as_posix()
    section_re = re.compile(r"(?ms)^##\s+(.+?)\s*$\n(.*?)(?=^##\s+|\Z)")
    # Uma entrada valida precisa ter travessao apos o termo na mesma linha.
    # Negritos usados dentro de uma definicao nao iniciam uma nova entrada.
    entry_re = re.compile(
        r"(?m)^\*\*(?P<term>[^*\n]+?)\*\*(?P<prefix>\s+\([^\n)]*\))?\s+—\s+"
    )
    entries: list[GlossaryEntry] = []

    for section_match in section_re.finditer(raw):
        section = clean_block(section_match.group(1))
        body = section_match.group(2)
        entry_matches = list(entry_re.finditer(body))
        for index, entry_match in enumerate(entry_matches):
            term = clean_block(entry_match.group("term")).rstrip(":")
            end = entry_matches[index + 1].start() if index + 1 < len(entry_matches) else len(body)
            prefix = clean_block(entry_match.group("prefix") or "")
            definition = clean_block(body[entry_match.end() : end])
            if prefix:
                term = f"{term} {prefix}".strip()
            if len(term) < 2 or len(definition) < 20:
                continue
            entry_start_offset = section_match.start(2) + entry_match.start()
            entry_text = raw[entry_start_offset : section_match.start(2) + end].rstrip()
            last_offset = entry_start_offset + len(entry_text) - 1
            line_start = raw.count("\n", 0, entry_start_offset) + 1
            line_end = raw.count("\n", 0, last_offset) + 1
            entries.append(
                GlossaryEntry(
                    source_path=path,
                    relative_path=relative,
                    source_sha256=source_hash,
                    evidence_sha256=line_excerpt_sha256(raw, line_start, line_end),
                    section=section,
                    line_start=line_start,
                    line_end=line_end,
                    term=term,
                    definition=definition,
                )
            )
    return entries


def verification_phrases(has_verification: bool) -> dict[str, str]:
    if has_verification:
        return {
            "verification": " Inclua também uma forma concreta de verificação.",
            "verification_short": " e inclua a verificação",
        }
    return {"verification": "", "verification_short": ""}


def render_diagnostic(lesson: Lesson, style_index: int) -> str:
    cause_label, rule_label, verify_label = OUTPUT_STYLES[style_index % len(OUTPUT_STYLES)]
    parts = [f"{cause_label}\n{lesson.cause}", f"{rule_label}\n{lesson.rule}"]
    if lesson.verification:
        parts.append(f"{verify_label}\n{lesson.verification}")
    return "\n\n".join(parts)


def render_action(lesson: Lesson, style_index: int) -> str:
    rule_label, verify_label = ACTION_STYLES[style_index % len(ACTION_STYLES)]
    parts = [f"{rule_label}\n{lesson.rule}"]
    if lesson.verification:
        parts.append(f"{verify_label}\n{lesson.verification}")
    return "\n\n".join(parts)


def make_record(
    *,
    task_type: str,
    instruction: str,
    output: str,
    source_path: str,
    source_section: str,
    source_sha256: str,
    line_start: int,
    line_end: int,
    template_id: str,
    evidence_sha256: str,
) -> dict[str, Any]:
    instruction = clean_block(instruction)
    output = clean_block(output)
    record_id = stable_id(source_path, source_section, task_type)
    return {
        "id": record_id,
        "task_type": task_type,
        "instruction": instruction,
        "output": output,
        "provenance": {
            "source_path": source_path,
            "source_section": source_section,
            "source_sha256": source_sha256,
            "line_start": line_start,
            "line_end": line_end,
            "license": SOURCE_LICENSE,
            "evidence_sha256": evidence_sha256,
        },
        "generation": {
            "method": METHOD,
            "version": VERSION,
            "template_id": template_id,
        },
    }


def records_from_lesson(lesson: Lesson) -> list[dict[str, Any]]:
    pivot = stable_number(lesson.relative_path, lesson.title)
    phrases = verification_phrases(bool(lesson.verification))
    diagnostic_index = stable_number(
        lesson.relative_path, lesson.title, "diagnostic-template"
    ) % len(DIAGNOSTIC_PROMPTS)
    diagnostic_instruction = DIAGNOSTIC_PROMPTS[diagnostic_index].format(
        title=lesson.title,
        symptom=lesson.symptom,
        **phrases,
    )
    diagnostic_output = render_diagnostic(lesson, pivot // len(DIAGNOSTIC_PROMPTS))

    action_index = stable_number(
        lesson.relative_path, lesson.title, "action-template"
    ) % len(ACTION_PROMPTS)
    action_instruction = ACTION_PROMPTS[action_index].format(
        title=lesson.title,
        cause=lesson.cause,
        **phrases,
    )
    action_output = render_action(lesson, pivot // len(ACTION_PROMPTS))
    diagnostic_record = make_record(
            task_type="diagnostico_operacional",
            instruction=diagnostic_instruction,
            output=diagnostic_output,
            source_path=lesson.relative_path,
            source_section=lesson.title,
            source_sha256=lesson.source_sha256,
            line_start=lesson.line_start,
            line_end=lesson.line_end,
            template_id=f"diag-{diagnostic_index:02d}",
            evidence_sha256=lesson.evidence_sha256,
        )
    action_record = make_record(
            task_type="diretriz_de_execucao",
            instruction=action_instruction,
            output=action_output,
            source_path=lesson.relative_path,
            source_section=lesson.title,
            source_sha256=lesson.source_sha256,
            line_start=lesson.line_start,
            line_end=lesson.line_end,
            template_id=f"acao-{action_index:02d}",
            evidence_sha256=lesson.evidence_sha256,
        )
    # Uma unica visao por licao evita que causa/regra sejam duplicadas em dois
    # pares semanticamente quase identicos. A alternancia preserva diversidade.
    task_choice = stable_number(lesson.relative_path, lesson.title, "task-choice")
    return [diagnostic_record if task_choice % 2 == 0 else action_record]


def record_from_glossary(entry: GlossaryEntry) -> dict[str, Any]:
    pivot = stable_number(entry.relative_path, entry.section, entry.term)
    template_index = pivot % len(GLOSSARY_PROMPTS)
    instruction = GLOSSARY_PROMPTS[template_index].format(term=entry.term)
    return make_record(
        task_type="conceito_tecnico",
        instruction=instruction,
        output=entry.definition,
        source_path=entry.relative_path,
        source_section=f"{entry.section} / {entry.term}",
        source_sha256=entry.source_sha256,
        line_start=entry.line_start,
        line_end=entry.line_end,
        template_id=f"gloss-{template_index:02d}",
        evidence_sha256=entry.evidence_sha256,
    )


def validate_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    if not records:
        raise ValueError("nenhum registro foi gerado")
    ids: set[str] = set()
    instructions: set[str] = set()
    outputs: set[str] = set()
    pairs: set[tuple[str, str]] = set()
    task_counts: Counter[str] = Counter()
    template_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    opening_counts: Counter[str] = Counter()
    privacy_hits: Counter[str] = Counter()
    filler_count: Counter[str] = Counter()

    for record in records:
        if list(record) != ["id", "task_type", "instruction", "output", "provenance", "generation"]:
            raise ValueError("ordem ou schema detalhado invalido")
        instruction = record["instruction"]
        output = record["output"]
        if not isinstance(instruction, str) or len(instruction) < 20:
            raise ValueError(f"instrucao curta ou invalida em {record['id']}")
        if not isinstance(output, str) or len(output) < 20:
            raise ValueError(f"resposta curta ou invalida em {record['id']}")
        if len(instruction) > 12_000 or len(output) > 12_000:
            raise ValueError(f"registro excessivamente longo em {record['id']}")
        if instruction != unicodedata.normalize("NFC", instruction):
            raise ValueError(f"instrucao fora de NFC em {record['id']}")
        if output != unicodedata.normalize("NFC", output):
            raise ValueError(f"resposta fora de NFC em {record['id']}")
        if "<think>" in normalized_key(instruction + "\n" + output):
            raise ValueError(f"raciocinio oculto em {record['id']}")

        # O registro inteiro e inspecionado, inclusive proveniencia e metadados.
        record_hits = sensitive_hits(
            json.dumps(record, ensure_ascii=False, sort_keys=True)
        )
        for hit in record_hits:
            privacy_hits[hit] += 1
        for hit in filler_hits(output):
            filler_count[hit] += 1

        record_id = record["id"]
        instruction_key = normalized_key(instruction)
        pair_key = (instruction_key, normalized_key(output))
        output_key = normalized_key(output)
        if record_id in ids:
            raise ValueError(f"id duplicado: {record_id}")
        if instruction_key in instructions:
            raise ValueError(f"instrucao duplicada: {record_id}")
        if pair_key in pairs:
            raise ValueError(f"par duplicado: {record_id}")
        if output_key in outputs:
            raise ValueError(f"resposta duplicada: {record_id}")
        ids.add(record_id)
        instructions.add(instruction_key)
        outputs.add(output_key)
        pairs.add(pair_key)

        task_counts[record["task_type"]] += 1
        template_counts[record["generation"]["template_id"]] += 1
        source_counts[record["provenance"]["source_path"]] += 1
        opening = " ".join(instruction_key.split()[:5])
        opening_counts[opening] += 1

    if privacy_hits:
        raise ValueError(f"padroes sensiveis no corpus: {dict(privacy_hits)}")
    if filler_count:
        raise ValueError(f"vicios de linguagem detectados: {dict(filler_count)}")

    assertive_terms = {
        term: sum(
            len(re.findall(rf"(?iu)\b{re.escape(term)}\b", record["output"]))
            for record in records
        )
        for term in ("sempre", "nunca", "jamais", "deve", "obrigatório")
    }

    max_opening = max(opening_counts.values())
    if max_opening / len(records) > 0.10:
        raise ValueError("abertura de instrucao excessivamente repetida")

    shingle_rows: list[tuple[str, set[tuple[str, ...]]]] = []
    for record in records:
        tokens = re.findall(r"[\wÀ-ÿ]+", normalized_key(record["output"]))
        shingles = {tuple(tokens[index : index + 4]) for index in range(max(0, len(tokens) - 3))}
        if shingles:
            shingle_rows.append((record["id"], shingles))
    max_similarity = 0.0
    closest_pair: tuple[str, str] | tuple[()] = ()
    for left_index, (left_id, left) in enumerate(shingle_rows):
        for right_id, right in shingle_rows[left_index + 1 :]:
            union = left | right
            similarity = len(left & right) / len(union) if union else 0.0
            if similarity > max_similarity:
                max_similarity = similarity
                closest_pair = (left_id, right_id)
    if max_similarity >= 0.92:
        raise ValueError(
            f"respostas quase duplicadas: {closest_pair[0]} e {closest_pair[1]} ({max_similarity:.4f})"
        )
    return {
        "status": "APROVADO",
        "records": len(records),
        "unique_ids": len(ids),
        "unique_instructions": len(instructions),
        "unique_outputs": len(outputs),
        "unique_pairs": len(pairs),
        "task_counts": dict(sorted(task_counts.items())),
        "source_counts": dict(sorted(source_counts.items())),
        "template_counts": dict(sorted(template_counts.items())),
        "privacy_hits": 0,
        "banned_filler_hits": 0,
        "source_assertive_term_counts": assertive_terms,
        "max_shared_five_word_opening": max_opening,
        "max_shared_five_word_opening_ratio": round(max_opening / len(records), 6),
        "max_output_fourgram_jaccard": round(max_similarity, 6),
        "closest_output_pair_ids": list(closest_pair),
        "max_instruction_chars": max(len(record["instruction"]) for record in records),
        "max_output_chars": max(len(record["output"]) for record in records),
    }


def source_inventory(premium_root: Path, used_sections: Counter[str]) -> dict[str, Any]:
    used_paths = {f"aprendizados_tecnicos/{name}" for name in TECHNICAL_FILES + (GLOSSARY_FILE,)}
    entries: list[dict[str, Any]] = []
    for path in sorted(premium_root.rglob("*")):
        if not path.is_file() or "geracao_de_conhecimento_sintetico" in path.parts:
            continue
        relative = path.relative_to(premium_root).as_posix()
        raw = path.read_bytes()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = ""
        hits = sensitive_hits(text) if text else []
        if relative in used_paths:
            status = "used"
            reason = "fonte Markdown estruturada, licenciada e aprovada pela lista positiva"
        elif relative.startswith("notas_pessoais/"):
            status = "excluded"
            reason = "notas operacionais com identificadores, infraestrutura ou segredo; exige sanitizacao manual"
        elif relative.startswith("gerador_docs_ia_manuais/"):
            status = "excluded"
            reason = "documentacao parcial e com recomendacoes que exigem revisao tecnica manual"
        else:
            status = "excluded"
            reason = "arquivo navegacional, duplicado, de licenca ou fora da lista positiva"
        entries.append(
            {
                "path": relative,
                "bytes": len(raw),
                "sha256": sha256_bytes(raw),
                "status": status,
                "reason": reason,
                "sensitive_pattern_categories": sorted(hits),
                "records_derived": used_sections.get(relative, 0),
            }
        )
    return {
        "policy": "allowlist",
        "formats_present": ["markdown"],
        "entries": entries,
        "summary": {
            "used_files": sum(entry["status"] == "used" for entry in entries),
            "excluded_files": sum(entry["status"] == "excluded" for entry in entries),
            "used_files_with_sensitive_patterns": sum(
                entry["status"] == "used" and bool(entry["sensitive_pattern_categories"])
                for entry in entries
            ),
            "excluded_files_with_sensitive_patterns": sum(
                entry["status"] == "excluded" and bool(entry["sensitive_pattern_categories"])
                for entry in entries
            ),
        },
    }


def build_records(premium_root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    technical_root = premium_root / "aprendizados_tecnicos"
    validate_source_license(premium_root)
    lessons: list[Lesson] = []
    rejected_sections: dict[str, list[str]] = {}
    ignored_label_candidates: dict[str, list[str]] = {}
    for filename in TECHNICAL_FILES:
        path = validate_local_source(technical_root / filename, premium_root)
        parsed, rejected, ignored = parse_lesson_file(path, premium_root)
        lessons.extend(parsed)
        if rejected:
            rejected_sections[path.relative_to(premium_root).as_posix()] = rejected
        if ignored:
            ignored_label_candidates[path.relative_to(premium_root).as_posix()] = ignored

    glossary_path = validate_local_source(technical_root / GLOSSARY_FILE, premium_root)
    glossary_entries = parse_glossary(glossary_path, premium_root)
    rejected_section_count = sum(len(items) for items in rejected_sections.values())
    lesson_sections_detected = len(lessons) + rejected_section_count
    lesson_coverage_ratio = (
        len(lessons) / lesson_sections_detected if lesson_sections_detected else 0.0
    )
    if lesson_sections_detected != EXPECTED_LESSON_SECTIONS:
        raise ValueError(
            "topologia das fontes mudou: "
            f"{lesson_sections_detected} secoes, esperado {EXPECTED_LESSON_SECTIONS}"
        )
    if len(lessons) < MIN_PARSED_LESSONS or lesson_coverage_ratio < MIN_LESSON_COVERAGE:
        raise ValueError(
            "cobertura do parser abaixo do limite: "
            f"{len(lessons)} licoes, {lesson_coverage_ratio:.4f} de cobertura"
        )
    if len(glossary_entries) != EXPECTED_GLOSSARY_ENTRIES:
        raise ValueError(
            "quantidade de verbetes diverge do snapshot revisado: "
            f"{len(glossary_entries)}, esperado {EXPECTED_GLOSSARY_ENTRIES}"
        )
    candidates: list[dict[str, Any]] = []
    for lesson in lessons:
        candidates.extend(records_from_lesson(lesson))
    candidates.extend(record_from_glossary(entry) for entry in glossary_entries)

    filtered_sensitive_records: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    for record in candidates:
        hits = sensitive_hits(json.dumps(record, ensure_ascii=False, sort_keys=True))
        if hits:
            filtered_sensitive_records.append(
                {
                    "id": record["id"],
                    "source_path": record["provenance"]["source_path"],
                    "source_section": record["provenance"]["source_section"],
                    "categories": sorted(hits),
                }
            )
            continue
        records.append(record)
    random.Random(SEED).shuffle(records)

    quality = validate_records(records)
    quality.update(
        {
            "generator_version": VERSION,
            "generation_method": METHOD,
            "seed": SEED,
            "parsed_lessons": len(lessons),
            "parsed_glossary_entries": len(glossary_entries),
            "lesson_sections_detected": lesson_sections_detected,
            "rejected_section_count": rejected_section_count,
            "lesson_coverage_ratio": round(lesson_coverage_ratio, 6),
            "coverage_policy": {
                "expected_lesson_sections": EXPECTED_LESSON_SECTIONS,
                "minimum_parsed_lessons": MIN_PARSED_LESSONS,
                "minimum_lesson_coverage_ratio": MIN_LESSON_COVERAGE,
                "expected_glossary_entries": EXPECTED_GLOSSARY_ENTRIES,
            },
            "rejected_sections": rejected_sections,
            "ignored_label_candidates": ignored_label_candidates,
            "filtered_sensitive_records": filtered_sensitive_records,
            "filtered_sensitive_record_count": len(filtered_sensitive_records),
            "grounding": "respostas compostas apenas de campos estruturados ou definicoes das fontes",
            "factual_review_scope": "grounding verificado; fatos tecnicos externos nao foram revalidados",
            "source_style_preserved": True,
            "external_calls": 0,
        }
    )
    return records, quality


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def jsonl_bytes(rows: Iterable[dict[str, Any]]) -> bytes:
    return b"".join(
        (json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
        for row in rows
    )


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def readme_text(quality: dict[str, Any]) -> str:
    counts = quality["task_counts"]
    return f"""# Geração de conhecimento sintético

Corpus premium fundamentado em Markdown técnico limpo e licenciado. A geração é local,
determinística e extrativa: os textos de resposta vêm dos campos estruturados da fonte;
nenhum modelo externo ou fato adicional é usado.

## Conteúdo

- `dataset/premium_grounded.jsonl`: {quality['records']} registros com ID, tarefa e proveniência.
- `dataset/premium_sft.jsonl`: os mesmos {quality['records']} pares no schema exato `instruction/output`.
- `source_inventory.json`: lista positiva de fontes e exclusões justificadas.
- `quality_report.json`: métricas e validações.
- `manifest.json`: hashes SHA-256, tamanhos e contagens.
- `SECURITY_NOTICE.md`: risco encontrado nas fontes que ficaram fora do corpus.

Não concatene os dois JSONL: eles representam os mesmos pares em schemas diferentes.

## Distribuição

| tarefa | registros |
|---|---:|
| diagnóstico operacional | {counts.get('diagnostico_operacional', 0)} |
| diretriz de execução | {counts.get('diretriz_de_execucao', 0)} |
| conceito técnico | {counts.get('conceito_tecnico', 0)} |
| **total** | **{quality['records']}** |

## Critérios aplicados

- Proveniência por arquivo, seção, licença e hash.
- Localizadores usam linhas inicial e final inclusivas; o hash de evidência cobre exatamente esse intervalo.
- Grounding por composição de `Sintoma`, `Causa`, `Regra` e `Como verificar`.
- Unicode NFC, UTF-8 sem BOM e finais de linha LF.
- IDs, instruções e pares únicos.
- Lista positiva de fontes; notas pessoais e manuais pendentes foram excluídos.
- Bloqueio de segredos, credenciais em URL, e-mails e raciocínio oculto.
- Bloqueio de aberturas formulaicas como “Claro!”, “Certamente!” e “Ótima pergunta”.
- Variação determinística de prompts e estruturas de resposta.
- Piso de cobertura do parser e snapshot de 308 seções/129 verbetes para detectar regressões.

## Limites conhecidos

- A auditoria comprova correspondência com as fontes, não atualização factual externa.
- Comandos e afirmações dependentes de versão herdam a data e o contexto do material original.
- Termos categóricos presentes nas regras técnicas foram preservados como evidência de origem;
  o gerador não acrescenta bordões nem intensificadores.
- Uma divisão treino/validação/teste deve ser feita por arquivo-fonte ou cluster semântico,
  nunca sorteando linhas isoladas.

## Reprodução

```powershell
python scripts/generate_dataset.py
python scripts/audit_dataset.py
```

Os scripts não fazem chamadas de rede e não escrevem fora desta pasta.
"""


def fonte_text(collected_on: str) -> str:
    return f"""# Fonte

- **De onde veio**: snapshot local `../aprendizados_tecnicos`, material técnico de autoria
  de Maxuel Campos. A URL/edição original não está registrada no `FONTE.md` recebido e não
  foi inferida. A edição usada é identificada pelos hashes em `source_inventory.json`.
- **Data desta coleta**: {collected_on}.
- **Licença**: MIT (`SPDX-License-Identifier: MIT`), conforme
  `../aprendizados_tecnicos/LICENSE`.
- **O que foi feito**: seleção por lista positiva, parsing de lições estruturadas,
  síntese extrativa de tarefas, normalização Unicode, deduplicação e auditoria de privacidade.
- **O que ficou fora**: índices e READMEs duplicados, `notas_pessoais` por conter contexto
  operacional identificável/segredo, e `gerador_docs_ia_manuais` até revisão técnica manual.
- **Formatos disponíveis nesta execução**: somente Markdown. Nenhum PDF, planilha,
  transcrição ou exportação tratada estava presente para inclusão.
"""


def security_notice_text(inspected_on: str) -> str:
    return f"""# Aviso de segurança das fontes excluídas

Na inspeção local de {inspected_on}, uma nota em `../notas_pessoais` continha um token
aparentemente operacional em texto claro,
além de domínios e detalhes de infraestrutura identificáveis. Todo o diretório foi excluído
da geração por lista positiva; nenhum valor sensível foi copiado para os datasets.

Trate o segredo como comprometido e revogue ou rotacione a credencial no provedor. Se a nota
foi enviada a um remoto, remover apenas a linha atual não elimina o valor do histórico Git.
O saneamento do histórico deve ser uma ação separada e consciente.
"""


def gitignore_text() -> str:
    return """# Os scripts fazem parte do pacote reproduzível, apesar do *.py ignorado na raiz.
!scripts/
!scripts/generate_dataset.py
!scripts/audit_dataset.py

scripts/__pycache__/
*.pyc
"""


def export(premium_root: Path, output_root: Path) -> dict[str, Any]:
    resolved_premium = premium_root.resolve()
    resolved_output = output_root.resolve()
    if resolved_premium not in resolved_output.parents:
        raise ValueError("o destino precisa ficar dentro de dados_premium")

    generated_at = datetime.now(timezone.utc).replace(microsecond=0)
    generated_at_text = generated_at.isoformat()
    generated_on = generated_at.date().isoformat()
    records, quality = build_records(premium_root)
    used_sections = Counter(record["provenance"]["source_path"] for record in records)
    inventory = source_inventory(premium_root, used_sections)

    grounded_path = output_root / "dataset" / "premium_grounded.jsonl"
    sft_path = output_root / "dataset" / "premium_sft.jsonl"
    quality_path = output_root / "quality_report.json"
    inventory_path = output_root / "source_inventory.json"
    readme_path = output_root / "README.md"
    fonte_path = output_root / "FONTE.md"
    security_path = output_root / "SECURITY_NOTICE.md"
    gitignore_path = output_root / ".gitignore"

    sft_rows = ({"instruction": record["instruction"], "output": record["output"]} for record in records)
    atomic_write(grounded_path, jsonl_bytes(records))
    atomic_write(sft_path, jsonl_bytes(sft_rows))
    atomic_write(quality_path, json_bytes(quality))
    atomic_write(inventory_path, json_bytes(inventory))
    atomic_write(readme_path, readme_text(quality).encode("utf-8"))
    atomic_write(fonte_path, fonte_text(generated_on).encode("utf-8"))
    atomic_write(security_path, security_notice_text(generated_on).encode("utf-8"))
    atomic_write(gitignore_path, gitignore_text().encode("utf-8"))

    generated_files = (
        grounded_path,
        sft_path,
        quality_path,
        inventory_path,
        readme_path,
        fonte_path,
        security_path,
        gitignore_path,
    )
    file_entries: dict[str, Any] = {}
    for path in generated_files:
        relative = path.relative_to(output_root).as_posix()
        entry: dict[str, Any] = {"bytes": path.stat().st_size, "sha256": sha256_file(path)}
        if path.suffix == ".jsonl":
            entry["records"] = quality["records"]
        file_entries[relative] = entry

    scripts_root = output_root / "scripts"
    manifest = {
        "name": "geracao_de_conhecimento_sintetico",
        "version": VERSION,
        "generated_at_utc": generated_at_text,
        "method": METHOD,
        "language": "pt-BR",
        "license": "MIT",
        "seed": SEED,
        "external_calls": 0,
        "records": quality["records"],
        "files": file_entries,
        "scripts": {
            "scripts/generate_dataset.py": sha256_file(scripts_root / "generate_dataset.py"),
            "scripts/audit_dataset.py": sha256_file(scripts_root / "audit_dataset.py"),
        },
    }
    atomic_write(output_root / "manifest.json", json_bytes(manifest))
    return {"quality": quality, "inventory": inventory["summary"], "manifest": manifest}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true", help="valida as fontes sem escrever")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_root = Path(__file__).resolve().parents[1]
    premium_root = output_root.parent
    if args.check_only:
        records, quality = build_records(premium_root)
        inventory = source_inventory(
            premium_root,
            Counter(record["provenance"]["source_path"] for record in records),
        )
        print(json.dumps({"quality": quality, "inventory": inventory["summary"]}, ensure_ascii=False, indent=2))
        return 0
    result = export(premium_root, output_root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
