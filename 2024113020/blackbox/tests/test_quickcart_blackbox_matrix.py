"""Large black-box matrix tests for QuickCart API header and scope contracts."""

from __future__ import annotations

import pytest


# (method, path, json_body, user_scoped)
ENDPOINT_CASES = [
    ("GET", "/api/v1/profile", None, True),
    ("PUT", "/api/v1/profile", {"name": "User Name", "phone": "9999999999"}, True),
    ("GET", "/api/v1/addresses", None, True),
    (
        "POST",
        "/api/v1/addresses",
        {
            "label": "HOME",
            "street": "Some Street Name 12",
            "city": "Hyderabad",
            "pincode": "500001",
            "is_default": False,
        },
        True,
    ),
    ("PUT", "/api/v1/addresses/1", {"street": "Updated Street 45", "is_default": False}, True),
    ("DELETE", "/api/v1/addresses/1", None, True),
    ("GET", "/api/v1/products", None, True),
    ("GET", "/api/v1/products/1", None, True),
    ("GET", "/api/v1/cart", None, True),
    ("POST", "/api/v1/cart/add", {"product_id": 1, "quantity": 1}, True),
    ("POST", "/api/v1/cart/update", {"product_id": 1, "quantity": 2}, True),
    ("POST", "/api/v1/cart/remove", {"product_id": 1}, True),
    ("DELETE", "/api/v1/cart/clear", None, True),
    ("POST", "/api/v1/coupon/apply", {"code": "SAVE10"}, True),
    ("POST", "/api/v1/coupon/remove", {}, True),
    ("POST", "/api/v1/checkout", {"payment_method": "COD", "address_id": 1}, True),
    ("GET", "/api/v1/wallet", None, True),
    ("POST", "/api/v1/wallet/add", {"amount": 100}, True),
    ("POST", "/api/v1/wallet/pay", {"amount": 10}, True),
    ("GET", "/api/v1/loyalty", None, True),
    ("POST", "/api/v1/loyalty/redeem", {"amount": 1}, True),
    ("GET", "/api/v1/orders", None, True),
    ("GET", "/api/v1/orders/1", None, True),
    ("POST", "/api/v1/orders/1/cancel", {}, True),
    ("GET", "/api/v1/orders/1/invoice", None, True),
    ("GET", "/api/v1/products/1/reviews", None, True),
    ("POST", "/api/v1/products/1/reviews", {"rating": 4, "comment": "good"}, True),
    ("POST", "/api/v1/support/ticket", {"subject": "Need support quickly", "message": "Need help"}, True),
    ("GET", "/api/v1/support/tickets", None, True),
    ("PUT", "/api/v1/support/tickets/1", {"status": "IN_PROGRESS"}, True),
    ("GET", "/api/v1/admin/users", None, False),
    ("GET", "/api/v1/admin/users/1", None, False),
    ("GET", "/api/v1/admin/carts", None, False),
    ("GET", "/api/v1/admin/orders", None, False),
    ("GET", "/api/v1/admin/products", None, False),
    ("GET", "/api/v1/admin/coupons", None, False),
    ("GET", "/api/v1/admin/tickets", None, False),
    ("GET", "/api/v1/admin/addresses", None, False),
]


def _case_id(case: tuple[str, str, dict | None, bool]) -> str:
    method, path, _json, user_scoped = case
    scope = "user" if user_scoped else "admin"
    return f"{method}:{path}:{scope}"


@pytest.mark.parametrize("case", ENDPOINT_CASES, ids=_case_id)
def test_missing_roll_number_returns_401_everywhere(client, case):
    method, path, payload, user_scoped = case
    headers = {"X-User-ID": "1"} if user_scoped else {}
    response = client(method, path, headers=headers, json=payload)
    assert response.status_code == 401


@pytest.mark.parametrize("case", ENDPOINT_CASES, ids=_case_id)
def test_invalid_roll_number_returns_400_everywhere(client, case):
    method, path, payload, user_scoped = case
    headers = {"X-Roll-Number": "invalid"}
    if user_scoped:
        headers["X-User-ID"] = "1"
    response = client(method, path, headers=headers, json=payload)
    assert response.status_code == 400


USER_ENDPOINT_CASES = [case for case in ENDPOINT_CASES if case[3]]


@pytest.mark.parametrize("case", USER_ENDPOINT_CASES, ids=_case_id)
def test_missing_user_id_returns_400_for_user_scoped_endpoints(client, case):
    method, path, payload, _user_scoped = case
    response = client(method, path, headers={"X-Roll-Number": "2024113020"}, json=payload)
    assert response.status_code == 400
