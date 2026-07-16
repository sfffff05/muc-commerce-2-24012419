from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd

# 显示设置
pd.set_option("display.max_columns", None)
pd.set_option("display.float_format", lambda x: f"{x:.2f}")

# 读取你的Excel文件
DATA_PATH = Path("E Commerce Dataset (1).xlsx")
if not DATA_PATH.exists():
    raise FileNotFoundError("未找到 E Commerce Dataset (1).xlsx，请确保文件和代码在同一文件夹")

# 输出文件夹
OUTPUT_DIR = Path("output") / "day04_project"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 读取原始数据
raw_df = pd.read_excel(DATA_PATH, sheet_name="E Comm")
print(f"原始数据路径: {DATA_PATH}")
print(f"项目输出目录: {OUTPUT_DIR}")
print(f"原始数据形状: {raw_df.shape}")
print("="*50)

# --------------------------任务1简答题答案--------------------------
"""
任务1 答案：
1. 每条记录代表一位电商平台独立用户的全量行为画像。
2. 目标变量是 Churn（用户是否流失）。
3. CustomerID 是用户唯一标识ID，仅用于区分用户，无数值大小意义；不能做加减、分组填充等数值运算，作为连续数值会误导模型。
"""

# --------------------------2. 构建数据质量报告函数（已修复round错误）--------------------------
def build_quality_report(data):
    """返回字段级数据质量报告。"""
    report = pd.DataFrame()
    report["字段名"] = data.columns
    report["数据类型"] = [str(data[col].dtype) for col in data.columns]
    report["缺失数量"] = [data[col].isna().sum() for col in data.columns]
    # 修复：对每个数值单独round，不直接对列表round
    report["缺失比例(%)"] = [round(data[col].isna().mean() * 100, 2) for col in data.columns]
    report["唯一值数量"] = [data[col].nunique() for col in data.columns]
    return report

# 生成清洗前质量报告
quality_before = build_quality_report(raw_df)
print("【清洗前数据质量报告】")
print(quality_before)
print("="*50)

# --------------------------任务2：初始审计（已修正列名）--------------------------
# 1. 完全重复行数
dup_count = raw_df.duplicated().sum()
print("完全重复行数: ", dup_count)

# 2. CustomerID重复数量
cid_dup = raw_df["CustomerID"].duplicated().sum()
print("CustomerID 重复数量: ", cid_dup)

# 3. Churn频数、流失率
print("\nChurn分布：")
print(raw_df["Churn"].value_counts())
churn_rate = raw_df["Churn"].mean()
print("流失率: ", round(churn_rate, 4))

# 4. 分类字段频数（全部修正为真实列名）
cat_cols = ["PreferredLoginDevice", "PreferredPaymentMode", "PreferedOrderCat"]
for col in cat_cols:
    print(f"\n===== {col} 分布 =====")
    print(raw_df[col].value_counts())
print("="*50)

# --------------------------3. 清洗规则常量定义（已修正列名）--------------------------
# 需要中位数填充的数值列
NUMERIC_MISSING_COLS = [
    "Tenure",
    "WarehouseToHome",
    "HourSpendOnApp",
    "OrderAmountHikeFromlastYear",
    "CouponUsed",
    "OrderCount",
    "DaySinceLastOrder",
]

# 类别标准化映射（已修正列名）
CATEGORY_MAPPINGS = {
    "PreferredLoginDevice": {
        "Phone": "Mobile Phone"
    },
    "PreferredPaymentMode": {
        "COD": "Cash on Delivery",
        "CC": "Credit Card"
    },
    "PreferedOrderCat": {
        "Mobile": "Mobile Phone"
    }
}

# --------------------------4. 清洗主函数--------------------------
def clean_ecommerce_data(data):
    df = data.copy()
    log_list = []
    total_before = df.shape[0]

    # 1 删除完全重复行
    dup_rows = df.duplicated().sum()
    df = df.drop_duplicates()
    log_list.append({
        "处理步骤": "删除完全重复记录",
        "处理规则": "去除全行完全重复数据",
        "处理前记录数": total_before,
        "处理后记录数": df.shape[0],
        "影响记录数": dup_rows
    })

    # 2 数值中位数填充
    for col in NUMERIC_MISSING_COLS:
        miss_num = df[col].isna().sum()
        median_val = df[col].median()
        df[col] = df[col].fillna(median_val)
        log_list.append({
            "处理步骤": f"数值列{col}缺失填充",
            "处理规则": "中位数填充，不使用0填充",
            "处理前记录数": df.shape[0],
            "处理后记录数": df.shape[0],
            "影响记录数": miss_num
        })

    # 3 类别统一映射
    for col, mapping_dict in CATEGORY_MAPPINGS.items():
        change_cnt = sum([(df[col] == k).sum() for k in mapping_dict.keys()])
        df[col] = df[col].replace(mapping_dict)
        log_list.append({
            "处理步骤": f"类别标准化 {col}",
            "处理规则": f"映射规则{mapping_dict}",
            "处理前记录数": df.shape[0],
            "处理后记录数": df.shape[0],
            "影响记录数": change_cnt
        })

    # 4 转整数
    df["Churn"] = df["Churn"].astype(int)
    df["Complain"] = df["Complain"].astype(int)
    log_list.append({
        "处理步骤": "Churn、Complain转为整数",
        "处理规则": "标签转0/1整数",
        "处理前记录数": df.shape[0],
        "处理后记录数": df.shape[0],
        "影响记录数": 0
    })

    cleaning_log = pd.DataFrame(log_list)
    return df, cleaning_log

