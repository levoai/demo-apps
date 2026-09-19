# Agent Instructions

## This repository is public — never reference customers

`levoai/demo-apps` is a **public** GitHub repository. Never add anything that
identifies or hints at a specific customer, prospect, or partner. This applies
everywhere: code, comments, docstrings, commit messages, PR titles/descriptions,
branch names, file names, fixture/test data, OpenAPI specs, and any other
artifact that ends up in this repo's history.

Specifically, never include:

- A customer's name, brand, ticker/company identifier, or any obvious
  abbreviation/misspelling of one (e.g. writing it split up or with extra
  punctuation still counts).
- Endpoint paths, operation IDs, class names, or variable names that echo a
  customer's product, domain, or industry jargon closely enough that someone
  could reverse-engineer which customer inspired the fixture (e.g. naming
  something after a specific trading platform's terminology because a
  brokerage customer uses that pattern).
- Screenshots, logs, tickets, URLs, or support-request text that came from a
  real customer engagement.

When a fixture is modeled on a real customer's system or a real engagement
finding, generalize it before it lands here:

- Describe the underlying *pattern* generically (e.g. "dual-token OR-auth",
  "step-up token fixture") instead of naming the customer or their product.
- Name endpoints, models, and variables after the generic pattern, not the
  customer's terminology.
- If a commit message or PR needs context for why a fixture exists, describe
  the vulnerability class or auth pattern being demonstrated, not the
  customer it came from.

If you are about to write a customer name, or something a search engine could
map back to one, stop and ask the user how to generalize it before committing
or pushing anything.
