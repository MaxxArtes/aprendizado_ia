# -*- coding: utf-8 -*-
"""Auditoria independente do corpus premium de conhecimento sintetico.

Este verificador nao importa o gerador. Ele recalcula hashes, inventario,
metricas, cobertura, privacidade e grounding diretamente dos artefatos e fontes.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


EXPECTED_FILES = {
    "dataset/premium_grounded.jsonl",
    "dataset/premium_sft.jsonl",
    "quality_report.json",
    "source_inventory.json",
    "README.md",
    "FONTE.md",
    "SECURITY_NOTICE.md",
    ".gitignore",
}
EXPECTED_SCRIPTS = {
    "scripts/generate_dataset.py",
    "scripts/audit_dataset.py",
}
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
ALLOWED_SOURCE_PATHS = {
    f"aprendizados_tecnicos/{name}" for name in TECHNICAL_FILES + (GLOSSARY_FILE,)
}
EXPECTED_LESSON_SECTIONS = 308
MIN_PARSED_LESSONS = 250
MIN_LESSON_COVERAGE = 0.80
EXPECTED_GLOSSARY_ENTRIES = 129
EXPECTED_METHOD = "deterministic-grounded-extractive"
EXPECTED_VERSION = "1.0.0"
EXPECTED_SEED = 20260828
EXPECTED_LICENSE = "MIT License — Copyright (c) 2026 Maxuel Campos"
TASK_TYPES = {
    "diagnostico_operacional",
    "diretriz_de_execucao",
    "conceito_tecnico",
}
OUTPUT_LABELS = {
    "Causa", "Conduta", "Verificação", "Diagnóstico", "Regra operacional",
    "Como conferir", "Origem do problema", "Ação recomendada", "Validação",
    "Mecanismo", "Prática indicada", "Checagem", "Explicação causal",
    "Diretriz", "Evidência esperada", "Leitura do incidente", "Próximo passo",
    "Teste", "Conduta recomendada", "Ação", "Evidência",
}
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
    "claro!", "certamente!", "com certeza!", "sem dúvida!", "ótima pergunta",
    "espero que isso ajude", "vale ressaltar que", "é importante destacar que", "vamos lá!",
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalized_key(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    return re.sub(r"\s+", " ", value).strip()


def clean_source_text(value: str) -> str:
    value = unicodedata.normalize("NFC", value.replace("\r\n", "\n").replace("\r", "\n"))
    value = "\n".join(line.rstrip() for line in value.strip().split("\n"))
    value = re.sub(r"(?m)^\s*---\s*$", "", value)
    value = re.sub(r"(?m)^↳\s*\[[^\]]+\]\([^\)]+\)\s*$", "", value)
    return re.sub(r"\n{3,}", "\n\n", value).strip()


def sensitive_counts(text: str) -> Counter[str]:
    return Counter(
        {
            name: len(list(pattern.finditer(text)))
            for name, pattern in SENSITIVE_PATTERNS.items()
            if pattern.search(text)
        }
    )


def filler_hits(text: str) -> list[str]:
    folded = normalized_key(text)
    return [phrase for phrase in BANNED_FILLER if normalized_key(phrase) in folded]


def read_json(path: Path) -> Any:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise AssertionError(f"BOM UTF-8 em {path.name}")
    if b"\r" in raw:
        raise AssertionError(f"fim de linha diferente de LF em {path.name}")
    if raw and not raw.endswith(b"\n"):
        raise AssertionError(f"arquivo sem LF final: {path.name}")
    return json.loads(raw.decode("utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise AssertionError(f"BOM UTF-8 em {path.name}")
    if b"\r" in raw:
        raise AssertionError(f"fim de linha diferente de LF em {path.name}")
    if raw and not raw.endswith(b"\n"):
        raise AssertionError(f"arquivo sem LF final: {path.name}")
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(raw.decode("utf-8").splitlines(), 1):
        try:
            value = json.loads(line)
        except json.JSONDecodeError as error:
            raise AssertionError(f"JSON invalido em {path.name}:{number}: {error}") from error
        if not isinstance(value, dict):
            raise AssertionError(f"registro nao e objeto em {path.name}:{number}")
        rows.append(value)
    return rows


def line_excerpt(text: str, line_start: int, line_end: int) -> str:
    lines = text.splitlines()
    if not (1 <= line_start <= line_end <= len(lines)):
        raise AssertionError(
            f"intervalo de linhas invalido: {line_start}-{line_end}, total {len(lines)}"
        )
    return "\n".join(lines[line_start - 1 : line_end])


def stable_id(source_path: str, source_section: str, task_type: str) -> str:
    payload = "\x1f".join((source_path, source_section, task_type)).encode("utf-8")
    return "gcs-" + hashlib.sha256(payload).hexdigest()[:20]


def output_fragments(record: dict[str, Any]) -> Iterable[str]:
    output = record["output"]
    if record["task_type"] == "conceito_tecnico":
        yield output
        return
    without_labels = "\n".join(
        "" if line.strip() in OUTPUT_LABELS else line for line in output.splitlines()
    )
    for fragment in re.split(r"\n\s*\n", clean_source_text(without_labels)):
        fragment = clean_source_text(fragment)
        if fragment:
            yield fragment


def verify_grounding(record: dict[str, Any], premium_root: Path) -> None:
    provenance = record["provenance"]
    relative = provenance["source_path"]
    if relative not in ALLOWED_SOURCE_PATHS:
        raise AssertionError(f"fonte fora da lista positiva em {record['id']}: {relative}")
    source = (premium_root / relative).resolve()
    if premium_root.resolve() not in source.parents or not source.is_file():
        raise AssertionError(f"fonte ausente ou fora da raiz em {record['id']}")
    if source.is_symlink():
        raise AssertionError(f"link simbolico nao permitido como fonte em {record['id']}")
    if sha256_file(source) != provenance["source_sha256"]:
        raise AssertionError(f"hash da fonte diverge em {record['id']}")

    source_text = source.read_text(encoding="utf-8")
    excerpt = line_excerpt(source_text, provenance["line_start"], provenance["line_end"])
    if sha256_bytes(excerpt.encode("utf-8")) != provenance["evidence_sha256"]:
        raise AssertionError(f"hash do intervalo de evidencia diverge em {record['id']}")
    compact_excerpt = normalized_key(clean_source_text(excerpt))
    for fragment in output_fragments(record):
        if normalized_key(fragment) not in compact_excerpt:
            raise AssertionError(f"saida sem apoio no intervalo de fonte em {record['id']}")
    section_parts = provenance["source_section"].split(" / ", 1)
    if len(section_parts) == 2:
        parent_section, term = section_parts
        primary_term = re.sub(r"\s+\([^)]*\)\s*$", "", term)
        if normalized_key(primary_term) not in compact_excerpt or normalized_key(parent_section) not in normalized_key(source_text):
            raise AssertionError(f"secao de proveniencia nao localizada em {record['id']}")
    elif normalized_key(section_parts[0]) not in compact_excerpt:
        raise AssertionError(f"secao de proveniencia nao localizada em {record['id']}")


def source_inventory(premium_root: Path, used_sections: Counter[str]) -> dict[str, Any]:
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
        categories = sorted(sensitive_counts(text)) if text else []
        if relative in ALLOWED_SOURCE_PATHS:
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
                "sensitive_pattern_categories": categories,
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


def source_shape(premium_root: Path) -> tuple[int, int, int]:
    technical_root = premium_root / "aprendizados_tecnicos"
    total_sections = 0
    complete_sections = 0
    section_re = re.compile(r"(?ms)^##\s+(.+?)\s*$\n(.*?)(?=^##\s+|\Z)")
    required = {
        "sintoma": re.compile(r"(?m)^\*\*Sintoma(?::\*\*|\*\*\s*:)"),
        "causa": re.compile(r"(?m)^\*\*Causa(?::\*\*|\*\*\s*:)"),
        "regra": re.compile(r"(?m)^\*\*(?:Regra|Solução)(?::\*\*|\*\*\s*:)"),
    }
    for filename in TECHNICAL_FILES:
        text = (technical_root / filename).read_text(encoding="utf-8")
        for match in section_re.finditer(text):
            total_sections += 1
            if all(pattern.search(match.group(2)) for pattern in required.values()):
                complete_sections += 1
    glossary = (technical_root / GLOSSARY_FILE).read_text(encoding="utf-8")
    glossary_entries = len(
        re.findall(r"(?m)^\*\*[^*\n]+?\*\*(?:\s+\([^\n)]*\))?\s+—\s+", glossary)
    )
    return total_sections, complete_sections, glossary_entries


def compute_metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
    ids: set[str] = set()
    instructions: set[str] = set()
    outputs: set[str] = set()
    pairs: set[tuple[str, str]] = set()
    task_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    template_counts: Counter[str] = Counter()
    opening_counts: Counter[str] = Counter()

    for record in records:
        if list(record) != ["id", "task_type", "instruction", "output", "provenance", "generation"]:
            raise AssertionError("schema ou ordem do registro detalhado invalido")
        if list(record["provenance"]) != [
            "source_path", "source_section", "source_sha256", "line_start", "line_end",
            "license", "evidence_sha256",
        ]:
            raise AssertionError(f"schema de proveniencia invalido em {record.get('id')}")
        if list(record["generation"]) != ["method", "version", "template_id"]:
            raise AssertionError(f"schema de geracao invalido em {record.get('id')}")
        if record["task_type"] not in TASK_TYPES:
            raise AssertionError(f"tipo de tarefa invalido em {record.get('id')}")
        if not re.fullmatch(r"gcs-[0-9a-f]{20}", record["id"]):
            raise AssertionError(f"id invalido: {record.get('id')}")
        if record["id"] != stable_id(
            record["provenance"]["source_path"], record["provenance"]["source_section"],
            record["task_type"],
        ):
            raise AssertionError(f"id nao deterministico: {record['id']}")
        if record["generation"]["method"] != EXPECTED_METHOD:
            raise AssertionError(f"metodo inesperado em {record['id']}")
        if record["generation"]["version"] != EXPECTED_VERSION:
            raise AssertionError(f"versao inesperada em {record['id']}")
        if record["provenance"]["license"] != EXPECTED_LICENSE:
            raise AssertionError(f"licenca inesperada em {record['id']}")
        if not re.fullmatch(r"[0-9a-f]{64}", record["provenance"]["source_sha256"]):
            raise AssertionError(f"hash de fonte invalido em {record['id']}")
        if not re.fullmatch(r"[0-9a-f]{64}", record["provenance"]["evidence_sha256"]):
            raise AssertionError(f"hash de evidencia invalido em {record['id']}")
        if not isinstance(record["provenance"]["line_start"], int) or not isinstance(
            record["provenance"]["line_end"], int
        ):
            raise AssertionError(f"localizador nao inteiro em {record['id']}")

        instruction = record["instruction"]
        output = record["output"]
        if not isinstance(instruction, str) or not 20 <= len(instruction) <= 12_000:
            raise AssertionError(f"instrucao invalida em {record['id']}")
        if not isinstance(output, str) or not 20 <= len(output) <= 12_000:
            raise AssertionError(f"saida invalida em {record['id']}")
        if instruction != unicodedata.normalize("NFC", instruction) or output != unicodedata.normalize("NFC", output):
            raise AssertionError(f"texto fora de NFC em {record['id']}")
        serialized = json.dumps(record, ensure_ascii=False, sort_keys=True)
        hits = sensitive_counts(serialized)
        if hits:
            raise AssertionError(f"padrao sensivel no registro {record['id']}: {sorted(hits)}")
        if filler_hits(output):
            raise AssertionError(f"vicio de linguagem em {record['id']}")
        if "<think>" in normalized_key(serialized):
            raise AssertionError(f"raciocinio oculto em {record['id']}")

        instruction_key = normalized_key(instruction)
        output_key = normalized_key(output)
        pair = (instruction_key, output_key)
        if record["id"] in ids or instruction_key in instructions or output_key in outputs or pair in pairs:
            raise AssertionError(f"duplicidade em {record['id']}")
        ids.add(record["id"])
        instructions.add(instruction_key)
        outputs.add(output_key)
        pairs.add(pair)
        task_counts[record["task_type"]] += 1
        source_counts[record["provenance"]["source_path"]] += 1
        template_counts[record["generation"]["template_id"]] += 1
        opening_counts[" ".join(instruction_key.split()[:5])] += 1

    assertive_terms = {
        term: sum(
            len(re.findall(rf"(?iu)\b{re.escape(term)}\b", record["output"]))
            for record in records
        )
        for term in ("sempre", "nunca", "jamais", "deve", "obrigatório")
    }
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
    max_opening = max(opening_counts.values())
    return {
        "records": len(records), "unique_ids": len(ids),
        "unique_instructions": len(instructions), "unique_outputs": len(outputs),
        "unique_pairs": len(pairs), "task_counts": dict(sorted(task_counts.items())),
        "source_counts": dict(sorted(source_counts.items())),
        "template_counts": dict(sorted(template_counts.items())),
        "source_assertive_term_counts": assertive_terms,
        "max_shared_five_word_opening": max_opening,
        "max_shared_five_word_opening_ratio": round(max_opening / len(records), 6),
        "max_output_fourgram_jaccard": round(max_similarity, 6),
        "closest_output_pair_ids": list(closest_pair),
        "max_instruction_chars": max(len(record["instruction"]) for record in records),
        "max_output_chars": max(len(record["output"]) for record in records),
    }


def verify_manifest(manifest: dict[str, Any], output_root: Path) -> None:
    expected_manifest_keys = {
        "name", "version", "generated_at_utc", "method", "language", "license", "seed",
        "external_calls", "records", "files", "scripts",
    }
    if set(manifest) != expected_manifest_keys:
        raise AssertionError("schema do manifesto diverge do esperado")
    if manifest["name"] != "geracao_de_conhecimento_sintetico":
        raise AssertionError("nome inesperado no manifesto")
    if (manifest["version"], manifest["method"], manifest["seed"]) != (
        EXPECTED_VERSION, EXPECTED_METHOD, EXPECTED_SEED,
    ):
        raise AssertionError("metadados de reproducao inesperados")
    if manifest["language"] != "pt-BR" or manifest["license"] != "MIT":
        raise AssertionError("idioma ou licenca inesperados")
    if manifest["external_calls"] != 0:
        raise AssertionError("manifesto indica chamadas externas")
    generated_at = datetime.fromisoformat(manifest["generated_at_utc"])
    if generated_at.tzinfo is None:
        raise AssertionError("data do manifesto sem fuso horario")
    if set(manifest["files"]) != EXPECTED_FILES:
        raise AssertionError("lista de arquivos do manifesto diverge do esperado")
    if set(manifest["scripts"]) != EXPECTED_SCRIPTS:
        raise AssertionError("lista de scripts do manifesto diverge do esperado")

    for relative, metadata in manifest["files"].items():
        path = output_root / relative
        expected_keys = {"bytes", "sha256", "records"} if path.suffix == ".jsonl" else {"bytes", "sha256"}
        if set(metadata) != expected_keys:
            raise AssertionError(f"metadados de arquivo invalidos: {relative}")
        if not path.is_file() or path.stat().st_size != metadata["bytes"]:
            raise AssertionError(f"arquivo ausente ou tamanho divergente: {relative}")
        if sha256_file(path) != metadata["sha256"]:
            raise AssertionError(f"hash divergente: {relative}")
    for relative, expected_hash in manifest["scripts"].items():
        path = output_root / relative
        if not path.is_file() or sha256_file(path) != expected_hash:
            raise AssertionError(f"script ausente ou alterado: {relative}")


def main() -> int:
    output_root = Path(__file__).resolve().parents[1]
    premium_root = output_root.parent
    license_path = premium_root / "aprendizados_tecnicos" / "LICENSE"
    if license_path.is_symlink() or premium_root.resolve() not in license_path.resolve().parents:
        raise AssertionError("arquivo de licenca fora da raiz ou ligado simbolicamente")
    license_text = license_path.read_text(encoding="utf-8")
    if not license_text.startswith(
        "MIT License\n\nCopyright (c) 2026 Maxuel Campos\n"
    ) or "Permission is hereby granted, free of charge" not in license_text:
        raise AssertionError("licenca da fonte diverge do metadado declarado")
    manifest = read_json(output_root / "manifest.json")
    quality = read_json(output_root / "quality_report.json")
    inventory = read_json(output_root / "source_inventory.json")
    verify_manifest(manifest, output_root)

    grounded = read_jsonl(output_root / "dataset" / "premium_grounded.jsonl")
    sft = read_jsonl(output_root / "dataset" / "premium_sft.jsonl")
    if len(grounded) != len(sft) or len(grounded) != manifest["records"]:
        raise AssertionError("contagem global diverge entre manifesto e JSONL")
    for relative in ("dataset/premium_grounded.jsonl", "dataset/premium_sft.jsonl"):
        if manifest["files"][relative]["records"] != len(grounded):
            raise AssertionError(f"contagem do arquivo diverge no manifesto: {relative}")
    expected_sft = [
        {"instruction": record["instruction"], "output": record["output"]}
        for record in grounded
    ]
    if sft != expected_sft:
        raise AssertionError("dataset SFT diverge da projecao fundamentada")
    if any(list(row) != ["instruction", "output"] for row in sft):
        raise AssertionError("schema SFT invalido")

    metrics = compute_metrics(grounded)
    for record in grounded:
        verify_grounding(record, premium_root)
    for key, expected in metrics.items():
        if quality.get(key) != expected:
            raise AssertionError(f"metrica divergente no relatorio: {key}")
    if quality.get("status") != "APROVADO" or quality.get("privacy_hits") != 0:
        raise AssertionError("relatorio nao esta aprovado e limpo")
    if quality.get("banned_filler_hits") != 0 or quality.get("external_calls") != 0:
        raise AssertionError("relatorio registra vicio de linguagem ou chamada externa")
    if (quality.get("generator_version"), quality.get("generation_method"), quality.get("seed")) != (
        EXPECTED_VERSION, EXPECTED_METHOD, EXPECTED_SEED,
    ):
        raise AssertionError("metadados do relatorio divergentes")

    total_sections, complete_sections, glossary_entries = source_shape(premium_root)
    rejected_count = sum(len(items) for items in quality.get("rejected_sections", {}).values())
    coverage = complete_sections / total_sections if total_sections else 0.0
    if (total_sections, glossary_entries) != (EXPECTED_LESSON_SECTIONS, EXPECTED_GLOSSARY_ENTRIES):
        raise AssertionError("snapshot estrutural das fontes diverge")
    if complete_sections < MIN_PARSED_LESSONS or coverage < MIN_LESSON_COVERAGE:
        raise AssertionError("cobertura independente abaixo do limite")
    if quality.get("parsed_lessons") != complete_sections:
        raise AssertionError("quantidade de licoes parseadas diverge da contagem independente")
    if quality.get("parsed_glossary_entries") != glossary_entries:
        raise AssertionError("quantidade de verbetes diverge da contagem independente")
    if quality.get("lesson_sections_detected") != total_sections:
        raise AssertionError("total de secoes diverge no relatorio")
    if quality.get("rejected_section_count") != rejected_count or rejected_count != total_sections - complete_sections:
        raise AssertionError("secoes rejeitadas nao fecham a cobertura")
    if quality.get("lesson_coverage_ratio") != round(coverage, 6):
        raise AssertionError("taxa de cobertura divergente")
    if quality.get("coverage_policy") != {
        "expected_lesson_sections": EXPECTED_LESSON_SECTIONS,
        "minimum_parsed_lessons": MIN_PARSED_LESSONS,
        "minimum_lesson_coverage_ratio": MIN_LESSON_COVERAGE,
        "expected_glossary_entries": EXPECTED_GLOSSARY_ENTRIES,
    }:
        raise AssertionError("politica de cobertura divergente")

    filtered = quality.get("filtered_sensitive_records", [])
    if quality.get("filtered_sensitive_record_count") != len(filtered):
        raise AssertionError("contagem de registros sensiveis filtrados diverge")
    if len({item.get("id") for item in filtered}) != len(filtered):
        raise AssertionError("registro filtrado repetido")
    included_ids = {record["id"] for record in grounded}
    if any(item.get("id") in included_ids for item in filtered):
        raise AssertionError("registro marcado como filtrado ainda esta no dataset")
    if len(grounded) != complete_sections + glossary_entries - len(filtered):
        raise AssertionError("contagem de candidatos, filtros e saidas nao fecha")

    used_counts = Counter(record["provenance"]["source_path"] for record in grounded)
    current_inventory = source_inventory(premium_root, used_counts)
    if inventory != current_inventory:
        raise AssertionError("inventario de fontes diverge do estado atual")
    filtered_categories: Counter[tuple[str, str]] = Counter()
    for item in filtered:
        for category in item.get("categories", []):
            if category not in SENSITIVE_PATTERNS:
                raise AssertionError("categoria desconhecida em registro filtrado")
            filtered_categories[(item.get("source_path"), category)] += 1
    for relative in ALLOWED_SOURCE_PATHS:
        text = (premium_root / relative).read_text(encoding="utf-8")
        for category, count in sensitive_counts(text).items():
            if filtered_categories[(relative, category)] < count:
                raise AssertionError(
                    f"ocorrencia sensivel sem contabilizacao de filtro: {relative} / {category}"
                )

    used = [entry for entry in inventory["entries"] if entry["status"] == "used"]
    excluded = [entry for entry in inventory["entries"] if entry["status"] == "excluded"]
    result = {
        "status": "APROVADO", "records": len(grounded),
        "unique_instructions": metrics["unique_instructions"],
        "unique_outputs": metrics["unique_outputs"], "unique_pairs": metrics["unique_pairs"],
        "task_counts": metrics["task_counts"], "used_sources": len(used),
        "excluded_sources": len(excluded), "lesson_coverage_ratio": round(coverage, 6),
        "privacy_hits_in_full_records": 0, "banned_filler_hits": 0,
        "filtered_sensitive_records": len(filtered),
        "max_output_fourgram_jaccard": metrics["max_output_fourgram_jaccard"],
        "external_calls": 0, "auditor_imports_generator": False,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"status": "REPROVADO", "erro": str(error)}, ensure_ascii=False, indent=2))
        raise SystemExit(1)
