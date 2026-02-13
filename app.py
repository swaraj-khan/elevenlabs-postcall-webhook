import sys
sys.path.append('/var/task/python')

import os
import uuid
import base64
import json
import os

if os.getenv("IS_OFFLINE"):
    from dotenv import load_dotenv
    load_dotenv()

from supabase import create_client


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME", "call-recordings")
CALLEE_NUMBER = os.getenv("CALLEE_NUMBER")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def upload_base64_audio(base64_str: str, call_id: str):
    try:
        if not base64_str:
            return None
        audio_bytes = base64.b64decode(base64_str)
        file_path = f"{call_id}.mp3"
        supabase.storage.from_(BUCKET_NAME).upload(
            file_path,
            audio_bytes,
            {"content-type": "audio/mpeg"},
        )
        return file_path

    except Exception as e:
        print("Audio upload failed:", e)
        return None


def lambda_handler(event, context):
    try:
        print("RAW EVENT:", json.dumps(event))

        payload = None
        body = event.get("body") if isinstance(event, dict) else None

        if body:
            if event.get("isBase64Encoded"):
                body = base64.b64decode(body).decode("utf-8")

            if isinstance(body, str):
                payload = json.loads(body)
            else:
                payload = body
        else:
            payload = event if isinstance(event, dict) else {}

        if not isinstance(payload, dict):
            payload = {}

        event_type = payload.get("type")
        print("EVENT TYPE:", event_type)

        data = payload.get("data", {}) or {}
        meta = data.get("metadata", {}) or {}

        call_id = (
            data.get("conversation_id")
            or data.get("call_id")
            or str(uuid.uuid4())
        )

        status = data.get("status")
        transcript = data.get("transcript")

        duration = meta.get("call_duration_secs") or meta.get("duration")
        cost = meta.get("cost") or meta.get("call_charge")

        phone_call = meta.get("phone_call") or {}
        caller = phone_call.get("from_number") or data.get("user_id")
        callee = phone_call.get("to_number") or CALLEE_NUMBER

        recording_path = None
        if event_type == "post_call_audio":
            base64_audio = data.get("full_audio")
            if base64_audio:
                recording_path = upload_base64_audio(base64_audio, call_id)

        update_data = {
            "call_id": call_id,
            "metadata": data,
            "raw_payload": payload,
        }

        if caller:
            update_data["caller"] = caller
        if callee:
            update_data["callee"] = callee
        if status:
            update_data["status"] = status
        if duration:
            update_data["duration"] = duration
        if transcript:
            update_data["transcript"] = str(transcript)
        if cost:
            update_data["cost"] = cost
        if recording_path:
            update_data["recording_path"] = recording_path

        supabase.table("voice_calls").upsert(
            update_data,
            on_conflict="call_id",
        ).execute()

        return {
            "statusCode": 200,
            "body": json.dumps({"ok": True})
        }

    except Exception as e:
        print("WEBHOOK ERROR:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps({"ok": False, "error": str(e)})
        }
