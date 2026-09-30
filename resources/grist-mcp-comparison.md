# Grist MCP servers

| Option | Best for | Main limitations |
|---|---|---|
| [Official Grist MCP](https://support.getgrist.com/mcp/) | Hosted or Full Grist; OAuth; current pages, widgets, attachments, and snapshots | Full-edition feature; no documented tools for exports, Automations, or service-account administration |
| [Python `mcp-server-grist`](https://pypi.org/project/mcp-server-grist/) | ACL administration, exports, attachment upload, and broad REST operations | API-key authentication; no pages/widgets or recent custom-widget features |
| [TypeScript `grist-mcp-server`](https://github.com/gwhthompson/grist-mcp-server) | Pages, linked widgets, summary tables, upserts, and compact tool schemas | API-key authentication; no attachments, exports, or recent custom-widget settings |

## Recommendation

Use the official server when available. Use the Python server for administrative and export workflows. Use the TypeScript server for agent-built dashboards and structured Grist applications.

Recent Grist 1.7.18–1.7.19 features—custom-widget mappings/options and native Calendar behavior—are verified only for the official server.

Full comparison: [`../docs/2026-09-24-grist-mcp-server-comparison.md`](../docs/2026-09-24-grist-mcp-server-comparison.md).
