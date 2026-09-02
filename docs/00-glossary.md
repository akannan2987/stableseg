# 00 · Glossary

[← Build guide](../BUILD_GUIDE.md) · [README](../README.md) · [Architecture](02-architecture.md)

Every term used anywhere in this project, in plain language, with an everyday
comparison where one helps. Keep this open while you read anything else. If a
word appears in the repository and is not here, that is a documentation bug
worth reporting.

Two groups: **the subject** (scans, structures, statistics) and **the
machinery** (software, tools, workflow). Within each, alphabetical.

---

## Part 1 — The subject: images, measurement, statistics

**Affine.** The 4 × 4 table of numbers in a scan's header that says how big
each voxel is and which way is up. *Everyday version:* the scale bar on a map.
Without it, the map's shapes mean nothing in kilometres. Lose the affine and
every volume you compute is wrong by an unknown factor.

**Bias field.** A slow, smooth brightness drift across an MRI: one side of the
image brighter than the other, for physical reasons rather than anatomical
ones. *Everyday version:* a photo taken with a lamp off to one side.

**Biomarker.** Any measurement that stands in for something about a patient.
An **imaging biomarker** is one computed from a scan, such as the volume of a
structure in cubic millimetres. *Everyday version:* the number on a bathroom
scale standing in for "how the diet is going".

**Bland–Altman plot.** A chart for comparing two measurements of the same
thing: their average on the horizontal axis, their difference on the vertical.
It reveals whether the error grows with the size of what you measure, which a
single correlation number hides. *Everyday version:* checking whether your
kitchen scale is fine for flour but hopeless for a whole turkey.

**Contrast.** How different in brightness a structure is from what surrounds
it. Low contrast means the edge is hard to find, for a human or a computer.

**CT (computed tomography).** An imaging method using X-rays from many angles.
Values are in standard units (Hounsfield units), which makes CT easier to
compare across scanners than MRI. StableSeg's perturbation profile for CT is
on the roadmap.

**Dice score.** A number from 0 to 1 saying how much two outlines overlap: 1 is
perfect agreement, 0 is none. The standard way segmentation accuracy is
reported. *What it does not tell you:* whether the measurement is stable, which
is the gap this project exists to fill.

**DICOM.** The file format hospitals use: typically one file per image slice,
carrying extensive patient and scanner information in its header. *Everyday
version:* a stack of individually labelled photographs.

**Ground truth.** The correct answer, usually an outline drawn by an expert.
Real scans have an expert's opinion; synthetic phantoms have an actual known
truth, which is why this project generates them.

**Hausdorff distance.** The worst-case gap between two outlines: how far the
most badly misplaced piece of a boundary is from where it should be.
*Everyday version:* not "how similar are these two coastlines on average", but
"where is the single biggest error, and how big is it".

**Hippocampus.** A small, curved structure deep in each half of the brain,
central to memory. It shrinks in neurodegenerative disease, so its volume
measured from MRI is used as an endpoint in clinical trials. StableSeg's first
real target.

**ICC (intraclass correlation coefficient).** A number from 0 to 1 saying what
fraction of the total variation in your measurements is real difference
between subjects, rather than measurement noise. High ICC means the
measurement separates people well. *Everyday version:* if everyone's weight
readings jump by two kilos at random, but people differ from each other by
thirty, the scale still ranks people correctly — ICC is high. If people differ
by one kilo, it does not — ICC is low.

**Label / mask.** The result of segmentation: a volume the same size as the
scan, where each voxel says which structure it belongs to (0 = background,
1 = first structure, 2 = second). *Everyday version:* a colouring-in layer
traced over a photograph.

**Minimum detectable change.** The smallest real change in a measurement that
can be told apart from measurement noise. The single most useful output of
this project. *Everyday version:* if your scale wobbles by two kilos, do not
believe a one-kilo loss.

**Modality.** The kind of imaging: MRI, CT, PET, ultrasound, and so on. Each
has its own physics and therefore its own realistic disturbances, which is why
StableSeg organises perturbations into **modality profiles**.

**Morphology (in image processing).** Simple operations that grow, shrink,
clean up or fill in a mask by looking at each voxel's neighbours. *Everyday
version:* tidying a hand-traced outline by rubbing out stray specks and
filling small gaps.

