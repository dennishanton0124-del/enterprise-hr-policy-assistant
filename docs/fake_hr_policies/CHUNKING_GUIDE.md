# RAG Chunking Guide for HR Policy Documents

This guide explains how the three HR documents are structured for optimal chunking in your RAG system, mapped to your `chunks` table schema.

---

## Document Inventory

| Document ID | Title | File | Policy Area |
| :---- | :---- | :---- | :---- |
| EH-2025-001 | Employee Handbook | `employee_handbook.md` | General Employment |
| PTO-2025-001 | Paid Time Off Policy | `pto_policy.md` | Time Off and Leave |
| WFH-2025-001 | Work From Home Policy | `work_from_home_policy.md` | Workplace Flexibility |

---

## Structural Design for Chunking

Every document follows the **same hierarchy**:

\# Document Title              → maps to: documents.title

\#\# N. Major Section           → maps to: chunks.section\_title (parent)

\#\#\# N.M Subsection            → maps to: chunks.section\_title (chunk-level)

\[paragraph(s) of policy text\] → maps to: chunks.chunk\_text

This three-level structure means you can chunk at the **subsection level (\#\#\# headers)** and get clean, self-contained chunks of roughly 80–250 words each — ideal for embedding.

---

## Recommended Chunking Strategy

### Primary approach: Header-based chunking at H3 level

Split each document on `###` headers. Each subsection becomes one chunk.

**Why this works:**

- Each subsection is a single self-contained policy concept (e.g., "3.1 Accrual Rates by Tenure")  
- Length is consistent (typically 60–250 words) — well below typical 512-token embedding limits  
- The H3 title becomes natural metadata for retrieval boosting and citation display  
- No semantic content is split mid-thought

### Schema field mapping

For each `###` subsection chunk, populate the `chunks` table as follows:

| chunks field | Source |
| :---- | :---- |
| `id` | Generated UUID |
| `document_id` | FK to documents (EH-2025-001 / PTO-2025-001 / WFH-2025-001) |
| `chunk_text` | Full text under the `###` header (excluding the header itself) |
| `embedding` | Vector from your embedding model (e.g. text-embedding-3-small) |
| `section_title` | The `###` heading text (e.g., "3.1 Accrual Rates by Tenure") |
| `page_or_section` | The dotted path (e.g., "3.1") plus parent (e.g., "Section 3: PTO Accrual \> 3.1") |
| `created_at` | Ingestion timestamp |

### Citation-ready output

When your generator creates an answer, the `query_sources.citation_text` can directly use the `section_title` field. Example citation: *"PTO Policy, Section 3.1: Accrual Rates by Tenure"* — clean and trustworthy for users.

---

## Why Markdown over PDF/DOCX for the demo

For the RAG ingestion pipeline, markdown is the cleanest source format because:

1. **Deterministic parsing.** Headers (`#`, `##`, `###`) are unambiguous splitters. PDF extraction often produces noisy text with broken layouts, headers/footers bleeding into content, and inconsistent section detection.  
2. **Stable section IDs.** The numbering scheme (1.1, 1.2, 2.1...) gives you a stable `page_or_section` value that survives reformatting.  
3. **No OCR or layout heuristics needed.** You can ingest with a 20-line Python script using standard markdown parsers (e.g., `markdown-it-py`, `mistune`) or simple regex on `^###` .  
4. **If your demo requires PDF/DOCX format**, you can convert these markdown files to either format with `pandoc` while keeping the markdown as your canonical source.

---

## Sensitive Topic Coverage Map

For your sensitive-topic classifier, here are the sections in each document that touch your sensitive categories. These are the sections most likely to trigger **escalation** rather than direct answer in your demo:

| Sensitive Category | Relevant Sections |
| :---- | :---- |
| Harassment | Handbook §7.1–7.6 (entire anti-harassment policy) |
| Discrimination | Handbook §1.2 (EEO statement), §7 (anti-harassment) |
| Termination | Handbook §14 (termination), §10.3 (disciplinary action) |
| Medical Leave | Handbook §9.1–9.4, PTO §6.2 (disability interaction) |
| Legal Risk | Handbook §6.5 (FCPA), §11.2 (workplace violence) |
| Retaliation | Handbook §7.5 (non-retaliation) |
| Compensation Disputes | Handbook §4.6, §14.3 (final paycheck) |
| Benefits Disputes | Handbook §5 (entire benefits section) |
| Employee Relations | Handbook §10 (performance management) |

This map is useful for **two demo scenarios**:

- Journey B (Escalation): Questions hitting these sections should escalate even if a confident answer exists  
- Journey A (Safe answer): Questions hitting non-listed sections (PTO accrual, WFH equipment, holidays, etc.) should answer cleanly

---

## Suggested Demo Test Queries by Journey

### Journey A — Safe Answer (high confidence \+ non-sensitive)

| Test Query | Expected Source |
| :---- | :---- |
| "What is the PTO carryover policy?" | PTO §5.1 |
| "How much PTO do I accrue after 5 years?" | PTO §3.1 |
| "What internet speed do I need to work from home?" | WFH §5.2 |
| "What holidays does the company observe?" | Handbook §8.4 |
| "When do I become eligible for the 401(k)?" | Handbook §5.2 |
| "Do I get a home office stipend?" | WFH §6.2 |

### Journey B — Escalation (sensitive topic)

| Test Query | Sensitive Category |
| :---- | :---- |
| "Can my manager fire me for taking medical leave?" | Termination \+ Medical Leave |
| "I think I'm being harassed by a coworker, what do I do?" | Harassment |
| "Is my pay lower because of my gender?" | Discrimination \+ Compensation |
| "Can I sue if I was retaliated against?" | Legal Risk \+ Retaliation |

### Journey C — Refusal (no source)

| Test Query | Why It Refuses |
| :---- | :---- |
| "What is the relocation policy for working abroad?" | Not covered (only short trips mentioned in WFH §9.3, no full relocation policy) |
| "What is the dress code?" | Not covered in any document |
| "What is the tuition reimbursement amount?" | Not covered in any document |
| "How do I get a parking pass?" | Not covered in any document |

These give you clean test cases for all three journeys without ambiguity.

---

## Quick Ingestion Pseudocode

import re

from pathlib import Path

def chunk\_markdown(file\_path, document\_id):

    text \= Path(file\_path).read\_text()

    chunks \= \[\]

    \# Split on \#\#\# headers

    sections \= re.split(r'\\n(?=\#\#\# )', text)

    for section in sections:

        if not section.startswith('\#\#\# '):

            continue

        lines \= section.split('\\n', 1\)

        section\_title \= lines\[0\].replace('\#\#\# ', '').strip()

        chunk\_text \= lines\[1\].strip() if len(lines) \> 1 else ''

        \# Extract dotted section number (e.g., "3.1")

        match \= re.match(r'(\\d+\\.\\d+)', section\_title)

        page\_or\_section \= match.group(1) if match else section\_title

        chunks.append({

            'document\_id': document\_id,

            'section\_title': section\_title,

            'page\_or\_section': page\_or\_section,

            'chunk\_text': chunk\_text,

        })

    return chunks

---

## File Statistics

| Document | Approx. Word Count | H3 Subsections | Avg Chunk Size |
| :---- | :---- | :---- | :---- |
| Employee Handbook | \~5,200 | \~75 | \~70 words |
| PTO Policy | \~2,900 | \~38 | \~75 words |
| WFH Policy | \~3,800 | \~50 | \~75 words |

Total: \~163 chunks across all three documents — a clean, testable size for a demo.  
