#!/usr/bin/env python3
"""Update the list of Lumen models in ~/.config/opencode/opencode.json.

opencode never asks Lumen which models it offers. It reads the list from
that file, so a model Lumen adds stays invisible until someone rewrites the
file. The zsh function in opencode.zsh runs this script each time Jake starts
opencode, so a new model appears at the next start.

Every model's longest reply is capped at 32768 tokens. Lumen reports larger
numbers for some models (256000 for qwen3-coder-next, whose context is
131066). With those numbers opencode asks for replies that fill the context,
and Lumen refuses them. LUMEN.md, under "The downloaded file's output
limits", gives the arithmetic.

The script replaces the Lumen model list and nothing else, copies the old
file to a dated backup before writing, and leaves the file alone whenever
anything goes wrong. It always exits 0, so opencode starts either way.

Usage: python3 lumen_refresh.py [--config PATH]
"""

import argparse
import copy
import datetime
import json
import os
import shutil
import sys
import tempfile
import urllib.request

CAP = 32768
MODELS_URL = "https://lumen.computes.illinois.edu/v1/models"
TIMEOUT_SECONDS = 5
DEFAULT_CONFIG = os.path.expanduser("~/.config/opencode/opencode.json")

# Used only when the file has no Lumen provider at all. The key is named,
# never written: opencode reads it from the environment.
LUMEN_PROVIDER = {
    "npm": "@ai-sdk/openai-compatible",
    "name": "Lumen",
    "options": {"baseURL": "https://lumen.computes.illinois.edu/v1",
                "apiKey": "{env:LUMEN_API_KEY}"},
}


def build_models(listing):
    """The opencode model list for Lumen's /v1/models reply. The rules are
    the ones in LUMEN.md's setup script. Raises ValueError when the reply is
    not a list of models or holds no model that takes text, because writing
    an empty list would leave opencode with no Lumen models."""
    data = listing.get("data") if isinstance(listing, dict) else None
    if not isinstance(data, list):
        raise ValueError("Lumen's reply holds no model list")
    models = {}
    for m in data:
        # opencode sends text; a model that takes only audio cannot answer.
        if "text" not in (m.get("input_modalities") or []):
            continue
        parent = m.get("parent")
        entry = {
            "name": m["id"] + " via Lumen"
                    + (f" (alias of {parent})" if parent else ""),
            "limit": {"context": m["max_model_len"],
                      "output": min(m.get("max_output_tokens") or CAP, CAP)},
            "cost": {"input": m["input_cost_per_million"],
                     "output": m["output_cost_per_million"]},
            "modalities": {"input": m["input_modalities"],
                           "output": m["output_modalities"]},
            # Lumen does not report tool support, and opencode can read or
            # edit a file only through a tool call.
            "tool_call": True,
        }
        if "image" in m["input_modalities"]:
            entry["attachment"] = True
        if m.get("supports_reasoning"):
            entry["reasoning"] = True
        models[m["id"]] = entry
    if not models:
        raise ValueError("Lumen's reply lists no model that takes text")
    return models


def merge(config, models):
    """A copy of config with the Lumen model list replaced by models and
    every other setting left as it was."""
    new = copy.deepcopy(config)
    lumen = new.setdefault("provider", {}).setdefault(
        "lumen", copy.deepcopy(LUMEN_PROVIDER))
    lumen["models"] = models
    return new


def lumen_models_in(config):
    return config.get("provider", {}).get("lumen", {}).get("models", {})


def write_atomically(path, config):
    """Write to a temporary file beside path and rename it over path. The
    opencode server rereads the file when it changes, and the rename keeps it
    from reading a file that is only half written."""
    folder = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=folder, prefix=".opencode.json.")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(config, fh, indent=2)
            fh.write("\n")
        shutil.copymode(path, tmp)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def refresh(config_path, fetch, today):
    """Update the Lumen model list in config_path. fetch() returns Lumen's
    /v1/models reply. Returns the message to show Jake, or "" when nothing
    changed."""
    not_updated = "Lumen model list not updated"
    if not os.path.exists(config_path):
        return (f"{not_updated}: {config_path} does not exist. Set it up with "
                "the script in ~/repos/ai_workflow/opencode/LUMEN.md.")
    try:
        with open(config_path, encoding="utf-8") as fh:
            config = json.load(fh)
    except (OSError, ValueError) as err:
        return f"{not_updated}: could not read {config_path} ({err})."
    try:
        listing = fetch()
    except Exception as err:  # any failure to reach Lumen keeps the old list
        return f"{not_updated}: could not get the list from Lumen ({err})."
    try:
        models = build_models(listing)
    except (ValueError, KeyError, TypeError) as err:
        return f"{not_updated}: {err}."

    new = merge(config, models)
    if new == config:
        return ""
    old = lumen_models_in(config)
    added = sorted(set(models) - set(old))
    removed = sorted(set(old) - set(models))

    # Keep the first backup of the day: it holds the file as it was before
    # any change that day.
    backup = f"{config_path}.before-refresh-{today}"
    if not os.path.exists(backup):
        shutil.copy2(config_path, backup)
    write_atomically(config_path, new)

    lines = [f"Lumen model list updated in {config_path}."]
    if added:
        lines.append("Added: " + ", ".join(added) + ".")
    if removed:
        lines.append("Removed: " + ", ".join(removed) + ".")
    if not added and not removed:
        lines.append("Same models; details such as limits or prices changed.")
    lines.append(f"Old file: {backup}")
    return "\n".join(lines)


def fetch_listing():
    """Lumen's /v1/models reply, using the key in LUMEN_API_KEY."""
    key = os.environ.get("LUMEN_API_KEY")
    if not key:
        raise RuntimeError("LUMEN_API_KEY is not set")
    request = urllib.request.Request(
        MODELS_URL, headers={"Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as resp:
        return json.load(resp)


def main(argv=None, fetch=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    args = parser.parse_args(argv)
    try:
        message = refresh(args.config, fetch or fetch_listing,
                          datetime.date.today().isoformat())
    except Exception as err:  # a failed refresh must never stop opencode
        message = f"Lumen model list not updated: {err}."
    if message:
        print(message, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
