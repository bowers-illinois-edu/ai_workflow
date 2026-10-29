# Using Illinois Lumen from opencode

Lumen is a University of Illinois service, run by NCSA, that hosts language
models on campus hardware. The models are ones whose makers published the
trained parameters (Qwen, GLM, DeepSeek, Gemma, and others). Programs send
Lumen requests in the same format they would send to OpenAI. So any client
written for OpenAI can use Lumen once it is given Lumen's URL and a Lumen key.
The steps below set up the opencode command-line client to use Lumen on a new
machine. The later sections record problems we found when we first set it up
on koelsch on 2026-10-18, and one we found on the Mac on 2026-10-28.

Sources: the connection page at
<https://lumen.computes.illinois.edu/help/connect> and the server code and
login script at <https://github.com/ncsa/lumen>.

## What the client needs

opencode needs three things to use Lumen.

1. The URL that every request starts with,
   `https://lumen.computes.illinois.edu/v1`. The hostname
   `lumen.ncsa.illinois.edu`, which `lumen.sh` (described below) uses by
   default, also answers. On 2026-10-18 it returned the same model list for
   the same key, so the two names appear to reach one server. The connection
   page uses the `computes` name, and so does everything here.
2. An API key, a string that begins `sk_`. A person creates one on the Profile
   page of the Lumen website, which shows the key once only. opencode reads the
   key from the environment variable `LUMEN_API_KEY`. On koelsch it is set by a line in
   `~/.zshrc`:

       export LUMEN_API_KEY="sk_..."

3. A section of `~/.config/opencode/opencode.json` that describes Lumen to
   opencode. opencode calls each such section a provider. The Lumen provider
   gives the URL above, tells opencode to read the key from the environment,
   and lists the models.

A key can use a model only after its owner has clicked "acknowledge" for that
model on the Lumen website. Until then the API hides the model or answers
with HTTP status 403.

## Checking the key before touching opencode

This command asks Lumen which models the key can use. If the key works, it
prints one model id per line. If the key is wrong, Lumen sends back an error
message instead of a list, and Python stops with `KeyError: 'data'`.

```sh
curl -sS -H "Authorization: Bearer $LUMEN_API_KEY" \
  https://lumen.computes.illinois.edu/v1/models |
  python3 -c 'import json,sys; [print(m["id"]) for m in json.load(sys.stdin)["data"]]'
```

## Writing the opencode configuration

`~/.config/opencode/opencode.json` has two parts. The settings at the top
and the description of the Lumen provider are written once, by hand. The list of models is written by
`lumen_refresh.py`, which sits beside this file. The script asks Lumen which
models the key can use and replaces the Lumen model list in the file with
them. It changes nothing else in the
file, and it prints a line only when the list changed or could not be
updated.

On a new machine, where the file does not exist yet, these commands write
the hand-made part and then let the script fill in the models. On a machine
that already has the file, run only the last command, because the `cat`
command would overwrite the file.

```sh
mkdir -p ~/.config/opencode
cat > ~/.config/opencode/opencode.json <<'EOF'
{
  "$schema": "https://opencode.ai/config.json",
  "instructions": ["CLAUDE.md", "POINT.md"],
  "model": "lumen/qwen3-coder-next",
  "enabled_providers": ["lumen"],
  "provider": {
    "lumen": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "Lumen",
      "options": {
        "baseURL": "https://lumen.computes.illinois.edu/v1",
        "apiKey": "{env:LUMEN_API_KEY}"
      }
    }
  }
}
EOF
python3 ~/repos/ai_workflow/opencode/lumen_refresh.py
```

The script follows three rules, each of which answers a problem recorded
later in this file. It caps
every model's longest reply at 32768 tokens, because a larger figure makes
Lumen refuse opencode's requests (see "The downloaded file's output limits").
It leaves out models that cannot take text, such as the speech model. It
marks every model as able to make tool calls, because Lumen does not report
tool support and opencode can read or edit a file only through a tool call.
Before it rewrites the file, it copies the old one to
`opencode.json.before-refresh-` followed by the date.

To run the script each time opencode starts, add this line to `~/.zshrc`:

    source ~/repos/ai_workflow/opencode/opencode.zsh

That file defines a zsh function named `opencode`, which runs the script and
then starts opencode with whatever followed `opencode` on the command line.
A model that Lumen adds then appears at the next start. The script gives up
after 5 seconds when Lumen does not answer, and opencode starts with the old
list. The script's tests are in `opencode/tests/test_lumen_refresh.py`, and
`make test-opencode`, run in ai_workflow, runs them.

Three settings in the hand-written part are choices, not requirements.

- `"instructions": ["CLAUDE.md", "POINT.md"]` makes opencode load those two
  files from the folder where a session starts. opencode reads a project's
  `AGENTS.md` on its own, but not its `CLAUDE.md`, and it does not follow the
  `@POINT.md` line inside a `CLAUDE.md`. In a test we ran on 2026-10-28, a
  session started in a project's top folder loaded both files. In a project
  with no `POINT.md`, it loaded `CLAUDE.md` and skipped the missing file
  without an error. We did not test whether a session started in a
  subfolder finds the files in the project's top folder.
- `"model": "lumen/qwen3-coder-next"` makes Lumen's coding model the default
  when opencode starts. Pick another in the session with `/models`, or on the
  command line with `-m lumen/<id>`.
