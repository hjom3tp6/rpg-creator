# rpg-creator

A Claude Code **plugin** (and single-plugin **marketplace**) that turns Claude Code into an RPG
authoring studio. It installs one skill, `rpg-creator`, which interviews you, designs a complete
narrative world (premise, cast, lore, story, mechanics), and then **compiles** it into its *own*
self-contained, directly-playable skill — a "baked game" with its own slash command (e.g.
`/neon-shrine`).

Each baked game carries its own bundled save/recap engine and a distilled rulebook, so it runs with
**no generic engine loaded at play time** — and the whole game folder is portable: copy it anywhere and
it just runs.

## What you get

- **`rpg-creator` skill** — the authoring + compiling tool.
- Character cards shaped like **SillyTavern V2** cards (minus the image), split into **主角
  (protagonist)** and **配角 (supporting cast)**.
- A bundled engine (`save.py` / `load.py` / `checkpoint.py` / `codex.py` / `rotate_log.py`) copied into
  every game so it has no shared dependency.
- A module library (`romance`, `magic-potency`, `language-coaching`, `drift`) you can mix per game.

## Install

```shell
# 1. Add this marketplace
/plugin marketplace add hjom3tp6/rpg-creator

# 2. Install the plugin
/plugin install rpg-creator@markcui-plugins
```

After install, the skill is available as `rpg-creator`. Just describe the game you want — e.g.
*"幫我做一個賽博龐克 RPG"* / *"build me a wuxia romance game"* — and it takes it from there.

## Update

Push changes to the repo, then in Claude Code:

```shell
/plugin marketplace update markcui-plugins
```

(Bump `version` in `.claude-plugin/plugin.json` on each release, or omit it to let every git commit
count as a new version.)

## Layout

```
rpg-creator/                       ← repo root = marketplace AND plugin (source: "./")
├── .claude-plugin/
│   ├── marketplace.json           ← catalog listing the plugin
│   └── plugin.json                ← the plugin manifest
└── skills/
    └── rpg-creator/               ← the skill (SKILL.md + assets/engine/module-library/references/scripts)
```

## License

Unlicensed / personal use unless a `LICENSE` file is added.
