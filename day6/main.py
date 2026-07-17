# -*- coding: utf-8 -*-
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings("ignore")

# 解决中文显示
plt.rcParams["font.sans-serif"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False
plt.switch_backend("Agg")  # 避免PyCharm绘图弹窗卡死

# ===================== 1 读取数据 =====================
df = pd.read_csv("ecommerce_clean.csv")
df_complain = pd.read_csv("投诉对比.csv")

# 缺失值填充
df["Tenure"] = df["Tenure"].fillna(0)
df["HourSpendOnApp"] = df["HourSpendOnApp"].fillna(df["HourSpendOnApp"].mean())

# 生命周期分段函数
def get_stage(x):
    if x == 0:
        return "新用户(0月)"
    elif 0 < x <= 6:
        return "0-6个月"
    elif 6 < x <= 12:
        return "7-12个月"
    elif 12 < x <= 24:
        return "13-24个月"
    else:
        return "24个月以上"

df["生命周期"] = df["Tenure"].apply(get_stage)

# ===================== 2 图1：生命周期流失率柱状图 =====================
stage_data = df.groupby("生命周期")["Churn"].mean().reset_index()
stage_data["流失率(%)"] = stage_data["Churn"] * 100

plt.figure(figsize=(10, 6))
sns.barplot(data=stage_data, x="生命周期", y="流失率(%)", color="#ff6b6b")
plt.title("各生命周期用户流失率对比", fontsize=14)
plt.xlabel("用户生命周期")
plt.ylabel("流失率(%)")
plt.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig("1_生命周期流失柱状图.png", dpi=300)
plt.close()

# ===================== 3 图2：订单&返现散点图 =====================
plt.figure(figsize=(10, 6))
sns.scatterplot(data=df, x="OrderCount", y="CashbackAmount", hue="Churn",
                alpha=0.6, palette=["#2ec7c9", "#ff4d4f"])
plt.title("年度订单数与返现金额分布（蓝=留存，红=流失）", fontsize=14)
plt.xlabel("年度订单数量")
plt.ylabel("返现金额")
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("2_订单返现散点图.png", dpi=300)
plt.close()

# ===================== 4 图3：时长+投诉流失折线图 =====================
tenure_com = df.groupby(["Tenure", "Complain"])["Churn"].mean().reset_index()
tenure_com["流失率(%)"] = tenure_com["Churn"] * 100

plt.figure(figsize=(11, 6))
sns.lineplot(data=tenure_com, x="Tenure", y="流失率(%)", hue="Complain", marker="o")
plt.legend(["无投诉", "有投诉"])
plt.title("用户使用时长与投诉流失趋势", fontsize=14)
plt.xlabel("注册时长（月）")
plt.ylabel("流失率(%)")
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("3_投诉流失折线图.png", dpi=300)
plt.close()

# ===================== 5 图4：商品品类环形图 =====================
cat_data = df["PreferedOrderCat"].value_counts()
fig, ax = plt.subplots(figsize=(8, 8))
wedges, texts, autotexts = ax.pie(
    cat_data, labels=cat_data.index, autopct="%1.1f%%",
    wedgeprops={"width": 0.3}, startangle=90
)
plt.title("用户首选商品品类占比环形图", fontsize=14)
plt.tight_layout()
plt.savefig("4_商品品类环形图.png", dpi=300)
plt.close()

# ===================== 6 2×2综合总图 =====================
fig_all, axes = plt.subplots(2, 2, figsize=(16, 12))
axes = axes.flatten()

# 子图1 柱状图
ax1 = axes[0]
sns.barplot(data=stage_data, x="生命周期", y="流失率(%)", color="#ff6b6b", ax=ax1)
ax1.set_title("各生命周期流失率")
ax1.set_xlabel("")

# 子图2 散点图
ax2 = axes[1]
sns.scatterplot(data=df, x="OrderCount", y="CashbackAmount", hue="Churn",
                alpha=0.6, palette=["#2ec7c9", "#ff4d4f"], ax=ax2)
ax2.set_title("订单-返现分布")
ax2.legend([], [], frameon=False)

# 子图3 折线图
ax3 = axes[2]
sns.lineplot(data=tenure_com, x="Tenure", y="流失率(%)", hue="Complain", marker="o", ax=ax3)
ax3.set_title("时长&投诉流失趋势")
ax3.legend(["无投诉", ""])

# 子图4 环形图
ax4 = axes[3]
wedges4, _, _ = ax4.pie(cat_data, autopct="%1.1f%%", wedgeprops={"width":0.3})
ax4.set_title("商品品类占比")

plt.suptitle("电商用户流失综合分析看板", fontsize=18, y=0.98)
plt.tight_layout()
plt.savefig("2x2综合总图.png", dpi=300)
plt.close()

# ===================== 7 生成图表清单chart_manifest.csv =====================
manifest = pd.DataFrame([
    {
        "图表文件名": "1_生命周期流失柱状图.png",
        "图表类型": "柱状图",
        "业务问题": "用户在哪个生命周期阶段流失风险最高？",
        "选用理由": "分类对比，直观展示不同生命周期流失率高低",
        "核心字段": "生命周期, Churn"
    },
    {
        "图表文件名": "2_订单返现散点图.png",
        "图表类型": "散点图",
        "业务问题": "消费频次与返现是否相关，高返现能否减少流失？",
        "选用理由": "展示两个连续变量关联，区分流失/留存群体",
        "核心字段": "OrderCount, CashbackAmount, Churn"
    },
    {
        "图表文件名": "3_投诉流失折线图.png",
        "图表类型": "折线图",
        "业务问题": "随使用时长增加，投诉对流失的影响如何变化？",
        "选用理由": "时间趋势对比，清晰看出有无投诉流失差距",
        "核心字段": "Tenure, Complain, Churn"
    },
    {
        "图表文件名": "4_商品品类环形图.png",
        "图表类型": "环形饼图",
        "业务问题": "平台用户偏好品类分布如何？",
        "选用理由": "直观展示各品类用户占比结构",
        "核心字段": "PreferedOrderCat"
    },
    {
        "图表文件名": "2x2综合总图.png",
        "图表类型": "组合看板",
        "业务问题": "多维度整体流失情况一览",
        "选用理由": "四张核心图整合，方便整体汇报",
        "核心字段": "全部核心字段"
    }
])
manifest.to_csv("chart_manifest.csv", index=False, encoding="utf-8-sig")

print("全部图表与清单生成完成！")
