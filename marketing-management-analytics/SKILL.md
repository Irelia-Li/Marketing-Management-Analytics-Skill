---
name: marketing-management-analytics
description: Automatically clean and analyze marketing management survey, product research, consumer behavior, and conjoint/CDC/CBC datasets from CSV or Excel. Use when the user asks to rename survey questions into variable names, clean questionnaire data, merge reliable 2-3 item scales into constructs, analyze the relationship between product variables and purchase intention, run descriptive statistics, randomness tests, independence tests, regression analysis, mediation effects, moderation effects, conjoint/CDC/CBC analysis, clustering, purchase-related question charts, or consumer persona profiling with basic, behavioral, and cognitive information.
---

# Marketing Management Analytics

## Workflow

Use this skill for marketing survey or product research data, especially when column headers are questionnaire items rather than usable variable names.

1. Preserve the raw file. Never overwrite the user's source data.
2. Inspect the codebook, column names, scales, missing values, and respondent identifiers.
3. Rename every question column into an analysis-ready variable name. Save a `variable_map.csv` mapping original question text to the generated variable.
4. Clean values: trim text, standardize missing tokens, convert Likert labels to numeric scores, reverse-code configured reverse items, and keep categorical columns as categories.
5. Merge constructs only when the items are conceptually related and empirically reliable. Prefer 2-3 item means with Cronbach alpha >= 0.70, or alpha >= 0.60 for exploratory work; report the items and reliability either way.
6. Identify purchase intention as the default outcome. If ambiguous, ask for the outcome or use a config file.
7. Generate per-question pie/bar chart analysis for purchase behavior, purchase intention, purchase tendency, preference, and purchase choice variables. When a multi-select question is stored as one binary column per option, merge all options under the same question stem into one pie/bar chart instead of charting each option separately.
8. Run randomness tests and independence tests where the data structure supports them.
9. Analyze product-to-purchase-intention relationships with descriptive statistics, correlations, regression, mediation, moderation, conjoint/CDC/CBC if present, clustering, and consumer personas.
10. Deliver a concise Chinese audit report plus a polished research-report-style `final_research_report.md` with numbered sections, table/chart references, result interpretation, and strategy implications.

## Quick Start

Run the bundled script when the user provides a `.csv`, `.xlsx`, or `.xls` survey dataset:

```powershell
& "C:\Users\xinyi.li01\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" `
  "C:\Users\xinyi.li01\.codex\skills\marketing-management-analytics\scripts\auto_marketing_analysis.py" `
  --input "path\to\survey.xlsx" `
  --output "path\to\analysis_output"
