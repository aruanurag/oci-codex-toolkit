# Prerequisites And Installation

Use this guide to set up Codex, browser access, and the OCI Codex Toolkit skills.
After setup, use the main [README](../README.md) for skill usage, sample prompts,
account scoring guidance, and output expectations.

## Prerequisites

- A ChatGPT account with Codex access.
- The Codex desktop app installed.
- Google Chrome installed.
- Access to this GitHub repository:
  <https://github.com/aruanurag/oci-codex-toolkit>
- Optional: LinkedIn Sales Navigator access if you want Codex to use visible
  Sales Navigator account or lead context.
- Optional: Git installed if you want to clone the repo from Terminal.

OpenAI setup references:

- Codex get started: <https://openai.com/codex/get-started/>
- Codex with your ChatGPT plan: <https://help.openai.com/en/articles/11369540>

## Step 1: Download Codex And Sign In

1. Go to <https://openai.com/codex/get-started/>.
2. Download and install the Codex desktop app.
3. Open Codex.
4. Select **Continue with ChatGPT**.
5. Sign in with your ChatGPT account.

Screenshot checkpoint:

- Codex welcome screen with the **Continue with ChatGPT** button.

## Step 2: Enable Browser Access

The skills can use public sources without browser plugins, but Sales Navigator
workflows need browser access because they use your logged-in Chrome session.

In Codex:

1. Open **Settings**.
2. Go to **Plugins** or **Browser plugins**.
3. Enable **Browser**.
4. Enable **Chrome**.
5. Enable **Computer Use** if it appears in your workspace and is required for
   browser control.
6. Follow any prompts to install or enable the Codex Chrome Extension.
7. Open Chrome and confirm you are logged in to LinkedIn Sales Navigator.

Screenshot checkpoints:

- Codex settings page showing Browser/Chrome plugin controls.
- Chrome extension prompt or enabled Codex Chrome Extension.
- Sales Navigator open in Chrome while logged in.

Notes:

- Codex should ask before reading Sales Navigator context.
- Codex should ask separately before clicking Sales Navigator Account IQ
  **Generate insights**.
- Do not ask Codex to send messages, save leads, export lists, or modify Sales
  Navigator unless you explicitly intend that action.

## Step 3: Get The Repo Locally

Choose one option.

### Option A: Clone With Git

Use this option if you are comfortable with Terminal and want future updates to
be easy.

GitHub copy-and-paste path:

1. Open <https://github.com/aruanurag/oci-codex-toolkit>.
2. Click **Code**.
3. Copy the HTTPS URL.
4. Open Terminal.
5. Type `git clone `, paste the URL, and press Enter.

Direct command:

```bash
git clone https://github.com/aruanurag/oci-codex-toolkit.git
```

This creates a local folder named `oci-codex-toolkit`.

To clone into a specific folder:

```bash
cd ~/Documents
git clone https://github.com/aruanurag/oci-codex-toolkit.git
```

Screenshot checkpoint:

- Terminal after `git clone` completes.

### Option B: Download The ZIP

Use this option if you do not want to use Terminal.

1. Open <https://github.com/aruanurag/oci-codex-toolkit>.
2. Click **Code**.
3. Click **Download ZIP**.
4. Unzip the downloaded file.
5. Move the unzipped folder somewhere easy to find, such as `Documents`.

Screenshot checkpoint:

- GitHub **Code** menu showing **Download ZIP**.

## Step 4: Open The Repo In Codex

1. Open Codex.
2. Click **Add project** or **Open folder**.
3. Select the cloned or downloaded `oci-codex-toolkit` folder.
4. Start a new thread in that project.

Codex automatically sees repo-local skills stored under `.agents/skills/`.
You do not need to manually copy the skills for normal use inside this repo.

Screenshot checkpoint:

- Codex project picker with the toolkit folder selected.

## Optional: Add The Skills Globally

Use this only if you want the OCI skills to appear in Codex projects outside
the toolkit repo. Most users can skip this and simply open the toolkit repo as
the Codex project.

From inside the cloned or downloaded repo, run:

```bash
mkdir -p ~/.codex/skills
cp -R .agents/skills/. ~/.codex/skills/
```

Then start a new Codex thread. The skills should be available from any project.

If you want the global install to track repo changes while you continue editing
the skills, symlink instead of copying:

```bash
REPO_ROOT=/path/to/oci-codex-toolkit
mkdir -p ~/.codex/skills
ln -s "$REPO_ROOT/.agents/skills/oci-architecture-generator" ~/.codex/skills/oci-architecture-generator
ln -s "$REPO_ROOT/.agents/skills/oci-architecture-powerpoint-generator" ~/.codex/skills/oci-architecture-powerpoint-generator
ln -s "$REPO_ROOT/.agents/skills/oci-bom-generator" ~/.codex/skills/oci-bom-generator
ln -s "$REPO_ROOT/.agents/skills/oci-diagram-patterns" ~/.codex/skills/oci-diagram-patterns
ln -s "$REPO_ROOT/.agents/skills/oci-opportunity-coach" ~/.codex/skills/oci-opportunity-coach
ln -s "$REPO_ROOT/.agents/skills/oci-ppt-design-director" ~/.codex/skills/oci-ppt-design-director
ln -s "$REPO_ROOT/.agents/skills/oci-sales-decks" ~/.codex/skills/oci-sales-decks
ln -s "$REPO_ROOT/.agents/skills/oci-technical-decks" ~/.codex/skills/oci-technical-decks
ln -s "$REPO_ROOT/.agents/skills/xlsx" ~/.codex/skills/xlsx
ln -s "$REPO_ROOT/.agents/skills/shared" ~/.codex/skills/shared
```

Global install notes:

- The typical global location is `~/.codex/skills/`.
- Keep the directory names exactly the same.
- Copy or symlink the full suite together, because several skills
  cross-reference one another.
- Include `shared/`, because review scripts import shared helpers by relative
  path.
- If the skills do not appear immediately, start a new Codex session.

## Step 5: Validate The Skill Is Available

Start a Codex thread in the toolkit project and ask:

```text
What OCI skills are available in this repo?
```

Or ask directly:

```text
Use the oci-opportunity-coach skill to prepare an account brief. Ask before using Sales Navigator.
```

If Codex does not see the skills:

- Confirm you opened the toolkit repository folder in Codex.
- Confirm `.agents/skills/oci-opportunity-coach/SKILL.md` exists in the repo.
- Start a new Codex thread after opening the project.

## Troubleshooting Browser Access

If Sales Navigator does not work:

- Confirm Chrome is installed.
- Confirm you are logged in to LinkedIn Sales Navigator in Chrome.
- Confirm the Browser and Chrome plugins are enabled in Codex settings.
- Confirm the Codex Chrome Extension is installed and enabled.
- Restart Chrome and start a new Codex thread if needed.
