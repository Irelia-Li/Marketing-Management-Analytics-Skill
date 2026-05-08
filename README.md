# Marketing Management Analytics Skill

An automated analytics workflow for marketing management research, consumer surveys, product testing, and choice-based product optimization.

This project turns raw questionnaire datasets into a structured research deliverable: cleaned data, analysis-ready variables, reliability-tested constructs, statistical models, segmentation results, charts, Excel appendices, and a Word-style market research report.

## What It Does

- Cleans raw CSV or Excel survey data while preserving the original source file.
- Renames long questionnaire items into analysis-ready variable names.
- Converts Likert-scale and categorical responses into usable analysis formats.
- Merges reliable 2-3 item survey scales into constructs using reliability checks.
- Runs descriptive statistics, randomness tests, and independence tests.
- Analyzes purchase intention, purchase behavior, purchase preference, and purchase choice questions.
- Automatically groups multi-select survey items into one combined chart per question.
- Estimates relationships between product perceptions and purchase intention through regression, mediation, and moderation models.
- Supports CDC/CBC/conjoint analysis when valid choice-experiment data is available.
- Runs PSM price sensitivity analysis, including segment-level OPP, IPP, PMC, and PME estimates.
- Performs consumer clustering and builds persona summaries with basic, behavioral, and cognitive information.
- Produces report-ready charts, tables, Excel workbooks, and Chinese market research reports.

## Core Analysis Modules

### Data Cleaning and Variable Mapping

The workflow standardizes messy questionnaire columns into compact variable names and saves a mapping table from original question text to generated variable names. This makes the dataset easier to audit, model, and reuse.

### Construct Reliability and Scale Merging

Conceptually related survey items can be merged into higher-level constructs when they show acceptable reliability. The output includes Cronbach's alpha, item counts, and reliability labels so the analyst can judge whether each construct is suitable for formal interpretation.

### Descriptive and Purchase-Related Charts

The tool generates frequency tables and visual summaries for categorical variables and purchase-related questions. For multi-select questions, all options under the same question stem are combined into one bar or pie chart instead of being treated as separate questions.

### Regression, Mediation, and Moderation

The workflow identifies key drivers of purchase intention and tests whether certain variables explain or change those relationships. This is useful for understanding how product perceptions, trust, risk, price concerns, and taste concerns shape consumer decisions.

### CDC/CBC Conjoint Analysis

When the dataset contains a valid choice-experiment structure, the skill estimates attribute-level utilities and relative attribute importance. It supports long-format choice data with fields such as respondent ID, task ID, alternative ID, chosen status, and product attributes.

### PSM Price Sensitivity

The PSM module estimates price thresholds using four standard price questions: too cheap, cheap, expensive, and too expensive. It reports:

- OPP: optimal price point
- IPP: indifference price point
- PMC: lower acceptable price
- PME: upper acceptable price

When clustering results are available, PSM is also calculated by consumer segment.

### Consumer Segmentation and Personas

The tool performs K-Means clustering and generates consumer persona tables. Each persona includes:

- Basic information, such as age, gender, income, occupation, and city
- Behavioral information, such as purchase target, content preference, and information channels
- Cognitive information, such as health involvement, functional trust, brand risk, and purchase intention
- Strategic positioning for marketing action

## Typical Inputs

- `.xlsx`, `.xls`, or `.csv` survey exports
- Questionnaire datasets with long question-text headers
- Optional configuration files for known constructs, outcomes, predictors, moderators, mediators, PSM variables, or conjoint attributes

## Typical Outputs

- `cleaned_data.csv`
- `variable_map.csv`
- `construct_summary.csv`
- `descriptives.csv`
- `categorical_distributions.csv`
- `purchase_question_distributions.csv`
- `randomness_tests.csv`
- `independence_tests.csv`
- `regression_coefficients.csv`
- `mediation.csv`
- `moderation.csv`
- `conjoint_utilities.csv`
- `conjoint_importance.csv`
- `psm_summary.csv`
- `psm_segment_summary.csv`
- `segment_profiles.csv`
- `consumer_persona_summary.csv`
- `analysis_workbook.xlsx`
- `final_research_report.md`
- A Word-style research report with charts, tables, and interpretation paragraphs

## Example Use Case

This workflow is designed for research questions such as:

- Which product attributes most strongly influence purchase intention?
- What are the main barriers to purchase?
- Which consumer segments should the brand prioritize?
- What is the optimal price range for the product?
- How do price concerns, taste concerns, or brand risk moderate purchase intention?
- Which product configuration is preferred in a CBC choice experiment?

## Example Command

```powershell
python auto_marketing_analysis.py `
  --input "survey_data.xlsx" `
  --output "analysis_output" `
  --config "config.json"
```

The configuration file is optional, but recommended for formal research projects because it clarifies construct definitions, purchase-intention outcomes, PSM variables, and conjoint attributes.

## Report Structure

The generated report follows a formal market research structure:

1. Data collection and preprocessing
2. Descriptive statistical analysis
3. Market analysis
4. Consumer identification
5. Strategy and product optimization

Each chart and table is paired with an interpretation paragraph so the final output reads like a complete research report rather than a raw statistical appendix.

## Notes

The workflow is designed to automate the heavy analytical work, but final research judgment still matters. Construct merging, mediation paths, moderation interpretation, and segment naming should be reviewed against the questionnaire design and business context before client-facing delivery.

