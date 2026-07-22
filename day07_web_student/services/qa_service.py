from pathlib import Path
import pandas as pd

def answer_question(base_dir: Path, question: str) -> str:
    data_dir = base_dir / "data"
    metrics_df = pd.read_csv(data_dir / "overall_metrics.csv", encoding="utf-8-sig")
    metrics = dict(zip(metrics_df["指标"], metrics_df["数值"]))
    normalized = question.replace(" ", "").lower()

    if any(word in normalized for word in ["多少用户", "用户数", "总用户"]):
        return f"数据集中共有{int(metrics['用户数']):,}名用户。"

    # 1.流失率相关
    if any(word in normalized for word in ["流失率", "流失人数", "流失"]):
        return f"平台整体流失率为{metrics['流失率']:.1%}，总流失用户{int(metrics['流失人数'])}人。"
    # 2.偏好品类相关
    if any(word in normalized for word in ["品类", "哪个品类用户最多", "偏好品类"]):
        cat_df = pd.read_csv(data_dir / "category_analysis.csv", encoding="utf-8-sig")
        top_cat = cat_df.loc[cat_df["用户数"].idxmax()]
        return f"用户数量最多的品类是{top_cat['PreferedOrderCat']}，共{top_cat['用户数']}位用户。"
    # 3.生命周期风险
    if any(word in normalized for word in ["生命周期", "风险最高", "新用户"]):
        seg_df = pd.read_csv(data_dir / "segment_analysis.csv", encoding="utf-8-sig")
        risk_row = seg_df.loc[seg_df["流失率"].idxmax()]
        return f"流失风险最高的生命周期分组是{risk_row['TenureGroup']}，流失率{risk_row['流失率']:.1%}。"
    # 4.订单相关
    if any(word in normalized for word in ["订单", "平均订单"]):
        return f"平台用户平均订单数为{metrics['平均订单数']:.2f}单。"

    return "暂时无法识别该问题，请更换与用户、流失、品类、订单相关的提问。"
