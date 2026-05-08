from __future__ import annotations

import argparse
import html
import itertools
import json
import math
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception:  # pragma: no cover - charts are optional when Pillow is absent
    Image = ImageDraw = ImageFont = None


MISSING_TOKENS = {
    "",
    " ",
    "na",
    "n/a",
    "nan",
    "null",
    "none",
    "-",
    "--",
    "缺失",
    "空",
    "无",
    "未知",
    "不清楚",
    "拒答",
}

LIKERT_MAP = {
    "非常不同意": 1,
    "很不同意": 1,
    "完全不同意": 1,
    "不同意": 2,
    "比较不同意": 2,
    "有点不同意": 2,
    "一般": 3,
    "中立": 3,
    "不确定": 3,
    "同意": 4,
    "比较同意": 4,
    "有点同意": 4,
    "非常同意": 5,
    "完全同意": 5,
    "非常不满意": 1,
    "很不满意": 1,
    "不满意": 2,
    "满意": 4,
    "比较满意": 4,
    "非常满意": 5,
    "完全满意": 5,
    "肯定不会": 1,
    "很可能不会": 2,
    "可能不会": 2,
    "说不清": 3,
    "可能会": 4,
    "很可能会": 4,
    "肯定会": 5,
    "是": 1,
    "否": 0,
    "yes": 1,
    "no": 0,
    "true": 1,
    "false": 0,
}

SEMANTIC_PATTERNS = [
    ("purchase_frequency", ["购买频率", "购买次数", "购买周期", "购买类似产品的频率", "purchase frequency", "buy frequency"]),
    ("usage_frequency", ["使用频率", "使用次数", "使用周期", "usage frequency", "use frequency"]),
    ("purchase_channel", ["购买渠道", "购买平台", "购买地点", "在哪里买", "purchase channel", "buy channel"]),
    ("monthly_spend", ["月均消费", "消费金额", "客单价", "花费", "spend", "expense", "basket size"]),
    ("usage_scene", ["使用场景", "消费场景", "使用情境", "usage scene", "occasion"]),
    ("psm_too_cheap", ["太便宜", "过于便宜", "too cheap"]),
    ("psm_cheap", ["便宜但能接受", "比较便宜", "觉得便宜", "cheap", "bargain"]),
    ("psm_expensive", ["贵但能接受", "比较贵", "觉得贵", "expensive"]),
    ("psm_too_expensive", ["太贵", "过于昂贵", "too expensive"]),
    ("brand_awareness", ["品牌认知", "品牌知晓", "了解这个品牌", "了解该品牌", "awareness", "brand awareness"]),
    ("purchase_intention", ["购买意愿", "购买意向", "购买可能", "愿意购买", "考虑购买", "购买这个产品", "复购", "推荐意愿", "推荐给", "purchase", "buy", "intention", "willingness", "recommend"]),
    ("brand_trust", ["品牌信任", "信任品牌", "信任这个品牌", "信赖", "可信", "品牌可靠", "trust", "credibility"]),
    ("brand_attitude", ["品牌态度", "喜欢品牌", "品牌好感", "brand attitude", "brand liking"]),
    ("product_quality", ["产品质量", "质量", "品质", "耐用", "可靠", "quality", "durable", "reliable"]),
    ("price_value", ["价格", "性价比", "划算", "贵", "便宜", "price", "value for money", "affordable"]),
    ("perceived_value", ["感知价值", "价值感", "值得", "有价值", "perceived value", "value"]),
    ("satisfaction", ["满意度", "满意", "满足", "satisfaction", "satisfied"]),
    ("perceived_risk", ["风险", "担心", "顾虑", "不放心", "risk", "concern"]),
    ("product_design", ["设计", "外观", "包装", "颜值", "款式", "design", "package", "packaging"]),
    ("product_feature", ["功能", "特性", "卖点", "功效", "feature", "function", "benefit"]),
    ("service_experience", ["服务", "售后", "客服", "体验", "service", "experience"]),
    ("promotion_response", ["促销", "折扣", "优惠", "活动", "promotion", "discount", "coupon"]),
    ("channel_convenience", ["渠道", "门店", "电商", "便利", "方便", "channel", "store", "online"]),
    ("social_influence", ["朋友", "家人", "社交", "口碑", "达人", "kol", "influencer", "social", "word of mouth"]),
    ("category_involvement", ["兴趣", "关注", "熟悉", "参与度", "involvement", "familiarity", "interest"]),
    ("age", ["年龄", "age"]),
    ("gender", ["性别", "gender", "sex"]),
    ("income", ["收入", "月收入", "家庭收入", "income"]),
    ("education", ["学历", "教育", "education"]),
    ("occupation", ["职业", "工作", "occupation", "job"]),
    ("marital_status", ["婚姻", "marital"]),
    ("city_tier", ["城市线级", "城市级别", "city tier"]),
    ("city", ["城市", "所在城市", "city"]),
]

BASIC_HINTS = {
    "age",
    "gender",
    "income",
    "city",
    "city_tier",
    "education",
    "occupation",
    "marital",
    "family",
    "household",
    "children",
    "region",
    "province",
}
BEHAVIOR_HINTS = {
    "frequency",
    "usage",
    "purchase_channel",
    "channel",
    "monthly_spend",
    "spend",
    "expense",
    "scene",
    "occasion",
    "loyalty",
    "membership",
    "coupon",
    "promotion",
    "store",
    "online",
    "platform",
}
COGNITIVE_HINTS = {
    "awareness",
    "attitude",
    "trust",
    "satisfaction",
    "risk",
    "quality",
    "value",
    "brand",
    "design",
    "feature",
    "involvement",
    "intention",
    "preference",
    "perceived",
}
DEMOGRAPHIC_NAMES = BASIC_HINTS
PRODUCT_HINTS = [
    "product",
    "quality",
    "price",
    "value",
    "brand",
    "trust",
    "design",
    "feature",
    "service",
    "promotion",
    "channel",
    "package",
    "perceived",
    "satisfaction",
    "risk",
    "attitude",
]
MEDIATOR_HINTS = ["perceived_value", "satisfaction", "trust", "risk", "attitude", "experience"]
MODERATOR_HINTS = ["age", "gender", "income", "city", "tier", "involvement", "familiarity", "segment"]
PURCHASE_QUESTION_HINTS = {
    "purchase",
    "buy",
    "choice",
    "chosen",
    "selection",
    "preference",
    "interest",
    "attract",
    "intention",
    "willingness",
    "recommend",
    "repurchase",
    "frequency",
    "channel",
    "spend",
    "expense",
    "购买",
    "选择",
    "意愿",
    "意向",
    "倾向",
    "偏好",
    "兴趣",
    "吸引",
    "关注",
    "了解",
    "复购",
    "推荐",
    "频率",
    "渠道",
    "消费",
    "花费",
}


def load_config(path: str | None) -> dict:
    if not path:
        return {}
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def read_data(path: str, sheet: str | None = None) -> pd.DataFrame:
    source = Path(path)
    if source.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(source, sheet_name=sheet if sheet else 0)
    if source.suffix.lower() == ".csv":
        return pd.read_csv(source, encoding="utf-8-sig")
    raise ValueError(f"Unsupported file type: {source.suffix}")


def ascii_slug(text: object, fallback: str) -> str:
    raw = "" if pd.isna(text) else str(text)
    normalized = unicodedata.normalize("NFKD", raw).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^0-9a-zA-Z]+", "_", normalized).strip("_").lower()
    slug = re.sub(r"_+", "_", slug)
    if not slug or slug.startswith("unnamed") or len(slug) < 2:
        return fallback
    if re.match(r"^\d", slug):
        slug = f"v_{slug}"
    return slug[:64].strip("_") or fallback


def semantic_name(text: object) -> str | None:
    haystack = "" if pd.isna(text) else str(text).lower()
    for name, needles in SEMANTIC_PATTERNS:
        if any(needle.lower() in haystack for needle in needles):
            return name
    return None


def clean_variable_name(name: object, fallback: str) -> str:
    text = "" if pd.isna(name) else str(name)
    sem = semantic_name(text)
    if sem:
        return sem
    q_match = re.search(r"\b(q|题|第)\s*0*(\d{1,3})\b", text, flags=re.I)
    if q_match:
        return f"q{int(q_match.group(2)):02d}"
    return ascii_slug(text, fallback)


def dedupe_name(base: str, used: dict[str, int]) -> str:
    if base not in used:
        used[base] = 1
        return base
    used[base] += 1
    return f"{base}_{used[base]}"


def rename_columns(df: pd.DataFrame, config: dict) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, str]]:
    rename_cfg = config.get("rename", {})
    used: dict[str, int] = {}
    original_to_new: dict[str, str] = {}
    rows = []
    for i, col in enumerate(df.columns, start=1):
        original = str(col)
        requested = rename_cfg.get(original, rename_cfg.get(col))
        if requested:
            base = ascii_slug(requested, f"q{i:02d}")
        else:
            base = clean_variable_name(original, f"q{i:02d}")
        new_name = dedupe_name(base, used)
        original_to_new[original] = new_name
        rows.append({"original_question": original, "variable_name": new_name})
    renamed = df.rename(columns=original_to_new)
    return renamed, pd.DataFrame(rows), original_to_new


def normalize_scalar(value: object) -> object:
    if pd.isna(value):
        return np.nan
    if isinstance(value, str):
        stripped = value.strip()
        compact = re.sub(r"\s+", "", stripped).lower()
        if compact in MISSING_TOKENS:
            return np.nan
        if compact in LIKERT_MAP:
            return LIKERT_MAP[compact]
        if stripped in LIKERT_MAP:
            return LIKERT_MAP[stripped]
        percent = re.match(r"^([-+]?\d+(\.\d+)?)%$", stripped)
        if percent:
            return float(percent.group(1)) / 100
        leading = re.match(r"^([-+]?\d+(\.\d+)?)", stripped)
        trailing = re.search(r"([-+]?\d+(\.\d+)?)$", stripped)
        if leading and len(stripped) <= 12:
            return float(leading.group(1))
        if trailing and any(token in stripped for token in ["非常", "同意", "满意", "可能", "分"]):
            return float(trailing.group(1))
        return stripped
    return value


def clean_values(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()
    for col in cleaned.columns:
        if cleaned[col].dtype == object or pd.api.types.is_string_dtype(cleaned[col]):
            mapped = cleaned[col].map(normalize_scalar)
            numeric = pd.to_numeric(mapped, errors="coerce")
            ratio = numeric.notna().mean()
            if ratio >= 0.70:
                cleaned[col] = numeric
            else:
                cleaned[col] = mapped
        else:
            cleaned[col] = pd.to_numeric(cleaned[col], errors="coerce")
    return cleaned


def resolve_names(names: list[str], original_to_new: dict[str, str]) -> list[str]:
    resolved = []
    for name in names:
        resolved.append(original_to_new.get(name, name))
    return resolved


def reverse_code(df: pd.DataFrame, items: list[str]) -> pd.DataFrame:
    out = df.copy()
    for item in items:
        if item in out.columns and pd.api.types.is_numeric_dtype(out[item]):
            series = out[item]
            lo, hi = series.min(skipna=True), series.max(skipna=True)
            if pd.notna(lo) and pd.notna(hi) and hi > lo:
                out[item] = hi + lo - series
    return out


def is_id_like(name: str, series: pd.Series, id_columns: set[str]) -> bool:
    lname = name.lower()
    if name in id_columns or any(token in lname for token in ["id", "编号", "openid", "phone", "email"]):
        return True
    if series.nunique(dropna=True) > max(20, len(series) * 0.75):
        return True
    return False


def is_likert_item(name: str, series: pd.Series, id_columns: set[str]) -> bool:
    if not pd.api.types.is_numeric_dtype(series):
        return False
    if is_id_like(name, series, id_columns):
        return False
    lname = name.lower()
    if any(lname.startswith(demo) for demo in DEMOGRAPHIC_NAMES):
        return False
    non_na = series.dropna()
    if len(non_na) < 8:
        return False
    unique = sorted(non_na.unique())
    if not 2 <= len(unique) <= 11:
        return False
    return float(np.nanmin(unique)) >= 0 and float(np.nanmax(unique)) <= 10


def cronbach_alpha(items: pd.DataFrame) -> float:
    data = items.dropna()
    k = data.shape[1]
    if k < 2 or data.shape[0] < max(8, k + 2):
        return float("nan")
    variances = data.var(axis=0, ddof=1)
    total_var = data.sum(axis=1).var(ddof=1)
    if total_var <= 0 or variances.isna().any():
        return float("nan")
    return float(k / (k - 1) * (1 - variances.sum() / total_var))


def mean_interitem_corr(items: pd.DataFrame) -> float:
    corr = items.corr(numeric_only=True).abs()
    if corr.shape[0] < 2:
        return float("nan")
    vals = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool)).stack()
    return float(vals.mean()) if len(vals) else float("nan")


def reliability_label(alpha: float, mean_corr: float) -> str:
    if pd.notna(alpha) and alpha >= 0.80:
        return "good"
    if pd.notna(alpha) and alpha >= 0.70:
        return "acceptable"
    if pd.notna(alpha) and alpha >= 0.60:
        return "exploratory"
    if pd.notna(mean_corr) and mean_corr >= 0.45:
        return "two_item_exploratory"
    return "weak"


def base_construct_name(name: str) -> str:
    lname = re.sub(r"_\d+$", "", name.lower())
    lname = re.sub(r"_[a-z]$", "", lname)
    for semantic, _ in SEMANTIC_PATTERNS:
        if lname.startswith(semantic):
            return semantic
    prefix = re.match(r"^([a-z]+_[a-z]+)", lname)
    return prefix.group(1) if prefix else lname


def best_reliable_subset(df: pd.DataFrame, items: list[str]) -> tuple[list[str], float, float, str] | None:
    candidates = []
    max_size = min(3, len(items))
    for size in range(2, max_size + 1):
        for subset in itertools.combinations(items, size):
            subset_df = df[list(subset)]
            alpha = cronbach_alpha(subset_df)
            mean_corr = mean_interitem_corr(subset_df)
            label = reliability_label(alpha, mean_corr)
            score = (alpha if pd.notna(alpha) else 0) + (mean_corr if pd.notna(mean_corr) else 0) / 2
            if label != "weak":
                candidates.append((list(subset), alpha, mean_corr, label, score))
    if not candidates:
        return None
    candidates.sort(key=lambda row: row[-1], reverse=True)
    subset, alpha, mean_corr, label, _ = candidates[0]
    return subset, alpha, mean_corr, label


