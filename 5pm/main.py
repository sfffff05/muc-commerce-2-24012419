from pathlib import Path
import pandas as pd
import numpy as np

try:
    from IPython.display import display
except ImportError:
    def display(obj):
        print(obj)

# ===================== TODO 填写个人信息与专题 =====================
STUDENT_NAME = "李清如"
TOPIC = "A"
# ==================================================================

pd.set_option("display.max_columns", 50)
pd.set_option("display.float_format", lambda x: f"{x:.2f}")

def find_workspace_root(start=None):
    start = Path.cwd() if start is None else Path(start)
    for candidate in [start, *start.parents]:
        data_path = candidate / "ecommerce_customer_cleaned (1).csv"
        if data_path.exists():
            return candidate
    raise FileNotFoundError("请把 ecommerce_customer_cleaned (1).csv 和代码放在同一文件夹")

ROOT = find_workspace_root()
DATA_PATH = ROOT / "ecommerce_customer_cleaned (1).csv"
OUTPUT_DIR = ROOT / "output" / "day05_analysis"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("姓名：", STUDENT_NAME)
print("专题：", TOPIC)
print("输入数据：", DATA_PATH)
print("输出目录：", OUTPUT_DIR)

# 检查点0校验
assert STUDENT_NAME != "请填写姓名", "请填写STUDENT_NAME"
assert STUDENT_NAME.strip(), "姓名不能为空"
TOPIC = TOPIC.strip().upper()
assert TOPIC in {"A", "B", "C", "D", "E"}, "TOPIC只能填写A、B、C、D或E"
expected_output_dir = ROOT / "output" / "day05_analysis"
assert OUTPUT_DIR == expected_output_dir

print("检查点0通过")
print("姓名：", STUDENT_NAME)
print("专题：", TOPIC)

# ===================== 任务1：读取并验收数据 =====================
df = pd.read_csv(DATA_PATH)
print("数据形状：", df.shape)
display(df.head())
print("\n字段类型：")
display(df.dtypes.to_frame("数据类型"))

core_cols = [
    "CustomerID",
    "Churn",
    "TenureGroup",
    "OrderCount",
    "CouponUsed",
    "CashbackAmount",
    "DaySinceLastOrder",
    "SatisfactionScore",
    "HourSpendOnApp",
    "Complain",
    "PreferedOrderCat"
]

row_cnt = df.shape[0]
col_cnt = df.shape[1]
customer_dup = df["CustomerID"].duplicated().sum()
missing_core = df[core_cols].isna().sum().sum()
churn_unique = sorted(df["Churn"].unique())

validation = pd.DataFrame([
    ["总行数", row_cnt],
    ["总列数", col_cnt],
    ["CustomerID重复行数", customer_dup],
    ["核心字段缺失总数", missing_core],
    ["Churn唯一取值", str(churn_unique)]
], columns=["验收项", "数值"])

display(validation)

# 检查点1校验
assert isinstance(df, pd.DataFrame), "df还不是DataFrame"
assert df.shape == (5630, 22), "数据形状应为(5630, 22)"
assert df["CustomerID"].is_unique, "CustomerID应保持唯一"
assert set(df["Churn"].unique()) == {0, 1}, "Churn只包含0和1"

required_core_cols = {
    "CustomerID",
    "Churn",
    "TenureGroup",
    "OrderCount",
    "CouponUsed",
    "CashbackAmount",
    "DaySinceLastOrder",
    "HourSpendOnApp",
    "SatisfactionScore",
    "Complain",
    "PreferedOrderCat"
}
assert required_core_cols.issubset(set(core_cols)), f"core_cols缺少字段：{required_core_cols - set(core_cols)}"
assert df[core_cols].notna().all().all(), "核心分析字段仍存在缺失值"
assert validation is not None, "请完成validation验收表"

print("检查点1通过")

"""
1. 一行数据代表什么：一条记录对应平台一位独立用户的全量行为画像，粒度为用户级，非订单级。
2. CustomerID不能求平均：Customer是用户唯一编码，仅用于标识用户，无数值大小含义，计算均值无业务意义。
"""

# ===================== 任务2：公共基础指标 =====================
total_user = len(df)
churn_user = df["Churn"].sum()
overall_churn_rate = churn_user / total_user
avg_order = df["OrderCount"].mean()
med_order = df["OrderCount"].median()
avg_coupon = df["CouponUsed"].mean()
avg_cashback = df["CashbackAmount"].mean()
avg_apptime = df["HourSpendOnApp"].mean()
avg_satis = df["SatisfactionScore"].mean()
avg_lastday = df["DaySinceLastOrder"].mean()

metric_data = [
    ["用户总数", total_user],
    ["流失用户数", churn_user],
    ["总体流失率", overall_churn_rate],
    ["平均订单数", avg_order],
    ["订单数中位数", med_order],
    ["平均优惠券使用次数", avg_coupon],
    ["平均返现金额", avg_cashback],
    ["平均App使用时长", avg_apptime],
    ["平均满意度", avg_satis],
    ["平均距上次下单天数", avg_lastday]
]
overall_metrics = pd.DataFrame(metric_data, columns=["指标", "数值"])

display(overall_metrics)