**MRI (magnetic resonance imaging).** An imaging method using strong magnets
and radio waves. Excellent soft-tissue contrast; its brightness values are not
in standardised units, which makes comparisons across scanners genuinely hard.

**NIfTI (`.nii`, `.nii.gz`).** The research file format for 3-D scans: one
file holds the whole volume plus a header with the voxel size and orientation.
*Everyday version:* one labelled box holding the entire stack of slices,
versus DICOM's loose pile of photographs.

**Normalisation (intensity).** Rescaling brightness values into a common range
so scans can be compared. *Everyday version:* adjusting the exposure on
photographs taken in different light before comparing them.

**Phantom.** A stand-in object used to test a measuring instrument, in place of
a real patient. In hospitals a physical phantom is a plastic or gel object of
known size that is scanned to check a scanner is measuring correctly. A
**digital phantom** is the same idea in software: an image generated by code,
containing shapes whose true size is known exactly, used to test an analysis
pipeline. *Everyday version:* the 1 kg calibration weight you put on a scale to
check the scale, rather than weighing a person and hoping. StableSeg generates
its own digital phantoms (`stableseg phantom`) for three reasons: the tests run
anywhere in seconds with no download; the true volume is known, so the pipeline
can be checked against an answer key that real scans never have; and the same
seed reproduces them identically on any machine. **They are synthetic, they are
not scans of anyone, and every document says so.** Built by
`src/stableseg/phantom.py`; explained step by step in
[phase 1, section 5](04-phase-tutorials/phase-01-skeleton.md).

**Perturbation.** A deliberate, controlled change to a scan that imitates a
real cause of scan-to-scan difference: noise, blur, a movement artefact, a
different slice thickness. The scan changes; the patient did not. The heart of
this project.

**Preprocessing.** Everything done to a scan before analysis: fixing
orientation, resampling to a common voxel size, normalising brightness,
sometimes denoising. *Everyday version:* squaring up and cropping a scanned
document before reading it.

**QIBA (Quantitative Imaging Biomarkers Alliance).** The group that publishes
the standard vocabulary for imaging-measurement quality — repeatability
coefficient, within-subject coefficient of variation, and so on. This project
uses their terms rather than inventing its own.

**Registration.** Aligning two scans of the same anatomy so they sit in the
same position. **Rigid** registration allows only rotation and shifting;
**deformable** allows stretching. *Everyday version:* laying two tracing-paper
copies of the same map on top of each other until they line up.

**Repeatability.** How close repeated measurements of the same unchanged thing
are to each other, with everything kept as constant as possible. Contrast with
**reproducibility**, which is the same question when something deliberately
differs (a different scanner, a different operator).

**Repeatability coefficient (RC).** A single number, in the units of your
measurement, such that the difference between two repeat measurements will be
smaller than it about 95 % of the time. *Everyday version:* "two weigh-ins of
the same person will agree within 1.4 kg."

**Resampling.** Recomputing a scan onto a different grid of voxels, for
example from 1.5 mm slices to 1 mm. Always involves interpolation, so always
loses or invents a little detail.

**Segmentation.** Drawing the outline of a structure on every slice of a scan,
usually by computer. The output is a mask. *Everyday version:* tracing one
country on every page of an atlas so you can measure its area.

**Sphericity.** A shape number saying how close a 3-D object is to a perfect
ball. Useful because a mask can have the right volume and still be the wrong
shape.

**Surface distance (normalised).** How far apart two outlines are along their
boundaries, on average. Complements Dice: two masks can overlap well and still
have a boundary error that matters clinically.

**Test–retest.** Scanning the same person twice with nothing changed in
between, to see how much the measurement moves. Rare in public data, which is
why StableSeg *simulates* it with perturbations — and says so in every report.

**Synthetic data.** Data created by a program rather than measured from the
world. Used here because no public dataset offers what the tests need, and
because a generated case can have a known true answer. Companies use it for
privacy, for rare events, and where no real data exists. Legitimate when
disclosed; dishonest when passed off as real. StableSeg labels it `synthetic:
true` inside the files themselves and states it in every document.