def detect_constructs(df: pd.DataFrame, config: dict, original_to_new: dict[str, str]) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, list[str]]]:
    id_columns = set(resolve_names(config.get("id_columns", []), original_to_new))
    construct_defs: dict[str, list[str]] = {}
    summary_rows = []
    used_items: set[str] = set()

    for raw_name, raw_items in config.get("constructs", {}).items():
        name = ascii_slug(raw_name, raw_name)
        items = [item for item in resolve_names(raw_items, original_to_new) if item in df.columns]
        numeric_items = [item for item in items if pd.api.types.is_numeric_dtype(df[item])]
        if len(numeric_items) >= 2:
            alpha = cronbach_alpha(df[numeric_items])
            mean_corr = mean_interitem_corr(df[numeric_items])
            label = reliability_label(alpha, mean_corr)
            construct_defs[name] = numeric_items
            used_items.update(numeric_items)
            summary_rows.append({
                "construct": name,
                "items": ", ".join(numeric_items),
                "n_items": len(numeric_items),
                "cronbach_alpha": alpha,
                "mean_interitem_corr": mean_corr,
                "reliability": label,
                "source": "config",
            })

    likert_items = [col for col in df.columns if is_likert_item(col, df[col], id_columns) and col not in used_items]
    grouped: dict[str, list[str]] = {}
    for item in likert_items:
        grouped.setdefault(base_construct_name(item), []).append(item)

    for group, items in grouped.items():
        if len(items) < 2 or group in construct_defs:
            continue
        best = best_reliable_subset(df, items)
        if not best:
            continue
        subset, alpha, mean_corr, label = best
        construct_defs[group] = subset
        used_items.update(subset)
        summary_rows.append({
            "construct": group,
            "items": ", ".join(subset),
            "n_items": len(subset),
            "cronbach_alpha": alpha,
            "mean_interitem_corr": mean_corr,
            "reliability": label,
            "source": "semantic_auto",
        })

    remaining = [item for item in likert_items if item not in used_items]
    corr = df[remaining].corr(numeric_only=True).abs() if len(remaining) >= 2 else pd.DataFrame()
    auto_idx = 1
    while len(remaining) >= 2 and not corr.empty:
        pairs = []
        for a, b in itertools.combinations(remaining, 2):
            val = corr.loc[a, b]
            if pd.notna(val):
                pairs.append((val, a, b))
        if not pairs:
            break
        val, a, b = max(pairs, key=lambda row: row[0])
        if val < 0.55:
            break
        subset = [a, b]
        for candidate in remaining:
            if candidate in subset:
                continue
            if all(pd.notna(corr.loc[candidate, s]) and corr.loc[candidate, s] >= 0.45 for s in subset):
                subset.append(candidate)
                break
        alpha = cronbach_alpha(df[subset])
        mean_corr = mean_interitem_corr(df[subset])
        label = reliability_label(alpha, mean_corr)
        if label == "weak":
            break
        name = f"construct_auto_{auto_idx}"
        auto_idx += 1
        construct_defs[name] = subset
        used_items.update(subset)
        summary_rows.append({
            "construct": name,
            "items": ", ".join(subset),
            "n_items": len(subset),
            "cronbach_alpha": alpha,
            "mean_interitem_corr": mean_corr,
            "reliability": label,
            "source": "correlation_auto",
        })
        remaining = [item for item in remaining if item not in subset]
        corr = df[remaining].corr(numeric_only=True).abs() if len(remaining) >= 2 else pd.DataFrame()

    scored = df.copy()
    score_rows = {}
    score_construct_defs = {}
    used_score_names = set(df.columns)
    construct_score_names = {}
    for construct, items in construct_defs.items():
        if construct in used_score_names:
            base = f"{construct}_score"
            score_name = base
            suffix = 2
            while score_name in used_score_names:
                score_name = f"{base}_{suffix}"
                suffix += 1
        else:
            score_name = construct
        used_score_names.add(score_name)
        construct_score_names[construct] = score_name
        score_construct_defs[score_name] = items
        min_count = max(1, math.ceil(len(items) / 2))
        scored[score_name] = df[items].mean(axis=1, skipna=True)
        scored.loc[df[items].notna().sum(axis=1) < min_count, score_name] = np.nan
        score_rows[score_name] = scored[score_name]

    construct_scores = pd.DataFrame(score_rows)
    summary = pd.DataFrame(summary_rows)
    if not summary.empty:
        summary["construct_base"] = summary["construct"]
        summary["construct"] = summary["construct"].map(construct_score_names).fillna(summary["construct"])
    return scored, summary, score_construct_defs


