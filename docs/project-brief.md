# Projekt-Brief: Wiederverwendbarer ISO-9001-QMS-Deployment-Generator

> **Kennzeichnungslegende**
>
> * **(bestätigt)** = vom Auftraggeber ausdrücklich vorgegeben.
> * **[Schlussfolgerung]** = Vorschlag/Ableitung, nicht final bestätigt.
> * **[Nicht verifiziert]** = nicht überprüfbar in diesem Rahmen.
> * **(belegt)** = in der vorangegangenen Recherche mit Quellen (u. a. Microsoft Learn, Atlassian-Doku, Zertifizierungsstellen wie NQA) belegt.
>
> Da Teile dieses Dokuments Vorschläge sind, gilt die Kennzeichnung für das gesamte Dokument. Die offenen Entscheidungen (Abschnitt 9) sind bewusst nicht gefüllt.

---

## 1. Ziel / Use Case (bestätigt)

* Ein **wiederverwendbares Framework**, das ein ISO-9001-QMS-**Gerüst** automatisiert in Ziel-Tools deployt („Tag 1").
* Danach werden die organisationsspezifischen Inhalte (Prozesse, Kontext, Risikoregister, Ziele) über ca. 2 Wochen ausgefüllt.
* Ergebnis: ein vollständig dokumentiertes, **audit-fähiges** QMS im Sinne von **interner Reife bzw. Kunden-/Zweitparteien-Audit** (Bedeutung 1, bestätigt).
* Einsatzkontext: Beratung kleiner Kanzleien/Firmen; das Framework soll **pro Kunde wiederverwendbar** sein.

## 2. Scope-Abgrenzung

* **Allgemeines ISO 9001** (branchenneutral), **keine** Medizinprodukte (kein ISO 13485 / IEC 62304). (bestätigt)
* Zielzustand ist Dokumentations-/interne Reife, **nicht** die akkreditierte Zertifizierung. (bestätigt)
* **(belegt)** Grenze: Eine akkreditierte Zertifizierung setzt zusätzlich eine Betriebsphase voraus (üblich ~3 Monate inkl. einem vollständigen internen Audit-Zyklus und einem Management-Review). Diese Zeit lässt sich nicht wegkonfigurieren und liegt außerhalb dessen, was das Deployment leistet.

## 3. Funktionaler Umfang – „voller Umfang" (bestätigt)

Pro Ziel-Tool soll deployt werden:

* **Struktur**: Space/Site/Projekt, Dokumentenbaum, Namenskonventionen.
* **Dokument-Templates** mit Platzhaltern: Qualitätspolitik, Verfahren, Management-Review-Agenda, internes Audit-Checklist, CAPA-/NC-Formular.
* **Record-Container**: Listen-/Issue-Schemata für NC, CAPA, Audits, Ziele/KPIs.
* **Workflows**: Freigabe/Review, CAPA-Routing, Review-Erinnerungen.
* **Dashboards**: KPI-/Status-Übersicht.
* Abdeckung der ISO-9001-Klauseln 4–10 als Gliederungslogik.

## 4. Zielplattformen + Reihenfolge (bestätigt)

Priorität: **1. self-hosted → 2. Atlassian (Confluence + Jira) → 3. Microsoft 365 (SharePoint)**.

Plattform-Constraints **(belegt)**, die beim Adapter-Bau zu beachten sind:

* **Atlassian**: Provisioning über Confluence-/Jira-REST-API bzw. Forge. Freigabe-Workflow + Versionierung sind in Confluence Cloud **nicht nativ** → Marketplace-App nötig (z. B. Comala); dieser Teil ist nur **teil-automatisierbar**. Kein offizieller First-Party-Terraform-Provider für Atlassian Cloud.
* **M365**: Template-basiertes Provisioning (PnP) ist **PowerShell-/.NET-nativ**; Site Scripts (JSON) und Power Automate für Freigabe/Erinnerungen. Python kann die REST-/Graph-API bedienen, hat aber **keine gepflegte PnP-Provisioning-Template-Engine**.
* **self-hosted**: end-to-end skriptbar (Docker/Compose + Seed über REST/DB); Betrieb/Wartung liegt beim Betreiber.

## 5. Architektur — [Schlussfolgerung]

[Schlussfolgerung] Vier Schichten, konfig-getrieben, idempotent:

```
qms-kit/
├─ config/
│  ├─ core.yaml            # tool-neutral: Klauseln 4–10, Dok-Liste, Record-Typen, Rollen, KPIs, CAPA-States
│  ├─ selfhosted.yaml      # Overlay: DB/Host, Modul-Mapping des OSS-Tools
│  ├─ atlassian.yaml       # Overlay: Space-Keys, Jira-Projekt/Issue-Types, App-Konfig
│  └─ m365.yaml            # Overlay: Site-URLs, Listen-Mapping, Flow-IDs
├─ templates/              # Textbausteine mit Platzhaltern (Jinja2)
│  ├─ policy.md.j2
│  ├─ procedure.md.j2
│  ├─ mgmt_review_agenda.md.j2
│  ├─ internal_audit_checklist.md.j2
│  └─ capa_form.md.j2
├─ core/                   # Config-Loader, Schema-Validierung, Template-Renderer
├─ adapters/
│  ├─ selfhosted/          # XWiki (Docs) + Redmine (Records): Docker-Compose + Seed via REST
│  ├─ atlassian/           # REST-Skripte (Spaces/Seiten/Jira-Issues/Dashboards)
│  └─ m365/                # PnP-PowerShell-Skripte + Site Scripts (JSON) + Power-Automate-Export
├─ cli/                    # Einstieg: deploy --target selfhosted|atlassian|m365
├─ docs/
└─ tests/
```

Schichtbeschreibung [Schlussfolgerung]:

1. **Config-Layer** – deklarative QMS-Substanz + Tool-Overlays.
2. **Template-Layer** – Textbausteine mit Variablen; beim Deployment gerendert und in die Zielplattform geschrieben.
3. **Adapter-Layer** – pro Tool ein Übersetzer von Config+Templates in echte Objekte.
4. **CLI-Layer** – ein Einstiegspunkt, idempotent.

## 6. Technische Entscheidungen

* **Config-Format: YAML** (bestätigt).
* **Sprache: Python als Kern/Orchestrator + im M365-Adapter PnP PowerShell per shell-out** (bestätigt).
* **Config-Struktur: tool-neutrale Kern-Config + Tool-Overlays** (bestätigt).

## 7. Wiederverwendbarkeit (bestätigt)

* Multi-Tenant: gleiche QMS-Substanz, pro Kunde ein Overlay/Instanz.
* Versioniert (Semver + Changelog), Adapter als austauschbare Module.
* Erweiterbar: neue Dokumente/Prozesse ergänzen, ohne Adapter zu ändern.

## 8. Nicht-Ziele / Grenzen

* Kein Erzeugen der akkreditierten Zertifizierungs-Reife (Betriebs-/Nachweisphase, s. Abschnitt 2).
* Auf Atlassian: Freigabe/Versionierung nur teil-automatisiert (App-abhängig).
* Der Generator liefert ein audit-*fähiges Gerüst*; die inhaltliche Prozessarbeit bleibt manuell.

## 9. Getroffene Entscheidungen

### 9.1 Self-hosted-Zielzustand (bestätigt): XWiki + Redmine

* **XWiki** = Dokumenten-Ebene (QM-Handbuch, Policy, Prozeduren, Templates). LGPL-2.1, automatische Versionierung, REST-API, offizielles Docker-Image. **[Nicht verifiziert]:** exakte Ausprägung des Approval-/Publication-Workflows.
* **Redmine** = Record-/Tracking-Ebene (CAPA, NC, Audits, Ziele/KPIs). GNU GPL v2, REST-API, Docker Official Image.
* **Verifizierte API-Grenze (Redmine):** Custom-Field-Definitionen sind per API nur lesbar; das Anlegen neuer Felder ist per API nicht möglich. Der Generator seedet Projekte/Issues/Feldwerte; die Felddefinitionen müssen einmalig manuell eingerichtet werden.

### 9.2 Config-Struktur (bestätigt): tool-neutrale Kern-Config + Tool-Overlays.

### 9.3 Sprache (bestätigt): Python-Kern + PnP-PowerShell im M365-Adapter.

### 9.4 Prozesszeichnung (bestätigt): Fallback draw.io (Docker-self-hostbar), PNG/SVG-Export in XWiki-Seite einfügen.

## 10. Lieferreihenfolge (bestätigt)

**self-hosted-Adapter zuerst**, dann Atlassian, dann M365. Kern-Config + Templates zuerst (tool-neutral).

---

## Anhang: Auftrag an Claude Code

* Erzeuge das Repo-Gerüst gemäß Abschnitt 5, beginnend mit Kern-Config + Templates + **self-hosted-Adapter**.
* Halte die Plattform-Constraints aus Abschnitt 4 ein.
* Fülle **keine** der offenen Entscheidungen selbstständig – frage nach oder markiere als TODO.
* Kennzeichne im Code/Docs, was Annahme vs. bestätigte Vorgabe ist.
