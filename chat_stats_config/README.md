# Statistics chats: configuration for the Claude app and ChatGPT

These four files set up a long-running chat --- in the Claude desktop app or in
ChatGPT --- for learning statistics and stress-testing research ideas. They are
not for Claude Code, which reaches the same kind of rules through `CLAUDE.md`
and `skills/`, as the top-level README describes. Neither chat app has a
`CLAUDE.md`, so both reach this material through two other slots: a per-project
instruction field and a per-project set of uploaded files.

The whole setup is one project per app, holding one pasted block and two
uploaded files.

## What each file is

- **`Revised_Statistical_Project_Instructions.md`** --- the short version of the
  whole orientation, written to be pasted into an instruction field: what to
  distinguish (estimand, identification, design, estimation, inference,
  sensitivity), what not to assume silently, the six-step default approach, and
  the instruction to stress-test rather than agree. This is the only file that
  gets pasted.
- **`Revised_Statistical_Perspective_and_Learning_Framework.md`** --- the long
  version, which the pasted block cannot hold: the influences and why they are
  reference points rather than doctrines, the questions to ask about any method,
  the split between learning mode and research mode, the mathematical standard,
  and the research interests. This file gets uploaded.
- **`03_Concept_Map_and_Notation.md`** --- the conventions that should survive
  from one conversation to the next: default symbols and what qualifies them,
  the inferential distinctions to keep separate, the conceptual connections
  worth making and the condition that stops each one from collapsing into an
  identity, plus registers for active questions and unresolved issues. This file
  gets uploaded, and it is the only one meant to change over time.
- **`README.md`** --- this file. It stays out of both apps.

I deliberately do not put usage instructions inside the other three files.
The framework and the concept map are uploaded whole, so every byte in them
arrives as content the model reads. A "how to install this" header inside one of
them would arrive as content too.

## Where the two slots are, in both apps

Each app needs the same two things from you: one field of instructions that
applies to every conversation inside a project, and a set of files attached to
that project. Everything below is navigation for reaching those two slots.

The Claude navigation below was checked against claude.ai on 24 August 2026, so
the labels are the real ones. The ChatGPT navigation was not checked, because
the browser I checked from was not signed in to ChatGPT, so treat that section
as a description of what to look for rather than as a click path.

Either way the labels will drift. This repository already records two such
changes on the Claude side alone: the account-wide instruction field was renamed
and moved, and custom styles disappeared. So when a label stops matching, do not
hunt for the old word. Look for the field whose own help text says it applies to
every chat in the project, and for the area that holds the files attached to the
project. Those two descriptions name what each control is for, which is the part
a relabel does not change.

## Setting up the Claude desktop app

The desktop app, claude.ai in a browser, and the phone app are one interface
over one account, and projects sync across all three. You therefore do this once
and it appears everywhere. I describe the desktop app because it is where I do
the setup, and because it opens a file picker onto the disk holding this
repository. claude.ai in a browser has the same slots and the same picker. The
phone is the one awkward case, which the note after the steps covers.

Before step 1, check which sidebar you are looking at. The two small buttons to
the right of the wordmark at the top left switch between a Claude sidebar and a
Claude Code sidebar, and they look nearly identical. **Projects appears only in
the Claude sidebar.** In the Claude Code sidebar there is no Projects entry at
all, and "More" holds Routines and Dispatch rather than the thing you are
looking for. Click the left-hand button, the speech bubbles, and the sidebar
should read New, Projects, Artifacts, Scheduled, Customize.

1. Click **Projects**, then **New project** at the top right of the projects
   page. Name it for the work rather than for the tool --- "Statistics" or
   "Design-based inference" --- since the name is what you will scan for later.
2. The project page puts a chat box on the left and a column of four panels on
   the right: **Instructions**, **Memory**, **Context**, and **Scheduled**.
   Click the pencil at the right of **Instructions** and paste the entire
   contents of `Revised_Statistical_Project_Instructions.md`, then the bridge
   block below it. Paste the file as it is; the headings help rather than hurt.
3. Click the **+** at the right of **Context** and add
   `Revised_Statistical_Perspective_and_Learning_Framework.md` and
   `03_Concept_Map_and_Notation.md`. Its own empty-state text says it takes
   PDFs, documents, or other text to reference in the project, and markdown
   arrives as text with nothing to convert.
4. Start every statistics conversation from inside the project. A chat started
   from the main window inherits none of this, and nothing on screen will tell
   you that it did not.

On the phone the same project is already there, and you can chat against it
without doing anything further. Uploading a replacement concept map from the
phone means getting the file into Files or iCloud first, so do that step from
the desktop.

**Memory is a fourth thing, and it is not one of your files.** The Memory panel
sits between Instructions and Context, fills itself from the project's own
chats, is marked "Only you," and has its own pencil for editing. It therefore
does what the concept map does, by a different route: it accumulates across
conversations. The two will disagree, because one is written by the model from
whatever the conversations happened to contain and the other is curated by me
and kept under version control. When they disagree, the concept map is the one
that is true, and the fix is to edit Memory, not to correct it in each new
chat. Read
Memory before you trust a convention that neither the instructions nor the
concept map states, since Memory is where such a convention will have come from.

These project instructions compose with the account-wide "Instructions for
Claude" that `claude_app/1_personal_preferences.md` fills, and neither needs to
repeat the other. The account-wide field says who I am, that output is plain
ASCII, how to disagree with me, and how to write; the project adds what to do
with a statistical question. The one thing to watch for is a claim in a project
file that contradicts the account-wide field, because the app gives you no
report of which one won. Nothing in these four files does that today.

