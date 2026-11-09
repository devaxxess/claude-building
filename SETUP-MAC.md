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
- Frontend: open in een tweede terminal met `make open`. Dat opent
  `localhost:3000` met je vaste sleutel, zodat ook Simulate en de instellingen
  werken. De sleutel staat in `backend/.ui-token` en blijft na een herstart
  dezelfde. Verwijder dat bestand om een nieuwe sleutel te maken.

Open daarna een **tweede** terminal, ga naar een van je projectmappen en start
`claude`. Je sessie verschijnt dan als boss in het gebouw. Subagents worden
employees.

## 4. Verdiepingen aanpassen

Zie `backend/floors.toml`. Een sessie komt op de verdieping waarvan de lijst
`repos` de **mapnaam** bevat waarin je `claude` startte.

- Bij de eerste start wordt het gebouw opgebouwd vanuit `floors.toml`.
- Pas je iets aan in de app (Building settings), dan wordt dat in de database
  bewaard en heeft het voorrang op het bestand.
- Wil je opnieuw vanuit het bestand beginnen, voer dan `make clean-db` uit.
  Dit wist ook de sessiegeschiedenis.

## Kantoorgeheugen (fase 2)

Elke sessie krijgt bij de start automatisch het geheugen van zijn verdieping mee
(via de hook `claude-office-hook-memory`). Het geheugen staat in `office/`:

- `office/building.md`: regels voor het hele gebouw. Schrijf hier zelf wat
  elke sessie moet weten.
- `office/floors/<verdieping>.md`: kennis per afdeling.
- `office/handoff/<verdieping>.md`: overdrachtsnotities die sessies zelf
  achterlaten.

Deze map gaat **niet** naar GitHub, want de repo is public. Meer uitleg staat in
`office/README.md`.

Controleren of het werkt: start `claude` in een projectmap en vraag
"op welke verdieping zit je en wat staat er in je kantoorgeheugen?".

## Updaten

```bash
cd ~/claude-building
git pull
make install              # alleen nodig als dependencies veranderd zijn
make hooks-install        # nodig als er hooks bijkomen (zoals in fase 2)
make dev
```

## Problemen

| Probleem | Oplossing |
|---|---|
| Sessie verschijnt niet | `make hooks-status`, en herstart daarna `claude` (hooks laden alleen bij het starten) |
| Hook-logs bekijken | `make hooks-debug-on`, daarna `make hooks-logs-follow` |
| Poort 3000/8000 bezet | Sluit het andere proces, of zoek het met `lsof -i :3000` |
