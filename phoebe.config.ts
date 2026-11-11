// Phoebe tenant config for mikeallisonJS/archimedius.
//
// Phoebe (https://github.com/JesusFilm/phoebe) picks up issues labelled
// `ready-for-agent`, works each one on a `phoebe/` branch in its own clone, runs
// the gates below, and opens a PR. This repo is one tenant of a Phoebe
// workspace: the workspace root discovers this file and runs the shared engine
// in its container. This file names only what is specific to this repo.
//
// No import on purpose: the container loads this file from a mount with no
// node_modules, and this repo has no `phoebe-agent` dependency. The fields are
// `PhoebeUserConfig` from phoebe-agent (docs/configuration.md).
//
// Everything else Phoebe reads lives in `.phoebe/` (`configDir` below): the
// engine's shipped prompts, unedited, in .phoebe/prompts/, and the gitignored
// secrets file .phoebe/.env (see .phoebe/.env.example):
// GH_TOKEN, a fine-grained PAT for this repo, and ANTHROPIC_AUTH_TOKEN, the
// provider key. The workspace image sends Claude Code through a shared proxy
// when that key is the one it is given.
//
// Gates from run-tests.yml: the blocking flake8 pass and pytest under Xvfb
// (the Tk tests open a window).

const config = {
  repoSlug: "mikeallisonJS/archimedius",
  repoUrl: "https://github.com/mikeallisonJS/archimedius.git",
  configDir: ".phoebe",
  installCommand:
    "python3 -m venv venv && venv/bin/pip install -r requirements.txt pytest pytest-cov flake8",
  checkCommand:
    "venv/bin/flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics --extend-exclude=venv",
  testCommand: "xvfb-run -a venv/bin/pytest",
  readyCommand:
    "venv/bin/flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics --extend-exclude=venv && xvfb-run -a venv/bin/pytest",
  defaultProvider: "claude",
  providerEnv: { claude: "ANTHROPIC_AUTH_TOKEN" },
};

export default config;
