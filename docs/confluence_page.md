# Implementation Document Generator (`/imp-doc-creator`)

## Background

The **Implementation Document Generator** is a Claude Code skill that automates the creation of merchant-facing integration documentation from BDM scoping CSVs.

### The Problem

During merchant handover, TAMs receive an **Implementation Scoping Document** (CSV) from the BDM team listing which providers, payment methods, and features are in scope. TAMs then need to manually create integration documentation with the correct Yuno docs links for each feature -- a repetitive and error-prone process.

### The Solution

The `/imp-doc-creator` skill reads the scoping CSV, identifies which features are implemented for each provider, and automatically generates:

- **Markdown file** (`.md`) -- editable by TAMs who want to customize or add notes before sharing
- **PDF file** (`.pdf`) -- professionally styled, merchant-facing document ready to share

The generated document includes:
- A **Merchant Scope Summary** table showing each provider, payment method, and their implemented features
- **Sequenced integration steps** with direct links to the relevant Yuno documentation pages
- **Master steps** (required for all integrations) followed by **feature-specific steps**

> **Note:** This tool generates integration documentation only. It does **not** generate test cases. For test case generation, use the [legacy web app](#legacy-web-app).

---

## Prerequisites

| Requirement | Details |
|---|---|
| Claude Code | Must have Claude Code installed and running (CLI, desktop app, or IDE extension) |
| Scoping CSV | The BDM Implementation Scoping Document exported as CSV |

No additional setup, API keys, or dependencies are needed. The skill is fully self-contained.

---

## How to Use

### Step 1: Invoke the Skill

Open Claude Code in any directory and type:

```
/imp-doc-creator
```

### Step 2: Answer the Prompts

Claude will ask you three questions:

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  What is the path to the BDM scoping CSV file?          │
│                                                         │
│  ○ Use sample CSV                                       │
│  ○ Other: [paste your CSV file path here]               │
│                                                         │
│  What is the merchant name and language?                 │
│                                                         │
│  ○ Defaults (Merchant, EN)                              │
│  ○ Custom: [e.g. "Merchant: SerEducacional English"]    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Tips:**
- You can drag & drop the CSV file into the terminal to paste its path
- Merchant name is used in the document title and output filename
- Supported languages: EN (English), ES (Spanish), PT (Portuguese)

### Step 3: Wait for Generation

Claude reads the CSV, matches features against the documentation rules, and generates both files:

```
╭──────────────────────────────────────────────────────────────╮
│                                                              │
│  CSV parsed:                                                 │
│  - 3 valid providers: PAGARME/CARD, PAGARME/PIX,            │
│    SAFRAPAY/CARD                                             │
│  - "Chargebacks/DisputesAPI/ Alerts" mapped to               │
│    Chargeback rule                                           │
│  - 20 implemented features across all providers              │
│                                                              │
│  Now let me read the feature rules and mapping to            │
│  generate the document.                                      │
│                                                              │
╰──────────────────────────────────────────────────────────────╯
```

### Step 4: Receive the Output

Claude confirms both files were created:

```
╭──────────────────────────────────────────────────────────────╮
│                                                              │
│  Both files generated:                                       │
│                                                              │
│  - SerEducacional_integration_doc.md  (7.1 KB)               │
│    → editable by TAMs                                        │
│                                                              │
│  - SerEducacional_integration_doc.pdf (11 KB)                │
│    → merchant-facing, professional styling                   │
│                                                              │
│  Summary:                                                    │
│  - 3 providers in scope                                      │
│  - 24 integration steps (3 master + 21 feature-specific)     │
│  - 19 implemented features per provider                      │
│                                                              │
╰──────────────────────────────────────────────────────────────╯
```

The files are created in your current working directory.

---

## Output Example

### PDF Output (Merchant-Facing)

The PDF is professionally styled with:
- Blue header bar with the merchant name
- Scope summary table with blue column headers
- Each integration step in a green-bordered box
- Clickable documentation URLs
- Page numbers (e.g., "Page 1/5")

**Page 1 -- Scope Summary + Master Steps:**

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  Implementation Documentation: SerEducacional                   │
│  ═══════════════════════════════════════════                     │
│                                                                 │
│  Generated on: 2026-03-30                                       │
│  Language: EN                                                   │
│                                                                 │
│                                                                 │
│  Merchant Scope Summary                                         │
│  ──────────────────────                                         │
│                                                                 │
│  ┌──────────┬────────────┬──────────────────────────────────┐   │
│  │ Provider │ Payment    │ Implemented Features             │   │
│  │          │ Method     │                                  │   │
│  ├──────────┼────────────┼──────────────────────────────────┤   │
│  │ PAGARME  │ CARD       │ Experience, Card Type Accepted,  │   │
│  │          │            │ Purchase, Refund, Cancel,        │   │
│  │          │            │ Partial Refund, Multiple Refunds │   │
│  │          │            │ Installments, 3DS, Split, ...    │   │
│  ├──────────┼────────────┼──────────────────────────────────┤   │
│  │ PAGARME  │ PIX        │ (same features)                  │   │
│  ├──────────┼────────────┼──────────────────────────────────┤   │
│  │ SAFRAPAY │ CARD       │ (same features)                  │   │
│  └──────────┴────────────┴──────────────────────────────────┘   │
│                                                                 │
│                                                                 │
│  Integration Steps                                              │
│  ──────────────────                                             │
│                                                                 │
│  Master Integration Steps                                       │
│                                                                 │
│  ┃ Step 1: Essential setup and configuration steps              │
│  ┃ required for all integrations.                               │
│  Documentation: https://docs.y.uno/docs/getting-started         │
│                                                                 │
│  ┃ Step 2: Testing cards                                        │
│  Documentation: https://docs.y.uno/docs/yuno-testing-gateway    │
│                                                                 │
│  ┃ Step 3: Payment status and response codes                    │
│  Documentation: https://docs.y.uno/reference/payment            │
│                                                                 │
│                                                         Page 1/5│
└─────────────────────────────────────────────────────────────────┘
```

**Pages 2-5 -- Feature-Specific Steps:**

Each feature-specific step shows:
- Step number and description with the feature name in parentheses
- A green left-border box for visual distinction
- A clickable documentation link below

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  Feature-Specific Integration Steps                             │
│                                                                 │
│  ┃ Step 4: Create payment documentation (Purchase)              │
│  Documentation: https://docs.y.uno/reference/create-payment     │
│                                                                 │
│  ┃ Step 6: Allows canceling authorized but not yet              │
│  ┃ captured payments. (Cancel)                                  │
│  Documentation: https://docs.y.uno/reference/cancel-payment     │
│                                                                 │
│  ┃ Step 7: Supports full or partial refunds. (Refund)           │
│  Documentation: https://docs.y.uno/reference/refund-payment     │
│                                                                 │
│  ...continues through Step 24 (ClickToPay)...                   │
│                                                                 │
│  ─────────────────────────────────────────                      │
│  This document was automatically generated from your            │
│  implementation scope using /imp-doc-creator.                   │
│                                                                 │
│                                                         Page 5/5│
└─────────────────────────────────────────────────────────────────┘
```

### Markdown Output (TAM-Editable)

The markdown file follows the same structure but is editable in any text editor:

```markdown
# Implementation Documentation: SerEducacional

**Generated on:** 2026-03-30
**Language:** EN

---

## Merchant Scope Summary

| Provider | Payment Method | Implemented Features |
|----------|---------------|---------------------|
| PAGARME  | CARD          | Experience, Purchase, Refund, ... |

---

## Integration Steps

### Master Integration Steps

#### Step 1: Essential setup and configuration

**Documentation:** [https://docs.y.uno/docs/getting-started](...)

### Feature-Specific Integration Steps

#### Step 4: Create payment documentation (Purchase)

**Documentation:** [https://docs.y.uno/reference/create-payment](...)
```

TAMs can edit this file to add custom notes, reorder steps, or remove steps that don't apply before converting to PDF.

---

## Supported Features

The tool recognizes 32 payment features from the scoping CSV. Each feature maps to specific Yuno documentation:

| Feature | Documentation Link |
|---|---|
| Purchase | [Create Payment](https://docs.y.uno/reference/create-payment) |
| Authorize | [Authorize Payment](https://docs.y.uno/reference/authorize-payment) |
| Capture | [Capture Authorization](https://docs.y.uno/reference/capture-authorization) |
| Cancel | [Cancel Payment](https://docs.y.uno/reference/cancel-payment) |
| Verify | [Card Verification](https://docs.y.uno/docs/card-verification) |
| Refund | [Refund Payment](https://docs.y.uno/reference/refund-payment) |
| Recurring | [Subscriptions](https://docs.y.uno/docs/subscriptions) |
| Installments | [Create Installments Plan](https://docs.y.uno/reference/create-installments-plan) |
| 3DS | [3D Secure](https://docs.y.uno/docs/security-and-compliance/3d-secure) |
| Webhook | [Webhooks Overview](https://docs.y.uno/docs/webhooks-overview) |
| PaymentLink | [Create Payment Link](https://docs.y.uno/reference/create-payment-link) |
| TokenVault | [Enroll Payment Methods](https://docs.y.uno/docs/payment-features/enrollment/enroll-payment-methods) |
| Chargeback | [Chargeback Management](https://docs.y.uno/docs/payouts-and-disputes/chargeback-management) |
| Split | [Split Payments Marketplace](https://docs.y.uno/docs/payment-features/split-payments-marketplace) |
| Experience | [Choose Integration](https://docs.y.uno/docs/choose-the-right-integration-for-you) |
| Card_Type | [Cards](https://docs.y.uno/docs/cards) |
| Network_Tokens | [Network Tokens](https://docs.y.uno/docs/network-tokens) |
| ApplePay | [Apple Pay](https://docs.y.uno/docs/apple-pay) |
| GooglePay | [Google Pay](https://docs.y.uno/docs/google-pay) |
| ClickToPay | [Click to Pay](https://docs.y.uno/docs/click-to-pay) |
| Conciliations | [Reconciliations](https://docs.y.uno/docs/reconciliations) |
| SubMerchants | [Manage Sellers](https://docs.y.uno/reference/sellers/manage-sellers) |

Plus: Partial_Capture, Partial_Refund, Multiple_Captures, Multiple_Refunds, Checkout, Redirect, External_Refunds, Market_Segment, Soft_Descriptor, APM_Expiration.

---

## How It Determines What's Implemented

The tool reads the **INFORMATION** column for each provider in the CSV. A feature is considered **implemented** if the value is anything other than:

- `FALSE`
- Empty / blank
- `#N/A`
- `No`
- `Not Applicable`

This means descriptive values like `"SDK Yuno"`, `"Yes, using Yuno's API"`, `"Credit"`, or `"Yuno"` are all treated as implemented.

---

## Adding or Updating Documentation Links

The feature-to-documentation mapping lives in:

```
~/.claude/skills/imp-doc-creator/references/feature_rules.json
```

To update a documentation URL, edit the `integration_steps` array for the relevant feature:

```json
{
  "Purchase": {
    "feature_name": "Purchase",
    "by_payment_method": {
      "universal": {
        "integration_steps": [
          {
            "documentation_url": "https://docs.y.uno/reference/create-payment",
            "comment": "Create payment documentation"
          }
        ]
      }
    }
  }
}
```

To add a new feature, add a new entry under `rules` with the same structure, and add the CSV-to-key mapping in `references/feature-name-mapping.md`.

---

## Legacy Web App

The original web application is still available for **test case generation** (which the skill intentionally does not do).

To run it:

```bash
cd /path/to/imp-doc-creator
./run_web.sh
# Opens at http://localhost:5001
```

The web app supports:
- Drag & drop CSV upload
- Test case generation with environment filtering (sandbox/production)
- Multiple output formats (HTML, DOCX, Markdown)
- Interactive feature rules management with inline editing
- Multi-language support (EN, ES, PT)

---

## Source Code

- **Skill location:** `~/.claude/skills/imp-doc-creator/`
- **Legacy web app:** [GitHub - imp-doc-creator](https://github.com/pedroyuno/imp-doc-creator)

---

*Last updated: 2026-03-30*
