#!/usr/bin/env Rscript
#
# verify_setup.R - prove the R toolchain works, before anything depends on it.
#
# WHY THIS SCRIPT EXISTS
#
# The statistics phase of this project uses R for one specific job: computing
# the agreement statistics a second time, independently, with the established
# R packages, and checking that the two implementations agree. Two unrelated
# implementations arriving at the same number is a far stronger check on a
# formula than one careful implementation.
#
# But there is no point discovering that R will not install on your machine
# at the moment you need it for real work. So this script arrives early. It
# does nothing scientific. It reads the phantom manifest that the Python side
# produced, prints a summary, and recomputes one number that the Python side
# also computed - so if the two disagree, something is wrong with the
# toolchain rather than with the science.
#
# The everyday version: before relying on a second pair of scales to check the
# first, you put a known weight on it. That is all this is.
#
# DELIBERATELY USES BASE R ONLY
#
# No packages are installed and none are required. A first-run script that
# needs a package download is a first-run script that fails behind a corporate
# proxy, on a locked-down machine, or on a bad connection. Package management
# (with renv) arrives in the statistics phase, when there is a real reason for
# it.
#
# HOW TO RUN
#   From the project root, in a terminal:
#       Rscript R/verify_setup.R
#   Or open the project in RStudio and press the "Source" button.
#
# EXPECTED: a summary table, then "R toolchain verified." and exit code 0.

# ---------------------------------------------------------------------------
# 0. Where are we? The script must work whether it is run from the project
#    root, from inside R/, or from RStudio with a different working directory.
# ---------------------------------------------------------------------------

find_project_root <- function() {
  # Walk upward from the working directory looking for a file that only the
  # project root has. `normalizePath` makes the comparison reliable on
  # Windows, macOS and Linux alike.
  here <- normalizePath(getwd(), winslash = "/", mustWork = TRUE)
  for (i in 1:5) {
    if (file.exists(file.path(here, "pyproject.toml"))) {
      return(here)
    }
    parent <- dirname(here)
    if (parent == here) break # reached the filesystem root
    here <- parent
  }
  stop(
    "Could not find the project root (looked for pyproject.toml).\n",
    "  Run this from the project folder: Rscript R/verify_setup.R"
  )
}

root <- find_project_root()
manifest_path <- file.path(root, "data", "phantom", "manifest.csv")

cat("StableSeg - R toolchain check\n")
cat(strrep("-", 60), "\n", sep = "")
cat("R version   :", R.version.string, "\n")
cat("Platform    :", R.version$platform, "\n")
cat("Project root:", root, "\n\n")

# ---------------------------------------------------------------------------
# 1. Is the data there? If not, say exactly how to make it rather than
#    failing with a file-not-found message the reader has to interpret.
# ---------------------------------------------------------------------------

if (!file.exists(manifest_path)) {
  cat("The phantom manifest is missing:\n  ", manifest_path, "\n\n", sep = "")
  cat("Generate it first, from the project root with the Python environment\n")
  cat("active:\n\n    stableseg phantom\n\n")
  quit(status = 1)
}

# ---------------------------------------------------------------------------
# 2. Read it. read.csv is base R: no packages, works everywhere.
# ---------------------------------------------------------------------------

manifest <- read.csv(manifest_path, stringsAsFactors = FALSE)

cat("Manifest read:", nrow(manifest), "cases,", ncol(manifest), "columns\n\n")

expected_columns <- c(
  "case_id",
  "true_volume_label1_mm3",
  "true_volume_label2_mm3",
  "true_volume_total_mm3",
  "synthetic",
  "seed"
)
missing <- setdiff(expected_columns, names(manifest))
if (length(missing) > 0) {
  cat("Unexpected manifest format. Missing column(s):\n")
  cat("  ", paste(missing, collapse = ", "), "\n", sep = "")
  quit(status = 1)
}

# ---------------------------------------------------------------------------
# 3. Summarise. This is the kind of thing R is good at, and is a preview of
#    what the statistics phase will do properly.
# ---------------------------------------------------------------------------

cat("Total structure volume per case (cubic millimetres):\n")
print(summary(manifest$true_volume_total_mm3))
cat("\n")

cat("Spread across cases:\n")
cat(sprintf(
  "  mean = %.2f   sd = %.2f   coefficient of variation = %.1f%%\n\n",
  mean(manifest$true_volume_total_mm3),
  sd(manifest$true_volume_total_mm3),
  100 * sd(manifest$true_volume_total_mm3) / mean(manifest$true_volume_total_mm3)
))
# The coefficient of variation is the spread expressed as a percentage of the
# average. It appears here because the same idea, applied to REPEATED
# measurements of the SAME case rather than across different cases, is the
# within-subject coefficient of variation - one of the statistics this project
# ultimately reports. This is a preview, not that statistic.

cat("Are the two label volumes related across cases?\n")
cat(sprintf(
  "  Pearson correlation (label 1 vs label 2) = %.4f\n\n",
  cor(manifest$true_volume_label1_mm3, manifest$true_volume_label2_mm3)
))
# Expect a strong positive value: each phantom is generated at a single random
# size, so both parts grow and shrink together. A weak value would mean the
# generator is not doing what it claims.

# ---------------------------------------------------------------------------
# 4. The actual cross-check: recompute a number the Python side also computed.
#    `stableseg phantom` prints mean_true_volume_mm3. With the default settings
#    that value is 2269.75, identically on every machine, because the generator
#    is seeded. If R computes the same mean from the saved file, then the file
#    was written correctly, read correctly, and both languages agree on the
#    arithmetic.
# ---------------------------------------------------------------------------

mean_total <- mean(manifest$true_volume_total_mm3)
cat("Cross-check against the Python side:\n")
cat(sprintf("  mean total volume computed in R: %.2f mm3\n", mean_total))

default_run <- nrow(manifest) == 8 && all(manifest$seed == 42)
if (default_run) {
  expected <- 2269.75
  cat(sprintf("  value published by the Python tool: %.2f mm3\n", expected))
  if (abs(mean_total - expected) < 1e-6) {
    cat("  -> match\n\n")
  } else {
    cat("  -> MISMATCH. Investigate before relying on either side.\n\n")
    quit(status = 1)
  }
} else {
  cat("  (skipped: this manifest is not the default 8-case, seed-42 set,\n")
  cat("   so there is no published value to compare against)\n\n")
}

# ---------------------------------------------------------------------------
# 5. Honest disclosure, in the output itself and not only in a document.
# ---------------------------------------------------------------------------

if (all(manifest$synthetic %in% c(TRUE, "True", "true"))) {
  cat("Note: this data is SYNTHETIC - generated by code, not scanned from\n")
  cat("anyone. It exists so the pipeline can be checked against a known\n")
  cat("true answer, which real scans never have.\n\n")
}

cat(strrep("-", 60), "\n", sep = "")
cat("R toolchain verified.\n")
quit(status = 0)