Two other Claude features could carry the same material, and I use neither:

- **A skill.** A skill loads when its description matches the task at hand. That
  is the wrong trigger here. This orientation should be on for every
  conversation in the project and off everywhere else, which is what a project
  already does, so a skill would add a matching step that can fail without
  adding anything.
- **A custom style.** Styles are built from example writing and govern prose, and
  none of this is about prose. The style slot, where it still exists, belongs to
  `claude_app/3_custom_style.md`.

If you already keep a statistics project in Claude, adding these files to it
beats starting a new one, because the existing project holds the chats. Read its
Instructions field first, though. Whatever is in there was written before these
four files existed and now has to either go or be reconciled with them, and a
project holding two orientations follows neither.


## Setting up ChatGPT

The mapping is the same, into differently named slots. ChatGPT also runs as a
desktop app, in a browser, and on the phone, and its projects sync the same way,
so again this is one setup rather than three.

I have not checked these steps against the live app, for the reason given above,
so read them as a description of the two things to find rather than as a click
path. The mapping itself does not depend on the labels: one instruction field
that covers the whole project, one place to attach files.

1. In the left sidebar, click **Projects**, then the control for a new project,
   and give it a name.
2. Open the project and find its instructions field. Look on the project page
   first and in the menu on the project's own row second. Paste the entire
   contents of
   `Revised_Statistical_Project_Instructions.md`, then the bridge block below
   it.
3. Add `Revised_Statistical_Perspective_and_Learning_Framework.md` and
   `03_Concept_Map_and_Notation.md` to the project's files, by its add-files
   control or by dragging them onto the project page.
4. Start conversations inside the project, not outside it.

Pick a reasoning model for these conversations rather than whichever fast model
is the default. The whole point of the pasted block is to get an estimand, a
source of randomness, and a stated assumption set before an answer, and that is
work a model does before it writes, which is exactly what the fast models skip.

Use the project's instruction field rather than the account-wide custom
instructions under settings. The account-wide field applies to every
conversation you have, including ones that have nothing to do with statistics,
and this orientation is strong enough to distort them.

If the instruction field rejects the text for length, cut in this order, and
never cut the bridge block, because the bridge block is what reaches the two
uploaded files:

1. "Preferred connections" --- the concept map covers the same connections and
   states the boundary condition on each one, which the list does not.
2. "Intellectual orientation" --- the framework's "Important influences" list
   covers the same traditions and explains why they are reference points.
3. "Literature" --- the framework's "Literature expectations" section says the
   same thing at more length.

Keep "Core commitments," "Default approach," "Mathematical style," "Research
collaboration mode," and "Explanation calibration." Those five shape every
answer. Without the first four, the first thing that goes wrong is that you get
an answer before you get an estimand. Without the fifth, you get an answer
pitched at the wrong reader, which is harder to notice and slower to fix.

The same cut order applies in Claude if that field ever refuses the paste, for
the same reason: the three sections named above are the three the two uploaded
files already cover.

## The bridge block

The three configuration files never mention each other, so on their own the
pasted instructions give the model no reason to open the two uploaded files.
This block supplies that reason. Paste it into the instruction field directly
below the project instructions, in both apps, unchanged.

It is written to work regardless of how a given app puts an uploaded file in
front of the model, because that machinery changes and is not something either
app reports to you.

-------------------------------------------------------------------------------

Two files accompany these instructions:
`Revised_Statistical_Perspective_and_Learning_Framework.md` and
`03_Concept_Map_and_Notation.md`.

Read both before answering a substantive statistical question, and read them
again whenever you are unsure which convention applies. Do not work from a
summary of them made earlier in the conversation.

The framework file governs how you answer. It holds the response protocol, the
mathematical standard, and the difference between learning mode, where I want to
understand an existing idea, and research mode, where I want you to attack a new
one.

The concept map governs the symbols you write and the distinctions you keep
apart. When a question involves an object the concept map gives a default symbol
to, use that symbol. When you depart from a default, say that you are departing
and say why. Neither file relieves you of defining notation in the conversation
where it first appears.

At the end of a working conversation, tell me whether anything durable changed:
a notation convention, a conceptual connection, an active research question, or
an unresolved issue. If something did, write the change as one to three entries
in the form the concept map's "Updating this map" section specifies, and print
them in a fenced code block I can copy. Do not summarize the conversation. If
nothing durable changed, say so in one sentence and write nothing further.

-------------------------------------------------------------------------------

## Keeping the concept map current

`03_Concept_Map_and_Notation.md` is the one file meant to grow, and neither app
can write to it. What the model produces at the end of a conversation is text
for me to apply, so the loop is:

1. Ask for the update, or let the bridge block prompt it.
2. Apply the entries to the copy in this repository, which is the version under
   version control and therefore the one that is true.
3. Re-upload the file to whichever projects you keep, replacing the old copy.

Do this in the repository first and upload second. If you edit inside an app
instead, the two apps and the repository each hold a different concept map
within a week, and nothing will tell you which one you are talking to.

The registers for active questions and unresolved issues are both empty right
now, and the file says not to infer an entry from a single conversation. That is
the right default. An entry belongs in one of those registers once the same
convention or the same question has come up in more than one conversation.