def descriptive_stats(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col in df.columns:
        series = df[col]
        if pd.api.types.is_numeric_dtype(series):
            rows.append({
                "variable": col,
                "count": int(series.notna().sum()),
                "missing": int(series.isna().sum()),
                "mean": series.mean(),
                "std": series.std(ddof=1),
                "min": series.min(),
                "p25": series.quantile(0.25),
                "median": series.median(),
                "p75": series.quantile(0.75),
                "max": series.max(),
                "unique": int(series.nunique(dropna=True)),
            })
    return pd.DataFrame(rows)


def categorical_distributions(df: pd.DataFrame, max_levels: int = 20) -> pd.DataFrame:
    rows = []
    for col in df.columns:
        series = df[col]
        if is_id_like(col, series, set()) or series.notna().sum() < 5:
            continue
        if categorical_like(series) or (pd.api.types.is_numeric_dtype(series) and series.nunique(dropna=True) <= 12):
            counts = series.dropna().astype(str).value_counts().head(max_levels)
            total = counts.sum()
            for order, (level, count) in enumerate(counts.items(), start=1):
                rows.append({
                    "variable": col,
                    "level_order": order,
                    "level": level,
                    "count": int(count),
                    "percent": float(count / total) if total else np.nan,
                })
    return pd.DataFrame(rows)


def chi_square_p_value(statistic: float, df: int) -> float:
    if not np.isfinite(statistic) or df <= 0:
        return float("nan")
    if statistic <= 0:
        return 1.0
    # Wilson-Hilferty normal approximation; sufficient for automated screening tables.
    z = ((statistic / df) ** (1 / 3) - (1 - 2 / (9 * df))) / math.sqrt(2 / (9 * df))
    return float(0.5 * math.erfc(z / math.sqrt(2)))


def categorical_like(series: pd.Series) -> bool:
    non_na = series.dropna()
    if non_na.empty:
        return False
    if not pd.api.types.is_numeric_dtype(series):
        return True
    return 2 <= non_na.nunique(dropna=True) <= 12


def chi_square_table(table: pd.DataFrame) -> tuple[float, int, float, float]:
    if table.shape[0] < 2 or table.shape[1] < 2:
        return float("nan"), 0, float("nan"), float("nan")
    observed = table.to_numpy(dtype=float)
    total = observed.sum()
    if total <= 0:
        return float("nan"), 0, float("nan"), float("nan")
    expected = np.outer(observed.sum(axis=1), observed.sum(axis=0)) / total
    valid = expected > 0
    statistic = float((((observed - expected) ** 2) / np.where(valid, expected, np.nan))[valid].sum())
    df = int((table.shape[0] - 1) * (table.shape[1] - 1))
    p_value = chi_square_p_value(statistic, df)
    denom = total * max(1, min(table.shape[0] - 1, table.shape[1] - 1))
    cramers_v = float(math.sqrt(statistic / denom)) if denom > 0 else float("nan")
    return statistic, df, p_value, cramers_v


def runs_test(series: pd.Series) -> dict | None:
    clean = series.dropna()
    if len(clean) < 20 or clean.nunique(dropna=True) < 2:
        return None
    if pd.api.types.is_numeric_dtype(clean) and clean.nunique(dropna=True) > 2:
        median = clean.median()
        signs = clean[clean != median] > median
    else:
        top = clean.value_counts().idxmax()
        signs = clean == top
    signs = signs.astype(int).to_numpy()
    n1 = int(signs.sum())
    n2 = int(len(signs) - n1)
    if n1 == 0 or n2 == 0:
        return None
    runs = int(1 + np.sum(signs[1:] != signs[:-1]))
    n = n1 + n2
    expected = 1 + 2 * n1 * n2 / n
    variance = (2 * n1 * n2 * (2 * n1 * n2 - n)) / (n**2 * (n - 1))
    if variance <= 0:
        return None
    z = (runs - expected) / math.sqrt(variance)
    p_value = normal_p_value(z)
    return {
        "method": "runs_test_sequence",
        "n": n,
        "n_low_or_other": n2,
        "n_high_or_top": n1,
        "runs": runs,
        "expected_runs": expected,
        "statistic": z,
        "df": np.nan,
        "approx_p": p_value,
        "interpretation": "sequence_may_be_non_random" if pd.notna(p_value) and p_value < 0.05 else "sequence_randomness_not_rejected",
    }


def run_randomness_tests(df: pd.DataFrame, config: dict, original_to_new: dict[str, str]) -> pd.DataFrame:
    cconf = config.get("conjoint", {})
    configured = []
    configured.extend(config.get("randomness_variables", []))
    configured.extend(cconf.get("attributes", []))
    configured = [name for name in resolve_names(configured, original_to_new) if name in df.columns]
    candidates = configured or [
        col for col in df.columns
        if not is_id_like(col, df[col], set()) and df[col].notna().sum() >= 20 and df[col].nunique(dropna=True) > 1
    ]
    candidates = list(dict.fromkeys(candidates))[:50]
    rows = []
    for col in candidates:
        result = runs_test(df[col])
        if result:
            result["variable"] = col
            rows.append(result)
        if col in configured and categorical_like(df[col]):
            counts = df[col].dropna().astype(str).value_counts()
            if 2 <= len(counts) <= 30:
                expected = np.repeat(counts.sum() / len(counts), len(counts))
                statistic = float(((counts.to_numpy(dtype=float) - expected) ** 2 / expected).sum())
                df_chi = int(len(counts) - 1)
                p_value = chi_square_p_value(statistic, df_chi)
                rows.append({
                    "variable": col,
                    "method": "level_balance_uniformity",
                    "n": int(counts.sum()),
                    "n_low_or_other": np.nan,
                    "n_high_or_top": np.nan,
                    "runs": np.nan,
                    "expected_runs": np.nan,
                    "statistic": statistic,
                    "df": df_chi,
                    "approx_p": p_value,
                    "interpretation": "level_distribution_not_uniform" if pd.notna(p_value) and p_value < 0.05 else "level_balance_not_rejected",
                })
    if not rows:
        return pd.DataFrame()
    cols = ["variable", "method", "n", "n_low_or_other", "n_high_or_top", "runs", "expected_runs", "statistic", "df", "approx_p", "interpretation"]
    return pd.DataFrame(rows)[cols]


def run_independence_tests(df: pd.DataFrame, config: dict, original_to_new: dict[str, str], outcome: str | None = None) -> pd.DataFrame:
    rows = []
    explicit_pairs = []
    for pair in config.get("independence_pairs", []):
        if isinstance(pair, (list, tuple)) and len(pair) == 2:
            a, b = resolve_names([pair[0], pair[1]], original_to_new)
            if a in df.columns and b in df.columns:
                explicit_pairs.append((a, b))

    categorical_cols = [
        col for col in df.columns
        if not is_id_like(col, df[col], set()) and categorical_like(df[col]) and 2 <= df[col].nunique(dropna=True) <= 20
    ]
    numeric_cols = [
        col for col in df.columns
        if not is_id_like(col, df[col], set()) and pd.api.types.is_numeric_dtype(df[col]) and df[col].nunique(dropna=True) > 2
    ]

    cat_pairs = explicit_pairs or list(itertools.combinations(categorical_cols[:18], 2))
    for a, b in cat_pairs[:100]:
        if a not in df.columns or b not in df.columns:
            continue
        if not categorical_like(df[a]) or not categorical_like(df[b]):
            continue
        table = pd.crosstab(df[a].astype(str), df[b].astype(str))
        statistic, df_chi, p_value, cramers_v = chi_square_table(table)
        if df_chi <= 0:
            continue
        rows.append({
            "variable_a": a,
            "variable_b": b,
            "method": "chi_square_independence",
            "n": int(table.to_numpy().sum()),
            "statistic": statistic,
            "df": df_chi,
            "approx_p": p_value,
            "effect_size": cramers_v,
            "effect_size_name": "cramers_v",
            "interpretation": "association_detected" if pd.notna(p_value) and p_value < 0.05 else "independence_not_rejected",
        })

    if "segment" in df.columns:
        tested = {tuple(sorted([row["variable_a"], row["variable_b"]])) for row in rows}
        segment_candidates = [
            col for col in df.columns
            if col != "segment" and not is_id_like(col, df[col], set()) and df[col].notna().sum() >= 12 and df[col].nunique(dropna=True) > 1
        ][:40]
        for col in segment_candidates:
            key = tuple(sorted(["segment", col]))
            if key in tested:
                continue
            other = df[col]
            if pd.api.types.is_numeric_dtype(other) and other.nunique(dropna=True) > 12:
                try:
                    other_group = pd.qcut(other, q=4, duplicates="drop").astype(str)
                except ValueError:
                    continue
            else:
                other_group = other.astype(str)
            table = pd.crosstab(df["segment"].astype(str), other_group)
            statistic, df_chi, p_value, cramers_v = chi_square_table(table)
            if df_chi <= 0:
                continue
            rows.append({
                "variable_a": "segment",
                "variable_b": col,
                "method": "segment_chi_square_independence",
                "n": int(table.to_numpy().sum()),
                "statistic": statistic,
                "df": df_chi,
                "approx_p": p_value,
                "effect_size": cramers_v,
                "effect_size_name": "cramers_v",
                "interpretation": "association_detected" if pd.notna(p_value) and p_value < 0.05 else "independence_not_rejected",
            })

    pearson_candidates = []
    priority = [col for col in [outcome] if col] + config.get("predictors", []) + config.get("mediators", []) + config.get("moderators", [])
    priority = [col for col in resolve_names(priority, original_to_new) if col in numeric_cols]
    if priority:
        for a in priority:
            for b in numeric_cols:
                if a != b:
                    pearson_candidates.append((a, b))
    else:
        pearson_candidates = list(itertools.combinations(numeric_cols[:14], 2))
    seen = set()
    for a, b in pearson_candidates[:100]:
        key = tuple(sorted([a, b]))
        if key in seen:
            continue
        seen.add(key)
        pair = df[[a, b]].replace([np.inf, -np.inf], np.nan).dropna()
        if len(pair) < 12:
            continue
        r = pair[a].corr(pair[b])
        if pd.isna(r) or abs(r) >= 1:
            continue
        z = 0.5 * math.log((1 + r) / (1 - r)) * math.sqrt(max(1, len(pair) - 3))
        p_value = normal_p_value(z)
        rows.append({
            "variable_a": a,
            "variable_b": b,
            "method": "pearson_correlation_independence",
            "n": len(pair),
            "statistic": z,
            "df": np.nan,
            "approx_p": p_value,
            "effect_size": r,
            "effect_size_name": "pearson_r",
            "interpretation": "association_detected" if pd.notna(p_value) and p_value < 0.05 else "independence_not_rejected",
        })

    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def normal_p_value(z: float) -> float:
    if not np.isfinite(z):
        return float("nan")
    return float(math.erfc(abs(z) / math.sqrt(2)))


def zscore(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    sd = numeric.std(ddof=0)
    if pd.isna(sd) or sd == 0:
        return pd.Series(np.nan, index=series.index)
    return (numeric - numeric.mean()) / sd


def encode_predictors(df: pd.DataFrame, predictors: list[str], standardize: bool = True) -> pd.DataFrame:
    matrices = []
    for pred in predictors:
        if pred not in df.columns:
            continue
        series = df[pred]
        if pd.api.types.is_numeric_dtype(series):
            encoded = zscore(series) if standardize else pd.to_numeric(series, errors="coerce")
            if encoded.notna().sum() >= 8 and encoded.std(ddof=0) > 0:
                matrices.append(encoded.rename(pred))
        else:
            nunique = series.nunique(dropna=True)
            if 2 <= nunique <= 8:
                dummies = pd.get_dummies(series.astype("category"), prefix=pred, dummy_na=False, drop_first=True)
                if standardize:
                    dummies = dummies.apply(zscore)
                matrices.append(dummies)
    if not matrices:
        return pd.DataFrame(index=df.index)
    return pd.concat(matrices, axis=1)


def fit_ols(y: pd.Series, x: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    matrix = pd.concat([y.rename("_y"), x], axis=1).replace([np.inf, -np.inf], np.nan).dropna()
    if matrix.shape[0] < max(12, x.shape[1] + 4) or x.shape[1] == 0:
        return pd.DataFrame(), {"n": matrix.shape[0], "r2": np.nan, "adj_r2": np.nan}
    yv = zscore(matrix["_y"]).to_numpy(dtype=float)
    xv = matrix.drop(columns=["_y"]).to_numpy(dtype=float)
    names = list(matrix.drop(columns=["_y"]).columns)
    design = np.column_stack([np.ones(len(xv)), xv])
    beta = np.linalg.pinv(design.T @ design) @ design.T @ yv
    fitted = design @ beta
    resid = yv - fitted
    n, p = design.shape
    df_resid = max(1, n - p)
    sse = float(np.sum(resid**2))
    sst = float(np.sum((yv - np.mean(yv)) ** 2))
    r2 = 1 - sse / sst if sst > 0 else np.nan
    adj_r2 = 1 - (1 - r2) * (n - 1) / df_resid if pd.notna(r2) else np.nan
    mse = sse / df_resid
    cov = mse * np.linalg.pinv(design.T @ design)
    se = np.sqrt(np.maximum(np.diag(cov), 0))
    t_vals = beta / se
    rows = []
    for term, coef, std_err, t_val in zip(["intercept"] + names, beta, se, t_vals):
        rows.append({
            "term": term,
            "standardized_beta": coef,
            "std_error": std_err,
            "t_or_z": t_val,
            "approx_p": normal_p_value(t_val),
        })
    return pd.DataFrame(rows), {"n": n, "r2": r2, "adj_r2": adj_r2}


def choose_outcome(df: pd.DataFrame, config: dict) -> str | None:
    configured = config.get("outcome")
    if configured and f"{configured}_score" in df.columns:
        return f"{configured}_score"
    if configured and configured in df.columns:
        return configured
    if "purchase_intention_score" in df.columns:
        return "purchase_intention_score"
    for col in df.columns:
        lname = col.lower()
        if "purchase_intention" in lname:
            return col
    for col in df.columns:
        lname = col.lower()
        if any(token in lname for token in ["purchase", "buy", "willingness", "recommend"]):
            return col
    return None


def numeric_corr_with(df: pd.DataFrame, outcome: str, candidates: list[str]) -> list[tuple[str, float]]:
    rows = []
    for col in candidates:
        if col == outcome or col not in df.columns or not pd.api.types.is_numeric_dtype(df[col]):
            continue
        pair = df[[outcome, col]].dropna()
        if len(pair) < 8:
            continue
        corr = pair[outcome].corr(pair[col])
        if pd.notna(corr):
            rows.append((col, abs(float(corr))))
    rows.sort(key=lambda row: row[1], reverse=True)
    return rows


def choose_predictors(df: pd.DataFrame, outcome: str | None, config: dict, construct_defs: dict[str, list[str]]) -> list[str]:
    configured = []
    for predictor in config.get("predictors", []):
        if f"{predictor}_score" in df.columns:
            configured.append(f"{predictor}_score")
        elif predictor in df.columns:
            configured.append(predictor)
    if configured:
        return configured
    if not outcome:
        return []
    construct_names = list(construct_defs.keys())
    construct_items = {item for items in construct_defs.values() for item in items}
    candidates = []
    for col in construct_names:
        if col == outcome or col in candidates:
            continue
        lname = col.lower()
        if any(hint in lname for hint in PRODUCT_HINTS) and pd.api.types.is_numeric_dtype(df[col]):
            candidates.append(col)
    if len(candidates) < 2:
        for col in df.columns:
            if col == outcome or col in construct_items or col in candidates:
                continue
            lname = col.lower()
            if any(hint in lname for hint in PRODUCT_HINTS) and pd.api.types.is_numeric_dtype(df[col]):
                candidates.append(col)
    if not candidates:
        candidates = [col for col in construct_names if col != outcome and pd.api.types.is_numeric_dtype(df[col])]
    ranked = numeric_corr_with(df, outcome, candidates)
    return [name for name, _ in ranked[:12]]


def run_regression(df: pd.DataFrame, outcome: str | None, predictors: list[str]) -> tuple[pd.DataFrame, dict]:
    if not outcome or outcome not in df.columns:
        return pd.DataFrame(), {"n": 0, "r2": np.nan, "adj_r2": np.nan}
    x = encode_predictors(df, predictors, standardize=True)
    table, meta = fit_ols(df[outcome], x)
    if not table.empty:
        table.insert(0, "outcome", outcome)
    return table, meta


def bootstrap_mediation(df: pd.DataFrame, x: str, m: str, y: str, boot: int, seed: int) -> dict:
    data = df[[x, m, y]].replace([np.inf, -np.inf], np.nan).dropna()
    if len(data) < 30:
        return {}
    rng = np.random.default_rng(seed)

    def indirect(sample: pd.DataFrame) -> tuple[float, float, float]:
        xa = encode_predictors(sample, [x], standardize=True)
        a_table, _ = fit_ols(sample[m], xa)
        xb = encode_predictors(sample, [x, m], standardize=True)
        b_table, _ = fit_ols(sample[y], xb)
        if a_table.empty or b_table.empty:
            return np.nan, np.nan, np.nan
        a = float(a_table.loc[a_table["term"] == x, "standardized_beta"].iloc[0]) if x in set(a_table["term"]) else np.nan
        b = float(b_table.loc[b_table["term"] == m, "standardized_beta"].iloc[0]) if m in set(b_table["term"]) else np.nan
        direct = float(b_table.loc[b_table["term"] == x, "standardized_beta"].iloc[0]) if x in set(b_table["term"]) else np.nan
        return a * b, a, direct

    point_indirect, a_path, direct = indirect(data)
    effects = []
    for _ in range(boot):
        idx = rng.integers(0, len(data), len(data))
        sampled = data.iloc[idx]
        effect, _, _ = indirect(sampled)
        if pd.notna(effect):
            effects.append(effect)
    if len(effects) < max(20, boot // 5):
        return {}
    lo, hi = np.percentile(effects, [2.5, 97.5])
    return {
        "predictor": x,
        "mediator": m,
        "outcome": y,
        "n": len(data),
        "a_path": a_path,
        "indirect_effect": point_indirect,
        "direct_effect": direct,
        "boot_ci_low": lo,
        "boot_ci_high": hi,
        "supported": bool(lo > 0 or hi < 0),
    }


def run_mediation(df: pd.DataFrame, outcome: str | None, predictors: list[str], config: dict, construct_names: list[str], boot: int) -> pd.DataFrame:
    if not outcome:
        return pd.DataFrame()
    mediators = []
    for mediator in config.get("mediators", []):
        if f"{mediator}_score" in df.columns:
            mediators.append(f"{mediator}_score")
        elif mediator in df.columns:
            mediators.append(mediator)
    if not mediators:
        mediators = [c for c in construct_names if c != outcome and any(h in c.lower() for h in MEDIATOR_HINTS)]
    mediators = [m for m in mediators if m not in predictors and pd.api.types.is_numeric_dtype(df[m])]
    rows = []
    for x in predictors[:6]:
        for m in mediators[:8]:
            if x == m:
                continue
            result = bootstrap_mediation(df, x, m, outcome, boot=boot, seed=42 + len(rows))
            if result:
                rows.append(result)
    return pd.DataFrame(rows)


def run_moderation(df: pd.DataFrame, outcome: str | None, predictors: list[str], config: dict, construct_names: list[str]) -> pd.DataFrame:
    if not outcome:
        return pd.DataFrame()
    moderators = []
    for moderator in config.get("moderators", []):
        if f"{moderator}_score" in df.columns:
            moderators.append(f"{moderator}_score")
        elif moderator in df.columns:
            moderators.append(moderator)
    if not moderators:
        for col in construct_names + list(df.columns):
            lname = col.lower()
            if col != outcome and any(h in lname for h in MODERATOR_HINTS):
                moderators.append(col)
    rows = []
    seen = set()
    for x in predictors[:6]:
        for w in moderators[:10]:
            if x == w or (x, w) in seen or not pd.api.types.is_numeric_dtype(df[x]) or not pd.api.types.is_numeric_dtype(df[w]):
                continue
            seen.add((x, w))
            temp = pd.DataFrame({
                x: zscore(df[x]),
                w: zscore(df[w]),
            })
            temp[f"{x}_x_{w}"] = temp[x] * temp[w]
            table, meta = fit_ols(df[outcome], temp[[x, w, f"{x}_x_{w}"]])
            if table.empty:
                continue
            interaction = table[table["term"] == f"{x}_x_{w}"]
            if interaction.empty:
                continue
            record = interaction.iloc[0].to_dict()
            record.update({"predictor": x, "moderator": w, "outcome": outcome, "n": meta["n"], "r2": meta["r2"]})
            rows.append(record)
    return pd.DataFrame(rows)


def logistic_fit(x: pd.DataFrame, y: pd.Series, lr: float = 0.08, epochs: int = 2500, l2: float = 0.001) -> np.ndarray:
    data = pd.concat([y.rename("_y"), x], axis=1).replace([np.inf, -np.inf], np.nan).dropna()
    if data.empty:
        return np.array([])
    yv = data["_y"].to_numpy(dtype=float)
    xv = data.drop(columns=["_y"]).to_numpy(dtype=float)
    design = np.column_stack([np.ones(len(xv)), xv])
    beta = np.zeros(design.shape[1])
    for _ in range(epochs):
        logits = np.clip(design @ beta, -30, 30)
        probs = 1 / (1 + np.exp(-logits))
        grad = design.T @ (probs - yv) / len(yv)
        grad[1:] += l2 * beta[1:]
        beta -= lr * grad
    return beta


def encode_conjoint_attributes(df: pd.DataFrame, attrs: list[str]) -> tuple[pd.DataFrame, dict[str, list[str]]]:
    frames = []
    groups: dict[str, list[str]] = {}
    for attr in attrs:
        if attr not in df.columns:
            continue
        series = df[attr]
        if pd.api.types.is_numeric_dtype(series) and series.nunique(dropna=True) > 8:
            encoded = zscore(series).rename(attr)
            frames.append(encoded)
            groups[attr] = [attr]
        else:
            dummies = pd.get_dummies(series.astype("category"), prefix=attr, dummy_na=False, drop_first=False)
            frames.append(dummies)
            groups[attr] = list(dummies.columns)
    if not frames:
        return pd.DataFrame(index=df.index), groups
    return pd.concat(frames, axis=1), groups


def resolve_one_name(name: str | None, original_to_new: dict[str, str]) -> str | None:
    if not name:
        return None
    return original_to_new.get(name, name)


def detect_conjoint(df: pd.DataFrame, config: dict, outcome: str | None, original_to_new: dict[str, str]) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    cconf = config.get("conjoint", {})
    chosen_col = resolve_one_name(cconf.get("chosen"), original_to_new)
    rating_col = resolve_one_name(cconf.get("rating"), original_to_new)
    attrs = [resolve_one_name(attr, original_to_new) for attr in cconf.get("attributes", [])]
    attrs = [attr for attr in attrs if attr]
    if not chosen_col:
        for candidate in ["chosen", "choice", "selected", "is_chosen", "是否选择"]:
            if candidate in df.columns:
                chosen_col = candidate
                break
    if not rating_col:
        for candidate in ["profile_rating", "rating", "preference", "preference_score"]:
            if candidate in df.columns:
                rating_col = candidate
                break
    if not attrs and (chosen_col or rating_col):
        exclude = {
            chosen_col,
            rating_col,
            outcome,
            resolve_one_name(cconf.get("respondent"), original_to_new),
            resolve_one_name(cconf.get("task"), original_to_new),
            resolve_one_name(cconf.get("alternative"), original_to_new),
        }
        attrs = []
        for col in df.columns:
            if col in exclude or col is None:
                continue
            nunique = df[col].nunique(dropna=True)
            if 2 <= nunique <= 20 and not is_id_like(col, df[col], set()):
                attrs.append(col)
        attrs = attrs[:10]
    if chosen_col and chosen_col in df.columns and attrs:
        y = pd.to_numeric(df[chosen_col], errors="coerce")
        x, groups = encode_conjoint_attributes(df, attrs)
        if x.empty or y.dropna().nunique() < 2:
            return pd.DataFrame(), pd.DataFrame(), "CDC/CBC choice structure was detected but could not be estimated."
        beta = logistic_fit(x, y)
        if len(beta) == 0:
            return pd.DataFrame(), pd.DataFrame(), "CDC/CBC choice model had insufficient usable rows."
        utility = pd.DataFrame({"term": ["intercept"] + list(x.columns), "utility": beta})
        utility["attribute"] = utility["term"].apply(lambda term: next((attr for attr, cols in groups.items() if term in cols), "model"))
        importance_rows = []
        for attr, cols in groups.items():
            vals = utility[utility["term"].isin(cols)]["utility"]
            if len(vals):
                importance_rows.append({"attribute": attr, "utility_range": vals.max() - vals.min()})
        importance = pd.DataFrame(importance_rows)
        if not importance.empty and importance["utility_range"].sum() > 0:
            importance["relative_importance"] = importance["utility_range"] / importance["utility_range"].sum()
        return utility, importance, "Estimated a binary CDC/CBC choice utility model."
    if rating_col and rating_col in df.columns and attrs:
        x, groups = encode_conjoint_attributes(df, attrs)
        table, meta = fit_ols(df[rating_col], x)
        if table.empty:
            return pd.DataFrame(), pd.DataFrame(), "Rating-based conjoint structure was detected but could not be estimated."
        utility = table.rename(columns={"standardized_beta": "utility"})
        utility["attribute"] = utility["term"].apply(lambda term: next((attr for attr, cols in groups.items() if term in cols), "model"))
        importance_rows = []
        for attr, cols in groups.items():
            vals = utility[utility["term"].isin(cols)]["utility"]
            if len(vals):
                importance_rows.append({"attribute": attr, "utility_range": vals.max() - vals.min()})
        importance = pd.DataFrame(importance_rows)
        if not importance.empty and importance["utility_range"].sum() > 0:
            importance["relative_importance"] = importance["utility_range"] / importance["utility_range"].sum()
        return utility, importance, "Estimated a rating-based conjoint model."
    return pd.DataFrame(), pd.DataFrame(), "No valid CDC/CBC/conjoint structure was detected."


def detect_psm_columns(df: pd.DataFrame, config: dict, original_to_new: dict[str, str]) -> dict[str, str]:
    configured = config.get("psm", {})
    keys = ["too_cheap", "cheap", "expensive", "too_expensive"]
    resolved = {}
    for key in keys:
        col = resolve_one_name(configured.get(key), original_to_new)
        if col in df.columns:
            resolved[key] = col
    if len(resolved) == 4:
        return resolved
    patterns = {
        "too_cheap": ["psm_too_cheap", "too_cheap", "太便宜"],
        "cheap": ["psm_cheap", "cheap", "便宜"],
        "expensive": ["psm_expensive", "expensive", "贵"],
        "too_expensive": ["psm_too_expensive", "too_expensive", "太贵"],
    }
    for key, needles in patterns.items():
        if key in resolved:
            continue
        for col in df.columns:
            lname = col.lower()
            if key == "cheap" and ("too_cheap" in lname or "太便宜" in lname):
                continue
            if key == "expensive" and ("too_expensive" in lname or "太贵" in lname):
                continue
            if any(needle.lower() in lname for needle in needles):
                resolved[key] = col
                break
    return resolved if len(resolved) == 4 else {}


def nearest_intersection(grid: np.ndarray, a: np.ndarray, b: np.ndarray) -> tuple[float, float]:
    if len(grid) == 0:
        return np.nan, np.nan
    raw_diff = a - b
    exact = np.where(np.isclose(raw_diff, 0, atol=1e-12))[0]
    if len(exact):
        blocks = []
        start = int(exact[0])
        prev = int(exact[0])
        for idx in exact[1:]:
            idx = int(idx)
            if idx == prev + 1:
                prev = idx
            else:
                blocks.append((start, prev))
                start = prev = idx
        blocks.append((start, prev))
        start, end = blocks[0]
        return float((grid[start] + grid[end]) / 2), 0.0
    signs = np.sign(raw_diff)
    crossings = np.where(signs[:-1] * signs[1:] < 0)[0]
    if len(crossings):
        idx = int(crossings[0])
        x0, x1 = float(grid[idx]), float(grid[idx + 1])
        y0, y1 = float(raw_diff[idx]), float(raw_diff[idx + 1])
        if y1 != y0:
            x = x0 - y0 * (x1 - x0) / (y1 - y0)
            return float(x), 0.0
    diff = np.abs(raw_diff)
    idx = int(np.nanargmin(diff))
    return float(grid[idx]), float(diff[idx])


def estimate_psm_tables(psm: pd.DataFrame, segment: int | None = None, persona: str = "") -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, str]:
    valid = psm.dropna()
    if len(valid) < 20:
        label = f" for segment {segment}" if segment is not None else ""
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), f"PSM columns were detected but usable sample size{label} was too small."
    monotonic_mask = (
        (valid["too_cheap"] < valid["cheap"]) &
        (valid["cheap"] < valid["expensive"]) &
        (valid["expensive"] < valid["too_expensive"])
    )
    monotonic = pd.DataFrame({
        "row_number": valid.index + 1,
        "too_cheap": valid["too_cheap"],
        "cheap": valid["cheap"],
        "expensive": valid["expensive"],
        "too_expensive": valid["too_expensive"],
        "monotonic_valid": monotonic_mask.to_numpy(),
    })
    valid_psm = valid[monotonic_mask]
    if len(valid_psm) < 20:
        note = f"PSM monotonicity check retained {len(valid_psm)}/{len(valid)} rows, too few for price-point estimation."
        if segment is not None:
            note = f"Segment {segment} {persona}: {note}"
            monotonic.insert(0, "persona", persona)
            monotonic.insert(0, "segment", segment)
        return monotonic, pd.DataFrame(), pd.DataFrame(), note
    lo = float(valid_psm.min().min())
    hi = float(valid_psm.max().max())
    observed_prices = valid_psm.to_numpy(dtype=float).ravel()
    observed_prices = observed_prices[np.isfinite(observed_prices)]
    grid = np.unique(np.concatenate([np.linspace(lo, hi, 5000), observed_prices]))
    curves = pd.DataFrame({
        "price": grid,
        "too_cheap_curve": [(valid_psm["too_cheap"] >= price).mean() for price in grid],
        "cheap_curve": [(valid_psm["cheap"] >= price).mean() for price in grid],
        "expensive_curve": [(valid_psm["expensive"] <= price).mean() for price in grid],
        "too_expensive_curve": [(valid_psm["too_expensive"] <= price).mean() for price in grid],
    })
    opp, opp_gap = nearest_intersection(grid, curves["too_cheap_curve"].to_numpy(), curves["too_expensive_curve"].to_numpy())
    ipp, ipp_gap = nearest_intersection(grid, curves["cheap_curve"].to_numpy(), curves["expensive_curve"].to_numpy())
    pmc, pmc_gap = nearest_intersection(grid, curves["too_cheap_curve"].to_numpy(), curves["expensive_curve"].to_numpy())
    pme, pme_gap = nearest_intersection(grid, curves["too_expensive_curve"].to_numpy(), 1 - curves["expensive_curve"].to_numpy())
    median_too_cheap = float(valid_psm["too_cheap"].median())
    median_cheap = float(valid_psm["cheap"].median())
    median_expensive = float(valid_psm["expensive"].median())
    median_too_expensive = float(valid_psm["too_expensive"].median())
    summary = pd.DataFrame([
        {"metric": "valid_raw_rows", "value": len(valid), "description": "Rows with four PSM prices present"},
        {"metric": "monotonic_valid_rows", "value": len(valid_psm), "description": "Rows passing too cheap < cheap < expensive < too expensive"},
        {"metric": "monotonic_valid_rate", "value": len(valid_psm) / len(valid), "description": "PSM monotonicity pass rate"},
        {"metric": "OPP_optimal_price_point", "value": opp, "description": "Intersection of too cheap and too expensive curves"},
        {"metric": "IPP_indifference_price_point", "value": ipp, "description": "Intersection of cheap and expensive curves"},
        {"metric": "PMC_lower_acceptable_price", "value": pmc, "description": "Lower bound from too cheap and expensive curves"},
        {"metric": "PME_upper_acceptable_price", "value": pme, "description": "Upper bound from too expensive and not-expensive curves"},
        {"metric": "median_too_cheap_price", "value": median_too_cheap, "description": "Median too-cheap threshold"},
        {"metric": "median_cheap_price", "value": median_cheap, "description": "Median cheap/acceptable threshold"},
        {"metric": "median_expensive_price", "value": median_expensive, "description": "Median expensive/still-acceptable threshold"},
        {"metric": "median_too_expensive_price", "value": median_too_expensive, "description": "Median too-expensive threshold"},
        {"metric": "OPP_curve_gap", "value": opp_gap, "description": "Residual curve gap at OPP"},
        {"metric": "IPP_curve_gap", "value": ipp_gap, "description": "Residual curve gap at IPP"},
        {"metric": "PMC_curve_gap", "value": pmc_gap, "description": "Residual curve gap at PMC"},
        {"metric": "PME_curve_gap", "value": pme_gap, "description": "Residual curve gap at PME"},
    ])
    if segment is not None:
        for table in (monotonic, summary, curves):
            table.insert(0, "persona", persona)
            table.insert(0, "segment", segment)
    note_prefix = f"Segment {segment} {persona}: " if segment is not None else ""
    note = f"{note_prefix}PSM monotonicity retained {len(valid_psm)}/{len(valid)} rows; OPP={opp:.2f}, acceptable range={pmc:.2f}-{pme:.2f}."
    return monotonic, summary, curves, note


def run_psm_analysis(df: pd.DataFrame, config: dict, original_to_new: dict[str, str]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, str]:
    cols = detect_psm_columns(df, config, original_to_new)
    if not cols:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), "No valid PSM price-sensitivity columns were detected."
    psm = df[[cols["too_cheap"], cols["cheap"], cols["expensive"], cols["too_expensive"]]].apply(pd.to_numeric, errors="coerce")
    psm.columns = ["too_cheap", "cheap", "expensive", "too_expensive"]
    return estimate_psm_tables(psm)


def run_segment_psm_analysis(
    df: pd.DataFrame,
    config: dict,
    original_to_new: dict[str, str],
    segment_assignments: pd.DataFrame,
    segment_profiles: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, str]:
    cols = detect_psm_columns(df, config, original_to_new)
    if not cols or segment_assignments.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), "No segment-level PSM analysis was generated."
    psm = df[[cols["too_cheap"], cols["cheap"], cols["expensive"], cols["too_expensive"]]].apply(pd.to_numeric, errors="coerce")
    psm.columns = ["too_cheap", "cheap", "expensive", "too_expensive"]
    segment_series = pd.Series(segment_assignments["segment"].to_numpy(), index=segment_assignments["row_number"].to_numpy() - 1)
    persona_map = {}
    if not segment_profiles.empty and {"segment", "persona"}.issubset(segment_profiles.columns):
        persona_map = segment_profiles.set_index("segment")["persona"].to_dict()
    monotonic_tables = []
    summary_tables = []
    curve_tables = []
    notes = []
    for segment in sorted(segment_series.dropna().unique()):
        idx = segment_series[segment_series == segment].index
        persona = str(persona_map.get(segment, ""))
        monotonic, summary, curves, note = estimate_psm_tables(psm.loc[idx], int(segment), persona)
        if not monotonic.empty:
            monotonic_tables.append(monotonic)
        if not summary.empty:
            summary_tables.append(summary)
        if not curves.empty:
            curve_tables.append(curves)
        notes.append(note)
    return (
        pd.concat(monotonic_tables, ignore_index=True) if monotonic_tables else pd.DataFrame(),
        pd.concat(summary_tables, ignore_index=True) if summary_tables else pd.DataFrame(),
        pd.concat(curve_tables, ignore_index=True) if curve_tables else pd.DataFrame(),
        " ".join(notes),
    )


