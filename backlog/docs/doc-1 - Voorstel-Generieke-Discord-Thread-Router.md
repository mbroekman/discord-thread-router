---
id: doc-1
title: Voorstel Generieke Discord Thread Router
type: specification
created_date: '2026-11-02 13:05'
updated_date: '2026-11-02 13:40'
---

# Voorstel: generieke Discord Thread Router

## 0. Besluiten (2026-11-02)

1. **Architectuur:** losse router + intake-API in aa-kanban. Akkoord.
2. **Eén plek voor alle regels:** alle kanalen, ook de kanbankanalen, staan in `rules.yaml` bij de bot. De bot leest het bestand opnieuw in zodra het wijzigt, dus een kanaal toevoegen vraagt geen herstart. Daardoor vervallen het model `DiscordIntakeChannel` en de kaart "Discord intake" in aa-kanban (3.2). Het endpoint krijgt bord, lijst, labels en team mee van de bot.
3. **Onbekende Discord-gebruiker:** de kaart komt op naam van de servicegebruiker "Discord intake". Akkoord.
4. **Hernoemen** naar `discord-thread-router`. Akkoord.
5. **Discord-server:** de bot draait op de 3GODS-Discord. Op welke host de container draait, leggen we vast bij de uitrol.
6. **aadiscordbot:** wordt op termijn vervangen door deze router. Tot die tijd wordt hij in aa-kanban gedoogd (AGENTS §15). Daar komt een aparte taak voor.

## 1. Doel

De `githubDiscordBOT` luistert nu naar twee vaste kanalen. Een nieuwe thread wordt daar een GitHub-issue of een GitHub-discussion. We maken er een generieke router van:

- **Kanalen vastleggen:** we kunnen vastleggen op welke Discord-kanalen de bot let. Dat kunnen forumkanalen zijn of tekstkanalen met threads.
- **Actie per kanaal:** we leggen per kanaal vast wat er gebeurt als daar een thread wordt geopend.
- **Nieuw doel, een kanbankaart:** opent iemand een thread in zo'n kanaal, dan maakt de bot een kaart aan op een aangewezen aa-kanban-bord, in een aangewezen lijst.
- **GitHub blijft:** issue en discussion blijven als acties bestaan.
- **Uitbreidbaar:** later is een actie toe te voegen zonder de bot te herschrijven, bijvoorbeeld een n8n-webhook.

## 2. Huidige situatie

`githubBOT.py` (165 regels):

- Twee kanaal-ID's in `.env`: `FORUM_CHANNEL_ID` levert een issue op, `DISCUSSION_CHANNEL_ID` een discussion.
- Eén GitHub-repo per installatie.
- Na het aanmaken antwoordt de bot in de thread met de link.

Gebreken die we in dit project meenemen:

| Gebrek | Gevolg |
|---|---|
| Kanalen en doelen staan vast in code en `.env` | Een kanaal toevoegen vraagt een codewijziging en een herstart |
| `requests` (synchroon) binnen async event-handlers | De bot hangt tijdens elke GitHub-call |
| `on_message` print elk bericht van de hele server; logging staat op DEBUG | Ruis in de logs, en berichtinhoud komt in de logs terecht |
| Eerste bericht ophalen met `sleep(2)` + history | Kan missen; bij forumthreads is het startbericht gewoon `thread.id` |
| Discussion pakt "de eerste" categorie | Geen keuze in categorie |
| Geen tests, geen ruff/pre-commit | Valt buiten de workspace-standaard (AGENTS §4, §13) |
| Geen bescherming tegen dubbele verwerking | Een herstart of reconnect kan dubbele issues geven |

## 3. Aanbevolen architectuur

De bot blijft een **losse service** (container, zoals nu). Hij krijgt een regel-engine. Alle regels staan in één bestand, `rules.yaml`. aa-kanban krijgt alleen een kleine intake-API (besluit 2).

