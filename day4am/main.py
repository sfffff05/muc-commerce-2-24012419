import pandas as pd
import numpy as np

# ==========修正读取Excel==========
df = pd.read_excel("E Commerce Dataset (1).xlsx", sheet_name="E Comm", header=0)
print("===== 原始数据信息 =====")
print(f"数据总行数：{df.shape[0]}，总列数：{df.shape[1]}")
print("字段列表：")
print(df.columns.tolist())
print("\n缺失值统计：")
print(df.isnull().sum())

# ========== 题目指定的需要中位数填充的字段 ==========
numeric_missing_cols = [
    "Tenure",
    "WarehouseToHome",
    "HourSpendOnApp",
    "OrderAmountHikeFromlastYear",
    "CouponUsed",
    "OrderCount",
    "DaySinceLastOrder",
]
# 循环中位数填充
for col in numeric_missing_cols:
    median_val = df[col].median()
    df[col].fillna(median_val, inplace=True)

print("\n===== 填充后缺失值检查 =====")
print(df[numeric_missing_cols].isna().sum())

# ========== 重复值检查 ==========
dup_row = df.duplicated().sum()
print(f"\n完全重复行数：{dup_row}")
dup_id = df["CustomerID"].duplicated().sum()
print(f"CustomerID重复数量：{dup_id}")

# ==========类别字段统一==========
df["PreferredLoginDevice"] = df["PreferredLoginDevice"].replace(["Phone", "Mobile"], "Mobile Phone")
df["PreferredPaymentMode"] = df["PreferredPaymentMode"].replace("COD", "Cash on Delivery")
df["PreferredPaymentMode"] = df["PreferredPaymentMode"].replace("CC", "Credit Card")

print("\n=====标准化之后类别取值=====")
print(df["PreferredLoginDevice"].value_counts())
print(df["PreferredPaymentMode"].value_counts())

# ========== IQR异常值函数 ==========
def detect_iqr(data, col):
    Q1 = data[col].quantile(0.25)
    Q3 = data[col].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    outlier = data[(data[col] < lower) | (data[col] > upper)]
    return len(outlier), outlier

check_cols = ["WarehouseToHome", "OrderCount", "CashbackAmount"]
print("\n===== IQR候选异常值检测 =====")
for c in check_cols:
    cnt, _ = detect_iqr(df, c)
    print(f"{c} 异常值数量：{cnt}")

# ==========业务规则校验==========
rules = {
    "使用时长小于0": len(df[df["HourSpendOnApp"] < 0]),
    "仓库距离小于0": len(df[df["WarehouseToHome"] < 0]),
    "订单数小于等于0": len(df[df["OrderCount"] <= 0]),
    "返现金额小于0": len(df[df["CashbackAmount"] < 0])
}
print("\n=====不符合业务规则的数据条数 =====")
for name, num in rules.items():
    print(f"{name}：{num}")

# ==========导出清洗后的数据==========
df.to_csv("ecommerce_clean.csv", index=False, encoding="utf-8-sig")
print("\n数据清洗完成！已生成 ecommerce_clean.csv")