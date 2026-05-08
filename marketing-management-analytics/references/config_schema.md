# Marketing Management Analytics Config Schema

Use a JSON config when automatic inference is not enough. All fields are optional.

## Top-Level Fields

```json
{
  "rename": {},
  "metadata": {},
  "constructs": {},
  "reverse_items": [],
  "id_columns": [],
  "outcome": "purchase_intention",
  "predictors": [],
  "mediators": [],
  "moderators": [],
  "controls": [],
  "conjoint": {},
  "psm": {},
  "segment_k": 4,
  "segment_names": {},
  "cluster_features": [],
  "randomness_variables": [],
  "independence_pairs": [],
  "purchase_question_variables": [],
  "persona_basic_variables": [],
  "persona_behavior_variables": [],
  "persona_cognitive_variables": []
}
```

## Field Meanings

- `rename`: map original column/question text to clean variable names.
- `metadata`: report metadata, such as data source, survey time, raw sample, valid sample, product name, category name, and client/project context.
- `constructs`: map construct names to item variable names. Items may refer to either original names or renamed variables.
- `reverse_items`: item variable names that should be reverse-coded before construct scoring.
- `id_columns`: respondent, task, or record identifiers to exclude from scale detection.
- `outcome`: dependent variable, usually purchase intention.
- `predictors`: product, brand, price, packaging, feature, campaign, or experience variables used to explain purchase intention.
- `mediators`: variables that explain why a product variable affects purchase intention, such as perceived value, satisfaction, trust, risk, or attitude.
- `moderators`: variables that change the strength or direction of a product-to-purchase-intention relationship, such as income, age, involvement, category familiarity, or segment.
- `controls`: optional covariates to include in future manual follow-up. The bundled script stores them but keeps the main automated models focused.
- `conjoint`: conjoint/CDC/CBC settings.
- `psm`: PSM price sensitivity settings for the four price questions.
- `segment_k`: preferred number of consumer segments. Use `3` or `4` for formal persona reports; the script defaults toward 4 or 3 when feasible.
- `segment_names`: optional names for final segments, keyed by segment number, such as `{ "1": "权威信赖者", "2": "创新采纳者", "3": "保守疏离者" }`.
- `cluster_features`: variables to use for clustering and persona profiles.
- `randomness_variables`: variables to run balance/uniformity checks on, especially randomized conjoint attributes or randomized stimuli.
- `independence_pairs`: explicit variable pairs for independence testing. Categorical pairs use chi-square; numeric pairs use a correlation independence screen.
- `purchase_question_variables`: every purchase behavior, purchase intention, purchase tendency, preference, or purchase choice question that must receive pie/bar chart analysis. For multi-select questions stored as binary option columns, list any or all related option variables; the analyzer will group all columns with the same question stem into one chart.
- `persona_basic_variables`: demographic and background fields for persona profiles, such as age, gender, income, education, city tier, occupation, or household.
- `persona_behavior_variables`: behavioral fields for persona profiles, such as purchase frequency, usage frequency, channel, monthly spend, scene, membership, promotion response, or media touchpoints.
- `persona_cognitive_variables`: cognitive and attitudinal fields for persona profiles, such as awareness, perceived quality, perceived value, brand trust, satisfaction, risk, attitude, involvement, and purchase intention.

## Conjoint Config

Choice-based long format:

```json
{
  "conjoint": {
    "format": "choice_long",
    "respondent": "respondent_id",
    "task": "task_id",
    "alternative": "alternative_id",
    "chosen": "chosen",
    "attributes": ["brand", "price", "package", "feature"]
  }
}
```

Rating-based conjoint:

```json
{
  "conjoint": {
    "format": "rating",
    "rating": "profile_rating",
    "attributes": ["brand", "price", "package", "feature"]
  }
}
```

## PSM Config

Use this when the questionnaire includes Van Westendorp/PSM price questions:

```json
{
  "psm": {
    "too_cheap": "太便宜，以至于怀疑质量的价格",
    "cheap": "便宜但可以接受的价格",
    "expensive": "贵但仍可接受的价格",
    "too_expensive": "太贵，不会购买的价格"
  }
}
```

The script checks the monotonic rule `too_cheap < cheap < expensive < too_expensive`, then estimates OPP, IPP, lower acceptable price, and upper acceptable price.

When segmentation is generated, the script also estimates PSM by segment and writes `psm_segment_summary.csv`, `psm_segment_curves.csv`, and `psm_segment_monotonicity.csv`. The main report treats curve-intersection OPP as the optimal price point and reports the acceptable price range from PMC to PME.

## Report Metadata

```json
{
  "metadata": {
    "data_source": "见数",
    "survey_time": "2026年4月",
    "raw_sample": 205,
    "valid_sample": 196,
    "product_name": "昭膳堂天麻核桃乳",
    "category_name": "植物蛋白饮品"
  }
}
```

## Practical Guidance

- Prefer 2-3 item constructs when reliability is acceptable and the items represent the same theoretical idea.
- Keep purchase intention as a construct if it has multiple reliable items.
- Add reverse-coded items explicitly. The script cannot safely infer reverse wording in every Chinese survey.
- Use the same variable names in `constructs`, `predictors`, `mediators`, and `moderators` after applying `rename`.
- For CDC/CBC data, provide `attributes`; automatic detection is intentionally conservative.
- For PSM data, provide all four price columns if the auto-detected names are unclear.
- Add all purchase-related questions to `purchase_question_variables` when the wording is unusual; the script otherwise auto-detects by variable names and original question text. Multi-select option columns sharing the same question stem are combined into one chart.
- Ranking-style brand perception columns such as `health_rank_*`, `function_rank_*`, and `daily_rank_*` are merged into ranking mean charts and `ranking_summary.csv`.
- Use persona variable lists when the report must separate basic information, behavior information, and cognitive information in a client-facing consumer portrait.
- Set `segment_k` to `3` or `4` when the final report must present exactly three or four consumer types. The output always includes `consumer_persona_summary.csv` and a persona table in `final_research_report.md`.
- Use `segment_names` after a first run when the automatically generated names need to match the research story or competition-report naming.
- Fill `metadata` when the final report needs formal wording about data source, survey period, raw sample, valid sample, product name, and category.