**Voxel.** A three-dimensional pixel: one small box in a scan. Multiply its
three side lengths to get its volume in cubic millimetres. Count the voxels in
a mask, multiply by that, and you have the biomarker.

**wCV (within-subject coefficient of variation).** The measurement noise
expressed as a percentage of the measurement itself. *Everyday version:*
"repeat weigh-ins of the same person vary by about 1.5 % of their weight."
Convenient because a percentage is comparable across structures of different
sizes.

**U-Net.** A particular design of neural network, shaped like the letter U,
that has been the standard architecture for medical image segmentation since
2015. A **3D U-Net** works on whole volumes rather than single slices.

---

## Part 2 — The machinery: software, tools, workflow

**API.** The set of functions one piece of software offers to another. *Everyday version:* the serving hatch between a
kitchen and a dining room — a defined opening through which things pass, so
neither side needs to know how the other is arranged. In this project,
`src/stableseg/api.py`.

**Argument / option (command line).** Extra information given to a command. An
argument is required and positional (`stableseg describe FILE`); an option is
named and usually optional (`--config configs/phantom.yaml`).

**Artefact (software).** A saved output file: a table, a chart, a trained
model. Computed slowly once, reused instantly many times. (Not to be confused
with an imaging **artefact**, which is a distortion in a scan. Both words
appear in this project; context separates them.)

**Backend.** The code doing the real work behind the scenes. *Everyday
version:* a restaurant kitchen. Customers never see it, only its results.

**Branch (Git).** A parallel line of snapshots. This project uses three:
`master` (released), `beta` (pre-release mirror), `develop` (all work).

**CI (continuous integration).** A service that automatically installs and
tests your project on fresh machines every time you push. *Everyday version:*
a colleague who silently rebuilds your work from scratch on three different
computers after every change and tells you if it broke. Ours is GitHub
Actions.

**CLI (command-line interface).** A program driven by typed commands rather
than clicks. `stableseg phantom` is one.

**Commit.** A saved snapshot of the whole project in Git, with a message
saying what changed. *Everyday version:* pressing save in a game, with a note.

**Config (configuration file).** A file holding the settings for a run, rather
than typing them each time. Ours are YAML files in `configs/`. *Everyday
version:* a recipe card, so the same dish can be made again identically.

**Dependency.** A library your project needs in order to run. Listed in
`pyproject.toml`; pinned to exact versions in `requirements.lock`.

**DuckDB.** A database that lives in a single file on your disk with no server
to run. Used from phase 4 to hold every measurement. *Everyday version:* a
filing cabinet you can question precisely, rather than a pile of loose
spreadsheets.

**Database.** Organised storage arranged in tables, questioned with a language
called SQL. *Everyday version:* a well-labelled pantry versus bags on the
floor.

**Editable install (`pip install -e`).** Installing your own project so that
Python can find it from anywhere, while still pointing at your working folder,
so edits take effect immediately without reinstalling.

**Environment variable.** A setting that lives in your shell rather than in a
file, often used for secrets. `.env.example` shows which ones this project
might use; `.env` (never committed) would hold real values.

**Fixture (testing).** A ready-made object or folder that tests share, so each
test starts from a known state. Ours are in `tests/conftest.py`.

**Frontend.** The part a person looks at and clicks. *Everyday version:* the
restaurant dining room. Ours will be a Streamlit page.

**Git.** A save-game system for a folder of code: snapshots, branches, and the
ability to return to any earlier state.

**GitHub.** A website that stores Git snapshots online, so they survive your
laptop and other people can read them.

**JSON.** A plain-text way of writing structured data: names and values in
braces. Every StableSeg command prints JSON so that both humans and other
programs can read the output.

**Lock file.** A list of every dependency at one exact version, produced from a
working install (`requirements.lock`). *Everyday version:* not "buy flour" but
"buy this brand, this bag, this batch", so the recipe comes out the same.

**Linter.** A tool that reads your code and points out mistakes and
inconsistencies without running it. Ours is `ruff`. *Everyday version:* a
spell-checker for code.

