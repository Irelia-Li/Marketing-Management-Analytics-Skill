---
name: marketing-management-analytics
description: Clean marketing survey data and generate purchase-intention models, CBC/PSM analysis, clusters, personas, charts, and research reports.
dependencies: python>=3.10, pandas, numpy, scipy, statsmodels, scikit-learn, matplotlib, openpyxl, python-docx
---

# Marketing Management Analytics

Use this skill when the user provides marketing management survey data, product research data, consumer behavior questionnaires, PSM price questions, or CDC/CBC/conjoint experiment data and wants an automated analysis report.

The skill is designed for raw CSV or Excel exports where many columns are full questionnaire texts rather than clean variable names.

## Primary Workflow

1. Preserve the raw input file. Never overwrite the user's source data.
2. Inspect the workbook or CSV structure, sheet names, column names, missing values, scale labels, and respondent identifiers.
3. Convert long questionnaire item headers into analysis-ready variable names and save a `variable_map.csv`.
4. Clean response values:
   - Trim text values.
   - Standardize missing tokens.
   - Convert Likert labels and numeric-looking strings into numeric scores where appropriate.
   - Keep categorical variables as categories.
   - Reverse-code configured reverse items.
5. Merge 2-3 related items into constructs only when they are conceptually coherent and empirically acceptable.
6. Identify purchase intention as the default outcome. If ambiguous, ask the user or use the provided config.
7. Generate distribution tables and charts for categorical variables and purchase-related questions.
8. For multi-select questions stored as one binary column per option, merge all options into one combined chart for the original question stem.
9. Run descriptive statistics, randomness tests, independence tests, correlations, regression, mediation, moderation, clustering, PSM, and CDC/CBC/conjoint analysis when the dataset supports them.
10. Produce a research-report-style output with numbered sections, figure/table references, interpretation paragraphs, and strategy implications.

## Running The Analysis Script

Use the bundled script for CSV, XLSX, or XLS survey files:

```bash
python scripts/auto_marketing_analysis.py \
  --input "/path/to/survey.xlsx" \
  --output "/path/to/analysis_output"
```

For a specific Excel sheet:

```bash
python scripts/auto_marketing_analysis.py \
  --input "/path/to/survey.xlsx" \
  --sheet "Sheet1" \
  --output "/path/to/analysis_output"
```

For formal client work, prefer a config file:

```bash
python scripts/auto_marketing_analysis.py \
  --input "/path/to/survey.xlsx" \
  --output "/path/to/analysis_output" \
  --config "/path/to/config.json"
```

Read `references/config_schema.md` when the user provides known variable names, constructs, reverse-coded items, mediators, moderators, PSM variables, persona variables, or conjoint attributes.

Read `references/report_style.md` when revising the final report into a formal competition, consulting, or market research writing style.

## Expected Outputs

When relevant, the script writes:

- `cleaned_data.csv`
- `variable_map.csv`
- `construct_summary.csv`
- `construct_scores.csv`
- `descriptives.csv`
- `categorical_distributions.csv`
- `purchase_question_distributions.csv`
- `purchase_question_charts.html`
- `ranking_summary.csv`
- `randomness_tests.csv`
- `independence_tests.csv`
- `correlations.csv`
- `regression_coefficients.csv`
- `mediation.csv`
- `moderation.csv`
- `conjoint_utilities.csv`
- `conjoint_importance.csv`
- `psm_summary.csv`
- `psm_curves.csv`
- `psm_segment_summary.csv`
- `psm_segment_curves.csv`
- `segment_assignments.csv`
- `segment_profiles.csv`
- `consumer_persona_summary.csv`
- `persona_profile_details.csv`
- `personas.md`
- `analysis_report.md`
- `final_research_report.md`
- `analysis_workbook.xlsx`

## Report Structure

Use this structure for final written reports unless the user requests another outline:

1. Data collection and preprocessing
2. Descriptive statistical analysis
3. Market analysis
4. Consumer identification
5. Strategy and product optimization

Each chart and table should be followed by a short interpretation paragraph. The paragraph should state the key result, explain its marketing meaning, and give a practical implication.

## Purchase-Related Chart Rules

For purchase behavior, purchase intention, purchase tendency, purchase preference, purchase choice, and non-purchase reason questions:

- Generate a frequency table.
- Generate a bar or pie chart when the variable is categorical.
- Do not create separate charts for each binary option of the same multi-select question.
- Instead, combine all options under the original question stem into one chart.
- Numeric-only scale items do not need individual charts unless they are central to a model or report finding.

## CDC/CBC/Conjoint Rules

Use CDC/CBC analysis only when the dataset has a valid structure.

Preferred choice-based long format:

- One row per alternative.
- A respondent identifier.
- A task or choice-set identifier.
- An alternative identifier.
- A `chosen` column coded 0/1.
- Attribute columns such as brand, price, feature, package, channel, certification, or ingredient.

If a valid choice structure is detected, estimate utilities and relative attribute importance. Use `conjoint_utilities.csv` and `conjoint_importance.csv` to explain product configuration trade-offs.

If no valid structure is detected, state that the dataset does not contain an estimable CDC/CBC/conjoint design. Do not invent utilities from ordinary survey questions.

## PSM Rules

Run PSM when the dataset includes four price questions:

- Too cheap
- Cheap
- Expensive
- Too expensive

Report:

- OPP: optimal price point
- IPP: indifference price point
- PMC: lower acceptable price
- PME: upper acceptable price

Use curve-intersection OPP as the main optimal price point. Report the acceptable price interval as PMC to PME. When segmentation is available, report PSM results by consumer segment.

## Randomness And Independence Tests

Run randomness tests when response sequence, random assignment, or conjoint/randomized attributes are present. Interpret `p < 0.05` as a signal to inspect fieldwork or assignment balance, not as automatic proof of invalid data.

Run independence tests for categorical variables using chi-square tests. Use correlation-style screens for numeric variables. Treat these as screening evidence, not causal proof.

## Consumer Personas

Default to three or four clusters when sample size and cluster stability allow. Use the user's requested number if specified.

Each persona summary should include:

- Basic information: age, gender, education, occupation, income, city, or region.
- Behavioral information: purchase target, content preference, information channel, brand choice, usage scenario, or non-purchase reason.
- Cognitive information: health involvement, functional trust, brand risk, origin story identity, product appeal, or purchase intention.
- Strategy positioning: target priority and recommended marketing action.

Always include a final persona summary table and name the consumer types in report-ready language.

## Interpretation Standards

- Do not average unrelated survey items just because they are correlated.
- Treat automated construct merging as a proposal that must be checked against questionnaire meaning.
- Explain regression, mediation, and moderation results in plain marketing language.
- Avoid causal claims unless the design supports causality.
- Clearly state weak assumptions, low reliability, small samples, or missing model structure.
- Preserve user data privacy and do not expose raw respondent-level data unless requested.

