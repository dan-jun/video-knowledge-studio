# Current limitations

These are real product boundaries for version 0.1.0.

## Multi-user and cloud

- No user accounts, organizations, invitations or per-user data isolation.
- One deployment password protects one shared workspace.
- No web upload, object storage, transcoding, quotas or billing.
- Not ready to be marketed as a public multi-tenant SaaS.

## Content processing

- The importer creates skeletons; it does not generate verified notes by itself.
- Automated ASR, subtitle acquisition, key-frame selection, OCR and semantic review are
  not bundled as a one-click pipeline.
- No built-in SRT, PDF, Obsidian or Anki exporter yet.
- No automatic source-license verification.

## AI

- AI output can be wrong; uncertainty must remain visible.
- Vision quality depends on the configured model and attached frame.
- Jobs are kept in memory and disappear after process restart.
- Answers are returned after job completion; token streaming is not implemented.
- No cost estimator or hard per-user AI budget.

## Operations

- State files are not encrypted at rest; rely on operating-system disk protection.
- No database migration layer; state is JSON on disk.
- No built-in background job persistence or distributed workers.
- No rate limiting or comprehensive audit trail.
- Public deployment requires an additional authenticated HTTPS reverse proxy.
- Docker files are provided, but automated container CI is not yet included.

## Browser and media

- Optimized for current Edge/Chrome. Other browsers are not part of the test matrix yet.
- Video formats depend on browser decoding support.
- Frame extraction requires FFmpeg.
- Very large course libraries increase scan time and local disk use.
