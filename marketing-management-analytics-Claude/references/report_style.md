# Formal Market Research Report Style

Use this style when producing the final deliverable, especially for competition, consulting, thesis, or client-facing market research reports.

## Structure

Prefer numbered sections with explanatory prose:

1. Data collection and preprocessing
   - Data source, survey period, raw sample, valid sample, valid rate.
   - Cleaning and quality control: time logic, missing values, straight-lining if available, randomness tests, independence tests, PSM monotonicity if present.
   - Variable construction: rename question text to variables, combine reliable multi-item constructs, report Cronbach alpha.
2. Descriptive statistics
   - Basic profile: gender, age, education, occupation, income, city/region.
   - Behavior profile: purchase frequency, channel, spend, usage scenario, media touchpoints.
   - Cognitive profile: awareness, trust, perceived quality/value/risk, satisfaction, purchase intention.
   - For multi-select questions, show one integrated pie/bar chart per question stem rather than separate charts for each option column.
   - Give a short interpretation after each key chart.
3. Market analysis
   - Product/brand perception, purchase behavior, purchase intention, preference or choice.
   - For ranking questions across brands/products, merge all brand columns in the same dimension into one ranking-mean bar chart.
   - Regression, mediation, and moderation where configured and theoretically plausible.
   - For moderation, explain interaction direction and recommend simple slope charts.
4. Consumer identification
   - K-Means or other segmentation method, feature selection, K choice, cluster validity.
   - Persona naming and explanation.
   - Include a persona summary table with all final segments. The final report should explicitly state the overall result, usually three or four consumer types, before describing each type.
   - Segment validation using purchase intention and demographic/behavioral/cognitive difference tests.
5. Strategy and product optimization
   - CDC/CBC conjoint: attribute importance, part-worth utilities, optimal configuration, market simulation if available.
   - PSM: monotonicity validation, curve-intersection OPP as the main optimal price, IPP, acceptable price range from PMC to PME, plus segment-level price points when personas or clusters are available.
   - Translate findings into target market, product, price, channel, and communication recommendations.

## Figure And Table Style

- Use `表` for statistical tables and `图` for charts.
- After each figure/table, write a conclusion paragraph in plain Chinese.
- Avoid listing outputs without interpretation. Explain what the result means for market opportunity, conversion barrier, target segment, or product strategy.
- When the output is Markdown, link to generated CSV/HTML chart files instead of embedding images directly.

## Writing Tone

Use formal but readable Chinese. Prefer sentences like:

- "结果表明..."
- "进一步分析显示..."
- "这说明..."
- "综合来看..."
- "因此，在策略上..."

Avoid overstating causality unless the design supports it.
