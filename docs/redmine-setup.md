# Redmine Setup — Manual Custom Field Definitions

## Why Manual?

The Redmine REST API supports reading custom field definitions (`GET /custom_fields.json`)
but **cannot create them**. This is a verified API limitation.

The qms-kit deployer seeds projects, issues, and field *values* automatically.
Field *definitions* must be created once manually before the first deployment.

## Required Custom Fields

Create the following fields in **Administration → Custom Fields** in Redmine.
Assign each field to the appropriate tracker.

### Nonconformity (NC) tracker

| Field name | Type | Required |
|------------|------|----------|
| Detected By | Text | Yes |
| Severity | List: Low / Medium / High / Critical | Yes |
| Root Cause | Long text | No |
| Correction | Long text | No |
| Correction Date | Date | No |

### CAPA tracker

| Field name | Type | Required |
|------------|------|----------|
| NC Reference | Text | No |
| Root Cause | Long text | Yes |
| Corrective Action | Long text | Yes |
| Effectiveness Check | Long text | No |
| Effectiveness Check Date | Date | No |

### Internal Audit tracker

| Field name | Type | Required |
|------------|------|----------|
| Auditor | Text | Yes |
| Audit Scope | Text | Yes |
| Findings | Long text | No |
| Observations | Long text | No |
| Follow-up Date | Date | No |

### KPI Measurement tracker

| Field name | Type | Required |
|------------|------|----------|
| KPI ID | Text | Yes |
| Period | Text | Yes |
| Target | Text | Yes |
| Actual | Text | Yes |
| Trend | List: Up / Stable / Down | No |
| Action Required | Boolean | No |

## Tracker Names

The tracker names in Redmine must match the values in your overlay config
(`config/clients/<client>.yaml` → `redmine.tracker_mapping`).

Default mapping from `config/selfhosted.yaml`:

```yaml
tracker_mapping:
  nc: "Nonconformity"
  capa: "CAPA"
  audit: "Internal Audit"
  kpi: "KPI Measurement"
```

Create trackers in **Administration → Trackers** before creating custom fields.

## After Manual Setup

Once fields and trackers exist, run the deployer normally:

```bash
python -m cli deploy --target selfhosted --config config/clients/<client>.yaml
```

The deployer will find the trackers by name and seed issues with the correct field values.
