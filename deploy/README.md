# Deploy (Deployability concept)

Two acceptable paths for judging:
1. **Local + documented** — runs locally with the steps in the root README. Sufficient:
   judging accepts a public repo + setup instructions; a live URL is not required.
2. **Cloud Run** — container this image and deploy. Document the exact commands.

Either way: the MCP server is bundled and spawned by the agent over stdio — no separate
service to stand up. Keep secrets in the environment, never in the image.
