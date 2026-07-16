from pathlib import Path
import pandas as pd
import numpy as np
try:
    from IPython.display import display
except ImportError:
    def display(obj):
        print(obj)

# 全局打印设置
pd.set_option("display.max_columns", 50)
pd.set_option("display.float_format", lambda x: f"{x:.2f}")

# 1. 文件路径（对应你正确的清洗文件）
ROOT = Path.cwd()
# 这里填你的csv文件名，直接放在项目根目录即可
DATA_PATH = ROOT / "ecommerce_customer_cleaned (1).csv"
OUTPUT_DIR = ROOT / "output" / "day05_analysis"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("数据文件路径：", DATA_PATH)
print("报表输出文件夹：", OUTPUT_DIR)

# 读取清洗完毕的数据
df = pd.read_csv(DATA_PATH)
print(f"数据总行列：{df.shape}")
print("="*60)

# --------------------------1. 数据验收校验--------------------------
core_cols = [
    "CustomerID", "Churn", "Tenure", "TenureGroup", "OrderCount",
    "CouponUsed", "CashbackAmount", "DaySinceLastOrder", "Complain",
    "PreferedOrderCat", "PreferredPaymentMode", "PreferredLoginDevice",
    "SatisfactionScore", "CityTier"
]

validation = pd.Series({
    "总行数": len(df),
    "总列数": df.shape[1],
    "CustomerID重复数量": int(df["CustomerID"].duplicated().sum()),
    "核心字段缺失总数": int(df[core_cols].isna().sum().sum()),
    "Churn唯一值": sorted(df["Churn"].unique().tolist()),
}, name="数据验收结果")

display(validation.to_frame())
display(df.head())

# 校验规则（数据不合格会直接提示）
assert df["CustomerID"].is_unique, "CustomerID存在重复用户"
assert df[core_cols].notna().all().all(), "核心字段存在缺失值"
assert set(df["Churn"].unique()) == {0, 1}, "流失标签只能是0/1"
print("✅ 数据验收全部通过！")
print("="*60)

# --------------------------2. 指标说明字典--------------------------
metric_dictionary = pd.DataFrame([
    ["独立用户总数", "CustomerID", "nunique", "统计不重复用户数量"],
    ["流失用户数", "Churn", "sum", "Churn=1的用户"],
    ["整体流失率", "Churn", "mean", "流失人数 / 总用户"],
    ["平均订单量", "OrderCount", "mean", "用户平均下单次数"],
    ["平均优惠券使用数", "CouponUsed", "mean", "人均用券次数"],
    ["平均返现金额", "CashbackAmount", "mean", "平台发放返现均值"],
    ["日均APP时长", "HourSpendOnApp", "mean", "用户APP使用平均时长"],
    ["平均上次下单间隔", "DaySinceLastOrder", "mean", "距离上次下单平均天数"],
], columns=["指标名称", "字段", "聚合方式", "指标解释"])
display(metric_dictionary)
print("="*60)

# --------------------------3. 整体用户大盘指标--------------------------
overall_metrics = pd.DataFrame({
    "指标": [
        "用户总数", "流失人数", "整体流失率", "订单均值", "订单中位数",
        "平均优惠券数", "平均返现", "平均APP时长", "平均满意度", "平均距上次下单天数"
    ],
    "数值": [
        df["CustomerID"].nunique(),
        df["Churn"].sum(),
        df["Churn"].mean(),
        df["OrderCount"].mean(),
        df["OrderCount"].median(),
        df["CouponUsed"].mean(),
        df["CashbackAmount"],
        df["HourSpendOnApp"].mean(),
        df["SatisfactionScore"].mean(),
        df["DaySinceLastOrder"].mean()
    ]
})
display(overall_metrics)
print(f"整体流失率: {df['Churn'].mean():.2%}")
print("="*60)

# 基础分类维度分布
profile_fields = ["TenureGroup", "PreferedOrderCat", "PreferredPaymentMode", "PreferredLoginDevice", "CityTier"]
for field in profile_fields:
    table = df[field].value_counts(dropna=False).rename("用户数").to_frame()
    table["用户占比"] = table / len(df)
    print(f"【{field} 用户分布】")
    display(table)
    print("-"*40)

# --------------------------4. 生命周期分组分析--------------------------
tenure_analysis = (
    df.groupby("TenureGroup", observed=True)
    .agg(
        用户数=("CustomerID", "nunique"),
        流失人数=("Churn", "sum"),
        流失率=("Churn", "mean"),
        平均订单=("OrderCount", "mean"),
        平均返现=("CashbackAmount", "mean"),
        平均间隔天数=("DaySinceLastOrder", "mean"),
    )
    .reset_index()
)
display(tenure_analysis)
print("="*60)