- `"enabled_providers": ["lumen"]` hides every provider but Lumen, including
  the free models opencode ships with, which send prompts to servers outside
  the university. Delete the line to get those models back.

## Testing it

```sh
opencode models                  # should list lumen/<id> for each model
mkdir -p /tmp/octest && cd /tmp/octest && echo "hello" > note.txt
opencode run -m lumen/qwen3-coder-next "Read note.txt and reply with its contents."
```

opencode works by having the model ask it to do things, such as read a file or
run a command. These requests are called tool calls. The last command succeeds
only if the model can make a tool call that reads `note.txt`, so it tests tool
calls as well as the connection. On koelsch it
printed the file's contents.

## Problems with the two official routes

The connection page offers two other ways to configure opencode. We used
neither on koelsch.

The "Download config.json" button on the connection page needs you to be
logged in to the Lumen website in a browser. The file it gives lists the
models available on the day you download it, so it goes out of date when
Lumen adds a model. On koelsch we did not download it. On the Mac it was
downloaded on 2026-10-05 and copied unedited to
`~/.config/opencode/opencode.json`. Its output limits then kept opencode from
getting any work done with `qwen3-coder-next`, for the reasons given under
"The downloaded file's output limits" below. If you install that file,
run `lumen_refresh.py` afterward, which caps its output limits.

The `lumen.sh` script in the GitHub repository logs in through the browser,
stores a key, and rewrites the Lumen block of `opencode.json`. We did not
run it, for three reasons.

1. It needs `jq`, which koelsch does not have (`sudo apt install jq`).
2. It writes `"tool_call": false` for every model unless the server reports
   `supports_function_calling: true`. On 2026-10-18 the server reported no
   value for that field for any model, yet `qwen3-coder-next`, `glm-5.3`,
   and `deepseek-v4-flash` each returned a correct tool call when asked
   directly. opencode reads files, runs commands, and edits code only by having
   the model make tool calls, so with `lumen.sh`'s settings opencode could do
   none of those things.
3. It appends its own `LUMEN_API_KEY` block to `~/.zshrc`, which would
   duplicate the line already there.

## The downloaded file's output limits

Each model in `opencode.json` has two limits. `limit.context` is the most
tokens that the prompt and the reply may use together, and `limit.output` is
the longest reply. The downloaded file copies `limit.output` from Lumen's
server, and for several models that number is larger than `limit.context`.
For `qwen3-coder-next` the file gave a context of 131066 and an output of
256000.

Every request opencode sends states the longest reply it will accept. For
`qwen3-coder-next`, Lumen refuses a request when the prompt plus that longest
reply exceeds 131072 tokens, six more than the file's 131066. When
`limit.output` cannot fit, opencode 2.2.0 sets the longest reply to
`limit.context` minus its own estimate of the prompt. That estimate is often
low by more than six tokens. In one request on 2026-10-28 opencode estimated
the prompt at 21364 tokens and set the longest reply to
131066 - 21364 = 109702. The prompt was in fact 21375 tokens, so the total
was 21375 + 109702 = 131077. Lumen refused the request with the message
"Requested token count exceeds the model's maximum context length".

opencode reads that refusal as a sign that the conversation has grown too
long, so it compacts the conversation: it replaces the history, including
the tool call just made, with a summary, and sends the request again. The
model sees only the summary and starts the same step again. The next
request is refused in the same way. The person at the terminal sees a new
paragraph announcing the step, over and over, while nothing gets done. On
the Mac on 2026-10-28, the log at `~/.local/share/opencode/log/opencode.log`
held 370 such refusals across four sessions. In one session the model
began the same step again 12 times in 76 seconds.

`lumen_refresh.py` caps `limit.output` at 32768. With that cap a prompt can
grow to 131066 - 32768 = 98298 tokens before the prompt plus the longest
reply reaches the 131066 in `limit.context`. On the Mac, capping every
model's `limit.output` at 32768 in the installed file stopped the refusals. The background server,
`opencode serve --service`, read the edited file within seconds, so a
session that was already running went on with no refusals and no restart.

This command counts the refusals in the log:

```sh
grep -c "provider rejected the request as too long" \
  ~/.local/share/opencode/log/opencode.log
```

## Models on 2026-10-18

The key on koelsch could reach these models. The context column is the
largest prompt plus reply, in tokens, that each accepts.

| id | context | notes |
|---|---|---|
| qwen3-coder-next | 131066 | coding model; the default above |
| glm-5.3 | 524282 | `glm` is an alias for it |
| deepseek-v4-flash | 511994 | |
| qwen3.6-35b-a3b | 262138 | |
| qwen3.8-27b | 250542 | |
| qwen3.8-flash | 262138 | accepts images |
| nemotron-3-super-120b-a12b | 262144 | |
| ornith-1.0-35b | 262138 | |
| muse-glimmer-30b | 131066 | |
| gemma-4-31b-it | 46790 | |
| granite-speech-4.1-2b-plus | 4096 | audio input; left out of the opencode config |

## Note on the key in `~/.zshrc`

On koelsch `~/.zshrc` has mode 644, which lets every account on the machine
read it and so read the key. `chmod 600 ~/.zshrc` restricts it to its owner.
