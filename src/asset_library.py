import json
import os
from datetime import datetime
from src.config import ASSET_LIBRARY_PATH


def load_library():
    if not os.path.exists(ASSET_LIBRARY_PATH):
        return {"records": []}
    with open(ASSET_LIBRARY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_library(library):
    os.makedirs(os.path.dirname(ASSET_LIBRARY_PATH), exist_ok=True)
    with open(ASSET_LIBRARY_PATH, "w", encoding="utf-8") as f:
        json.dump(library, f, ensure_ascii=False, indent=2)


def add_record(account, driver_result, templates, candidates, similarity_results, high_analyses):
    library = load_library()
    for cand in candidates:
        if "status" not in cand:
            cand["status"] = "pending_review"
    record = {
        "id": f"rec_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "created_at": datetime.now().isoformat(),
        "account": account,
        "driver_result": driver_result,
        "templates": templates,
        "candidates": candidates,
        "similarity_results": similarity_results,
        "high_performance_topics": [a.get("topic", "") for a in high_analyses[:3]],
    }
    library["records"].append(record)
    save_library(library)
    return record["id"]


def update_candidate_status(record_id, candidate_index, status):
    library = load_library()
    for record in library["records"]:
        if record["id"] == record_id:
            if 0 <= candidate_index < len(record["candidates"]):
                record["candidates"][candidate_index]["status"] = status
                save_library(library)
                return True
    return False


def update_record_status(record_id, status, feedback=None):
    library = load_library()
    for record in library["records"]:
        if record["id"] == record_id:
            record["status"] = status
            if feedback:
                record["feedback"] = feedback
            save_library(library)
            return True
    return False


def update_candidate_performance(record_id, candidate_index, performance_data):
    library = load_library()
    for record in library["records"]:
        if record["id"] == record_id:
            if 0 <= candidate_index < len(record["candidates"]):
                record["candidates"][candidate_index]["performance"] = performance_data
                save_library(library)
                return True
    return False


def delete_record(record_id):
    library = load_library()
    library["records"] = [r for r in library["records"] if r["id"] != record_id]
    save_library(library)
    return True


def update_candidate(record_id, candidate_index, new_content):
    library = load_library()
    for record in library["records"]:
        if record["id"] == record_id:
            if 0 <= candidate_index < len(record["candidates"]):
                record["candidates"][candidate_index]["content"] = new_content
                save_library(library)
                return True
    return False


def get_all_records():
    library = load_library()
    return library.get("records", [])


def get_pending_records():
    library = load_library()
    return [r for r in library.get("records", []) if r["status"] == "pending_review"]
