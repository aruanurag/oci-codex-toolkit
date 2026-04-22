# Bundled Oracle Reference Architectures

These Oracle-provided `.drawio` files were imported from the user-supplied zip archives and are now bundled under:

- `assets/reference-architectures/oracle/`

Use them as the first visual baseline before inventing a layout from scratch. For mixed requests, prefer one primary reference and optionally one or two supporting references that cover DR, security, or workload-specific nuances.

You can inspect matches with:

```bash
python3 scripts/select_reference_architecture.py --query "your request" --bundle --top 5
```

## Imported Reference Set

| Bundled `.drawio` | Source archive(s) | Best-fit use |
| --- | --- | --- |
| `ai-llm-workflow-architecture.drawio` | `ai-llm-workflow-architecture-oracle.zip` | LLM, RAG, workflow, and GenAI pipeline layouts |
| `architecture-ai-vision.drawio` | `architecture-ai-vision-oracle.zip` | OCI Vision and event-driven AI image-processing patterns |
| `architecture-use-bastion-service.drawio` | `architecture-use-bastion-service-oracle.zip` | Bastion-based administrative access into private OCI resources |
| `autonomous-database-db-at-azure-diagram.drawio` | `autonomous-database-db-azure-diagram-oracle.zip` | Autonomous Database patterns that span OCI and Azure |
| `cloudany-migration-dr-logical-arch.drawio` | `cloudany-migration-dr-logical-arch-oracle.zip` | Migration and DR posture, especially failover or standby concepts |
| `deploy-ai-chatbot-arch.drawio` | `deploy-ai-chatbot-arch.zip` | Chatbot and OCI Generative AI application layouts |
| `exadb-dr-on-db-at-azure.drawio` | `exadb-dr-db-azure-oracle.zip` | Exadata DR or cross-cloud database resilience patterns |
| `hub-spoke-oci.drawio` | `hub-and-spoke-oci.zip` | Hub-and-spoke VCN, LPG, DRG, FastConnect, VPN, and transit networking |
| `multi-tenant-app-oci.drawio` | `multi-tenant-app-oci-oracle.zip` | Multi-tenant SaaS isolation and tenant-aware application layouts |
| `mushop-infrastructure.drawio` | `mushop-infrastructure-oracle.zip` | MuShop-style OKE e-commerce and microservice baselines |
| `oke-architecture-diagram.drawio` | `oke-architecture-diagram-oracle.zip` | OKE platform deployments with OCI network framing |
| `oracle-integration-rest-oauth-diagram.drawio` | `oracle-integration-rest-oauth-diagram-oracle.zip` | Integration and OAuth-secured REST interaction patterns |
| `secure-web-applications-oci-api-gateway-open-id-architecture.drawio` | `secure-web-applications-oci-api-gateway-open-id-architecture.zip`, `secure-web-applications-oci-api-gateway-open-id-architecture (1).zip` | Secure web application topologies with API Gateway and OpenID Connect |
| `secure-web-applications-oci-api-gateway-open-id-data-flow.drawio` | `secure-web-applications-oci-api-gateway-open-id-data-flow.zip` | Detailed data-flow companion for the secure API Gateway and OpenID pattern |

## Selection Guidance

- If the request clearly names a topology, keep that as the primary reference.
- If the request mixes workload and DR or security concerns, use a supporting reference rather than replacing the primary topology baseline.
- Prefer `architecture` references over `data-flow` or `logical` references when generating physical OCI deployment diagrams.
- Treat the Oracle examples as visual/layout baselines, not as an excuse to skip OCI network completeness or icon-resolution checks.