```
Discord (thread geopend)
   │  on_thread_create
   ▼
Thread Router (bot) ── regel voor dit kanaal? ── nee → negeren
   │ ja: één of meer acties
   ├─ github_issue       → GitHub REST
   ├─ github_discussion  → GitHub GraphQL (vaste categorie)
   └─ kanban_card        → POST aa-kanban /kanban/api/intake/discord-thread/
                              │
                              ▼
                     aa-kanban: bord + lijst + labels + team (uit de regel)
                     create_kanban_card(), card.discord_thread_id = thread.id
   ◄── antwoord in de thread: "Kaart #123 aangemaakt op bord X" + link
```

### 3.1 Bot: regels en acties

- **Regel:** kanaal-ID → lijst van acties met hun instellingen, bijvoorbeeld:
  ```yaml
  channels:
    "123456789012345678":            # #bugs (forum)
      - action: github_issue
        repo: mbroekman/aa-industry
        labels: [from-discord]
    "987654321098765432":            # #suggesties
      - action: github_discussion
        repo: mbroekman/aa-industry
        category: Ideas
    "111111111111111111":            # #ticket-intake
      - action: kanban_card
        board: corp-tickets          # slug van het bord
        list: Backlog                # anders de eerste lijst
        labels: [Discord]            # alleen bestaande labels
        team: IT                     # optioneel, KanbanTeam-naam
  ```
  De URL van aa-kanban en de API-sleutel komen uit `.env` (`KANBAN_BASE_URL`, `KANBAN_API_KEY`), net als de tokens.
- **Acties:** elke actie is een klein Python-object met dezelfde interface (`async def handle(thread, starter) -> Result`). Een nieuwe actie is één nieuw bestand.
- **Wijzigen zonder herstart:** de bot kijkt bij elke thread of `rules.yaml` gewijzigd is en leest het dan opnieuw in. Een ongeldig bestand wordt gelogd en de vorige regels blijven gelden.
- **Meerdere acties per kanaal:** mag. Een bugkanaal kan dan zowel een GitHub-issue als een kanbankaart opleveren.

### 3.2 aa-kanban: intake-API

- **API-sleutel:** een `IntakeApiKey`, alleen in Django admin (technische infrastructuur, §8). De sleutel wordt gehasht opgeslagen; de bot stuurt hem mee als `Authorization: Bearer …`.
- **`POST /kanban/api/intake/discord-thread/`** krijgt `board`, `list`, `labels`, `team`, `thread_id`, `title`, `content`, `author_discord_id`, `author_name` en `jump_url` mee. Onbekend bord: 404; onbekende labels of team worden overgeslagen en in het antwoord gemeld.
  - **Idempotent:** bestaat er al een kaart met dit `discord_thread_id`, dan geeft het endpoint die kaart terug en maakt het geen nieuwe.
  - **Maker:** de Auth-gebruiker die via de Discord-koppeling van Alliance Auth zelf (`DiscordUser`, platform) bij `author_discord_id` hoort. Zonder koppeling wordt het een vaste servicegebruiker "Discord intake", met de Discord-naam in de beschrijving.
  - **Kaart:** via de bestaande `services.create_kanban_card()`, zodat de webhook-melding van het bord gewoon blijft werken. Daarna wordt `discord_thread_id` gezet.
  - **Antwoord:** `card_id` en `card_url`, die de bot in de thread post.
- **Gratis meegenomen:** omdat `discord_thread_id` gezet wordt, werken de bestaande koppelingen van aa-kanban (`KanbanTicketCog`) direct voor deze kaarten:
  - berichten in de thread worden reacties op de kaart;
  - verplaatst iemand de kaart, dan verschijnt dat in de thread.

  Dat geldt alleen als de aadiscordbot meedraait; zie 5.2.

### 3.3 Lussen voorkomen

aa-kanban maakt zelf ook threads aan, als ticketthreads in `discord_ticket_channel_id`. Is dat kanaal ook een intake-kanaal, dan zou een kaart een thread maken, en die thread weer een kaart. Daarom:

- de bot negeert threads die door een bot zijn geopend;
- het endpoint is idempotent op `thread_id`;

## 4. Fasering

