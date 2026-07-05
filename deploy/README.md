# Deploy to Google Cloud Run (from scratch)

The whole app — the FastAPI web layer, the one ADK agent, and the bundled stdio MCP server —
ships as **one container** (`Dockerfile` at the repo root). The agent spawns the MCP server as a
local subprocess, so there is no second service to stand up. These steps assume you start with
**no GCP account**.

**Default model: Gemini 3.5 Flash via Vertex AI.** This path needs **no API key** — the Cloud Run
service account authenticates to Vertex via ADC — and the usage is covered by your Google Cloud
free-trial credit. (To deploy on DeepSeek instead, see the appendix at the bottom.)

> Two settings that matter:
> - **`--max-instances=1`** — the backend keeps onboarding sessions *in memory* and Cloud Run is
>   serverless, so this stops a live conversation being split across instances. (`--min-instances=1`
>   keeps one instance warm for a smooth demo; see the cost note.)
> - **`GOOGLE_CLOUD_LOCATION=global`** — newer Gemini models (3.x) are served on Vertex's *global*
>   endpoint and 404 on regional ones like `us-central1`. This is the model endpoint, separate from
>   your Cloud Run `--region`.

---

## 0. One-time account setup

1. Sign in to a Google account, go to <https://console.cloud.google.com>, accept the terms. New
   accounts get a free-trial credit.
2. **Enable billing** (required even on the free tier): Console → Billing → link a billing account.
   Starting the free trial does this for you.
3. **Install the gcloud CLI:** <https://cloud.google.com/sdk/docs/install> (macOS:
   `brew install --cask google-cloud-sdk`). Then authenticate:
   ```bash
   gcloud auth login
   ```

## 1. Create a project and pick a region

```bash
export PROJECT_ID="mom-day-organiser-$(date +%s)"   # globally-unique, lowercase/digits/hyphens
export REGION="us-central1"                          # Cloud Run region (model uses 'global', below)
export SERVICE="mom-day-organiser"

gcloud projects create "$PROJECT_ID"
gcloud config set project "$PROJECT_ID"
gcloud config set run/region "$REGION"
```

If you have more than one billing account, link it explicitly:
```bash
gcloud billing accounts list
gcloud billing projects link "$PROJECT_ID" --billing-account=XXXXXX-XXXXXX-XXXXXX
```

## 2. Enable the APIs

```bash
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  aiplatform.googleapis.com
```

## 3. Let the Cloud Run service account call Vertex

No API key — the runtime service account authenticates via ADC. Grant it the Vertex role:

```bash
export PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

## 4. Deploy

`--source .` lets Cloud Build build the root `Dockerfile` and push it for you (it auto-creates an
Artifact Registry repo on first run). Run from the **repo root**:

```bash
gcloud run deploy "$SERVICE" \
  --source . \
  --region "$REGION" \
  --allow-unauthenticated \
  --max-instances=1 \
  --min-instances=1 \
  --memory=1Gi \
  --cpu=1 \
  --timeout=300 \
  --set-env-vars=ADK_MODEL=gemini-3.5-flash,GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_CLOUD_LOCATION=global
```

On success gcloud prints a **Service URL** (`https://mom-day-organiser-XXXX.a.run.app`). Open it —
the tracker UI loads at `/`, and onboarding drives `/converse`.

> No `--set-secrets` here: Vertex uses the service account's ADC, so there is no key to inject.

## 5. Verify

```bash
URL="$(gcloud run services describe "$SERVICE" --region "$REGION" --format='value(status.url)')"
curl -sS "$URL/" | head -c 200          # should return the tracker HTML
```
Then open `$URL` and complete an onboarding conversation end to end — if it composes a day, Vertex
is working and drawing on your credit.

## 6. Update after a code change

Re-run the **same** `gcloud run deploy --source .` command from step 4. Each deploy is a new
revision; traffic shifts to it automatically.

## 7. Teardown (stop all costs)

```bash
gcloud run services delete "$SERVICE" --region "$REGION"
# or remove everything:
gcloud projects delete "$PROJECT_ID"
```

---

## Cost note

`--min-instances=1` keeps one instance always warm (no cold-start lag during a demo) but bills you
for that idle instance — a few dollars a month at this size, often inside the free tier. Outside
demo windows, redeploy with `--min-instances=0`; keep `--max-instances=1` regardless, since that is
the flag protecting in-memory sessions.

## Security checklist before sharing the URL

- **No API key anywhere** on the Vertex path — auth is the service account's ADC. (`.env` is
  gitignored and in `.dockerignore`, so nothing local leaks into the image either.)
- The service is `--allow-unauthenticated`, so anyone with the URL can use the agent and spend your
  Vertex credit. Fine for a judged demo; delete or lock down the service afterward.
- Personal data still stays in the parent's browser (localStorage); only `age_months` reaches a
  knowledge tool. The deployment does not change the privacy model.

## Troubleshooting

- **404 `Publisher model ... not found`** — almost always the region. Ensure
  `GOOGLE_CLOUD_LOCATION=global` (3.x Gemini is global-endpoint only). Confirm the exact model id at
  <https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/3-5-flash>.
- **403 / permission or project errors** — use the project *ID* (not the number) in
  `GOOGLE_CLOUD_PROJECT`, and confirm step 3 granted `roles/aiplatform.user`.
- **Build used buildpacks / wrong image** — make sure you ran from the repo root so Cloud Build
  picks up the root `Dockerfile`.

---

## Appendix — deploy on DeepSeek instead

DeepSeek runs via LiteLlm and needs `DEEPSEEK_API_KEY` (no Vertex). Store the key in Secret Manager
and swap the model env vars; everything else is identical.

```bash
# Enable Secret Manager and store the key (piped in, not echoed to shell history).
gcloud services enable secretmanager.googleapis.com
printf '%s' 'PASTE_YOUR_DEEPSEEK_KEY' | gcloud secrets create deepseek-key --data-file=-
gcloud secrets add-iam-policy-binding deepseek-key \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Deploy — secret instead of the Vertex env vars.
gcloud run deploy "$SERVICE" \
  --source . --region "$REGION" --allow-unauthenticated \
  --max-instances=1 --min-instances=1 --memory=1Gi --cpu=1 --timeout=300 \
  --set-env-vars=ADK_MODEL=deepseek/deepseek-chat \
  --set-secrets=DEEPSEEK_API_KEY=deepseek-key:latest
```

Switching backends is env-only (see `resolve_model()` in `agent/agent.py` and the profiles in
`.env.example`) — no code change either way.
