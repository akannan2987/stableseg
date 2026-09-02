# 06 · Product and Technology Roadmap

[← README](../README.md) · [All docs in order](../README.md#the-tutorial-in-order) · [Glossary](00-glossary.md) · [Roadmap](05-roadmap.md)

**Prerequisites:** none. Every technology named here is explained from zero.
**Learning goal:** after this page you understand what each major piece of
modern software infrastructure actually *is*, in everyday terms — web front
ends, warehouses, orchestrators, containers, tool servers, ontologies — and,
more importantly, how to decide whether a project needs one. The deciding is
the transferable skill.
**Checkpoint:** you can explain why this project uses a single-file database
rather than a database server, and name the one change that would reverse that
decision.

---

## 1. The question this page answers

StableSeg today is a tool that runs on one laptop. Suppose it were to become a
product: something hosted, used by people who did not build it, possibly paid
for. What would that take, and which of the many available technologies would
actually be needed?

There is a strong pull in software toward adding things. Every technology below
is genuinely good at something, is used by serious organisations, and looks
impressive on a diagram. The discipline is to add each one only when a specific
problem demands it — because every addition costs setup, maintenance,
documentation, and a chunk of the next person's attention.

**The rule this project follows: justify, do not accumulate.**

So each option below gets four things:

1. **What it is** — in plain language, with an everyday comparison.
2. **What problem it solves** — the specific pain it removes.
3. **A verdict** — one of four:
   - **Required now** — in the project today, or it should be.
   - **Recommended later** — a clear future yes, with a phase attached.
   - **Optional** — would work, but the benefit is not obvious yet.
   - **Not needed** — no, and here is why.
4. **The trigger** — the specific, observable change that would flip the
   verdict. A verdict without a trigger is an opinion; with one it is a
   decision you can revisit rationally.

---

## 2. Product surface: what a person actually touches

### 2.1 A web front end (React or similar)

**What it is.** A **front end** is the part of a program a person looks at and
clicks — the dining room of the restaurant, as opposed to the kitchen. React
is a widely used toolkit for building those pages out of reusable pieces, in a
language called JavaScript (or TypeScript, which is JavaScript with type
checking — think of types as seatbelts that catch a whole class of mistake
before the page ever runs).

**What problem it solves.** Complete control over how the page looks and
behaves, multiple people using it at once, custom interactions that a simpler
tool cannot express.

**Verdict: Not needed.** The planned explorer uses **Streamlit**, which turns a
Python script into a web page with no web code at all. For "pick a disturbance
from a dropdown, look at a chart, read a table", Streamlit is not a compromise —
it is the right size. Choosing React instead would mean maintaining a second
language and a separate build process to display the same three charts.

**Trigger to reconsider:** more than one person needs to be logged in with
different permissions, or the interface needs something Streamlit genuinely
cannot express — freehand outline editing on a scan slice, for example, or a
drag-and-drop workflow builder.

### 2.2 Desktop and mobile packaging, distribution through stores

**What it is.** Wrapping the software so it installs like any other program on
a computer or phone, and distributing it through a company's store.

**What problem it solves.** Reaching people who will never open a terminal.

**Verdict: Not needed.** The users of a measurement-system audit are imaging
scientists and analysts who already work with files and command-line tools. A
phone is the wrong device for inspecting a 3-D scan. Store distribution adds
code signing, review processes, and — for anything that touches medical data —
a regulatory conversation.

**Trigger:** a defined group of users who cannot install Python and who need
this on a machine you do not control.

### 2.3 Licensing and payments

**What it is.** Charging money: a licence saying what a buyer may do, and a
payment system to collect it.

**What problem it solves.** Making the work sustainable.

**Verdict: Not needed.** The project is MIT-licensed, which means anyone may
use, modify and redistribute it, including commercially. That is deliberate: an
audit tool people can inspect and re-run is more credible than one they cannot.
There is no product to sell yet, and adding payments before there is is
building a till for an empty shop.

**Trigger:** an organisation asks for something the open version does not
provide — support commitments, validation documentation, hosted infrastructure.
Note the pattern: the sellable thing is usually the *service*, not the code.

---

## 3. Data platform: where numbers live

### 3.1 PostgreSQL (a database server)

**What it is.** A **database** is organised storage in tables, questioned with
a language called SQL. PostgreSQL is a **server** database: a program that runs
continuously and that several programs connect to at once. StableSeg instead
uses **DuckDB**, which is a complete database in a single file, with no server
running.

The everyday comparison: DuckDB is a filing cabinet in your office. PostgreSQL
is a records department with a counter, a queue, and staff who enforce who may
see what.

**What problem it solves.** Several people or programs reading and writing at
the same time, without corrupting each other's work. Permissions. Backups.
Data that outlives any one machine.

**Verdict: Recommended later.** Correct once anything is hosted; unnecessary
while one person runs audits on one laptop. The important design decision is
already made: all output goes through the `Storage` layer in `storage.py`, so
swapping the backend means writing one new class, not editing the project.

**Trigger:** a second person needs to read the results, or the tool starts
running somewhere other than a laptop.

### 3.2 Databricks and Snowflake (cloud data platforms)

**What they are.** Rented computing and storage for data work at large scale.
**Snowflake** is a warehouse — a database built for analysing enormous tables,
where you pay for the machine time you use. **Databricks** is a platform for
running computations across many machines at once, built around a system called
Spark.

Everyday comparison: your kitchen can cook dinner for eight. These are catering
companies with an industrial kitchen. Excellent for a wedding, absurd for
Tuesday.

**What problem they solve.** Tables with billions of rows; computations too big
for one machine; many teams sharing governed data.

**Verdict: Not needed.** The numbers here are small — a few hundred cases times
a few dozen disturbances times a handful of measurements is tens of thousands
of rows. DuckDB answers questions on that in milliseconds. The *images* are
large, but images are files, and neither of these platforms is a good place to
put files.

**Trigger:** joining the biomarker table to enterprise-scale clinical data
already living in one of these platforms. Note the direction — the trigger is
where the *other* data lives, not how big this project's data gets.

### 3.3 dbt (a transformation tool)

**What it is.** dbt lets you write data transformations as SQL files that are
version-controlled, tested and documented, and run in the right order
automatically.

Everyday comparison: a recipe book where each recipe lists which other recipes
must be made first, and every recipe has a taste test attached.

**What problem it solves.** Transformation logic sprawling across notebooks and
scripts with no tests and no dependency order.

**Verdict: Not needed.** dbt earns its keep when there are dozens of
interdependent SQL transformations. StableSeg's transformations are in Python,
because they operate on 3-D image arrays rather than tables — SQL is the wrong
language for resampling a volume. The tabular layer is thin.

**Trigger:** the tabular layer grows past roughly ten interdependent SQL
transformations, or a team wants to add their own without touching Python.

### 3.4 An orchestrator (Airflow, Dagster, Prefect)

**What it is.** A program that runs your steps in the right order, on a
schedule, retries failures, and tells you what broke.

Everyday comparison: an alarm clock combined with a checklist and a supervisor
who phones you when a step fails.

**What problem it solves.** Multi-step work that must run unattended, on time,
reliably.

**Verdict: Not needed.** One command runs the whole audit, in minutes, when a
person decides to run it. Nothing is scheduled and nothing is unattended. An
orchestrator is a service you must install, configure, secure and keep running —
substantial cost for a problem that does not exist here.

**Trigger:** audits need to run automatically — nightly across many models, or
whenever new data arrives. Note the gentle path when that day comes: a scheduled
task on your own machine first, an orchestrator only when the dependency graph
genuinely branches.

### 3.5 Object storage (Amazon S3 and equivalents)

**What it is.** Storage for files in the cloud, addressed by name, effectively
unlimited, paid for by the gigabyte.

Everyday comparison: a self-storage unit rather than the cupboard in your flat.
Cheap, enormous, slightly slower to reach, accessible from anywhere.

**What problem it solves.** Files too big or too shared for one laptop.

**Verdict: Recommended later.** Arrives with hosting, not before. The
`Storage` layer already isolates the change.

**Trigger:** the tool runs on a machine that is not yours, or two people need
the same input data.

### 3.6 Data and model versioning (DVC and similar)

**What it is.** Git tracks code well and large files badly. These tools store
the large files elsewhere and keep a small pointer in Git, so "the data as it
was at this commit" remains recoverable.

Everyday comparison: a library catalogue card. The card is in the drawer; the
book is on a shelf in the basement; the card tells you exactly which shelf.

**What problem it solves.** Knowing which data produced which result, months
later.

**Verdict: Recommended later.** Partly solved already, and worth understanding
why: the input data is either downloaded from a fixed public source or
regenerated by a seeded script, and every run records the code version and full
settings in `run.json`. That gets reproducibility without new infrastructure.
Trained models are the gap — a model file is neither downloadable nor cheaply
regenerable.

**Trigger:** the deep-learning phase produces trained models worth keeping, or
input data starts changing over time.

---

## 4. The intelligent layer

### 4.1 Language-model tooling

**What it is.** A **large language model** is a program trained on enormous
amounts of text that can write fluent prose and follow instructions. Used here,
it would turn computed numbers into readable sentences.

**What problem it solves.** A repeatability coefficient of 91 mm³ means nothing
to most readers. A paragraph explaining what it implies for a study means a
great deal.

**Verdict: Recommended later (0.4.0).** With one hard constraint: the narration
must be **grounded**, meaning the model is given the computed numbers and asked
only to explain them, never to produce numbers itself. These models will state
a plausible figure with complete confidence when they do not know one, and in a
measurement audit that is disqualifying. The design that manages the risk:
numbers come from the pipeline, sentences come from the model, and the report
labels which is which.

**Trigger:** the report exists and its numbers are stable. Explaining output
that is still changing is wasted effort.

### 4.2 Retrieval over documents

**What it is.** Instead of hoping a model memorised something, you search your
own documents for the relevant passages and hand those to the model along with
the question. Commonly called retrieval-augmented generation.

Everyday comparison: an open-book exam. The model is a fluent writer; retrieval
is the librarian who puts the right page in front of it.

**What problem it solves.** Answering questions about *your* material rather
than about the world in general.

**Verdict: Optional.** Genuinely useful once there are many audit reports to
ask questions across — "which of our models was least stable under movement?"
With a handful of reports, reading them is faster than building a search layer.

**Trigger:** roughly a dozen accumulated reports, or a body of methodological
literature worth searching alongside them.

### 4.3 A tool server (Model Context Protocol)

**What it is.** A shared convention that lets one program offer its
capabilities to another in a standard, machine-readable way. Model Context
Protocol is one such convention.

Everyday comparison: a USB port. Before it, every device needed its own
connector; after it, one shape fits everything.

**What problem it solves.** Other programs — including automated agents — can
run an audit and read its results without a person typing commands, and without
anyone writing custom glue for each combination.

**Verdict: Recommended later (0.4.0).** The groundwork is already laid, which
is the point worth noticing: every capability lives in `api.py` as a plain
function with typed inputs and dictionary outputs. A tool server is a thin
wrapper over those functions. That was a deliberate design choice in phase 1,
made so this addition would be *additive* rather than a rewrite.

Two constraints when it arrives: expose read-only operations first, because a
program that can trigger work is a program that can trigger expensive or
destructive work; and validate every input, because the caller may be another
program with no judgement.

**Trigger:** the audit functions are stable and there is a real reason to drive
them from outside — a second tool in a workflow, or automating comparisons
across many models.

### 4.4 Knowledge graphs and clinical vocabularies

**What they are.** A **knowledge graph** stores information as things and the
relationships between them — a family tree for concepts, rather than a table.
A **clinical vocabulary** is an agreed dictionary of medical terms with stable
identifiers: **SNOMED CT** covers clinical concepts broadly, **RadLex** covers
radiology specifically. Together they mean "left hippocampus" is recorded as a
code that every system agrees on, rather than as free text that one system
spells differently from the next.

Everyday comparison: postcodes. "The house with the red door on the corner"
works between neighbours and fails everywhere else. A postcode works
everywhere, forever.

**What problem they solve.** Findings that other systems can consume without a
human translating them.

**Verdict: Optional.** StableSeg's output today is numeric and narrow: one
structure, one biomarker, one repeatability figure. A vocabulary adds real
value when findings are varied, textual, and destined for another system. There
is a cheap partial step worth taking earlier — recording the anatomical
structure as a stable identifier rather than the string `"hippocampus"` — which
costs almost nothing and makes the later step easy.

**Trigger:** results must flow into a clinical or research system that expects
coded terms, or the tool covers enough structures that free-text naming becomes
a source of error. Note that SNOMED CT has licensing conditions that vary by
country; check before depending on it.

---

## 5. Running it somewhere other than your laptop

### 5.1 Containers (Docker, Podman)

**What they are.** A container packages a program together with everything it
needs to run — libraries, settings, the lot — so it behaves identically on any
machine.

Everyday comparison: a food truck instead of a restaurant. The kitchen travels
with the cook, so the dish comes out the same wherever it parks.

**What problem they solve.** "It works on my machine" — the oldest complaint in
software.

**Verdict: Recommended later (0.2.0).** Not yet, and the reason is worth
stating: reproducibility is already demonstrated a different way — pinned
dependency versions plus automated checks on three operating systems and two
Python versions, all green. A container becomes genuinely valuable when the
dependencies get heavier and harder to install, which is exactly what the
deep-learning phase brings.

**Trigger:** the deep-learning phase lands, or the tool needs to run on a
machine where you cannot install Python.

### 5.2 Kubernetes and serverless computing

**What they are.** **Kubernetes** manages many containers across many machines,
restarting what crashes and scaling what is busy. **Serverless** means you
upload a function and the provider runs it on demand, charging per call.

Everyday comparison: Kubernetes is a shipping port with cranes and a schedule —
indispensable at scale, ridiculous for one parcel. Serverless is a taxi rather
than owning a car: no vehicle to maintain, but you pay per journey and cannot
keep luggage in the boot.

**What problem they solve.** Many users, unpredictable load, high availability.

**Verdict: Not needed.** There is no service. There are no users but you. An
audit run takes minutes and holds large volumes in memory, which suits
serverless poorly — most serverless platforms cap how long a function may run
and how much memory it may hold.

**Trigger:** a hosted service with enough traffic that a single machine cannot
keep up. That is a long way off, and a single well-chosen machine goes further
than people expect.

### 5.3 Automated checks on every change

**What it is.** A service that installs and tests the project on fresh machines
every time you push a change.

Everyday comparison: a colleague who silently rebuilds your work from scratch
on three different computers after every edit and tells you if it broke.

**Verdict: Required now — and already in place.** `.github/workflows/ci.yml`
runs on Windows, macOS and Linux, on Python 3.12 and 3.13: six combinations,
every push. It caught a real problem during phase 1 — a dependency floor that
made the declared Python range wrong — and it is the only reason the
cross-platform claim in the README is a claim rather than a hope.

### 5.4 Monitoring, and a cost model

**What they are.** **Monitoring** watches a running system and alerts you when
it misbehaves. A **cost model** is the arithmetic of what running it will cost
per month.

**Verdict: Not needed** for either, today. Nothing runs unattended, and running
on your own laptop costs nothing.

**Trigger:** the first hosted deployment. Both become mandatory the same day —
an unmonitored service fails silently, and an unbudgeted one produces a
surprising bill. For scale, a small hosted setup of this shape is typically
tens of dollars a month, dominated by whichever machine is always on.

### 5.5 Privacy law and medical-device rules

**What they are.** **GDPR** is European law giving people rights over data
about them; health data gets the strictest treatment. **HIPAA** is the American
equivalent for health information. **Medical-device software** rules apply when
software informs a clinical decision — bringing a quality management system,
formal validation, and legal liability.

Everyday comparison: a home kitchen versus a commercial one. Same cooking, but
one has inspections, records, and someone whose name is on the certificate.

**Verdict: Documented now, enforced later.** Today the project touches only
open, de-identified, publicly licensed research data, and it makes no clinical
claim. That is precisely why it can be developed openly.

**Trigger — and this one is a hard line, not a preference:** the moment real
patient data or a clinical decision is involved, the entire engineering
approach changes. Storage becomes access-controlled and audited, deployment
becomes location-constrained, every change becomes documented and approved, and
someone qualified must be accountable. "We will add compliance later" is the
most expensive sentence in health software. Knowing where that line sits, and
staying on the correct side of it deliberately, is itself the professional
skill.

---

## 6. If it ever became a product people found

### 6.1 Being findable: search, answer engines, generative engines

**What they are.** **Search engine optimisation** is making a page rank well in
a conventional search. **Answer engine optimisation** is making it the source
that gets quoted when a system answers a question directly instead of listing
links. **Generative engine optimisation** is the same idea for systems that
compose an answer from several sources.

Everyday comparison: search optimisation is being on the right shelf in the
shop. Answer optimisation is being the thing the assistant recommends when
someone asks. The second is increasingly how people arrive.

**What they share, practically.** All three reward the same underlying things:
clear structure, honest specific claims, self-contained sections that can be
quoted without surrounding context, plain definitions of terms, and content
that answers a real question rather than circling it.

**Verdict: Not needed** as an activity — there is no product site. Worth
noticing, though: writing documentation the way this project does — every term
defined, every section self-contained, claims stated plainly — is the same
discipline. Good documentation is discoverable documentation, at no extra cost.

**Trigger:** a public site exists with something to offer beyond the repository.

### 6.2 Pricing and packaging, sketched

Purely hypothetical, and included because thinking it through clarifies what
would actually be valuable.

| Tier | Who | What they get | Roughly |
|---|---|---|---|
| **Open** | Anyone | The full tool, MIT-licensed, self-run | Free, always |
| **Hosted** | Small teams without infrastructure | Run audits in a browser, results stored and shared | Per seat, monthly |
| **Validated** | Regulated environments | Validation documentation, version pinning, support commitments | Annual contract |

The pattern worth noticing: the code stays free in every tier. What is sold is
convenience, assurance and accountability. That is the norm in scientific
software for a good reason — a measurement tool nobody can inspect is a
measurement tool nobody should trust.

---

## 7. What the finished product would actually do

End to end, with today's contribution marked:

```
1. INGEST     scans arrive: files, a hospital archive, or a folder      ⬜ 0.2.0
                  │
2. SEGMENT    outline the structure — own model, classical baseline,    ⬜ 0.2.0
   OR IMPORT  or outlines exported from another tool                    ⬜ 0.3.0
                  │
3. AUDIT      apply the disturbance bank, re-measure every variant,     ⬜ 0.2.0
              compute repeatability statistics                          ⬜ 0.2.0
                  │
4. REPORT     a readable record: methods, figures, the minimum          ⬜ 0.3.0
              detectable change, the honest limitations
                  │
5. SERVE      the explorer, the sample-size calculator, and a way       ⬜ 0.3.0
              for other programs to ask                                 ⬜ 0.4.0
```

**What version 0.1.0 already contributes to that pipeline** — and this is the
part worth being clear about, because a frame looks like nothing until you
notice what it holds up:

| Piece in place | Which stage it serves |
|---|---|
| `io.py` — loading with geometry preserved | 1 · ingest |
| `Storage` layer with provenance stamps | every stage writes through it |
| `config.py` — one validated file describes one run | every stage is configured by it |
| `api.py` — typed functions, dictionary results | 5 · serve, and the tool server after it |
| `phantom.py` — data with a known true answer | 3 · audit, as the correctness check |
| Automated checks on six platform combinations | every stage, on every change |
| The documentation set | every stage, for anyone arriving later |

Five of the six pieces exist to make the *next* stages cheap to add. That was
the point of building them first.

---

## 8. The decision summary

| Option | Verdict | Trigger that would change it |
|---|---|---|
| React web front end | Not needed | Multi-user with permissions, or an interaction Streamlit cannot express |
| Desktop / mobile / store distribution | Not needed | Users who cannot install Python, on machines you do not control |
| Licensing and payments | Not needed | Someone asks for support, validation or hosting |
| PostgreSQL | Recommended later | A second reader, or anything hosted |
| Databricks / Snowflake | Not needed | Joining to enterprise data that already lives there |
| dbt | Not needed | More than ~10 interdependent SQL transformations |
| Orchestrator | Not needed | Audits must run unattended on a schedule |
| Object storage | Recommended later | Running off-laptop, or shared input data |
| Data / model versioning | Recommended later | Trained models worth keeping; changing inputs |
| Language-model narration | Recommended later (0.4.0) | The report exists and its numbers are stable |
| Retrieval over documents | Optional | Roughly a dozen accumulated reports |
| Tool server | Recommended later (0.4.0) | A real external caller for the audit functions |
| Knowledge graphs / clinical vocabularies | Optional | Output must feed a system expecting coded terms |
| Containers | Recommended later (0.2.0) | The deep-learning phase, or a machine without Python |
| Kubernetes / serverless | Not needed | A hosted service outgrowing one machine |
| Automated checks on every change | **Required now — in place** | — |
| Monitoring and a cost model | Not needed | The first hosted deployment |
| Privacy law / medical-device rules | Documented now | Real patient data or any clinical claim — a hard line |
| Search / answer / generative optimisation | Not needed | A public product site exists |

**Fourteen of nineteen are "no" today.** That is the intended result. Every one
of them would work, and adding them would make the architecture diagram more
impressive and the project worse. The discipline of writing down *why not*, and
what would change the answer, is what makes it a decision rather than neglect —
and it means that when a trigger does fire, the reasoning is already done.

---

## 9. Committing changes to this document

```bash
git switch develop
git add -A
git commit -m "docs: update product and technology roadmap"
git push origin develop develop:beta develop:master

## --tags is optional, only when required

git switch master
git pull --ff-only origin master
git switch develop
```

---

Next: [`HOSTING.md`](HOSTING.md) — the practical version of section 5, for when
the explorer and the report do need to go online.
