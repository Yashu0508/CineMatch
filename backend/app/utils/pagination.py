from fastapi import Query


def pagination(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)) -> tuple[int, int]:
    return page, page_size


def page_payload(items: list, page: int, page_size: int, total: int) -> dict:
    return {"items": items, "page": page, "total": total, "total_pages": max(1, (total + page_size - 1) // page_size)}