def kmeans(x: np.ndarray, k: int, seed: int = 42, n_init: int = 10, max_iter: int = 100) -> tuple[np.ndarray, float]:
    rng = np.random.default_rng(seed)
    best_labels = np.zeros(len(x), dtype=int)
    best_inertia = float("inf")
    for _ in range(n_init):
        centers = x[rng.choice(len(x), size=k, replace=False)].copy()
        labels = np.zeros(len(x), dtype=int)
        for _ in range(max_iter):
            distances = ((x[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)
            new_labels = distances.argmin(axis=1)
            if np.array_equal(new_labels, labels):
                break
            labels = new_labels
            for cluster in range(k):
                if np.any(labels == cluster):
                    centers[cluster] = x[labels == cluster].mean(axis=0)
                else:
                    centers[cluster] = x[rng.integers(0, len(x))]
        inertia = float(((x - centers[labels]) ** 2).sum())
        if inertia < best_inertia:
            best_inertia = inertia
            best_labels = labels.copy()
    return best_labels, best_inertia


def silhouette_score_sample(x: np.ndarray, labels: np.ndarray, seed: int = 42, max_points: int = 500) -> float:
    unique = np.unique(labels)
    if len(unique) < 2:
        return np.nan
    rng = np.random.default_rng(seed)
    idx = np.arange(len(x))
    if len(idx) > max_points:
        idx = rng.choice(idx, size=max_points, replace=False)
    scores = []
    for i in idx:
        same = labels == labels[i]
        other_clusters = [c for c in unique if c != labels[i]]
        if same.sum() <= 1:
            continue
        distances = np.sqrt(((x - x[i]) ** 2).sum(axis=1))
        a = distances[same].sum() / (same.sum() - 1)
        b = min(distances[labels == c].mean() for c in other_clusters if np.any(labels == c))
        scores.append((b - a) / max(a, b) if max(a, b) > 0 else 0)
    return float(np.mean(scores)) if scores else np.nan


def persona_label(profile_z: pd.Series) -> str:
    highs = [idx for idx, val in profile_z.sort_values(ascending=False).head(4).items() if val > 0.25]
    lows = [idx for idx, val in profile_z.sort_values().head(3).items() if val < -0.25]
    high_text = " ".join(highs).lower()
    low_text = " ".join(lows).lower()
    if "purchase" in high_text and any(token in high_text for token in ["quality", "value", "brand", "trust", "satisfaction"]):
        return "高转化拥护型"
    if "purchase" in low_text and any(token in low_text for token in ["quality", "value", "brand", "trust", "satisfaction"]):
        return "低认同待培育型"
    if "risk" in high_text:
        return "风险顾虑型"
    if "purchase" in high_text or "satisfaction" in high_text:
        return "高转化潜力型"
    if "brand" in high_text or "trust" in high_text:
        return "品牌信任驱动型"
    if "feature" in high_text or "quality" in high_text:
        return "产品体验驱动型"
    if "price" in high_text or "value" in high_text:
        return "价值感驱动型"
    return "综合均衡型"


def variable_matches(name: str, hints: set[str]) -> bool:
    lname = name.lower()
    tokens = set(re.split(r"[^a-z0-9]+", lname))
    snake = set(lname.split("_"))
    for hint in hints:
        h = hint.lower()
        if h == lname or h in tokens or h in snake:
            return True
        if "_" in h and (lname.startswith(f"{h}_") or lname.endswith(f"_{h}") or f"_{h}_" in lname):
            return True
        if len(h) >= 5 and h in lname:
            return True
    return False


def profile_groups(df: pd.DataFrame, config: dict, original_to_new: dict[str, str], construct_names: list[str], outcome: str | None, predictors: list[str]) -> dict[str, list[str]]:
    configured = {
        "basic": resolve_names(config.get("persona_basic_variables", []), original_to_new),
        "behavior": resolve_names(config.get("persona_behavior_variables", []), original_to_new),
        "cognitive": resolve_names(config.get("persona_cognitive_variables", []), original_to_new),
    }
    groups = {key: [col for col in cols if col in df.columns] for key, cols in configured.items()}
    for col in df.columns:
        if is_id_like(col, df[col], set()):
            continue
        if col not in groups["basic"] and variable_matches(col, BASIC_HINTS):
            groups["basic"].append(col)
        if col not in groups["behavior"] and variable_matches(col, BEHAVIOR_HINTS):
            groups["behavior"].append(col)
        cognitive_seed = col in construct_names or col in predictors or col == outcome
        if col not in groups["cognitive"] and (cognitive_seed or variable_matches(col, COGNITIVE_HINTS)):
            groups["cognitive"].append(col)
    for key, cols in groups.items():
        groups[key] = [
            col for col in dict.fromkeys(cols)
            if col in df.columns and df[col].notna().mean() >= 0.20 and df[col].nunique(dropna=True) > 1
        ][:18]
    return groups


def summarize_profile_value(series: pd.Series, mask: pd.Series, group: str, variable: str, segment: int, force_numeric: bool = False) -> list[dict]:
    clean_all = series.dropna()
    clean_seg = series[mask].dropna()
    if clean_all.empty or clean_seg.empty:
        return []
    if pd.api.types.is_numeric_dtype(series) and (force_numeric or series.nunique(dropna=True) > 12):
        overall_mean = float(clean_all.mean())
        segment_mean = float(clean_seg.mean())
        sd = float(clean_all.std(ddof=0))
        return [{
            "segment": segment,
            "group": group,
            "variable": variable,
            "summary_type": "numeric_mean",
            "segment_value": segment_mean,
            "overall_value": overall_mean,
            "delta_or_index": (segment_mean - overall_mean) / sd if sd > 0 else np.nan,
            "top_category": "",
            "segment_share": np.nan,
            "overall_share": np.nan,
        }]
    all_counts = clean_all.astype(str).value_counts(normalize=True)
    seg_counts = clean_seg.astype(str).value_counts(normalize=True)
    rows = []
    for category, seg_share in seg_counts.head(2).items():
        overall_share = float(all_counts.get(category, 0))
        rows.append({
            "segment": segment,
            "group": group,
            "variable": variable,
            "summary_type": "category_share",
            "segment_value": np.nan,
            "overall_value": np.nan,
            "delta_or_index": float(seg_share / overall_share) if overall_share > 0 else np.nan,
            "top_category": category,
            "segment_share": float(seg_share),
            "overall_share": overall_share,
        })
    return rows


def build_persona_details(
    df: pd.DataFrame,
    labels: np.ndarray,
    usable_index: pd.Index,
    groups: dict[str, list[str]],
    force_numeric_variables: set[str] | None = None,
) -> pd.DataFrame:
    rows = []
    force_numeric_variables = force_numeric_variables or set()
    labels_series = pd.Series(labels + 1, index=usable_index)
    for segment in sorted(labels_series.unique()):
        mask = labels_series == segment
        for group, variables in groups.items():
            for variable in variables:
                rows.extend(
                    summarize_profile_value(
                        df.loc[usable_index, variable],
                        mask,
                        group,
                        variable,
                        int(segment),
                        force_numeric=variable in force_numeric_variables,
                    )
                )
    return pd.DataFrame(rows)


def format_persona_group(details: pd.DataFrame, segment: int, group: str) -> str:
    sub = details[(details["segment"] == segment) & (details["group"] == group)].copy()
    if sub.empty:
        return "未识别到足够信息"
    parts = []
    numeric = sub[sub["summary_type"] == "numeric_mean"].copy()
    if not numeric.empty:
        numeric["abs_delta"] = numeric["delta_or_index"].abs()
        for row in numeric.sort_values("abs_delta", ascending=False).head(4).itertuples():
            parts.append(f"{row.variable}均值{row.segment_value:.2f}(整体{row.overall_value:.2f})")
    categorical = sub[sub["summary_type"] == "category_share"].copy()
    if not categorical.empty:
        over_index = categorical[categorical["delta_or_index"] >= 1].copy()
        categorical = over_index if not over_index.empty else categorical
        categorical["index_strength"] = (categorical["delta_or_index"] - 1).abs()
        categorical = categorical.sort_values("index_strength", ascending=False).drop_duplicates("variable")
        for row in categorical.sort_values("index_strength", ascending=False).head(4).itertuples():
            parts.append(f"{row.variable}偏向“{row.top_category}”({row.segment_share:.1%}, 整体{row.overall_share:.1%})")
    return "；".join(parts[:6]) if parts else "未识别到足够信息"


def desired_segment_k(config: dict, candidates: list[tuple[int, np.ndarray, float, float]]) -> int | None:
    configured = config.get("segment_k", config.get("n_segments", config.get("cluster_k")))
    available = {row[0] for row in candidates}
    if configured:
        try:
            k = int(configured)
            if k in available:
                return k
        except (TypeError, ValueError):
            pass
    preferred = [4, 3]
    preferred_available = [k for k in preferred if k in available]
    if preferred_available:
        scored = [row for row in candidates if row[0] in preferred_available]
        return max(scored, key=lambda row: row[3] if pd.notna(row[3]) else -999)[0]
    return None


def persona_strategy(row: pd.Series) -> str:
    text = " ".join(str(row.get(col, "")) for col in ["persona", "behavior_info", "cognitive_info", "high_features_z", "low_features_z"])
    if any(token in text for token in ["高转化", "拥护", "高意愿"]):
        return "优先转化与口碑扩散，强化复购、会员权益和社交分享触点。"
    if any(token in text for token in ["风险", "信任", "权威"]):
        return "加强权威背书、真实评价和试用保障，降低决策不确定性。"
    if any(token in text for token in ["价格", "价值", "性价比"]):
        return "突出价格梯度、优惠机制和价值感表达，降低首次购买门槛。"
    if any(token in text for token in ["低认同", "待培育", "疏离"]):
        return "以低成本触达和场景教育为主，先提升认知与试用意愿。"
    if any(token in text for token in ["体验", "品质", "产品"]):
        return "强调产品体验、功能差异和品质稳定性，推动从认知到购买转化。"
    return "围绕核心场景进行差异化触达，并结合行为触点持续验证转化效果。"


def build_persona_summary(profiles: pd.DataFrame) -> pd.DataFrame:
    if profiles.empty:
        return pd.DataFrame()
    rows = []
    for _, row in profiles.sort_values("segment").iterrows():
        rows.append({
            "类型编号": f"第{int(row['segment'])}类",
            "消费者类型": row.get("persona", ""),
            "样本量": int(row.get("size", 0)),
            "占比": f"{float(row.get('share', 0)):.2%}",
            "基础信息": row.get("basic_info", "未识别到足够信息"),
            "行为信息": row.get("behavior_info", "未识别到足够信息"),
            "认知信息": row.get("cognitive_info", "未识别到足够信息"),
            "核心区分特征": row.get("high_features_z", ""),
            "策略定位": persona_strategy(row),
        })
    return pd.DataFrame(rows)


def markdown_table(df: pd.DataFrame, max_col_chars: int = 90) -> list[str]:
    if df.empty:
        return []
    display = df.copy()
    for col in display.columns:
        display[col] = display[col].astype(str).map(lambda x: x if len(x) <= max_col_chars else x[: max_col_chars - 1] + "…")
    lines = ["| " + " | ".join(display.columns) + " |", "| " + " | ".join(["---"] * len(display.columns)) + " |"]
    for _, row in display.iterrows():
        vals = [str(row[col]).replace("|", "｜") for col in display.columns]
        lines.append("| " + " | ".join(vals) + " |")
    return lines


def run_clustering(df: pd.DataFrame, config: dict, construct_names: list[str], outcome: str | None, predictors: list[str], original_to_new: dict[str, str]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, str]:
    configured = [c for c in resolve_names(config.get("cluster_features", []), original_to_new) if c in df.columns]
    groups = profile_groups(df, config, original_to_new, construct_names, outcome, predictors)
    behavior_numeric = [c for c in groups["behavior"] if pd.api.types.is_numeric_dtype(df[c]) and df[c].nunique(dropna=True) > 2]
    features = configured or [c for c in construct_names + predictors + behavior_numeric + ([outcome] if outcome else []) if c and c in df.columns]
    features = [f for f in dict.fromkeys(features) if pd.api.types.is_numeric_dtype(df[f]) and df[f].notna().mean() >= 0.60]
    if len(features) < 2 or len(df) < 30:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), "Not enough usable numeric features or rows for clustering."
    matrix = df[features].copy()
    matrix = matrix.fillna(matrix.median(numeric_only=True))
    z = matrix.apply(zscore).dropna(axis=1)
    if z.shape[1] < 2:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), "Clustering features had near-zero variance."
    usable = z.dropna()
    x = usable.to_numpy(dtype=float)
    max_k = min(6, max(2, len(x) // 20))
    candidates = []
    for k in range(2, max_k + 1):
        labels, inertia = kmeans(x, k)
        counts = pd.Series(labels).value_counts(normalize=True)
        if counts.min() < 0.05:
            continue
        sil = silhouette_score_sample(x, labels)
        candidates.append((k, labels, inertia, sil))
    if not candidates:
        labels, inertia = kmeans(x, 2)
        best = (2, labels, inertia, silhouette_score_sample(x, labels))
    else:
        desired_k = desired_segment_k(config, candidates)
        if desired_k:
            best = max([row for row in candidates if row[0] == desired_k], key=lambda row: row[3] if pd.notna(row[3]) else -999)
        else:
            best = max(candidates, key=lambda row: row[3] if pd.notna(row[3]) else -999)
    k, labels, inertia, sil = best
    assignments = pd.DataFrame({"row_number": usable.index + 1, "segment": labels + 1})
    with_segments = usable.copy()
    with_segments["segment"] = labels + 1
    raw = df.loc[usable.index, features].copy()
    raw["segment"] = labels + 1
    profiles = raw.groupby("segment")[features].mean()
    overall = df[features].mean()
    overall_sd = df[features].std(ddof=0).replace(0, np.nan)
    z_profiles = (profiles - overall) / overall_sd
    force_numeric_variables = set(features + construct_names + predictors + ([outcome] if outcome else []))
    detail_table = build_persona_details(df, labels, usable.index, groups, force_numeric_variables)
    rows = []
    for segment, row in profiles.iterrows():
        profile_z = z_profiles.loc[segment]
        high_parts = [f"{idx}={val:.2f}" for idx, val in profile_z.sort_values(ascending=False).items() if val > 0.25][:5]
        low_parts = [f"{idx}={val:.2f}" for idx, val in profile_z.sort_values().items() if val < -0.25][:3]
        high = "; ".join(high_parts) if high_parts else "无明显高于整体的特征"
        low = "; ".join(low_parts) if low_parts else "无明显低于整体的特征"
        rows.append({
            "segment": segment,
            "size": int((labels + 1 == segment).sum()),
            "share": float((labels + 1 == segment).mean()),
            "persona": persona_label(profile_z),
            "basic_info": format_persona_group(detail_table, int(segment), "basic"),
            "behavior_info": format_persona_group(detail_table, int(segment), "behavior"),
            "cognitive_info": format_persona_group(detail_table, int(segment), "cognitive"),
            "high_features_z": high,
            "low_features_z": low,
            "silhouette": sil,
        })
    profile_table = pd.DataFrame(rows)
    segment_names = config.get("segment_names", {})
    if segment_names and not profile_table.empty:
        profile_table["persona"] = profile_table.apply(
            lambda row: segment_names.get(str(int(row["segment"])), segment_names.get(int(row["segment"]), row["persona"])),
            axis=1,
        )
    for feature in features:
        profile_table[f"mean_{feature}"] = profile_table["segment"].map(profiles[feature])
    note = f"Selected k={k} with silhouette={sil:.3f}."
    return assignments, profile_table, detail_table, note


def write_personas(path: Path, profiles: pd.DataFrame) -> None:
    if profiles.empty:
        path.write_text("未能生成消费者画像：可用聚类特征不足。\n", encoding="utf-8")
        return
    summary = build_persona_summary(profiles)
    type_names = "、".join(summary["消费者类型"].astype(str).tolist()) if not summary.empty else ""
    lines = [
        "# 消费者画像",
        "",
        f"## 总体结果",
        f"本研究最终将样本划分为 {len(profiles)} 类消费者：{type_names}。",
        "",
        "## 消费者画像总表",
        "",
    ]
    lines.extend(markdown_table(summary))
    lines.append("")
    for _, row in profiles.iterrows():
        lines.append(f"## Segment {int(row['segment'])}: {row['persona']}")
        lines.append(f"- 占比: {row['share']:.1%}，样本量: {int(row['size'])}")
        lines.append(f"- 基础信息: {row.get('basic_info', '未识别到足够信息')}")
        lines.append(f"- 行为信息: {row.get('behavior_info', '未识别到足够信息')}")
        lines.append(f"- 认知信息: {row.get('cognitive_info', '未识别到足够信息')}")
        lines.append(f"- 高于整体: {row['high_features_z']}")
        lines.append(f"- 低于整体: {row['low_features_z']}")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def top_terms(table: pd.DataFrame, n: int = 5) -> str:
    if table.empty or "term" not in table.columns:
        return "无可报告结果"
    coef_col = "standardized_beta" if "standardized_beta" in table.columns else "utility"
    filtered = table[table["term"] != "intercept"].copy()
    if filtered.empty:
        return "无可报告结果"
    filtered["abs_coef"] = filtered[coef_col].abs()
    parts = []
    for _, row in filtered.sort_values("abs_coef", ascending=False).head(n).iterrows():
        direction = "正向" if row[coef_col] > 0 else "负向"
        p_text = f", p≈{row['approx_p']:.3f}" if "approx_p" in row and pd.notna(row["approx_p"]) else ""
        parts.append(f"{row['term']}({direction}, β={row[coef_col]:.3f}{p_text})")
    return "；".join(parts)


def fmt_float(value: object, digits: int = 3) -> str:
    try:
        if pd.isna(value):
            return "NA"
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return "NA"


def fmt_pct(value: object) -> str:
    try:
        if pd.isna(value):
            return "NA"
        return f"{float(value):.2%}"
    except (TypeError, ValueError):
        return "NA"


def fmt_p(value: object) -> str:
    try:
        if pd.isna(value):
            return "p = NA"
        value = float(value)
    except (TypeError, ValueError):
        return "p = NA"
    if value < 0.001:
        return "p < 0.001"
    return f"p = {value:.3f}"


def top_distribution_sentence(distributions: pd.DataFrame, variable: str) -> str:
    sub = distributions[distributions["variable"] == variable].copy()
    if sub.empty:
        return ""
    top = sub.sort_values("percent", ascending=False).head(3)
    parts = [f"{row.level}（{fmt_pct(row.percent)}）" for row in top.itertuples()]
    return "、".join(parts)


def psm_metric(summary: pd.DataFrame, metric: str) -> float:
    if summary.empty:
        return np.nan
    row = summary[summary["metric"] == metric]
    if row.empty:
        return np.nan
    return float(row["value"].iloc[0])


def psm_segment_table(segment_summary: pd.DataFrame) -> pd.DataFrame:
    if segment_summary.empty or not {"segment", "metric", "value"}.issubset(segment_summary.columns):
        return pd.DataFrame()
    index_cols = ["segment"]
    if "persona" in segment_summary.columns:
        index_cols.append("persona")
    pivot = segment_summary.pivot_table(index=index_cols, columns="metric", values="value", aggfunc="first").reset_index()
    rows = []
    for row in pivot.sort_values("segment").itertuples(index=False):
        data = row._asdict()
        rows.append({
            "细分客群": data.get("persona", f"Segment {int(data.get('segment'))}"),
            "有效样本": int(data.get("valid_raw_rows", 0)) if pd.notna(data.get("valid_raw_rows", np.nan)) else np.nan,
            "单调性通过率": fmt_pct(data.get("monotonic_valid_rate", np.nan)),
            "最优价格点OPP": fmt_float(data.get("OPP_optimal_price_point", np.nan), 2),
            "无差异价格点IPP": fmt_float(data.get("IPP_indifference_price_point", np.nan), 2),
            "可接受下限PMC": fmt_float(data.get("PMC_lower_acceptable_price", np.nan), 2),
            "可接受上限PME": fmt_float(data.get("PME_upper_acceptable_price", np.nan), 2),
        })
    return pd.DataFrame(rows)


def chinese_conjoint_note(note: str) -> str:
    if "binary CDC/CBC" in note:
        return "本次检测到选择型 CDC/CBC 数据，并完成二元选择效用模型估计。"
    if "rating-based conjoint" in note:
        return "本次检测到评分型联合分析数据，并完成属性效用模型估计。"
    if "No valid" in note:
        return "本次数据未检测到可估计的 CDC/CBC/联合分析结构。"
    if "could not be estimated" in note:
        return "本次数据虽检测到联合分析结构，但有效样本或属性信息不足，未能完成稳定估计。"
    return note


def chinese_cluster_note(note: str) -> str:
    match = re.search(r"Selected k=(\d+) with silhouette=([-0-9.]+)", note)
    if match:
        return f"系统自动选择 K={match.group(1)}，轮廓系数为 {match.group(2)}"
    if "Not enough" in note:
        return "由于有效聚类特征或样本数量不足，本次未形成稳定聚类方案。"
    if "near-zero variance" in note:
        return "由于聚类特征方差过低，本次未形成稳定聚类方案。"
    return note


def chinese_psm_note(note: str) -> str:
    if "No valid PSM" in note:
        return "本次数据未检测到完整 PSM 四价格题项。"
    if "too few" in note:
        return "本次虽检测到 PSM 题项，但通过单调性校验的样本量不足，未进行价格点估计。"
    price_number = r"([0-9]+(?:\.[0-9]+)?)"
    retained = re.search(rf"PSM monotonicity retained (\d+)/(\d+) rows; OPP={price_number}, acceptable range={price_number}-{price_number}", note)
    if retained:
        return f"PSM 单调性校验保留 {retained.group(1)}/{retained.group(2)} 个样本，曲线最优价格点 OPP 约为 {retained.group(3)}，可接受价格区间约为 {retained.group(4)} 至 {retained.group(5)}。"
    return note


def write_final_research_report(
    output: Path,
    raw_n: int,
    df: pd.DataFrame,
    config: dict,
    variable_map: pd.DataFrame,
    construct_summary: pd.DataFrame,
    descriptives: pd.DataFrame,
    categorical_dist: pd.DataFrame,
    randomness: pd.DataFrame,
    independence: pd.DataFrame,
    purchase_distributions: pd.DataFrame,
    ranking_summary: pd.DataFrame,
    regression: pd.DataFrame,
    regression_meta: dict,
    mediation: pd.DataFrame,
    moderation: pd.DataFrame,
    conjoint_note: str,
    conjoint_importance: pd.DataFrame,
    psm_summary: pd.DataFrame,
    psm_segment_summary: pd.DataFrame,
    psm_note: str,
    cluster_note: str,
    profiles: pd.DataFrame,
    outcome: str | None,
    predictors: list[str],
) -> None:
    meta = config.get("metadata", {})
    source = meta.get("data_source", "问卷星/线上问卷平台或用户提供数据源")
    survey_time = meta.get("survey_time", "调研实施时间未在配置中指定")
    raw_count = int(meta.get("raw_sample", raw_n))
    valid_count = int(meta.get("valid_sample", len(df)))
    valid_rate = valid_count / raw_count if raw_count else np.nan
    product_name = meta.get("product_name", "目标产品")
    category_name = meta.get("category_name", "目标品类")
    chart_n = purchase_distributions["variable"].nunique() if not purchase_distributions.empty else 0
    multi_chart_n = (
        purchase_distributions.loc[purchase_distributions.get("chart_type", pd.Series(dtype=str)).eq("multi_select_group"), "variable"].nunique()
        if not purchase_distributions.empty and "chart_type" in purchase_distributions.columns else 0
    )

    lines = [
        "# 营销管理数据分析报告",
        "",
        "## 3.1 数据收集过程与预处理",
        "### 3.1.1 数据采集过程与样本分布",
        f"本研究的数据采集工作依托于{source}开展，{survey_time}。本次共计回收原始问卷 {raw_count} 份，经过数据清洗、逻辑校验与有效样本识别后，最终纳入统计分析的有效样本为 {valid_count} 份，样本有效率为 {fmt_pct(valid_rate)}。",
        "",
        "### 3.1.2 数据清洗与质量控制策略",
        "（1）基础数据清洗。研究首先对原始问卷字段进行变量化处理，将题干式字段统一转换为可分析变量名，并输出变量字典 `variable_map.csv`；随后对缺失值、空白值、Likert 文本、百分比与可数值化字段进行标准化处理。",
        "（2）随机性检验。为评估样本作答顺序与关键变量分布是否存在明显非随机迹象，本研究对可检验变量执行游程检验，并在 CDC/CBC 或随机属性变量存在时进一步执行水平平衡检验。",
    ]
    if randomness.empty:
        lines.append("本次数据未生成有效随机性检验结果，可能原因是缺少可检验序列变量或随机化属性配置。")
    else:
        flagged = randomness[randomness["approx_p"] < 0.05]
        lines.append(f"结果显示，共完成 {len(randomness)} 项随机性检验，其中 {len(flagged)} 项达到 p < 0.05 的提示水平，详细结果见表 `randomness_tests.csv`。")
    lines.append("（3）独立性检验。为识别分类变量之间以及关键数值变量之间的关联结构，研究进一步执行卡方独立性检验与相关独立性筛查，为后续分群、回归与调节分析提供依据。")
    if independence.empty:
        lines.append("本次数据未生成有效独立性检验结果。")
    else:
        sig = independence[independence["approx_p"] < 0.05]
        lines.append(f"结果显示，共完成 {len(independence)} 项独立性检验，其中 {len(sig)} 项呈现显著关联，说明样本内部存在可用于后续解释的结构性差异。")
    if not psm_summary.empty:
        pass_rate = psm_metric(psm_summary, "monotonic_valid_rate")
        lines.append("（4）价格敏感度（PSM）单调性约束校验。针对 PSM 模块，研究依据“太便宜 < 便宜 < 贵 < 太贵”的价格逻辑对样本进行强制性审查。")
        segment_extra = "同时按消费者画像分群输出分群最优价格点，详见 `psm_segment_summary.csv`。" if not psm_segment_summary.empty else ""
        lines.append(f"校验结果显示，PSM 单调性通过率为 {fmt_pct(pass_rate)}，并据此估计最优价格点与可接受价格区间，详见 `psm_summary.csv`。{segment_extra}")
    else:
        lines.append("（4）价格敏感度（PSM）校验。本次数据未检测到完整 PSM 四价格题项，因此未执行 PSM 单调性与价格区间测算。")

    lines.extend([
        "",
        "### 3.1.3 变量构建与合成变量测算",
    ])
    if construct_summary.empty:
        lines.append("本次数据未形成满足自动阈值的多题项构念。建议在正式报告前结合问卷设计，通过 `config.json` 指定理论构念及其题项。")
    else:
        construct_names = "、".join(construct_summary["construct"].astype(str).tolist())
        lines.append(f"本研究将多题项量表转化为可供统计分析的合成变量。经语义识别与信度检验，共形成 {len(construct_summary)} 个核心构念：{construct_names}。各构念采用题项均值法测算，并在 `construct_summary.csv` 中报告 Cronbach alpha、题项数量与构念来源。")
        for row in construct_summary.itertuples():
            lines.append(f"- {row.construct}：由 {row.n_items} 个题项构成，Cronbach alpha = {fmt_float(row.cronbach_alpha)}，信度判断为 {row.reliability}。")

    lines.extend([
        "",
        "## 3.2 描述性统计分析",
        f"基于本次调研回收的 {valid_count} 份有效样本，研究首先对受访者基础信息、购买行为、产品认知与购买意愿进行描述性统计。数值变量的均值、标准差、分位数与缺失情况见 `descriptives.csv`，分类变量频数分布见 `categorical_distributions.csv`。",
        "",
        "### 3.2.1 基础信息与样本结构",
    ])
    basic_vars = [v for v in ["gender", "age", "income", "education", "occupation", "city_tier", "city"] if v in df.columns]
    if basic_vars:
        for var in basic_vars:
            if pd.api.types.is_numeric_dtype(df[var]) and df[var].nunique(dropna=True) > 12:
                lines.append(f"{var} 的样本均值为 {fmt_float(df[var].mean(), 2)}，标准差为 {fmt_float(df[var].std(ddof=1), 2)}。")
            else:
                top_text = top_distribution_sentence(categorical_dist, var)
                if top_text:
                    lines.append(f"{var} 的主要分布为：{top_text}。")
    else:
        lines.append("系统未自动识别到典型基础信息字段。")

    lines.extend(["", "### 3.2.2 购买行为、购买意愿与购买选择题项分析"])
    if chart_n:
        extra = f"其中 {multi_chart_n} 道为多选题组，已按同一题干合并选项后制图。" if multi_chart_n else ""
        lines.append(f"针对购买行为、购买意愿、购买倾向与购买选择相关题项，本研究逐题输出频数占比，并生成饼图与柱状图，详见 `purchase_question_charts.html`。共识别 {chart_n} 道购买相关题项。{extra}")
        for variable in purchase_distributions["variable"].drop_duplicates().head(8):
            original = purchase_distributions.loc[purchase_distributions["variable"] == variable, "original_question"].iloc[0]
            chart_type = purchase_distributions.loc[purchase_distributions["variable"] == variable, "chart_type"].iloc[0] if "chart_type" in purchase_distributions.columns else "single_question"
            if chart_type == "multi_select_group":
                lines.append(f"图：{original}。该题为多选题，合并各选项后结果显示，主要选择项为 {top_distribution_sentence(purchase_distributions, variable)}（按选择次数占比）。")
            else:
                lines.append(f"图：{original}。结果显示，{variable} 的主要选项为 {top_distribution_sentence(purchase_distributions, variable)}。")
    else:
        lines.append("本次数据未自动识别购买行为、购买意愿、购买倾向或购买选择相关题项。正式分析时可在 `purchase_question_variables` 中手动指定。")

    lines.extend(["", "## 3.3 市场分析", "### 3.3.1 产品认知排序与竞品比较"])
    if ranking_summary.empty:
        lines.append("本次数据未检测到可合并的品牌排序题组。")
    else:
        lines.append("针对品牌排序题，本研究按同一维度合并各品牌题项，计算排名均值并输出合并柱状图，详见 `ranking_summary.csv` 与 `charts/` 文件夹。")
        for dimension, group in ranking_summary.groupby("dimension", sort=False):
            group = group.sort_values("mean_rank")
            title = str(group["dimension_label"].iloc[0])
            top_parts = [f"{row.brand}（{row.mean_rank:.2f}）" for row in group.head(3).itertuples()]
            image_name = f"charts/{safe_chart_name(dimension)}_bar.png"
            lines.append(f"图：{title}。排名均值越低表示排序越靠前，结果显示前三位为 {'、'.join(top_parts)}。")
            lines.append(f"![{title}]({image_name})")

    lines.extend(["", "### 3.3.2 产品认知、购买意愿与转化关系"])
    if regression.empty:
        lines.append("由于购买意愿变量、产品认知变量或有效样本不足，本次未形成可解释的回归模型。")
    else:
        lines.append(f"为检验产品相关变量与购买意愿之间的关系，本研究以 {outcome or '购买意愿'} 为因变量，将 {', '.join(predictors) if predictors else '产品/构念变量'} 纳入标准化回归模型。模型样本量 n = {regression_meta.get('n', 0)}，R² = {fmt_float(regression_meta.get('r2'))}，调整 R² = {fmt_float(regression_meta.get('adj_r2'))}。")
        for row in regression[regression["term"] != "intercept"].sort_values("standardized_beta", key=lambda s: s.abs(), ascending=False).head(6).itertuples():
            direction = "正向" if row.standardized_beta > 0 else "负向"
            lines.append(f"{row.term} 对购买意愿呈现{direction}影响（β = {fmt_float(row.standardized_beta)}，{fmt_p(row.approx_p)}）。")
        lines.append("综合来看，产品认知评价与购买意愿之间的关系可作为后续策略制定的重要依据；但回归结果仅代表统计关联，仍需结合样本结构与业务场景进行解释。")

    lines.extend(["", "### 3.3.3 中介效应与调节效应分析"])
    if mediation.empty:
        lines.append("本次数据未形成可自动估计的中介路径。若研究需要检验“产品认知—心理机制—购买意愿”的作用机制，应在配置中指定 mediators。")
    else:
        supported = mediation[mediation["supported"] == True]  # noqa: E712
        lines.append(f"本研究共估计 {len(mediation)} 条中介路径，其中 {len(supported)} 条路径的 bootstrap 区间不含 0，提示可能存在中介效应。")
    if moderation.empty:
        lines.append("本次数据未形成显著可解释的调节路径。若需要复现示例报告中的简单斜率式解读，应在配置中指定 moderators，并结合业务假设筛选交互项。")
    else:
        top_mod = moderation.sort_values("standardized_beta", key=lambda s: s.abs(), ascending=False).head(5)
        for row in top_mod.itertuples():
            direction = "正向" if row.standardized_beta > 0 else "负向"
            lines.append(f"{row.predictor} 与 {row.moderator} 的交互项呈{direction}调节趋势（β = {fmt_float(row.standardized_beta)}，{fmt_p(row.approx_p)}）。")
        lines.append("上述结果可用于绘制简单斜率图，并进一步解释不同消费者情境下认知因素向购买意愿转化的强弱差异。")

    lines.extend(["", "## 3.4 消费者识别", "### 3.4.1 聚类分析与消费者画像"])
    lines.append(f"为识别异质化需求，本研究基于核心构念、购买行为与购买意愿变量执行 K-Means 聚类分析。{chinese_cluster_note(cluster_note)}")
    if profiles.empty:
        lines.append("由于有效聚类特征不足，本次未形成消费者画像。")
    else:
        persona_summary = build_persona_summary(profiles)
        type_names = "、".join(persona_summary["消费者类型"].astype(str).tolist())
        lines.append(f"综合聚类中心、群体规模及画像特征，本研究最终将样本划分为 {len(profiles)} 类消费者：{type_names}。总体画像结果见表 `consumer_persona_summary.csv`。")
        lines.append("")
        lines.append("表：消费者画像总体结果")
        lines.extend(markdown_table(persona_summary[["类型编号", "消费者类型", "样本量", "占比", "基础信息", "行为信息", "认知信息", "策略定位"]], max_col_chars=58))
        lines.append("")
        for row in profiles.itertuples():
            lines.append(f"第 {int(row.segment)} 类群体定义为{row.persona}，样本量为 {int(row.size)} 人，占比 {fmt_pct(row.share)}。该群体的基础信息表现为：{row.basic_info}；行为信息表现为：{row.behavior_info}；认知信息表现为：{row.cognitive_info}。")
    lines.extend(["", "### 3.4.2 细分人群有效性验证"])
    if not independence.empty and "segment" in set(independence["variable_a"]).union(set(independence["variable_b"])):
        seg_tests = independence[(independence["variable_a"] == "segment") | (independence["variable_b"] == "segment")]
        sig_seg = seg_tests[seg_tests["approx_p"] < 0.05]
        lines.append(f"为验证分群方案的实操价值，本研究进一步将 segment 与基础信息、行为信息及认知变量进行独立性检验。结果显示，{len(sig_seg)} 项 segment 相关检验达到显著水平，说明不同细分客群在关键变量上存在结构性差异。")
    else:
        lines.append("本次未形成 segment 相关独立性检验结果。正式分析时可将年龄、职业、收入、城市、购买频率等变量加入 `independence_pairs` 进行交叉验证。")

    lines.extend(["", "## 3.5 策略与产品优化", "### 3.5.1 基于 CDC/CBC 联合分析的产品配置洞察"])
    lines.append(chinese_conjoint_note(conjoint_note))
    if not conjoint_importance.empty:
        top_attr = conjoint_importance.sort_values("relative_importance", ascending=False)
        attr_text = "、".join([f"{row.attribute}（{fmt_pct(row.relative_importance)}）" for row in top_attr.itertuples()])
        lines.append(f"属性重要性结果显示，影响消费者选择的关键属性依次为：{attr_text}。这说明产品配置优化应优先围绕高重要性属性展开。")
    else:
        lines.append("本次数据未形成可估计的联合分析属性重要性结果。")

    lines.extend(["", "### 3.5.2 基于 PSM 模型的价格敏感度分析"])
    lines.append(chinese_psm_note(psm_note))
    if not psm_summary.empty:
        opp = psm_metric(psm_summary, "OPP_optimal_price_point")
        ipp = psm_metric(psm_summary, "IPP_indifference_price_point")
        pmc = psm_metric(psm_summary, "PMC_lower_acceptable_price")
        pme = psm_metric(psm_summary, "PME_upper_acceptable_price")
        lines.append(f"PSM 测算结果显示，曲线最优价格点 OPP 约为 {fmt_float(opp, 2)}，无差异价格点 IPP 约为 {fmt_float(ipp, 2)}，可接受价格区间约为 {fmt_float(pmc, 2)} 至 {fmt_float(pme, 2)}。该区间位于 OPP 两侧，可作为后续定价策略、促销折扣与产品线分层的重要参考。")
        segment_price_table = psm_segment_table(psm_segment_summary)
        if not segment_price_table.empty:
            lines.append("进一步按消费者画像分群测算 PSM，结果见表 `psm_segment_summary.csv`。不同客群的 OPP 与可接受价格区间存在差异，可用于制定分层定价、礼盒装与尝鲜装组合策略。")
            lines.append("")
            lines.append("表：分群 PSM 价格敏感度结果")
            lines.extend(markdown_table(segment_price_table, max_col_chars=40))
    else:
        lines.append("若后续问卷包含 PSM 四价格题项，可自动补充单调性校验、最优价格点与可接受价格区间分析。")

    lines.extend(["", "### 3.5.3 综合策略建议"])
    if profiles.empty:
        lines.append(f"结合本次统计结果，{product_name} 应围绕核心购买意愿驱动因素优化产品表达，并通过购买相关题项分布识别主要转化阻碍。")
    else:
        target = profiles.sort_values("share", ascending=False).head(2)
        target_names = "、".join(target["persona"].astype(str).tolist())
        lines.append(f"综合聚类画像与购买意愿模型，{product_name} 在 {category_name} 中的优先目标客群可聚焦于 {target_names}。策略上，应围绕其基础信息、行为触点与认知诉求进行差异化触达。")
    lines.append("整体而言，本报告建议将数据分析结果转化为“目标人群—核心诉求—产品配置—价格策略—传播触点”的闭环策略：先通过消费者画像明确人群，再通过购买意愿模型识别转化驱动，最后结合 CDC/CBC 与 PSM 结果优化产品与价格。")

    (output / "final_research_report.md").write_text("\n".join(lines), encoding="utf-8")


def write_report(
    output: Path,
    df: pd.DataFrame,
    variable_map: pd.DataFrame,
    construct_summary: pd.DataFrame,
    descriptives: pd.DataFrame,
    randomness: pd.DataFrame,
    independence: pd.DataFrame,
    purchase_distributions: pd.DataFrame,
    regression: pd.DataFrame,
    regression_meta: dict,
    mediation: pd.DataFrame,
    moderation: pd.DataFrame,
    conjoint_note: str,
    conjoint_importance: pd.DataFrame,
    cluster_note: str,
    profiles: pd.DataFrame,
    outcome: str | None,
    predictors: list[str],
) -> None:
    lines = [
        "# 营销管理数据分析报告",
        "",
        "## 1. 数据概况",
        f"- 样本行数: {len(df)}",
        f"- 清洗后变量数: {df.shape[1]}",
        f"- 购买意愿/结果变量: {outcome or '未能自动识别'}",
        f"- 产品/构念预测变量: {', '.join(predictors) if predictors else '未能自动识别'}",
        "",
        "## 2. 变量命名与清洗",
        f"- 已将 {len(variable_map)} 个原始问题/字段转换为变量名，详见 `variable_map.csv`。",
        "- 已标准化常见缺失值、Likert 文本、百分比和可数值化字段。",
        "",
        "## 3. 构念合并与信效度",
    ]
    if construct_summary.empty:
        lines.append("- 未发现满足阈值的自动构念。建议提供 config.json 指定题项归属。")
    else:
        for _, row in construct_summary.iterrows():
            alpha = row["cronbach_alpha"]
            alpha_text = "NA" if pd.isna(alpha) else f"{alpha:.3f}"
            lines.append(f"- {row['construct']}: {row['n_items']} 个题项，alpha={alpha_text}，可靠性={row['reliability']}，来源={row['source']}。")
    chart_n = purchase_distributions["variable"].nunique() if not purchase_distributions.empty else 0
    lines.extend(["", "## 4. 描述性统计与购买题项图表", f"- 已输出 {len(descriptives)} 个数值变量的均值、标准差、分位数和缺失情况。"])
    if chart_n:
        multi_chart_n = purchase_distributions.loc[purchase_distributions["chart_type"].eq("multi_select_group"), "variable"].nunique() if "chart_type" in purchase_distributions.columns else 0
        extra = f"其中 {multi_chart_n} 道多选题已按题干合并为题组图表。" if multi_chart_n else ""
        lines.append(f"- 已为 {chart_n} 道购买行为、购买意愿、购买倾向/选择相关题项生成频数占比、饼图和柱状图，详见 `purchase_question_charts.html`。{extra}")
    else:
        lines.append("- 未自动识别到购买相关题项图表。可在 config.json 中指定 purchase_question_variables。")
    lines.extend(["", "## 5. 随机性与独立性检验"])
    if randomness.empty:
        lines.append("- 未生成随机性检验，通常是因为有效序列或配置的随机化变量不足。")
    else:
        flagged = randomness[randomness["approx_p"] < 0.05]
        lines.append(f"- 已生成 {len(randomness)} 项随机性检验，其中 p<0.05 的提示项 {len(flagged)} 项，详见 `randomness_tests.csv`。")
    if independence.empty:
        lines.append("- 未生成独立性检验，通常是因为分类变量/可检验变量不足。")
    else:
        significant = independence[independence["approx_p"] < 0.05]
        strongest = independence.copy()
        strongest["abs_effect"] = strongest["effect_size"].abs()
        top = strongest.sort_values("abs_effect", ascending=False).head(3)
        top_text = "；".join([f"{r.variable_a} vs {r.variable_b}({r.effect_size_name}={r.effect_size:.3f}, p≈{r.approx_p:.3f})" for r in top.itertuples()])
        lines.append(f"- 已生成 {len(independence)} 项独立性检验，其中 p<0.05 的关联项 {len(significant)} 项。主要结果: {top_text}")
    lines.extend(["", "## 6. 产品与购买意愿关系"])
    if regression.empty:
        lines.append("- 回归模型未能估计，通常是因为结果变量、预测变量或有效样本不足。")
    else:
        lines.append(f"- 标准化回归样本量 n={regression_meta.get('n', 0)}，R²={regression_meta.get('r2', np.nan):.3f}，调整 R²={regression_meta.get('adj_r2', np.nan):.3f}。")
        lines.append(f"- 主要关系: {top_terms(regression)}")
    lines.extend(["", "## 7. 中介效应"])
    if mediation.empty:
        lines.append("- 未发现可自动估计的中介路径。建议在 config.json 中指定 mediators。")
    else:
        supported = mediation[mediation["supported"] == True]  # noqa: E712
        lines.append(f"- 已估计 {len(mediation)} 条中介路径，其中 bootstrap 区间不含 0 的路径 {len(supported)} 条。")
    lines.extend(["", "## 8. 调节效应"])
    if moderation.empty:
        lines.append("- 未发现可自动估计的调节关系。建议在 config.json 中指定 moderators。")
    else:
        strongest = moderation.sort_values("standardized_beta", key=lambda s: s.abs(), ascending=False).head(5)
        lines.append(f"- 已估计 {len(moderation)} 个交互项。主要交互: {top_terms(strongest)}")
    lines.extend(["", "## 9. CDC/CBC/联合分析", f"- {conjoint_note}"])
    if not conjoint_importance.empty:
        top_attr = conjoint_importance.sort_values("relative_importance", ascending=False).head(3)
        attrs = "；".join([f"{r.attribute}: {r.relative_importance:.1%}" for r in top_attr.itertuples()])
        lines.append(f"- 关键属性重要性: {attrs}")
    lines.extend(["", "## 10. 聚类与消费者画像", f"- {cluster_note}"])
    if profiles.empty:
        lines.append("- 未能生成画像。")
    else:
        summary = build_persona_summary(profiles)
        type_names = "、".join(summary["消费者类型"].astype(str).tolist())
        lines.append(f"- 最终划分为 {len(profiles)} 类消费者：{type_names}。画像总表见 `consumer_persona_summary.csv`。")
        for _, row in profiles.iterrows():
            lines.append(f"- Segment {int(row['segment'])} {row['persona']}: 占比 {row['share']:.1%}；基础信息: {row.get('basic_info', '未识别')}；行为信息: {row.get('behavior_info', '未识别')}；认知信息: {row.get('cognitive_info', '未识别')}。")
    lines.extend([
        "",
        "## 11. 使用提醒",
        "- 自动构念和自动因果路径是探索性结果；正式报告前应结合问卷设计、理论模型和业务背景复核。",
        "- 中介、调节和联合分析的结论依赖样本量、题项质量和数据结构；不满足条件时应降级为描述性洞察。",
    ])
    (output / "analysis_report.md").write_text("\n".join(lines), encoding="utf-8")


def safe_to_csv(df: pd.DataFrame, path: Path) -> None:
    if not df.empty:
        df.to_csv(path, index=False, encoding="utf-8-sig")


def purchase_question_variables(df: pd.DataFrame, variable_map: pd.DataFrame, config: dict, original_to_new: dict[str, str], outcome: str | None) -> list[tuple[str, str]]:
    configured = [name for name in resolve_names(config.get("purchase_question_variables", []), original_to_new) if name in df.columns]
    questions = []
    mapped_variables = set(variable_map["variable_name"]) if "variable_name" in variable_map.columns else set()
    if not variable_map.empty:
        for row in variable_map.itertuples():
            variable = getattr(row, "variable_name")
            original = getattr(row, "original_question")
            haystack = f"{variable} {original}".lower()
            if variable in df.columns and any(hint.lower() in haystack for hint in PURCHASE_QUESTION_HINTS):
                questions.append((variable, str(original)))
    for variable in configured:
        if variable not in [v for v, _ in questions]:
            questions.append((variable, variable))
    if outcome and outcome in df.columns and outcome in mapped_variables and outcome not in [v for v, _ in questions]:
        questions.append((outcome, outcome))
    filtered = []
    for variable, question in questions:
        if is_id_like(variable, df[variable], set()) or df[variable].notna().sum() < 5 or df[variable].nunique(dropna=True) < 2:
            continue
        filtered.append((variable, question))
    return filtered[:80]


def distribution_for_chart(series: pd.Series) -> pd.DataFrame:
    clean = series.dropna()
    if clean.empty:
        return pd.DataFrame()
    if pd.api.types.is_numeric_dtype(clean) and clean.nunique(dropna=True) > 12:
        try:
            binned = pd.qcut(clean, q=min(6, clean.nunique(dropna=True)), duplicates="drop")
        except ValueError:
            binned = pd.cut(clean, bins=min(6, clean.nunique(dropna=True)), duplicates="drop")
        counts = binned.astype(str).value_counts(sort=False)
    else:
        counts = clean.astype(str).value_counts().head(20)
    total = counts.sum()
    return pd.DataFrame({
        "level": counts.index.astype(str),
        "count": counts.to_numpy(dtype=int),
        "percent": counts.to_numpy(dtype=float) / total if total else np.nan,
    })


def split_multi_select_question(question: str) -> tuple[str, str]:
    text = str(question).strip()
    separators = [" - ", "—", "－", "-"]
    for sep in separators:
        if sep in text:
            left, right = text.rsplit(sep, 1)
            if left.strip() and right.strip():
                return left.strip(), right.strip()
    return text, ""


def is_binary_selection_series(series: pd.Series) -> bool:
    clean = series.dropna()
    if clean.empty:
        return False
    values = {str(v).strip().lower() for v in clean.unique()}
    binary_sets = [
        {"0", "1"},
        {"0.0", "1.0"},
        {"否", "是"},
        {"no", "yes"},
        {"false", "true"},
    ]
    return any(values.issubset(allowed) and len(values) >= 2 for allowed in binary_sets)


def selected_count(series: pd.Series) -> int:
    clean = series.dropna()
    selected = clean.map(lambda v: str(v).strip().lower() in {"1", "1.0", "是", "yes", "true"})
    return int(selected.sum())


def common_variable_prefix(variables: list[str], fallback: str) -> str:
    tokenized = [str(v).split("_") for v in variables if v]
    if not tokenized:
        return fallback
    prefix = []
    for tokens in zip(*tokenized):
        if len(set(tokens)) == 1:
            prefix.append(tokens[0])
        else:
            break
    if prefix:
        return "_".join(prefix)
    return fallback


def purchase_question_distributions(df: pd.DataFrame, variable_map: pd.DataFrame, config: dict, original_to_new: dict[str, str], outcome: str | None) -> pd.DataFrame:
    rows = []
    questions = purchase_question_variables(df, variable_map, config, original_to_new, outcome)
    all_by_base: dict[str, list[tuple[str, str, str]]] = {}
    if not variable_map.empty:
        for row in variable_map.itertuples():
            variable = getattr(row, "variable_name")
            question = str(getattr(row, "original_question"))
            if variable not in df.columns:
                continue
            base, option = split_multi_select_question(question)
            if option and is_binary_selection_series(df[variable]):
                all_by_base.setdefault(base, []).append((variable, question, option))
    by_base: dict[str, list[tuple[str, str, str]]] = {}
    for variable, question in questions:
        base, option = split_multi_select_question(question)
        by_base.setdefault(base, []).append((variable, question, option))
    grouped_variables = set()
    group_index = 1
    for base, items in by_base.items():
        candidate_items = all_by_base.get(base, items)
        binary_items = [(variable, question, option) for variable, question, option in candidate_items if option and is_binary_selection_series(df[variable])]
        if len(binary_items) < 2:
            continue
        variables = [variable for variable, _, _ in binary_items]
        group_id = common_variable_prefix(variables, f"multi_select_{group_index}")
        if group_id in grouped_variables or any(row.get("variable") == group_id for row in rows):
            group_id = f"{group_id}_{group_index}"
        group_index += 1
        counts = []
        respondent_n = int(pd.concat([df[variable] for variable in variables], axis=1).notna().any(axis=1).sum())
        for variable, _, option in binary_items:
            count = selected_count(df[variable])
            if count > 0:
                counts.append((option, count, variable))
        total_selected = sum(count for _, count, _ in counts)
        if total_selected <= 0:
            continue
        for order, (option, count, source_variable) in enumerate(counts, start=1):
            rows.append({
                "variable": group_id,
                "original_question": base,
                "level_order": order,
                "level": option,
                "count": int(count),
                "percent": float(count / total_selected),
                "chart_type": "multi_select_group",
                "source_variable": source_variable,
                "respondent_n": respondent_n,
                "respondent_percent": float(count / respondent_n) if respondent_n else np.nan,
            })
        grouped_variables.update(variables)
    for variable, question in questions:
        if variable in grouped_variables:
            continue
        dist = distribution_for_chart(df[variable])
        for order, row in enumerate(dist.itertuples(), start=1):
            rows.append({
                "variable": variable,
                "original_question": question,
                "level_order": order,
                "level": row.level,
                "count": int(row.count),
                "percent": float(row.percent),
                "chart_type": "single_question",
                "source_variable": variable,
                "respondent_n": int(df[variable].notna().sum()),
                "respondent_percent": float(row.percent),
            })
    return pd.DataFrame(rows)


def css_pie_gradient(dist: pd.DataFrame) -> str:
    colors = ["#2563eb", "#16a34a", "#f59e0b", "#dc2626", "#7c3aed", "#0891b2", "#db2777", "#65a30d", "#9333ea", "#0f766e"]
    stops = []
    start = 0.0
    for i, row in enumerate(dist.itertuples()):
        end = start + float(row.percent) * 100
        color = colors[i % len(colors)]
        stops.append(f"{color} {start:.2f}% {end:.2f}%")
        start = end
    return ", ".join(stops) if stops else "#e5e7eb 0% 100%"


CHART_COLORS = ["#3778B8", "#59A14F", "#F2B134", "#E15759", "#7B61B9", "#4EBCD8", "#D65F9E", "#8CBF26", "#9C6ADE", "#1F8A70"]


def chart_font(size: int, bold: bool = False):
    if ImageFont is None:
        return None
    candidates = [
        "C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/simsun.ttc",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for candidate in candidates:
        try:
            if Path(candidate).exists():
                return ImageFont.truetype(candidate, size=size)
        except Exception:
            continue
    return ImageFont.load_default()


def text_wh(draw, text: str, font) -> tuple[int, int]:
    box = draw.textbbox((0, 0), str(text), font=font)
    return int(box[2] - box[0]), int(box[3] - box[1])


def wrap_label(text: str, max_chars: int = 16) -> str:
    text = str(text)
    if len(text) <= max_chars:
        return text
    parts = [text[i:i + max_chars] for i in range(0, len(text), max_chars)]
    return "\n".join(parts[:3])


def safe_chart_name(name: str) -> str:
    safe = re.sub(r"[^0-9A-Za-z_\-\u4e00-\u9fff]+", "_", str(name)).strip("_")
    return safe[:80] or "chart"


def draw_horizontal_bar_chart(path: Path, title: str, labels: list[str], values: list[float], value_suffix: str = "%") -> None:
    if Image is None or not labels:
        return
    width = 1100
    row_h = 42
    top = 90
    left = 330
    right = 90
    bottom = 50
    height = top + bottom + row_h * len(labels)
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    title_font = chart_font(26, bold=True)
    label_font = chart_font(17)
    value_font = chart_font(16)
    tw, _ = text_wh(draw, title, title_font)
    draw.text(((width - tw) / 2, 28), title, fill="#111827", font=title_font)
    max_value = max(max(values), 1e-9)
    chart_w = width - left - right
    for i, (label, value) in enumerate(zip(labels, values)):
        y = top + i * row_h
        color = CHART_COLORS[i % len(CHART_COLORS)]
        draw.text((24, y + 7), wrap_label(label, 22), fill="#111827", font=label_font)
        draw.rounded_rectangle((left, y + 8, left + chart_w, y + 28), radius=4, fill="#E5E7EB")
        bar_w = chart_w * (value / max_value)
        draw.rounded_rectangle((left, y + 8, left + bar_w, y + 28), radius=4, fill=color)
        if value_suffix == "%":
            value_text = f"{value:.1%}"
        else:
            value_text = f"{value:.2f}{value_suffix}"
        draw.text((left + chart_w + 12, y + 5), value_text, fill="#374151", font=value_font)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def draw_pie_chart(path: Path, title: str, labels: list[str], values: list[float]) -> None:
    if Image is None or not labels:
        return
    width, height = 1100, 700
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    title_font = chart_font(28, bold=True)
    label_font = chart_font(17)
    small_font = chart_font(15)
    tw, _ = text_wh(draw, title, title_font)
    draw.text(((width - tw) / 2, 28), title, fill="#111827", font=title_font)
    total = float(sum(values))
    if total <= 0:
        return
    box = (70, 105, 570, 605)
    start = -90
    for i, value in enumerate(values):
        extent = 360 * value / total
        draw.pieslice(box, start=start, end=start + extent, fill=CHART_COLORS[i % len(CHART_COLORS)], outline="white", width=2)
        start += extent
    legend_x = 630
    y = 120
    for i, (label, value) in enumerate(zip(labels, values)):
        color = CHART_COLORS[i % len(CHART_COLORS)]
        draw.rectangle((legend_x, y + 5, legend_x + 20, y + 25), fill=color)
        pct = value / total
        draw.text((legend_x + 32, y), f"{wrap_label(label, 24)}  {pct:.1%}", fill="#111827", font=label_font)
        y += 54
        if y > height - 60:
            break
    draw.text((70, 625), "注：多选题饼图按各选项被选择次数占总选择次数的比例绘制。", fill="#6B7280", font=small_font)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def draw_vertical_bar_chart(path: Path, title: str, labels: list[str], values: list[float], y_label: str = "均值") -> None:
    if Image is None or not labels:
        return
    width, height = 1100, 760
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    title_font = chart_font(28, bold=True)
    label_font = chart_font(16)
    axis_font = chart_font(15)
    tw, _ = text_wh(draw, title, title_font)
    draw.text(((width - tw) / 2, 28), title, fill="#111827", font=title_font)
    left, right, top, bottom = 90, 60, 90, 190
    chart_w = width - left - right
    chart_h = height - top - bottom
    max_value = max(max(values) * 1.12, 5.0)
    draw.line((left, top, left, top + chart_h), fill="#111827", width=2)
    draw.line((left, top + chart_h, left + chart_w, top + chart_h), fill="#111827", width=2)
    for tick in range(0, int(math.ceil(max_value)) + 1):
        y = top + chart_h - chart_h * tick / max_value
        draw.line((left - 5, y, left + chart_w, y), fill="#E5E7EB" if tick else "#111827", width=1)
        draw.text((left - 38, y - 9), str(tick), fill="#111827", font=axis_font)
    draw.text((18, top + chart_h / 2 - 20), y_label, fill="#374151", font=axis_font)
    gap = 20
    bar_w = max(32, (chart_w - gap * (len(labels) + 1)) / len(labels))
    for i, (label, value) in enumerate(zip(labels, values)):
        x0 = left + gap + i * (bar_w + gap)
        x1 = x0 + bar_w
        y1 = top + chart_h
        y0 = y1 - chart_h * value / max_value
        draw.rectangle((x0, y0, x1, y1), fill="#3778B8")
        value_text = f"{value:.2f}"
        vw, _ = text_wh(draw, value_text, axis_font)
        draw.text((x0 + (bar_w - vw) / 2, y0 - 24), value_text, fill="#374151", font=axis_font)
        label_img = Image.new("RGBA", (240, 80), (255, 255, 255, 0))
        label_draw = ImageDraw.Draw(label_img)
        label_draw.text((0, 0), wrap_label(label, 12), fill="#111827", font=label_font)
        rotated = label_img.rotate(28, expand=True)
        image.paste(rotated, (int(x0 - 20), int(y1 + 8)), rotated)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def write_purchase_chart_images(chart_dir: Path, distributions: pd.DataFrame) -> None:
    if distributions.empty:
        return
    for variable, group in distributions.groupby("variable", sort=False):
        question = str(group["original_question"].iloc[0])
        labels = group["level"].astype(str).tolist()
        pie_values = group["percent"].astype(float).tolist()
        if "respondent_percent" in group.columns and group["chart_type"].iloc[0] == "multi_select_group":
            bar_values = group["respondent_percent"].astype(float).fillna(0).tolist()
            suffix = "%"
        else:
            bar_values = pie_values
            suffix = "%"
        name = safe_chart_name(variable)
        draw_pie_chart(chart_dir / f"{name}_pie.png", question, labels, pie_values)
        draw_horizontal_bar_chart(chart_dir / f"{name}_bar.png", question, labels, bar_values, value_suffix=suffix)


BRAND_LABELS = {
    "six_walnut": "六个核桃",
    "tianma_walnut_milk": "天麻核桃乳",
    "lulu_almond": "露露杏仁露",
    "oatly": "Oatly燕麦奶",
    "doubendou_soymilk": "豆本豆豆奶",
    "yeshu_coconut": "椰树椰汁",
}


RANK_DIMENSIONS = {
    "health_rank": "健康认知排序",
    "function_rank": "功能认知排序",
    "daily_rank": "适合日常饮用认知排序",
}


def ranking_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for prefix, title in RANK_DIMENSIONS.items():
        for col in [c for c in df.columns if c.startswith(prefix + "_")]:
            brand_key = col[len(prefix) + 1:]
            numeric = pd.to_numeric(df[col], errors="coerce")
            if numeric.notna().sum() < 5:
                continue
            rows.append({
                "dimension": prefix,
                "dimension_label": title,
                "variable": col,
                "brand": BRAND_LABELS.get(brand_key, brand_key.replace("_", " ")),
                "mean_rank": float(numeric.mean()),
                "median_rank": float(numeric.median()),
                "n": int(numeric.notna().sum()),
            })
    return pd.DataFrame(rows)


def write_ranking_charts(chart_dir: Path, ranks: pd.DataFrame) -> None:
    if ranks.empty:
        return
    for dimension, group in ranks.groupby("dimension", sort=False):
        group = group.sort_values("mean_rank")
        title = str(group["dimension_label"].iloc[0])
        labels = group["brand"].astype(str).tolist()
        values = group["mean_rank"].astype(float).tolist()
        draw_vertical_bar_chart(chart_dir / f"{safe_chart_name(dimension)}_bar.png", title, labels, values, y_label="排名均值")


def write_purchase_charts_html(path: Path, distributions: pd.DataFrame) -> None:
    if distributions.empty:
        path.write_text("<!doctype html><meta charset='utf-8'><p>未识别到购买行为、购买意愿或购买选择相关题项。</p>", encoding="utf-8")
        return
    css = """
    body{font-family:Arial,'Microsoft YaHei',sans-serif;margin:32px;color:#111827;background:#f8fafc}
    h1{font-size:26px;margin-bottom:8px} h2{font-size:18px;margin:0 0 8px}
    .note{color:#64748b;margin-bottom:24px}.card{background:white;border:1px solid #e5e7eb;border-radius:8px;padding:18px;margin:0 0 18px}
    .question{color:#475569;font-size:13px;margin-bottom:14px}.viz{display:grid;grid-template-columns:180px 1fr;gap:24px;align-items:center}
    .pie{width:160px;height:160px;border-radius:50%;border:1px solid #e5e7eb}
    .bar-row{display:grid;grid-template-columns:minmax(110px,260px) 1fr minmax(90px,170px);gap:10px;align-items:center;margin:7px 0;font-size:13px}
    .track{background:#e5e7eb;height:18px;border-radius:4px;overflow:hidden}.bar{height:18px;background:#2563eb}
    .label{overflow-wrap:anywhere}.pct{text-align:right;color:#475569}.legend{margin-top:10px;font-size:12px;color:#475569}
    @media(max-width:720px){.viz{grid-template-columns:1fr}.pie{width:140px;height:140px}}
    """
    parts = [
        "<!doctype html><html><head><meta charset='utf-8'>",
        f"<style>{css}</style></head><body>",
        "<h1>购买相关题项图表分析</h1>",
        "<div class='note'>每道购买行为、购买意愿、购买倾向或购买选择相关题项均提供饼图和柱状图；同一题干拆分出的多选项已合并为一个题组图表，饼图展示各选项在总选择次数中的占比。</div>",
    ]
    for variable, group in distributions.groupby("variable", sort=False):
        question = group["original_question"].iloc[0]
        chart_type = group["chart_type"].iloc[0] if "chart_type" in group.columns else "single_question"
        gradient = css_pie_gradient(group)
        parts.append("<section class='card'>")
        parts.append(f"<h2>{html.escape(str(variable))}</h2>")
        if chart_type == "multi_select_group":
            total_selected = int(group["count"].sum())
            respondent_n = int(group["respondent_n"].dropna().iloc[0]) if "respondent_n" in group.columns and group["respondent_n"].notna().any() else 0
            parts.append(f"<div class='question'>{html.escape(str(question))}（多选题合并；总选择次数 {total_selected}，有效答题人数 {respondent_n}）</div>")
        else:
            parts.append(f"<div class='question'>{html.escape(str(question))}</div>")
        parts.append("<div class='viz'>")
        parts.append(f"<div><div class='pie' style='background:conic-gradient({gradient})'></div></div>")
        parts.append("<div>")
        for row in group.itertuples():
            pct = float(row.percent)
            respondent_pct = getattr(row, "respondent_percent", np.nan)
            if chart_type == "multi_select_group" and pd.notna(respondent_pct):
                pct_text = f"占选择 {pct:.1%} / 选择率 {float(respondent_pct):.1%}"
                bar_width = min(float(respondent_pct), 1.0) * 100
            else:
                pct_text = f"{pct:.1%}"
                bar_width = pct * 100
            parts.append("<div class='bar-row'>")
            parts.append(f"<div class='label'>{html.escape(str(row.level))}</div>")
            parts.append(f"<div class='track'><div class='bar' style='width:{bar_width:.1f}%'></div></div>")
            parts.append(f"<div class='pct'>{pct_text}</div>")
            parts.append("</div>")
        parts.append("</div></div></section>")
    parts.append("</body></html>")
    path.write_text("\n".join(parts), encoding="utf-8")


def write_workbook(path: Path, tables: dict[str, pd.DataFrame]) -> None:
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        wrote = False
        for name, table in tables.items():
            if table is not None and not table.empty:
                table.to_excel(writer, sheet_name=name[:31], index=False)
                wrote = True
        if not wrote:
            pd.DataFrame({"message": ["No analysis tables were generated."]}).to_excel(writer, sheet_name="summary", index=False)


def make_demo(path: Path) -> None:
    rng = np.random.default_rng(42)
    n = 180
    quality = rng.normal(0, 1, n)
    value = 0.65 * quality + rng.normal(0, 0.8, n)
    trust = 0.45 * quality + rng.normal(0, 0.9, n)
    price_sens = rng.normal(0, 1, n)
    involvement = rng.normal(0, 1, n)
    purchase = 0.45 * quality + 0.45 * value + 0.25 * trust + 0.20 * quality * involvement - 0.25 * price_sens + rng.normal(0, 0.8, n)

    def likert(latent: np.ndarray) -> np.ndarray:
        scaled = np.clip(np.round(3 + latent), 1, 5)
        return scaled.astype(int)

    data = pd.DataFrame({
        "受访者ID": np.arange(1, n + 1),
        "我认为这个产品质量很好": likert(quality + rng.normal(0, 0.25, n)),
        "这个产品的做工可靠": likert(quality + rng.normal(0, 0.25, n)),
        "这个产品品质让我放心": likert(quality + rng.normal(0, 0.25, n)),
        "这个产品值得这个价格": likert(value + rng.normal(0, 0.25, n)),
        "这个产品性价比高": likert(value + rng.normal(0, 0.25, n)),
        "我信任这个品牌": likert(trust + rng.normal(0, 0.25, n)),
        "这个品牌让我感到可靠": likert(trust + rng.normal(0, 0.25, n)),
        "我对这个品类很感兴趣": likert(involvement + rng.normal(0, 0.25, n)),
        "我经常关注类似产品": likert(involvement + rng.normal(0, 0.25, n)),
        "我了解这个品牌": likert(trust + involvement * 0.25 + rng.normal(0, 0.35, n)),
        "我担心这个产品不适合我": likert(price_sens + rng.normal(0, 0.25, n)),
        "过去一个月购买类似产品的频率": np.clip(np.round(2.5 + involvement + rng.normal(0, 0.8, n)), 1, 5).astype(int),
        "常用购买渠道": rng.choice(["电商平台", "品牌官网", "线下门店", "直播间"], n, p=[0.45, 0.18, 0.25, 0.12]),
        "月均消费金额": np.clip(np.round(220 + 70 * involvement + 40 * quality + rng.normal(0, 80, n)), 20, 800),
        "主要使用场景": rng.choice(["日常自用", "家庭共享", "送礼", "工作学习"], n, p=[0.52, 0.22, 0.16, 0.10]),
        "我愿意购买这个产品": likert(purchase + rng.normal(0, 0.25, n)),
        "我会考虑把这个产品推荐给朋友": likert(purchase + rng.normal(0, 0.25, n)),
        "年龄": rng.integers(18, 55, n),
        "收入": rng.choice([1, 2, 3, 4, 5], n, p=[0.12, 0.26, 0.32, 0.20, 0.10]),
        "性别": rng.choice(["男", "女"], n),
    })
    data.to_excel(path, index=False)


def run(args: argparse.Namespace) -> None:
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    if args.make_demo:
        demo_path = output / "demo_marketing_survey.xlsx"
        make_demo(demo_path)
        args.input = str(demo_path)
    config = load_config(args.config)
    raw = read_data(args.input, args.sheet)
    renamed, variable_map, original_to_new = rename_columns(raw, config)
    cleaned = clean_values(renamed)
    reverse_items = resolve_names(config.get("reverse_items", []), original_to_new)
    cleaned = reverse_code(cleaned, reverse_items)
    scored, construct_summary, construct_defs = detect_constructs(cleaned, config, original_to_new)
    construct_names = list(construct_defs.keys())
    outcome = choose_outcome(scored, config)
    predictors = choose_predictors(scored, outcome, config, construct_defs)
    descriptives = descriptive_stats(scored)
    categorical_dist = categorical_distributions(scored)
    numeric = scored.select_dtypes(include=[np.number])
    correlations = numeric.corr().reset_index().rename(columns={"index": "variable"}) if numeric.shape[1] >= 2 else pd.DataFrame()
    randomness = run_randomness_tests(scored, config, original_to_new)
    regression, regression_meta = run_regression(scored, outcome, predictors)
    mediation = run_mediation(scored, outcome, predictors, config, construct_names, boot=args.bootstrap)
    moderation = run_moderation(scored, outcome, predictors, config, construct_names)
    conjoint_utility, conjoint_importance, conjoint_note = detect_conjoint(scored, config, outcome, original_to_new)
    psm_monotonicity, psm_summary, psm_curves, psm_note = run_psm_analysis(scored, config, original_to_new)
    segment_assignments, segment_profiles, persona_details, cluster_note = run_clustering(scored, config, construct_names, outcome, predictors, original_to_new)
    psm_segment_monotonicity, psm_segment_summary, psm_segment_curves, psm_segment_note = run_segment_psm_analysis(
        scored, config, original_to_new, segment_assignments, segment_profiles
    )
    consumer_persona_summary = build_persona_summary(segment_profiles)
    independence_df = scored.copy()
    if not segment_assignments.empty:
        segment_series = pd.Series(segment_assignments["segment"].to_numpy(), index=segment_assignments["row_number"].to_numpy() - 1)
        independence_df["segment"] = pd.Series(index=independence_df.index, dtype="float")
        independence_df.loc[segment_series.index, "segment"] = segment_series
    independence = run_independence_tests(independence_df, config, original_to_new, outcome=outcome)
    purchase_distributions = purchase_question_distributions(scored, variable_map, config, original_to_new, outcome)
    rank_summary = ranking_summary(scored)
    chart_dir = output / "charts"

    variable_map.to_csv(output / "variable_map.csv", index=False, encoding="utf-8-sig")
    scored.to_csv(output / "cleaned_data.csv", index=False, encoding="utf-8-sig")
    safe_to_csv(pd.DataFrame({name: scored[name] for name in construct_names if name in scored.columns}), output / "construct_scores.csv")
    safe_to_csv(construct_summary, output / "construct_summary.csv")
    safe_to_csv(descriptives, output / "descriptives.csv")
    safe_to_csv(categorical_dist, output / "categorical_distributions.csv")
    safe_to_csv(correlations, output / "correlations.csv")
    safe_to_csv(randomness, output / "randomness_tests.csv")
    safe_to_csv(independence, output / "independence_tests.csv")
    safe_to_csv(purchase_distributions, output / "purchase_question_distributions.csv")
    write_purchase_charts_html(output / "purchase_question_charts.html", purchase_distributions)
    write_purchase_chart_images(chart_dir, purchase_distributions)
    safe_to_csv(rank_summary, output / "ranking_summary.csv")
    write_ranking_charts(chart_dir, rank_summary)
    safe_to_csv(regression, output / "regression_coefficients.csv")
    safe_to_csv(mediation, output / "mediation.csv")
    safe_to_csv(moderation, output / "moderation.csv")
    safe_to_csv(conjoint_utility, output / "conjoint_utilities.csv")
    safe_to_csv(conjoint_importance, output / "conjoint_importance.csv")
    safe_to_csv(psm_monotonicity, output / "psm_monotonicity.csv")
    safe_to_csv(psm_summary, output / "psm_summary.csv")
    safe_to_csv(psm_curves, output / "psm_curves.csv")
    safe_to_csv(psm_segment_monotonicity, output / "psm_segment_monotonicity.csv")
    safe_to_csv(psm_segment_summary, output / "psm_segment_summary.csv")
    safe_to_csv(psm_segment_curves, output / "psm_segment_curves.csv")
    safe_to_csv(segment_assignments, output / "segment_assignments.csv")
    safe_to_csv(segment_profiles, output / "segment_profiles.csv")
    safe_to_csv(persona_details, output / "persona_profile_details.csv")
    safe_to_csv(consumer_persona_summary, output / "consumer_persona_summary.csv")
    write_personas(output / "personas.md", segment_profiles)
    write_report(
        output=output,
        df=scored,
        variable_map=variable_map,
        construct_summary=construct_summary,
        descriptives=descriptives,
        randomness=randomness,
        independence=independence,
        purchase_distributions=purchase_distributions,
        regression=regression,
        regression_meta=regression_meta,
        mediation=mediation,
        moderation=moderation,
        conjoint_note=conjoint_note,
        conjoint_importance=conjoint_importance,
        cluster_note=cluster_note,
        profiles=segment_profiles,
        outcome=outcome,
        predictors=predictors,
    )
    write_final_research_report(
        output=output,
        raw_n=len(raw),
        df=scored,
        config=config,
        variable_map=variable_map,
        construct_summary=construct_summary,
        descriptives=descriptives,
        categorical_dist=categorical_dist,
        randomness=randomness,
        independence=independence,
        purchase_distributions=purchase_distributions,
        ranking_summary=rank_summary,
        regression=regression,
        regression_meta=regression_meta,
        mediation=mediation,
        moderation=moderation,
        conjoint_note=conjoint_note,
        conjoint_importance=conjoint_importance,
        psm_summary=psm_summary,
        psm_segment_summary=psm_segment_summary,
        psm_note=psm_note,
        cluster_note=cluster_note,
        profiles=segment_profiles,
        outcome=outcome,
        predictors=predictors,
    )
    write_workbook(
        output / "analysis_workbook.xlsx",
        {
            "variable_map": variable_map,
            "construct_summary": construct_summary,
            "descriptives": descriptives,
            "categorical_dist": categorical_dist,
            "correlations": correlations,
            "randomness_tests": randomness,
            "independence_tests": independence,
            "purchase_question_dist": purchase_distributions,
            "ranking_summary": rank_summary,
            "regression": regression,
            "mediation": mediation,
            "moderation": moderation,
            "conjoint_utilities": conjoint_utility,
            "conjoint_importance": conjoint_importance,
            "psm_summary": psm_summary,
            "psm_segment_summary": psm_segment_summary,
            "psm_monotonicity": psm_monotonicity,
            "psm_segment_monotonicity": psm_segment_monotonicity,
            "segment_profiles": segment_profiles,
            "persona_details": persona_details,
            "persona_summary": consumer_persona_summary,
        },
    )
    print(f"Analysis complete: {output}")
    print(f"Report: {output / 'analysis_report.md'}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Automated marketing management survey analytics.")
    parser.add_argument("--input", help="Input CSV/XLSX/XLS file.")
    parser.add_argument("--output", required=True, help="Output directory.")
    parser.add_argument("--sheet", default=None, help="Excel sheet name.")
    parser.add_argument("--config", default=None, help="Optional JSON config file.")
    parser.add_argument("--bootstrap", type=int, default=300, help="Bootstrap samples for mediation intervals.")
    parser.add_argument("--make-demo", action="store_true", help="Create and analyze a demo marketing survey dataset.")
    args = parser.parse_args()
    if not args.input and not args.make_demo:
        parser.error("--input is required unless --make-demo is used.")
    return args


if __name__ == "__main__":
    run(parse_args())