| Fase | Inhoud | Project |
|---|---|---|
| **1. Bot opschonen** | <ul><li>Regel-engine met `rules.yaml`</li><li>GitHub-acties ombouwen (async `httpx`, vaste discussioncategorie)</li><li>Startbericht via `thread.id`</li><li>Bots negeren</li><li>DEBUG-logging en `on_message` weg</li><li>pytest, ruff en pre-commit</li><li>De `.env`-sleutels blijven als terugval werken</li></ul> | githubDiscordBOT |
| **2. Intake in aa-kanban** | <ul><li>`IntakeApiKey` (met migratie, beheer in admin)</li><li>Servicegebruiker "Discord intake"</li><li>Endpoint `POST discord-thread`</li><li>Tests, NL-vertalingen, handleiding</li></ul> | aa-kanban |
| **3. Kanban-actie in de bot** | <ul><li>`kanban_card`-actie</li><li>Antwoord met link in de thread</li><li>Foutmelding in de thread als aa-kanban niet bereikbaar is (geen stille fout)</li></ul> | githubDiscordBOT |
| **4. Optioneel** | <ul><li>Forum-tags worden kanbanlabels</li><li>Kaart gearchiveerd → thread gesloten</li><li>Kanaalnamen tonen in de frontend</li><li>Actie `webhook` (n8n)</li></ul> | beide |

Fase 1 en 2 kunnen tegelijk. Fase 3 heeft beide nodig.

## 5. Alternatief en aandachtspunten

### 5.1 Alternatief: alles in de aa-kanban-cog

We kunnen ook `on_thread_create` toevoegen aan de bestaande `KanbanTicketCog`, die binnen de aadiscordbot draait:

- **Voordelen:** geen API en geen sleutel nodig, en minder code.
- **Nadelen:**
  - de GitHub-bot blijft dan een apart, specifiek ding, en dat is precies wat we generiek willen maken;
  - het kanbandeel gaat dan nog zwaarder leunen op de aadiscordbot (zie 5.2).

**Daarom niet aanbevolen.**

### 5.2 aadiscordbot en AGENTS §15

aa-kanban gebruikt nu al `aadiscordbot`, een Alliance Auth-app van een andere ontwikkelaar, voor:

- DM's;
- ticketthreads;
- de comment-sync-cog.

Die app staat niet op de lijst met toegestane platform-afhankelijkheden in §15. Dit voorstel voegt daar niets aan toe: de nieuwe intake loopt via onze eigen bot. Wel moet besloten worden of `aadiscordbot` als platform geldt, of dat aa-kanban die rol op termijn overdraagt aan deze eigen bot. In het tweede geval wordt de router de algemene Discord-bot van onze tools.

### 5.3 Naam en hosting

- **Naam:** de repo heet `githubDiscordBOT`, maar dat dekt de lading straks niet meer. Voorstel: hernoemen naar `discord-thread-router`. GitHub zet de oude URL automatisch door.
- **Hosting:** de bot draait als container met `restart: unless-stopped`. Voor de kanban-actie moet hij aa-kanban kunnen bereiken. Draait hij op devauth naast Alliance Auth, dan kan dat via het interne adres.
- **Discord-rechten:** de bot heeft per kanaal `View Channel`, `Read Message History` en `Send Messages in Threads` nodig. De Message Content Intent blijft nodig om het startbericht te lezen.

## 6. Open beslissingen

Zie sectie 0. Nog open: de host waarop de container draait (bij de uitrol).

## 7. Acceptatiecriteria (na fase 3)

- Een beheerder koppelt in `rules.yaml` een Discord-kanaal aan een bord en een lijst. Zonder herstart van de bot leidt een nieuwe thread in dat kanaal binnen enkele seconden tot een kaart.
- De kaart heeft:
  - de threadtitel als titel;
  - het startbericht, de Discord-auteur en een link naar de thread in de beschrijving;
  - de ingestelde labels en het ingestelde team.
- De bot antwoordt in de thread met een link naar de kaart.
- Berichten in de thread verschijnen als reactie op de kaart (bestaande sync).
- Een herstart van de bot of een tweede event voor dezelfde thread maakt geen tweede kaart.
- Threads van bots en kanalen zonder regel worden genegeerd.
- Issues en discussions op GitHub blijven werken zoals nu, maar dan via `rules.yaml`.
- Tests dekken:
  - de regel-engine;
  - elke actie, met gemockte HTTP-calls;
  - het intake-endpoint: sleutel, idempotentie, gebruikerskoppeling en een onbekend bord.
