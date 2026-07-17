# -*- coding: utf-8 -*-
import pandas as pd

# 读取数据
df = pd.read_excel('淘宝全品类全国数据.xlsx')

# ========== 任务1 ==========
print("数据形状:", df.shape)
print("列名:", df.columns.tolist())
print(df.head(5))
df.info()

# ========== 任务2 ==========
print(df.dtypes)
print(df.isna().sum().sort_values(ascending=False))

# ========== 任务3 ==========
price_series = df["商品价格"]  # Series
product_view = df[["商品id", "一级品类", "商品价格", "省份", "商品销量"]]
print(df.loc[0:4, ["商品id", "一级品类", "商品价格"]])
print(df.iloc[0:5, [0, 1, 4]])

# ========== 任务4 ==========
guangdong = df[df["省份"] == "广东"]
guangdong_high = df[(df["省份"] == "广东") & (df["商品价格"] >= 1000)]
result = guangdong_high[["商品id", "一级品类", "二级品类", "商品价格", "省份", "商品销量"]]
print(result.sort_values("商品价格", ascending=False).head(10))

zj_js = df[df["省份"].isin(["浙江", "江苏"])]
print("浙江江苏总数:", len(zj_js))

# ========== 任务5 ==========
print(df["商品价格"].describe().round(2))
print(df["一级品类"].value_counts())

category_summary = df.groupby("一级品类").agg(
    商品数=("商品id", "count"),
    平均价格=("商品价格", "mean"),
    中位价格=("商品价格", "median")
).round(2).sort_values("平均价格", ascending=False)
print(category_summary)

# ========== 挑战任务 ==========
two_provinces = df[df["省份"].isin(["广东", "江苏"])]
province_summary = two_provinces.groupby("省份").agg(
    商品数=("商品id", "count"),
    平均价格=("商品价格", "mean"),
    中位价格=("商品价格", "median")
).round(2)
print(province_summary)
print("广东TOP3品类:", df[df["省份"] == "广东"]["一级品类"].value_counts().head(3))
print("江苏TOP3品类:", df[df["省份"] == "江苏"]["一级品类"].value_counts().head(3))