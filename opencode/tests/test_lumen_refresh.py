#!/usr/bin/env python3
"""Tests for lumen_refresh.py, which updates the list of Lumen models in
~/.config/opencode/opencode.json each time Jake starts opencode.

Why this exists. opencode reads its list of Lumen models from that file and
never asks Lumen for it. On 2026-10-28 the file still held the list Lumen
offered for download on 2026-10-05, so two models Jake had accepted on
2026-10-27 (beam-1.0 and deepseek-v4.1-flash) were missing. The same file gave
qwen3-coder-next a longest reply of 256000 tokens against a context of 131066.
opencode then asked Lumen for replies that filled the whole context, Lumen
refused every such request, and opencode compacted the conversation and
started the step again, 370 times across four sessions. Capping every model's
longest reply at 32768 stopped the refusals. Jake chose on 2026-10-28 to have
a zsh function named `opencode` run this refresh before starting opencode.

What the tests require:

  * Every model the refresh writes has a longest reply of at most 32768
    tokens, whatever Lumen reports. This is the cap that stopped the
    refusals, so a refresh that dropped it would bring them back.
  * The refresh replaces the Lumen model list and nothing else. Jake's other
    settings ("instructions", "enabled_providers", any other provider, the
    Lumen URL and the key reference) come through unchanged, and it adds no
    default model when the file has none.
  * The API key itself never reaches the file. The file names the
    environment variable, "{env:LUMEN_API_KEY}", and keeps naming it.
  * When the list has not changed, the file is not rewritten and no backup
    is made, so starting opencode leaves no trace.
  * When the list has changed, the old file is copied to a dated backup
    before the new one is written, and the message names the models added
    and removed.
  * When anything goes wrong the file is left exactly as it was: Lumen does
    not answer, Lumen answers with an error instead of a list (a wrong key),
    Lumen answers with an empty list, the current file is not valid JSON, or
    there is no file. An empty list matters most: written out, it would
    leave opencode with no Lumen models at all.
  * The command always exits 0, so a failed refresh never stops opencode
    from starting.

Not covered: the network call itself, which the tests replace with a
stand-in, and the zsh function that calls the script. The cap also does not
remove the problem for every prompt: once a prompt passes the context minus
32768 tokens (98298 for qwen3-coder-next, 14022 for gemma-4-31b-it), opencode
again asks for a reply that fills the context.

Run: python3 opencode/tests/test_lumen_refresh.py
"""

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                ".."))
import lumen_refresh as lr  # noqa: E402

KEY_REF = "{env:LUMEN_API_KEY}"


def lumen_model(mid, context, output, inputs=("text",), parent=None):
    """One entry of Lumen's /v1/models reply, with the fields the refresh
    reads, in the shape Lumen returned on 2026-10-28."""
    return {"id": mid, "max_model_len": context, "max_output_tokens": output,
            "input_cost_per_million": 0.2, "output_cost_per_million": 1.2,
            "input_modalities": list(inputs), "output_modalities": ["text"],
            "parent": parent, "supports_reasoning": False}


# Lumen's list on 2026-10-28, cut to the cases that matter: a model whose
# reported longest reply exceeds its context, one under the cap, an audio-only
# model, and an alias.
LISTING = {"object": "list", "data": [
    lumen_model("qwen3-coder-next", 131066, 256000),
    lumen_model("gemma-4-31b-it", 46790, 16000, inputs=("text", "image")),
    lumen_model("granite-speech-4.1-2b-plus", 4096, 16384, inputs=("audio",)),
    lumen_model("glm", 524282, 131072, parent="glm-5.3"),
]}


