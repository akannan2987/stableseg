# Hosting: every way to put StableSeg online, compared

[← README](../README.md) · [All docs in order](../README.md#the-tutorial-in-order) · [Glossary](00-glossary.md) · [Product roadmap](06-product-and-technology-roadmap.md)

**Prerequisites:** the project installed and running locally (your setup
guide). Nothing here is needed to use StableSeg — everything works offline on
your own machine.
**Learning goal:** after this page you know what "hosting" actually means, the
difference between serving a *file* and running a *program*, what each free
option costs in constraints, and which one to pick for each of StableSeg's two
publishable outputs.
**Checkpoint:** you can explain why the report is far cheaper to host than the
explorer, and name what would have to be true before paying for hosting made
sense.

**Status:** nothing is deployed yet. The explorer arrives in phase 7 and the
report in phase 8. This page exists now so the decision is made deliberately
rather than in a hurry later.

---

## 1. What "hosting" means, from zero

Your project currently lives on your laptop. When you close the lid, it is
unreachable. **Hosting** means putting it on a computer that is always on and
connected, so anyone with the address can reach it.

Everyday comparison: a recipe in your kitchen drawer versus a recipe pinned to
a public noticeboard. Same recipe. The noticeboard costs something — you have
to rent the board, and keep it tidy — but other people can read it without
visiting your kitchen.

**The single most important distinction**, and the one that decides everything
below:

- **A static file** is finished before anyone asks for it. The server just
  hands over the bytes. A photograph, a PDF, a finished web page. Cheap,
  usually free, essentially unbreakable.
- **A running program** does work when someone asks. It needs a computer with
  memory and processor time, sitting idle between visitors. Costs real money,
  or comes with real limits.

The everyday version: the noticeboard is static — you pin it and walk away. A
person standing at a desk answering questions is a running program, and someone
has to pay them to stand there.

StableSeg has one of each:

| Output | Which kind | Consequence |
|---|---|---|
| **The report** (phase 8) | Static file — the numbers are computed before publishing | Free hosting, trivially |
| **The explorer** (phase 7) | Running program — it recomputes when you move a slider | Needs a machine; free tiers have limits |

---

## 2. Hosting the report — the easy half

The report is a self-contained web page produced by **Quarto**, a tool that
combines text, code and the code's output into one document. Once rendered, it
is a file. Any file host will serve it.

### GitHub Pages — the recommended choice

**What it is.** GitHub will serve files straight out of your repository as a
website, free, for public repositories.

**Why it wins here.** The report already lives in the repository next to the
code that produced it. Publishing means committing it. No new account, no new
service, no cost, and the address sits beside the source — which for a
reproducible-analysis project is exactly the right relationship.

**The address it produces:**
```
https://akannan2987.github.io/stableseg/
```

**Setup, when phase 8 lands** (recorded here so it is not researched twice):

1. Render the report into a folder the site serves from — conventionally
   `docs/` or a branch named `gh-pages`. Since `docs/` here is the tutorial,
   a dedicated `site/` folder published to `gh-pages` keeps the two separate.
2. On GitHub: **Settings → Pages → Source**, choose the branch and folder.
3. Wait a minute, then open the address. GitHub shows it on that same page.

**Cost:** none. **Limits:** public repositories only (private ones need a paid
plan), a soft site-size limit around 1 GB, and it serves files only — no
program runs.

### The alternatives, and why not

| Option | What it is | Why not here |
|---|---|---|
| **Netlify / Vercel** | Polished static hosting with build automation | Genuinely good, and free — but a second account and service for something GitHub already does next to the code |
| **A web host you rent** | Shared hosting, upload files by FTP | Costs money to do what GitHub does free |
| **Your own server** | A rented machine you administer | Enormous overkill for one HTML file |

---

## 3. Hosting the explorer — the interesting half

The explorer is **Streamlit**, a tool that turns a Python script into an
interactive web page. When someone moves a slider, Python runs. That means a
machine must be awake, with the project installed, waiting.

### Streamlit Community Cloud — the recommended choice

**What it is.** The makers of Streamlit host apps from public GitHub
repositories, free.

**Why it wins here.** It reads the repository directly, installs the
dependencies, runs the app, and gives it an address. Updating it means pushing
a commit — the same loop you already use. Nothing new to learn, nothing to
maintain.

**The address it produces:**
```
https://<something>.streamlit.app
```

**Setup, when phase 7 lands:**

1. Sign in at the Streamlit Community Cloud site with your GitHub account.
2. Point it at `akannan2987/stableseg`, branch `master`, and the app file.
3. Confirm it can read the repository. It installs and starts the app.

**Cost:** none.

**Limits, and they matter** — check the current figures before relying on them,
since free tiers change:

- **Modest memory.** Enough for tables and charts; not enough to train a
  neural network or hold many large volumes at once.
- **It sleeps.** After a period without visitors the app shuts down, and the
  next visitor waits while it restarts.
- **Public repository required** on the free tier.

**How the design already handles this**, and it is worth seeing the connection:
the explorer will read *precomputed* results out of the database rather than
recomputing an audit on demand. The heavy work happens on your laptop; the
hosted app reads a table and draws charts. That is what keeps it inside a free
tier's memory, and it is why the storage layer exists.

If you deploy the full project as-is, the deep-learning add-on would try to
install PyTorch — hundreds of megabytes for something the explorer never calls.
The optional-extras split in `pyproject.toml` prevents that: the hosted app
installs the core plus the app extra, and nothing more. A design decision from
phase 1 paying off in phase 7.

### The alternatives, and why not (yet)

| Option | What it is | Verdict |
|---|---|---|
| **Hugging Face Spaces** | Free hosting for data-science demos, Streamlit supported | Solid fallback. Chosen second only because Streamlit's own service reads the repository more directly |
| **A rented small server** | A virtual machine you install and maintain | Always awake, no sleeping — but you become the administrator: updates, certificates, security. Real work, small money |
| **Serverless functions** | Upload a function, provider runs it per request | Poor fit: audits take minutes and hold big arrays; serverless caps both |
| **Kubernetes** | Manages many containers across many machines | Not remotely warranted. See the product roadmap |

---

## 4. Choosing, in one table

| You want to publish | Use | Cost | Main constraint |
|---|---|---|---|
| The rendered report | GitHub Pages | Free | Public repository; static files only |
| The interactive explorer | Streamlit Community Cloud | Free | Sleeps when idle; modest memory |
| Both, always awake, custom address | A small rented server | Money and your time | You maintain it |
| Nothing — local use only | Nothing | Free | Reachable only by you |

**The honest recommendation for this project:** GitHub Pages for the report,
Streamlit Community Cloud for the explorer, and nothing else until there is a
concrete reason. Together they cost nothing, need no maintenance, and update
themselves from the same push you already do.

---

## 5. Before you deploy anything: the safety checklist

Publishing is different from committing. Committing puts code in a repository;
deploying puts a *running program* on the public internet. Five things to
verify:

1. **No credentials in the repository.** `python scripts/preflight.py` checks
   this on every push. If a hosted service ever needs a secret, it goes in that
   service's own secrets settings, never in a file.
2. **No data that cannot be published.** Everything here is open, licensed,
   de-identified research data, plus synthetic phantoms. That is why deploying
   is uncomplicated. It would not be with patient data — see the hard line in
   [`06-product-and-technology-roadmap.md`](06-product-and-technology-roadmap.md),
   section 5.5.
3. **The synthetic disclosure survives.** The phantoms are generated, and the
   simulated repeat scans are simulated. Both must say so *in the interface a
   stranger sees*, not only in the README they may never open.
4. **It runs from a clean clone.** If it only works because of a file sitting
   on your laptop, hosting will find out immediately. The automated checks
   already prove this on six platform combinations.
5. **Someone else's licence terms are respected.** The imaging dataset is
   CC-BY-SA 4.0, which requires attribution and share-alike terms. Credit it
   wherever it is used, including in anything hosted.

---

## 6. Publishing checklist for phase 8

Not actionable yet; here so the phase does not have to rediscover it.

- [ ] Report renders from a clean clone with one command
- [ ] Every number in it comes from the database, none typed by hand
- [ ] Limitations section present: synthetic phantoms, simulated repeats,
      sample size
- [ ] Dataset credited with its licence
- [ ] `scripts/preflight.py` clean
- [ ] Pages source configured and the address recorded in the README
- [ ] Explorer reads precomputed results only
- [ ] Explorer installs core + app extras, not the deep-learning extra
- [ ] Both addresses added to the README badges

---

## 7. Committing changes to this document

```bash
git switch develop
git add -A
git commit -m "docs: update hosting options"
git push origin develop develop:beta develop:master

## --tags is optional, only when required

git switch master
git pull --ff-only origin master
git switch develop
```

---

Next: [`CLI_COOKBOOK.md`](CLI_COOKBOOK.md) — ready-to-paste commands, from the
first run to a full audit.
