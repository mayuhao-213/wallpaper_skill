# AI.md

## Purpose

This file is for OpenClaw / AI Agents.

Its purpose is to guide the agent to deploy `wallpaper_skill` into the user's OpenClaw environment and verify that the skill works.

Do not treat this file as a general project introduction.
Treat it as an execution workflow.

---

## Task

Install and validate `wallpaper_skill` for the user.

After completion, the user should be able to call the skill from OpenClaw to:

- generate static wallpapers from images
- get style recommendations
- generate live wallpaper workflows when needed

---

## Rules

1. Execute step by step.
2. Do not skip environment checks.
3. Do not invent user credentials.
4. Ask the user for the Google API Key when needed.
5. Create the `.env` file using the user's real input.
6. Do not store the real API key in public files.
7. Validate the installation before declaring success.
8. If a step fails, explain the failure and continue with the most direct fix.

---

## Required user input

You must ask the user for:

- Google API Key

You may also need to ask for:

- OpenClaw workspace path, if it cannot be detected reliably
- preferred Python environment strategy, if multiple valid options exist

---

## Default repository

Use this repository unless the user provides another source:

`https://github.com/mayuhao-213/wallpaper_skill.git`

---

## Deployment workflow

### Step 1. Check OpenClaw

Run:

```bash
which openclaw
openclaw --version
```

If OpenClaw is not available, stop and tell the user OpenClaw must be installed first.

---

## Step 2. Detect the active OpenClaw skills directory

Find the OpenClaw workspace currently used by the user.

Preferred target skill directory:

`<workspace>/skills/wallpaper_skill`

Use the same workspace that the user’s current OpenClaw installation already uses.

Do not guess a different workspace if an active one already exists.

---

## Step 3. Get the repository

If the project does not exist locally, clone it:
```bash

    git clone https://github.com/mayuhao-213/wallpaper_skill.git
```

If it already exists, ask the user whether to update or reuse the current local copy.

---

## Step 4. Place the skill into the correct skills directory

Move or copy the `wallpaper_skill` folder into the active OpenClaw `skills/` directory.

The final directory must contain at least:

- `SKILL.md`
- `AI.md`
- `README.md`
- `skill.py`
- `run_skill.sh`
- `requirements.txt`

---

## Step 5. Check Python

Run:
```bash

    python3 --version
    python --version
```

Target:

- Python 3.10+
- Recommended: Python 3.11

If the available Python is too old, do not continue with dependency installation until a valid environment is prepared.

---

## Step 6. Create or activate a Python environment

Preferred option: conda
```bash
    conda create -n wallpaper_skill python=3.11 -y
    conda activate wallpaper_skill
```

Alternative option: venv
```bash

    python3 -m venv .venv
    source .venv/bin/activate
```

Use a dedicated environment when possible.

---

## Step 7. Install dependencies

From the skill root directory, run:
```bash
    pip install --upgrade pip
    pip install -r requirements.txt
```

If installation fails, identify whether the cause is:

- Python version mismatch
- network issue
- environment conflict

---

## Step 8. Ask the user for the Google API Key

You must ask the user for their real Google API Key.

Example:

> Please provide your Google API Key so I can create the `.env` file for this skill.

Do not continue past this step with a fake or placeholder key.

---

## Step 9. Create `.env`

Create the `.env` file in the `wallpaper_skill` root directory.

Required content:

    GOOGLE_API_KEY=<user_provided_real_key>

If `.env` already exists, ask the user whether to overwrite it.

Do not write the real key into `.env.example`, `README.md`, `AI.md`, or `SKILL.md`.

---

## Step 10. Ensure wrapper permissions

Run:
```bash
    chmod +x run_skill.sh
```

If the wrapper uses a fixed conda path, confirm that the path matches the user’s real environment.

---

## Step 11. Verify required files

Confirm that the skill directory contains:

- `SKILL.md`
- `skill.py`
- `run_skill.sh`
- `requirements.txt`

If `SKILL.md` is missing, OpenClaw will not recognize the skill.

---

## Step 12. Refresh OpenClaw

Try:
```bash
    openclaw gateway restart
```

If the user’s OpenClaw is managed through another launcher or installer, use that mechanism instead.

---

## Step 13. Verify that OpenClaw recognizes the skill

Run:
```bash

    openclaw skills list
```

Expected result: `wallpaper_skill` appears in the list.

If available, also run:

    openclaw skills info wallpaper_skill

If the skill is missing, check:

- correct `skills/` directory
- `SKILL.md` presence
- correct active workspace

---

## Step 14. Smoke test

Run a minimal test from the skill root:
```bash

    ./run_skill.sh --mode static --image examples/demo_inputs/sample.jpg --count 1 --output-dir runtime/outputs/openclaw_runs
```

If this fails, inspect:

- `.env`
- Python environment
- wrapper permissions
- `/tmp/wallpaper_skill_bash.log`
- `/tmp/wallpaper_skill_debug.log`

---

## Step 15. Tell the user how to use it

After deployment, provide short usage examples.

Preferred Chinese examples:

- “帮我把这张图做成壁纸”
- “先看看这张图适合什么风格，再帮我生成”
- “把这张图做成动态壁纸”

Preferred explicit trigger examples:

- “请使用 wallpaper_skill，把这张图片生成 1 张静态壁纸”
- “请使用 wallpaper_skill，把这张图做成动态壁纸”

---

## Success criteria

Do not declare success unless the following are true:

- OpenClaw is available
- `wallpaper_skill` is in the active `skills/` directory
- Python environment is valid
- dependencies are installed
- `.env` exists with the user-provided real API key
- `run_skill.sh` is executable
- `openclaw skills list` shows `wallpaper_skill`
- the smoke test passes or an equivalent validation succeeds

---

## Failure handling

### OpenClaw missing

Stop and tell the user OpenClaw must be installed first.

### Python too old

Prepare a newer Python environment before installing dependencies.

### Dependency installation fails

Explain the failing package and identify whether the problem is Python, network, or environment related.

### User has not provided API key

Pause at the `.env` step and wait for the user.

### Skill not recognized

Check:

- active workspace
- `skills/` directory
- `SKILL.md`

### Smoke test fails

Check:

- `.env`
- wrapper permissions
- Python environment
- debug logs

---

## Response style for the agent

During deployment:

- be concise
- be explicit
- ask for missing user inputs when needed
- confirm each major completed stage
- do not pretend a step succeeded if it has not been run

Good examples:

- “I found your active OpenClaw skills directory. Next I will set up the Python environment for this skill.”
- “Dependencies are installed. I now need your Google API Key to create the `.env` file.”
- “The skill is now recognized by OpenClaw. I will run one smoke test to confirm it works.”

---

## Final note

Your job is not to explain the project in abstract terms.

Your job is to help the user deploy `wallpaper_skill` successfully, with a valid environment, a valid `.env`, and a working OpenClaw skill entry.