# 执行清洗
cleaned_df, cleaning_log = clean_ecommerce_data(raw_df)
print("【数据处理日志】")
print(cleaning_log)
print("="*50)

# --------------------------5. IQR异常值 + 衍生字段--------------------------
def iqr_outlier_summary(series):
    s = series.dropna()
    q1 = s.quantile(0.25)
    q3 = s.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    outlier_num = int(((s < lower) | (s > upper)).sum())
    return {
        "Q1": q1,
        "Q3": q3,
        "IQR": iqr,
        "下限": lower,
        "上限": upper,
        "候选异常值数量": outlier_num
    }

# 分层字段 TenureGroup
tenure_bins = [0, 10, 20, 30, 60, 100]
tenure_labels = ["0-10月", "10-20月", "20-30月", "30-60月", "60月以上"]
cleaned_df["TenureGroup"] = pd.cut(cleaned_df["Tenure"], bins=tenure_bins, labels=tenure_labels)

# 移动端标识
cleaned_df["IsMobileLogin"] = np.where(cleaned_df["PreferredLoginDevice"] == "Mobile Phone", 1, 0)

# 异常值报告
outlier_cols = ["WarehouseToHome", "OrderCount", "CashbackAmount"]
outlier_report = []
for col in outlier_cols:
    res = iqr_outlier_summary(cleaned_df[col])
    res["检查字段"] = col
    outlier_report.append(res)
outlier_report = pd.DataFrame(outlier_report)
print("【IQR候选异常值报告】")
print(outlier_report)
print("="*50)

# --------------------------任务4 业务规则检查--------------------------
rule1 = (cleaned_df["Tenure"] < 0).sum()
rule2 = (cleaned_df["WarehouseToHome"] < 0).sum()
rule3 = (cleaned_df["OrderCount"] <= 0).sum()
rule4 = (cleaned_df["CashbackAmount"] < 0).sum()

business_rule_report = pd.DataFrame({
    "规则": [
        "使用时长Tenure小于0",
        "仓库距离WarehouseToHome小于0",
        "订单数量OrderCount<=0",
        "返现CashbackAmount小于0"
    ],
    "不合规记录数": [rule1, rule2, rule3, rule4]
})
print("【业务不合规数据统计】")
print(business_rule_report)
"""
处理结论：
业务负数值属于脏数据，本项目规则要求不直接删除，仅记录留待业务人员复核；所有异常行全部保留在清洗后数据集，标注在报告中，交由业务确认是否剔除。
"""
print("="*50)

# --------------------------6. 导出全部交付文件--------------------------
quality_after = build_quality_report(cleaned_df)
print("【清洗后数据质量报告】")
print(quality_after)

# 校验断言
assert cleaned_df[NUMERIC_MISSING_COLS].isna().sum().sum() == 0
assert "Phone" not in cleaned_df["PreferredLoginDevice"].unique()
assert "COD" not in cleaned_df["PreferredPaymentMode"].unique()
assert "CC" not in cleaned_df["PreferredPaymentMode"].unique()
assert {"TenureGroup", "IsMobileLogin"}.issubset(cleaned_df.columns)

# 全部导出 utf-8-sig编码
quality_before.to_csv(OUTPUT_DIR / "data_quality_before.csv", index=True, encoding="utf-8-sig")
quality_after.to_csv(OUTPUT_DIR / "data_quality_after.csv", index=True, encoding="utf-8-sig")
cleaning_log.to_csv(OUTPUT_DIR / "cleaning_log.csv", index=False, encoding="utf-8-sig")
cleaned_df.to_csv(OUTPUT_DIR / "ecommerce_customer_cleaned.csv", index=False, encoding="utf-8-sig")
outlier_report.to_csv(OUTPUT_DIR / "outlier_report.csv", index=False, encoding="utf-8-sig")
business_rule_report.to_csv(OUTPUT_DIR / "business_rule_report.csv", index=False, encoding="utf-8-sig")

print("\n=== 所有交付文件已生成至 output/day04_project ===")
for f in OUTPUT_DIR.glob("*.csv"):
    print(f)

# --------------------------项目复盘--------------------------
"""
项目复盘（200字内）
1. 发现问题：数值字段缺失、类别名称不统一、完全重复记录、业务负数值、IQR极端异常值。
2. 处理策略：缺失值用总体中位数填充；统一类别文本；重复记录直接删除；异常值仅记录，不自动剔除。
3. 清洗后无缺失、分类标准化、新增分层特征，字段完整合规，可直接用于第五天流失建模分析。
4. 仓库距离、订单数负数值、IQR极端异常样本，需要业务人员复核确认是否剔除。
"""