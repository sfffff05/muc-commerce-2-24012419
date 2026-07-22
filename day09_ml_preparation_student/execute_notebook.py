"""
执行第9天 Notebook，生成 output/ 下的 4 个 CSV 文件。
用法：python execute_notebook.py
"""
import subprocess
import sys
from pathlib import Path

NB_PATH = Path(__file__).resolve().parent / "notebooks/day09_ml_preparation_student.ipynb"
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# 清理旧输出
for f in OUTPUT_DIR.glob("*.csv"):
    f.unlink()

print(f"执行 Notebook: {NB_PATH}")
result = subprocess.run(
    [
        sys.executable, "-m", "jupyter", "nbconvert",
        "--to", "notebook",
        "--execute",
        "--output", str(NB_PATH),
        "--ExecutePreprocessor.timeout=120",
        str(NB_PATH),
    ],
    capture_output=True,
    text=True,
    cwd=str(NB_PATH.parent.parent),
)

if result.returncode != 0:
    print("STDERR:", result.stderr)
    print("STDOUT:", result.stdout)
    raise SystemExit(f"Notebook 执行失败，退出码: {result.returncode}")

# 验证输出文件
required = {"feature_schema.csv", "split_summary.csv", "model_matrix_preview.csv", "baseline_metrics.csv"}
actual = {p.name for p in OUTPUT_DIR.glob("*.csv")}
print(f"生成文件: {sorted(actual)}")

missing = required - actual
if missing:
    raise SystemExit(f"缺少输出文件: {missing}")

print("全部 4 个输出文件生成成功！")