# 检查点2校验
assert isinstance(overall_metrics, pd.DataFrame), "overall_metrics应为DataFrame"
assert len(overall_metrics) >= 10
assert abs(overall_churn_rate - 0.16838365896980462) < 1e-8
print("检查点2通过")

"""
公共指标初步观察：样本共5630名用户，整体流失率约16.84%，用户平均下单量偏低，复购意愿一般。
"""

# ===================== 任务3：单维专题A 生命周期 =====================
topic_fields = {
    "A": {"TenureGroup"},
    "B": {"Complain", "SatisfactionScore"},
    "C": {"PreferedOrderCat"},
    "D": {"PreferredPaymentMode"},
    "E": {"CityTier", "PreferredLoginDevice"},
}
print("当前专题：", TOPIC)
print("可选主分组字段：", topic_fields[TOPIC])

segment_field = "TenureGroup"

segment_analysis = df.groupby(segment_field).agg(
    用户数=("CustomerID", "count"),
    流失人数=("Churn", "sum"),
    流失率=("Churn", "mean"),
    平均订单数=("OrderCount", "mean"),
    平均满意度=("SatisfactionScore", "mean"),
    平均距上次下单天数=("DaySinceLastOrder", "mean")
).reset_index()

# 生命周期排序
tenure_sort_map = {"新用户":0, "0-6个月":1, "7-12个月":2, "13-24个月":3, "24个月以上":4}
segment_analysis["sort_key"] = segment_analysis["TenureGroup"].map(tenure_sort_map)
segment_analysis = segment_analysis.sort_values("sort_key").drop("sort_key", axis=1)
display(segment_analysis)

# 检查点3校验
assert segment_field in df.columns
assert segment_field in topic_fields[TOPIC]
assert isinstance(segment_analysis, pd.DataFrame)
assert "用户数" in segment_analysis.columns
assert segment_analysis["用户数"].sum() == len(df)
print("检查点3通过")

"""
1. 业务问题：不同生命周期分层用户在流失、订单、满意度上有哪些差异？
2. 现象：新用户、0-6个月用户流失率远高于老用户，24个月以上用户流失最低；用户周期越长满意度越高。
3. 解释：新用户对平台信任不足，容易流失；长期用户养成消费习惯，留存更好。
"""

# ===================== 任务4：双维度交叉 生命周期+投诉 =====================
allowed_cross_fields = {
    "TenureGroup",
    "Complain",
    "PreferedOrderCat",
    "CityTier",
    "PreferredLoginDevice",
}

dim_1 = "TenureGroup"
dim_2 = "Complain"

cross_analysis = df.groupby([dim_1, dim_2]).agg(
    用户数=("CustomerID", "count"),
    流失人数=("Churn", "sum"),
    流失率=("Churn", "mean"),
    平均满意度=("SatisfactionScore", "mean")
).reset_index()

cross_analysis["样本提示"] = np.where(cross_analysis["用户数"] < 30, "小样本", "可观察")
cross_analysis = cross_analysis.sort_values("流失率", ascending=False)
display(cross_analysis)

# 检查点4校验
assert dim_1 in allowed_cross_fields and dim_2 in allowed_cross_fields
assert dim_1 != dim_2
assert isinstance(cross_analysis, pd.DataFrame)
assert cross_analysis["用户数"].sum() == len(df)
print("检查点4通过")

"""
1. 重点组合：0-6个月+有投诉用户
2. 对比：该群体流失率近38%，同周期无投诉仅18%，差距极大
3. 样本充足，无小样本风险
4. 仅为相关性，不能判定投诉直接导致流失，存在其他干扰因素
"""

# ===================== 任务5 导出报表 =====================
outputs = {
    "overall_metrics.csv": overall_metrics,
    "segment_analysis.csv": segment_analysis,
    "cross_analysis.csv": cross_analysis,
}
for filename, table in outputs.items():
    path = OUTPUT_DIR / filename
    table.to_csv(path, index=False, encoding="utf-8-sig")
    print("已输出：", path.relative_to(ROOT))

# 校验导出文件
for filename, table in outputs.items():
    path = OUTPUT_DIR / filename
    assert path.exists()
    reloaded = pd.read_csv(path)
    assert reloaded.shape == table.shape
print("检查点5通过")

# ===================== 任务6 完整分析结论 =====================
"""
### 核心结论
1. 0-6个月新用户流失率24.14%，远高于整体16.84%（segment_analysis.csv）
2. 同生命周期内，有投诉用户流失率几乎是无投诉用户两倍（cross_analysis.csv）
3. 用户使用周期越长，平均满意度持续提升，老用户留存更好

### 分析局限
仅静态快照数据，无时间序列订单、消费金额，无法追踪流失前行为；缺少售后处理信息。

### 运营建议
针对新投诉用户做客服回访+优惠券留存；后续增加时序数据，用A/B测试验证留存效果。

### 反思5问
1. 最重要发现：新用户+投诉双重人群是核心流失群体
2. 数据验收检查点最容易提前发现脏数据
3. 投诉与流失仅相关，不能直接说因果，极易误读
4. 希望新增订单GMV字段，分层消费能力
5. 生命周期表做成折线图，直观展示流失随周期变化
"""