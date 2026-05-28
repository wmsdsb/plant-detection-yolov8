"""将 data.yaml 中的相对路径替换为绝对路径，适配云平台。

用法：
    python prepare_data_yaml.py --input data.yaml --output data_fixed.yaml
"""

import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="修复 data.yaml 路径")
    parser.add_argument("--input", type=str, required=True, help="原始 data.yaml 路径")
    parser.add_argument("--output", type=str, required=True, help="输出 data.yaml 路径")
    args = parser.parse_args()

    input_path = Path(args.input)
    dataset_dir = input_path.parent.resolve()

    lines = input_path.read_text(encoding="utf-8").splitlines()
    fixed = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(("train:", "val:", "test:")) and "../" in stripped:
            key = stripped.split(":")[0]
            rel_path = stripped.split(":", 1)[1].strip()
            abs_path = (dataset_dir / rel_path).resolve()
            fixed.append(f"{key}: {abs_path}")
        else:
            fixed.append(line)

    Path(args.output).write_text("\n".join(fixed), encoding="utf-8")
    print(f"已生成: {args.output}")

if __name__ == "__main__":
    main()