**`.nii.gz`.** A NIfTI file that has been compressed. `.nii` is the scan, `.gz`
means it was squeezed smaller with a program called gzip (the same compression
as a `.zip`, different container). Analysis tools read `.nii.gz` directly
without you unzipping anything. *Everyday version:* a vacuum-packed bag — same
contents, less shelf space, opened automatically by whatever needs it.

**`phantom_000.nii.gz` (reading a StableSeg filename).** `phantom` says it came
from the generator rather than a real scanner; `000` is the case number,
zero-padded so that case 2 sorts before case 10 rather than after it;
`.nii.gz` is the compressed 3-D image format. The file at
`data/phantom/images/phantom_000.nii.gz` is the *picture* of case 0, and
`data/phantom/labels/phantom_000.nii.gz` is the matching *outline* — same case,
same size, same grid, one file saying how bright each voxel is and the other
saying which structure it belongs to. Pairing them by identical filename in two
folders is a convention this project borrows from public imaging datasets.

**Manifest.** A plain table listing every case in a dataset with its key facts.
Ours is `data/phantom/manifest.csv`, one row per phantom with its known true
volumes. *Everyday version:* the packing list in a shipping crate.

**Package (Python).** A folder of code that Python can import by name once
installed. Ours is `stableseg`, living under `src/`.

**pathlib.** Python's modern way of handling file paths, which works
identically on Windows, macOS and Linux. Using it everywhere is why this
project runs unchanged on all three.

**pip.** The tool that installs Python libraries.

**Provenance.** The record of what produced a result: which version of the
code, which settings, when. Every StableSeg run writes `run.json`. *Everyday
version:* the label on a lab sample saying who took it, when, and how.

**Prompt (terminal).** The text the terminal shows before you type, indicating
where you are. When it starts with `(.venv)`, the project's private toolbox is
active.

**pydantic.** A library that checks structured settings against declared types
and rules, refusing bad input with a clear message. *Everyday version:* a form
with typed boxes that will not submit if you write "eight" where a number
belongs.

**pytest.** The tool that runs the automated tests.

**Quarto.** A tool that combines text, code and the code's output into one
polished document that regenerates itself when the data change. *Everyday
version:* a lab notebook that re-runs its own calculations.

**Reproducibility.** The property that running the same code on the same
inputs gives the same outputs, on any machine, at any time. Achieved here with
fixed random seeds, pinned dependencies and one-way data flow.

**Repository (repo).** The project folder, together with its Git history.

**Seed (random).** A starting number for a random-number generator. The same
seed produces the same sequence, which is what makes "random" data
reproducible. This project passes seeds explicitly everywhere and never relies
on a global one.

**Shell.** The program interpreting your typed commands. PowerShell on
Windows, `zsh` or `bash` on macOS, `bash` on Linux.

**SQL.** The language for asking a database questions. *Everyday version:* a
very literal, very patient librarian.

**src layout.** Putting the code one folder down, in `src/`, so Python cannot
import it accidentally from the project root and tests are forced to use the
properly installed version. Prevents a whole class of "works on my machine"
failures.

**Storage abstraction.** A small interface all output goes through, so that
changing where results live (local folder now, cloud bucket later) means
writing one new class instead of editing the whole project.

**Streamlit.** A tool that turns a Python script into an interactive web page
without writing any web code.

**Terminal.** The window where you type commands. Not the same thing as the
shell running inside it, but in practice people use the words
interchangeably.

**Test (unit test).** A small automated check proving one piece of code does
what it claims. *Everyday version:* weighing a known 1 kg reference before
trusting the scale.

**Version (semantic).** Three numbers, `MAJOR.MINOR.PATCH`. A new PATCH fixes
things, a new MINOR adds capability, a new MAJOR breaks compatibility.
StableSeg is at 0.1.0: early, capability being added, interfaces may still
change.

**Virtual environment (`venv`).** A private toolbox for one project: its own
copies of libraries, isolated from the system and from other projects.
*Everyday version:* a separate toolbox per job, so the plumbing tools do not
end up mixed into the electrical kit.

**YAML.** A plain-text format for settings, using indentation instead of
brackets. Our config files are YAML.

---

*Missing a word? Open an issue titled "glossary: <word>". A term used but not
defined is a defect in the documentation, not a gap in the reader.*
