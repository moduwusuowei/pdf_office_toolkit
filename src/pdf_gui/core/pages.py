"""页码子集解析：all / last / "1,3,5"。"""


def parse_page_spec(spec: str, total: int) -> list[int]:
    """返回 0 起页索引列表；非法输入抛 ValueError。"""
    spec = spec.strip().lower()
    if spec in ("", "all"):
        return list(range(total))
    if spec == "last":
        return [total - 1]
    result = []
    for part in spec.replace("，", ",").split(","):
        part = part.strip()
        if not part:
            continue
        try:
            n = int(part)
        except ValueError:
            raise ValueError(f"无效页码: {part}") from None
        if n < 1 or n > total:
            raise ValueError(f"页码超出范围: {part}（共 {total} 页）")
        result.append(n - 1)
    return result