def installed_config():
    """The file as it stood after the fix of 2026-10-28: Jake's two
    top-level settings and a Lumen list missing the alias glm."""
    return {
        "$schema": "https://opencode.ai/config.json",
        "instructions": ["CLAUDE.md", "POINT.md"],
        "enabled_providers": ["lumen"],
        "provider": {
            "lumen": {
                "npm": "@ai-sdk/openai-compatible",
                "name": "Lumen",
                "options": {"baseURL": "https://lumen.computes.illinois.edu/v1",
                            "apiKey": KEY_REF},
                "models": {
                    "qwen3-coder-next": {"name": "qwen3-coder-next via Lumen",
                                         "limit": {"context": 131066,
                                                   "output": 32768}},
                    "ornith-1.0-35b": {"name": "ornith-1.0-35b via Lumen",
                                       "limit": {"context": 262138,
                                                 "output": 32768}},
                },
            },
            "other": {"name": "a provider Jake added by hand"},
        },
    }


class BuildModels(unittest.TestCase):
    """The model list the refresh builds from Lumen's reply."""

    def test_no_longest_reply_exceeds_the_cap(self):
        models = lr.build_models(LISTING)
        for mid, entry in models.items():
            self.assertLessEqual(entry["limit"]["output"], 32768, mid)
        # Lumen reported 256000 for this model; the cap is what stops the
        # refusals.
        self.assertEqual(models["qwen3-coder-next"]["limit"]["output"], 32768)

    def test_a_smaller_reported_limit_is_kept(self):
        models = lr.build_models(LISTING)
        self.assertEqual(models["gemma-4-31b-it"]["limit"]["output"], 16000)

    def test_context_is_lumens_figure(self):
        models = lr.build_models(LISTING)
        self.assertEqual(models["qwen3-coder-next"]["limit"]["context"],
                         131066)

    def test_audio_only_models_are_left_out(self):
        # opencode sends text; a model that takes only audio cannot answer.
        self.assertNotIn("granite-speech-4.1-2b-plus",
                         lr.build_models(LISTING))

    def test_every_model_is_marked_as_making_tool_calls(self):
        # Lumen reports no tool support, and opencode can read or edit a file
        # only through a tool call (LUMEN.md, "Problems with the two official
        # routes").
        for entry in lr.build_models(LISTING).values():
            self.assertIs(entry["tool_call"], True)

    def test_an_error_reply_is_refused(self):
        with self.assertRaises(ValueError):
            lr.build_models({"error": "invalid api key"})

    def test_an_empty_list_is_refused(self):
        with self.assertRaises(ValueError):
            lr.build_models({"object": "list", "data": []})


class Merge(unittest.TestCase):
    """What the refresh keeps and what it replaces."""

    def test_only_the_lumen_model_list_changes(self):
        before = installed_config()
        after = lr.merge(installed_config(), lr.build_models(LISTING))
        after_models = after["provider"]["lumen"].pop("models")
        before["provider"]["lumen"].pop("models")
        self.assertEqual(after, before)
        self.assertEqual(set(after_models),
                         {"qwen3-coder-next", "gemma-4-31b-it", "glm"})

    def test_no_default_model_is_added(self):
        after = lr.merge(installed_config(), lr.build_models(LISTING))
        self.assertNotIn("model", after)

    def test_a_default_model_already_there_is_kept(self):
        config = installed_config()
        config["model"] = "lumen/glm-5.3"
        after = lr.merge(config, lr.build_models(LISTING))
        self.assertEqual(after["model"], "lumen/glm-5.3")


