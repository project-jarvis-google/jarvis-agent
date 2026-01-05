# dynamic_analysis_tools.py

import csv, json, io
from datetime import datetime

def normalize_timestamp(ts):
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).isoformat()
    except Exception:
        return None

def LogAnalysisTool(raw_log_text: str, file_type: str) -> dict:
    """
    Normalize raw log text (csv, tsv, ndjson, json) into:
    { "events": [ {timestamp, user_id, screen_id, event_type, element_id, metadata}, ... ] }
    """
    events = []

    if file_type == "json":
        data = json.loads(raw_log_text)
        if isinstance(data, dict) and "events" in data:
            # Already normalized
            return data
        elif isinstance(data, list):
            rows = data
        else:
            return {"error": "JSON not in expected format."}

    elif file_type in ["csv", "tsv"]:
        delimiter = "," if file_type == "csv" else "\t"
        reader = csv.DictReader(io.StringIO(raw_log_text), delimiter=delimiter)
        rows = list(reader)

    elif file_type == "ndjson":
        rows = [json.loads(line) for line in raw_log_text.splitlines() if line.strip()]

    else:
        return {"error": "Unsupported file type."}

    for r in rows:
        ts = normalize_timestamp(r.get("timestamp"))
        if not ts:
            continue

        meta = r.get("metadata", {})
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except Exception:
                meta = {"raw": meta}

        event = {
            "timestamp": ts,
            "user_id": r.get("user_id"),
            "screen_id": r.get("screen_id"),
            "event_type": r.get("event_type"),
            "element_id": r.get("element_id"),
            "metadata": meta,
        }

        events.append(event)

    #return {"events": events}
    return json.dumps({"events": events})
