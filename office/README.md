# office/ - kantoorgeheugen

Deze map wordt automatisch gevuld zodra de backend draait. De inhoud blijft
**lokaal** (zie `.gitignore`), omdat de repo publiek is.

| Bestand | Wat erin hoort | Wie schrijft |
|---|---|---|
| `building.md` | Regels voor elke sessie in het gebouw | Jij |
| `floors/<verdieping>.md` | Duurzame kennis per afdeling: architectuur, beslissingen, valkuilen | Jij + Claude-sessies |
| `handoff/<verdieping>.md` | Korte overdrachtsnotities, nieuwste onderaan | Claude-sessies |

Bij elke sessiestart (en na `/clear` of compaction) geeft de hook
`claude-office-hook-memory` een samenvatting van deze bestanden aan Claude, voor
de verdieping waarop die sessie staat. Het blok is begrensd tot 8000 tekens
(`MEMORY_CONTEXT_MAX_CHARS`), want alles wat hier staat kost inputtokens bij elke start.

Een backup maken: kopieer deze map, of maak er een privé-repo van.
