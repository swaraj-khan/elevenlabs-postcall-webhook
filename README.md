# ElevenLabs Post Call Webhook Processor

A serverless webhook processor that receives post-call events from ElevenLabs, stores call data in Supabase, uploads audio recordings, and generates structured summaries using Google Gemini.

This service is designed to run on **AWS Lambda using the Serverless Framework** and acts as the **data ingestion and analysis layer** for voice conversations.

The webhook processes events after a call ends, analyzes the transcript using AI, and stores structured insights that can later be retrieved by downstream APIs.

---

# Purpose

This service processes voice call events and transforms raw call data into structured insights that power automated workflows.

Specifically, it:

- Receives call events from ElevenLabs webhooks
- Uploads base64 encoded call recordings to Supabase Storage
- Stores call metadata and transcripts in Supabase
- Analyzes conversations using Google Gemini
- Generates structured summaries describing user intent and call outcomes
- Stores summaries in the `voice_calls` table for downstream APIs

This allows the system to convert long voice conversations into actionable data that can drive recruitment automation.

---

# Deployment Architecture

The webhook processor runs as a **Python AWS Lambda function** deployed using the **Serverless Framework**.

Components involved:

- AWS Lambda — serverless compute runtime
- API Gateway — receives webhook requests
- Supabase Database — stores call metadata, transcripts, and summaries
- Supabase Storage — stores call audio recordings
- Google Gemini — analyzes transcripts and generates structured summaries
- Serverless Framework — deployment and infrastructure management

---

# Webhook Flow

1. ElevenLabs sends a webhook after a call event.
2. The Lambda function receives the payload.
3. Audio (base64) is uploaded to Supabase Storage.
4. Call metadata and transcript are stored in Supabase.
5. The transcript is cleaned and formatted.
6. Google Gemini analyzes the conversation using the prompt defined in `prompts/intention-finder.md`.
7. A structured summary is generated.
8. The summary is stored in the `voice_calls` table.

---

# Webhook Events

The webhook may receive different event types such as:

- `post_call_audio`
- `post_call_transcript`
- `call_completed`

The processor extracts relevant information including:

- call ID
- caller phone number
- transcript
- audio recording
- call duration
- cost
- metadata

---

# Example Webhook Payload

Example payload received from ElevenLabs:

```json
{
  "type": "post_call_audio",
  "data": {
    "conversation_id": "conv_8901kktmb51qfaabxyygahbefg38",
    "status": "completed",
    "transcript": [
      {
        "role": "agent",
        "message": "Hello, we provide verified overseas job opportunities."
      },
      {
        "role": "user",
        "message": "I am not interested in overseas jobs."
      }
    ],
    "full_audio": "<base64 encoded audio>",
    "metadata": {
      "call_duration_secs": 210,
      "cost": 0.08,
      "phone_call": {
        "from_number": "+919999999999",
        "to_number": "+918000000000"
      }
    }
  }
}
```

---

# Generated Summary Structure

The Gemini model generates summaries in a strict structured format.

```
User Intent: <user's primary goal>
Job Role: <job role discussed or selected>
Country Preference: <country mentioned>
Action Taken: <what occurred during the call>
Next Step / Request: <user's requested next action>
Callback Time: <specific callback datetime if requested, otherwise blank>
```

Example stored summary:

```
User Intent: Not interested in overseas job opportunities.
Job Role:
Country Preference:
Action Taken: User expressed disinterest.
Next Step / Request: User ended the call.
Callback Time:
```

---

# Database Schema

Call data is stored in the `voice_calls` table in Supabase.

```sql
create table public.voice_calls (
  id uuid not null default gen_random_uuid (),
  call_id text not null,
  caller text null,
  callee text null,
  status text null,
  duration integer null,
  transcript text null,
  summary text null,
  recording_path text null,
  cost numeric null,
  metadata jsonb null,
  raw_payload jsonb null,
  created_at timestamp with time zone null default now(),
  constraint voice_calls_pkey primary key (id),
  constraint voice_calls_id_key unique (call_id)
);
```

Recommended index for fast lookup:

```sql
CREATE INDEX idx_voice_calls_lookup
ON voice_calls (caller, created_at DESC);
```

---

# Supabase Storage

Audio recordings are uploaded to the Supabase Storage bucket.

Default bucket:

```
call-recordings
```

File naming convention:

```
<call_id>.mp3
```

Example:

```
conv_8901kktmb51qfaabxyygahbefg38.mp3
```

---

# Environment Variables

Create a `.env` file in the project root.

```
SUPABASE_URL=xxxx
SUPABASE_KEY=xxxx
BUCKET_NAME=call-recordings
CALLEE_NUMBER=xxxx

GOOGLE_API_KEY=xxxx
GEMINI_MODEL=gemini-2.5-flash
```

---

# Project Structure

```
project/
│
├── app.py
├── prompts/
│   └── intention-finder.md
│
├── requirements.txt
├── serverless.yml
```

The `prompts/intention-finder.md` file defines the prompt used for conversation analysis.

---

# Local Development

Install dependencies.

```
pip install -r requirements.txt -t python
```

Run locally with Serverless Offline.

```
npx serverless offline
```

---

# Deployment

Make sure **Docker is running** because the Serverless Python requirements plugin builds Lambda-compatible packages using Docker.

Deploy the webhook processor:

```
serverless deploy
```

The deployment will:

- Package the Lambda function
- Install Python dependencies
- Deploy the webhook endpoint
- Configure API Gateway

After deployment, the webhook URL will be available via API Gateway.

---

# End-to-End System Architecture

```
Voice Call
   │
   ▼
ElevenLabs
   │
   ▼
Webhook Processor (Lambda)
   │
   ├── Upload audio → Supabase Storage
   ├── Store transcript → Supabase DB
   └── Generate summary → Gemini
            │
            ▼
       voice_calls table
            │
            ▼
Conversation Analyzer API
            │
            ▼
Recruitment Workflow System
```

The webhook processor acts as the **data ingestion and AI analysis layer**, while the API service acts as the **data retrieval layer**.