# 有无投诉分组对比
complain_analysis = (
    df.groupby("Complain")
    .agg(
        用户数=("CustomerID", "nunique"),
        流失人数=("Churn", "sum"),
        流失率=("Churn", "mean"),
        平均满意度=("SatisfactionScore", "mean"),
        平均订单=("OrderCount", "mean"),
    )
    .reset_index()
)
complain_analysis["投诉状态"] = complain_analysis["Complain"].map({0: "无投诉", 1: "有投诉"})
display(complain_analysis[["投诉状态", "用户数", "流失人数", "流失率", "平均满意度", "平均订单"]])
print("="*60)

# --------------------------5. 品类、支付渠道流失分析--------------------------
# 偏好商品品类
category_analysis = (
    df.groupby("PreferedOrderCat")
    .agg(
        用户数=("CustomerID", "nunique"),
        流失率=("Churn", "mean"),
        平均订单=("OrderCount", "mean"),
        平均优惠券=("CouponUsed", "mean"),
        平均返现=("CashbackAmount", "mean"),
    )
    .reset_index()
.sort_values(by=["流失率", "用户数"], ascending=[False, False])
)
category_analysis["用户占比"] = category_analysis["用户数"] / len(df)
display(category_analysis)
print("-"*40)

# 支付方式
payment_analysis = (
    df.groupby("PreferredPaymentMode")
    .agg(
        用户数=("CustomerID", "nunique"),
        流失率=("Churn", "mean"),
        平均订单=("OrderCount", "mean"),
        平均优惠券=("CouponUsed", "mean"),
        平均返现=("CashbackAmount", "mean"),
    )
    .reset_index()
    .sort_values("用户数", ascending=False)
)
display(payment_analysis)
print("-"*40)

# 流失/未流失用户行为对比
churn_behavior = (
    df.groupby("Churn")
    .agg(
        用户数=("CustomerID", "nunique"),
        平均订单=("OrderCount", "mean"),
        平均优惠券=("CouponUsed", "mean"),
        平均返现=("CashbackAmount", "mean"),
        平均APP时长=("HourSpendOnApp", "mean"),
        平均满意度=("SatisfactionScore", "mean"),
        平均间隔天数=("DaySinceLastOrder", "mean"),
    )
    .reset_index()
)
churn_behavior["用户状态"] = churn_behavior["Churn"].map({0: "未流失", 1: "已流失"})
display(churn_behavior.drop(columns="Churn"))
print("="*60)

# --------------------------6. 生命周期 × 投诉交叉透视--------------------------
tenure_complain = (
    df.groupby(["TenureGroup", "Complain"], observed=True)
    .agg(
        用户数=("CustomerID", "nunique"),
        流失人数=("Churn", "sum"),
        流失率=("Churn", "mean"),
        平均订单=("OrderCount", "mean"),
    )
    .reset_index()
)
tenure_complain["投诉状态"] = tenure_complain["Complain"].map({0: "无投诉", 1: "有投诉"})
tenure_complain["样本提示"] = np.where(tenure_complain["用户数"] < 30, "小样本", "正常样本")
display(tenure_complain)

# 透视表
count_pivot = pd.pivot_table(
    df, index="Tenure", columns="Complain", values="CustomerID", aggfunc="nunique", fill_value=0
).rename(columns={0: "无投诉用户", 1: "有投诉用户"})

churn_pivot = pd.pivot_table(
    df, index="Tenure", columns="Complain", values="Churn", aggfunc="mean"
).rename(columns={0: "无投诉流失率", 1: "有投诉流失率"})

cross_table = count_pivot.join(churn_pivot).reset_index()
display(cross_table)
print("="*60)

# --------------------------7. 全部报表导出CSV--------------------------
output_files = {
    "整体指标.csv": overall_metrics,
    "生命周期分析.csv": tenure_analysis,
    "投诉对比.csv": complain_analysis,
    "商品品类分析.csv": category_analysis,
    "支付渠道分析.csv": payment_analysis,
    "流失行为对比.csv": churn_behavior,
    "生命周期投诉交叉表.csv": tenure_complain,
    "透视汇总表.csv": cross_table
}

for name, data in output_files.items():
    save_path = OUTPUT_DIR / name
    data.to_csv(save_path, index=False, encoding="utf-8-sig")
    print(f"已导出：{save_path}")

print("\n🎉 全部分析报表生成完毕！")

# --------------------------8. 作业结论（直接复制提交）--------------------------
"""
1. 流失率计算公式：流失用户数量 / 全部独立用户；分子Churn=1，分母全部用户。
2. 核心发现：有投诉用户流失率远高于无投诉用户，售后体验是流失关键因素。
3. 规范表述：样本显示投诉行为与高流失存在强关联，但不能直接判定投诉一定会流失，需结合订单、满意度进一步验证。
4. 无法计算GMV、月度趋势：数据集没有订单金额、交易时间字段，仅用户静态画像。

整体总结：
新用户、有投诉、低满意度人群流失风险最高；平台可针对投诉用户跟进售后、给新用户发放优惠券留存。
"""