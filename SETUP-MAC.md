# Claude Building: installatie op je MacBook

Dit doe je één keer. Daarna is `git pull` + `make dev` genoeg.

## 0 tokens

Het gebouw leest alleen lokaal wat Claude Code doet: hook-events en
JSONL-transcripts. Het roept zelf nooit Claude aan.

- AI-samenvattingen staan standaard **uit**: `SUMMARY_BACKEND=disabled` en
  `SUMMARY_ENABLED=False` in `backend/app/config.py`.
- Zet ze niet aan met `claude-cli`. Dat start voor elke samenvatting een
  `claude -p`-proces op je abonnement, en dat kost dus tokens.

## 1. Vereisten installeren

Open **Terminal** en voer uit:

```bash
# Homebrew (sla over als `brew --version` al werkt)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

brew install uv node git
```

- `uv` installeert zelf de juiste Python-versie (3.13+), dus die hoef je niet
  apart te installeren.
- Node 20+ is nodig. Controleer met `node --version`.

## 2. Repo ophalen en installeren

```bash
cd ~                      # of een andere map waar je projecten staan
git clone https://github.com/devaxxess/claude-building.git
cd claude-building
make install              # backend, frontend en hooks
make hooks-install        # registreert de hooks in ~/.claude/settings.json
```

- `make hooks-install` past `~/.claude/settings.json` aan. Je bestaande
  instellingen blijven behouden.
- Ongedaan maken kan met `make hooks-uninstall`.

## 3. Starten

```bash
make dev
```

- Backend: http://localhost:8000
- Frontend: http://localhost:3000. Open die in je browser.

Open daarna een **tweede** terminal, ga naar een van je projectmappen en start
`claude`. Je sessie verschijnt dan als boss in het gebouw. Subagents worden
employees.

## 4. Verdiepingen aanpassen

Zie `backend/floors.toml`. Een sessie komt op de verdieping waarvan de lijst
`repos` de **mapnaam** bevat waarin je `claude` startte. Je kunt dit ook in de
app aanpassen via Building settings.

## Updaten

```bash
cd ~/claude-building
git pull
make install              # alleen nodig als dependencies veranderd zijn
make dev
```

## Problemen

| Probleem | Oplossing |
|---|---|
| Sessie verschijnt niet | `make hooks-status`, en herstart daarna `claude` (hooks laden alleen bij het starten) |
| Hook-logs bekijken | `make hooks-debug-on`, daarna `make hooks-logs-follow` |
| Poort 3000/8000 bezet | Sluit het andere proces, of zoek het met `lsof -i :3000` |