class Refresh(unittest.TestCase):
    """The refresh as the zsh function runs it, on a file in a temporary
    folder, with the network call replaced."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self._tmp.name, "opencode.json")
        self.backup = self.path + ".before-refresh-2026-10-29"

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, text):
        with open(self.path, "w", encoding="utf-8") as fh:
            fh.write(text)

    def read(self):
        with open(self.path, encoding="utf-8") as fh:
            return fh.read()

    def run_refresh(self, fetch):
        return lr.refresh(self.path, fetch, today="2026-10-29")

    def assert_untouched(self, original):
        self.assertEqual(self.read(), original)
        self.assertFalse(os.path.exists(self.backup))

    def test_a_changed_list_is_written_after_a_backup(self):
        original = json.dumps(installed_config(), indent=2) + "\n"
        self.write(original)
        message = self.run_refresh(lambda: LISTING)
        with open(self.backup, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), original)
        models = json.loads(self.read())["provider"]["lumen"]["models"]
        self.assertIn("glm", models)
        self.assertNotIn("ornith-1.0-35b", models)
        # The message names what changed, so Jake sees it when opencode starts.
        self.assertIn("glm", message)
        self.assertIn("gemma-4-31b-it", message)
        self.assertIn("ornith-1.0-35b", message)

    def test_an_unchanged_list_leaves_no_trace(self):
        config = lr.merge(installed_config(), lr.build_models(LISTING))
        original = json.dumps(config, indent=2) + "\n"
        self.write(original)
        mtime = os.path.getmtime(self.path)
        self.assertEqual(self.run_refresh(lambda: LISTING), "")
        self.assert_untouched(original)
        self.assertEqual(os.path.getmtime(self.path), mtime)

    def test_the_key_never_reaches_the_file(self):
        self.write(json.dumps(installed_config(), indent=2))
        saved = os.environ.get("LUMEN_API_KEY")
        os.environ["LUMEN_API_KEY"] = "sk_SENTINEL_DO_NOT_WRITE"
        try:
            self.run_refresh(lambda: LISTING)
        finally:
            if saved is None:
                os.environ.pop("LUMEN_API_KEY")
            else:
                os.environ["LUMEN_API_KEY"] = saved
        text = self.read()
        self.assertNotIn("sk_SENTINEL_DO_NOT_WRITE", text)
        self.assertEqual(
            json.loads(text)["provider"]["lumen"]["options"]["apiKey"],
            KEY_REF)

    def test_a_second_change_on_one_day_keeps_the_first_backup(self):
        # The day's backup should hold the file as it was before the first
        # change, not after it.
        original = json.dumps(installed_config(), indent=2) + "\n"
        self.write(original)
        self.run_refresh(lambda: LISTING)
        smaller = {"object": "list", "data": LISTING["data"][:1]}
        self.run_refresh(lambda: smaller)
        with open(self.backup, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), original)

    def test_no_answer_from_lumen_leaves_the_file(self):
        original = json.dumps(installed_config(), indent=2)
        self.write(original)

        def no_answer():
            raise TimeoutError("timed out")

        message = self.run_refresh(no_answer)
        self.assert_untouched(original)
        self.assertIn("not updated", message)

    def test_an_error_reply_leaves_the_file(self):
        original = json.dumps(installed_config(), indent=2)
        self.write(original)
        self.run_refresh(lambda: {"error": "invalid api key"})
        self.assert_untouched(original)

    def test_an_empty_list_leaves_the_file(self):
        original = json.dumps(installed_config(), indent=2)
        self.write(original)
        self.run_refresh(lambda: {"object": "list", "data": []})
        self.assert_untouched(original)

    def test_a_file_that_is_not_json_is_left_alone(self):
        original = '{"provider": {"lumen": '  # cut off mid-edit
        self.write(original)
        self.run_refresh(lambda: LISTING)
        self.assert_untouched(original)

    def test_a_missing_file_is_not_created(self):
        # A new machine is set up with the script in LUMEN.md, not by this
        # refresh.
        self.run_refresh(lambda: LISTING)
        self.assertFalse(os.path.exists(self.path))


class Main(unittest.TestCase):
    """The command the zsh function runs before opencode starts."""

    def test_a_failed_refresh_still_exits_zero(self):
        def no_answer():
            raise OSError("network is unreachable")

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "opencode.json")
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(installed_config(), fh)
            with contextlib.redirect_stderr(io.StringIO()):
                code = lr.main(["--config", path], fetch=no_answer)
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