```

Use `--sheet "Sheet1"` for a specific Excel sheet. Use `--config config.json` when the user provides known variable names, constructs, reverse-coded items, mediators, moderators, or conjoint attributes.

## Script Outputs

The script writes these files when relevant:

- `cleaned_data.csv`: cleaned respondent-level data with generated variables.
- `variable_map.csv`: original question text to variable name mapping.
- `construct_summary.csv`: merged constructs, included items, Cronbach alpha, and reliability label.
- `construct_scores.csv`: respondent-level construct scores.
- `descriptives.csv` and `correlations.csv`: descriptive statistics and correlations.
- `purchase_question_distributions.csv` and `purchase_question_charts.html`: frequency/percentage tables plus pie and bar charts for every purchase behavior, intention, tendency, preference, or choice question detected. Multi-select option columns are grouped by shared question stem; pie percentages use each option's share of total selected mentions, while the table also keeps respondent-level selection rates.
- `charts/`: PNG chart assets, including merged multi-select pie/bar charts and merged ranking bar charts suitable for insertion into formal reports.
- `ranking_summary.csv`: merged brand/product ranking means for dimensions such as health cognition, functional cognition, and daily drinking fit when ranking-style columns are detected.
- `randomness_tests.csv`: sequence runs tests and configured/conjoint attribute balance checks.
- `independence_tests.csv`: chi-square independence tests for categorical variables and Pearson-style independence screens for numeric variables.
- `categorical_distributions.csv`: frequency tables for categorical and low-cardinality variables.
- `regression_coefficients.csv`: standardized regression of purchase intention on product/construct predictors.
- `mediation.csv` and `moderation.csv`: effect tests with approximate p-values and bootstrap intervals for mediation.
- `conjoint_utilities.csv` and `conjoint_importance.csv`: part-worth utilities and attribute importance for CDC/CBC/conjoint data when detectable.
- `psm_monotonicity.csv`, `psm_summary.csv`, and `psm_curves.csv`: PSM price monotonicity checks and price sensitivity estimates when four PSM price questions are detected.
- `psm_segment_summary.csv`, `psm_segment_curves.csv`, and `psm_segment_monotonicity.csv`: segment-level PSM results after clustering, including curve-based OPP, IPP, PMC, and PME for each consumer type when sample size allows.
- `segment_assignments.csv`, `segment_profiles.csv`, `consumer_persona_summary.csv`, `persona_profile_details.csv`, and `personas.md`: clustering results, the required consumer persona summary table, and detailed persona evidence.
- `analysis_report.md`: Chinese executive report.
- `final_research_report.md`: polished market research report modeled after formal competition/consulting report writing, with sections such as data collection, quality checks, descriptive charts, market analysis, consumer identification, conjoint/PSM, and strategy recommendations.
- `analysis_workbook.xlsx`: Excel workbook collecting the main tables.

## Config

Read `references/config_schema.md` when a run needs explicit mappings or more control. Prefer a config file for real client work because it prevents false construct merges and clarifies which variables are product predictors, mediators, moderators, purchase intention, and conjoint attributes.

Read `references/report_style.md` when writing or revising the final report. Use it to make the output resemble a formal competition/consulting market research report with numbered sections, figure/table references, interpretation paragraphs, and strategy implications.

Minimal config example:

```json
{
  "rename": {
    "我认为这个产品质量很好": "product_quality_1",
    "我愿意购买这个产品": "purchase_intention_1"
  },
  "constructs": {
    "product_quality": ["product_quality_1", "product_quality_2", "product_quality_3"],
    "purchase_intention": ["purchase_intention_1", "purchase_intention_2"]
  },
  "reverse_items": ["risk_reverse_1"],
  "outcome": "purchase_intention",
  "predictors": ["product_quality", "price_value", "brand_trust"],
  "mediators": ["perceived_value", "satisfaction"],
  "moderators": ["income", "age", "involvement"],
  "metadata": {
    "data_source": "见数/问卷星/用户提供数据源",
    "survey_time": "2026年4月",
    "raw_sample": 205,
    "valid_sample": 196,
    "product_name": "目标产品",
    "category_name": "目标品类"
  },
  "randomness_variables": ["brand", "price", "feature"],
  "independence_pairs": [["gender", "purchase_channel"], ["income", "purchase_intention"]],
  "purchase_question_variables": ["purchase_frequency", "purchase_channel", "purchase_intention_1"],
  "segment_k": 4,
  "segment_names": {"1": "权威信赖者", "2": "创新采纳者", "3": "保守疏离者"},
  "persona_basic_variables": ["age", "gender", "income", "city_tier"],
  "persona_behavior_variables": ["purchase_frequency", "purchase_channel", "monthly_spend"],
  "persona_cognitive_variables": ["brand_awareness", "product_quality", "price_value", "purchase_intention"],
  "conjoint": {
    "format": "choice_long",
    "chosen": "chosen",
    "attributes": ["brand", "price", "package", "feature"]
  },
  "psm": {
    "too_cheap": "psm_too_cheap",
    "cheap": "psm_cheap",
    "expensive": "psm_expensive",
    "too_expensive": "psm_too_expensive"
  }
}
```

## Analysis Rules

- Treat automated construct merging as a proposal, not final theory. In the report, name which items were merged and flag exploratory constructs.
- Do not average unrelated questions just because correlations are high; prefer semantic item groups first, then correlation-based auto groups only when no codebook exists.
- For mediation, test only plausible paths: product/attribute predictor -> mediator such as perceived value, trust, satisfaction, risk, or attitude -> purchase intention.
- For moderation, center numeric variables before interactions and explain the interaction direction in plain language.
- For CDC/CBC choice data, prefer long format with one row per alternative, a `chosen` 0/1 column, task/respondent identifiers if available, and attribute columns.
- For purchase behavior/intention/tendency/choice questions, include a distribution table and both pie and bar views for every detected question. For multi-select questions split across binary option columns, chart the whole question once by aggregating all selected options. If auto-detection misses a question, add it to `purchase_question_variables`.
- For randomness tests, interpret p < 0.05 as a signal to inspect sequence/order or random assignment balance; do not claim a sampling flaw without checking fieldwork design.
- For independence tests, use chi-square results for categorical variables and correlation screens for numeric variables; treat p-values as screening evidence, not full causal proof.
- For personas, default to a three-class or four-class segmentation result when the sample and cluster sizes allow it; use `segment_k` when the user wants exactly 3 or exactly 4 groups. Always include a consumer persona summary table and a final overall result naming the three/four consumer types. Also report three layers when available: basic information, behavior information, and cognitive information. Avoid overstating causality; describe personas as data-driven segments.
- Use `segment_names` after the first pass when the data-driven segments need report-ready labels such as "权威信赖者", "创新采纳者", or "保守疏离者".
- Structure the final report like a formal market research deliverable: data collection and preprocessing, data quality tests, variable construction, descriptive statistics with chart references, market analysis, mediation/moderation, consumer identification, CDC/CBC or PSM product optimization, and strategy implications. When both clustering and PSM are available, report PSM price points by consumer segment; use curve-intersection OPP as the main optimal price point and report the acceptable range from PMC to PME.
- Use numbered tables and figures in the prose. Link to generated CSV/HTML chart files when the report is Markdown rather than a rendered document.
- If model assumptions are weak, sample size is small, or no valid conjoint structure is detected, say so directly and still provide the reliable outputs.
