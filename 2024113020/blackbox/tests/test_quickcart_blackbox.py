"""Black-box API tests for QuickCart based only on public documentation."""

from __future__ import annotations

from uuid import uuid4

import pytest


def _extract_list(data):
    """Return a list from either direct-list or wrapped-list API responses."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("addresses", "items", "data", "results", "orders"):
            value = data.get(key)
            if isinstance(value, list):
                return value
    return []


def _ensure_address_id(client, common_headers):
    """Get an address id for checkout, creating one if needed."""
    existing = client("GET", "/api/v1/addresses", headers=common_headers)
    if existing.status_code == 200:
        addresses = _extract_list(existing.json())
        for addr in addresses:
            addr_id = addr.get("address_id", addr.get("id"))
            if addr_id is not None:
                return addr_id

    # Try documented field first.
    payload = {
        "label": "HOME",
        "street": f"Street {uuid4().hex[:8]} House",
        "city": "Hyderabad",
        "pincode": "500001",
        "is_default": True,
    }
    created = client("POST", "/api/v1/addresses", headers=common_headers, json=payload)
    if created.status_code in {200, 201}:
        data = created.json()
        body = data.get("address", data)
        addr_id = body.get("address_id", body.get("id"))
        if addr_id is not None:
            return addr_id

    # Fallback for known buggy server expecting alternate key.
    payload_alt = {
        "label": "HOME",
        "street": f"Street {uuid4().hex[:8]} House",
        "city": "Hyderabad",
        "pin_code": "500001",
        "is_default": True,
    }
    created_alt = client("POST", "/api/v1/addresses", headers=common_headers, json=payload_alt)
    if created_alt.status_code in {200, 201}:
        data = created_alt.json()
        body = data.get("address", data)
        addr_id = body.get("address_id", body.get("id"))
        if addr_id is not None:
            return addr_id

    return None


def test_missing_roll_number_header_returns_401(client):
    response = client("GET", "/api/v1/admin/products")
    assert response.status_code == 401


def test_invalid_roll_number_header_returns_400(client):
    response = client("GET", "/api/v1/admin/products", headers={"X-Roll-Number": "abc"})
    assert response.status_code == 400


def test_missing_user_id_header_on_user_endpoint_returns_400(client):
    response = client("GET", "/api/v1/profile", headers={"X-Roll-Number": "2024113020"})
    assert response.status_code == 400


def test_profile_get_success_with_valid_headers(client, common_headers):
    response = client("GET", "/api/v1/profile", headers=common_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)


def test_profile_update_rejects_invalid_phone_length(client, common_headers):
    payload = {"name": "Valid Name", "phone": "12345"}
    response = client("PUT", "/api/v1/profile", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_profile_update_rejects_too_short_name(client, common_headers):
    payload = {"name": "A", "phone": "9999999999"}
    response = client("PUT", "/api/v1/profile", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_add_address_with_invalid_label_returns_400(client, common_headers):
    payload = {
        "label": "HOSTEL",
        "street": "Street Name 123",
        "city": "Hyderabad",
        "pincode": "500001",
        "is_default": False,
    }
    response = client("POST", "/api/v1/addresses", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_add_address_with_invalid_pincode_length_returns_400(client, common_headers):
    payload = {
        "label": "HOME",
        "street": "Street Name 123",
        "city": "Hyderabad",
        "pincode": "12345",
        "is_default": False,
    }
    response = client("POST", "/api/v1/addresses", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_add_address_with_non_numeric_pincode_returns_400(client, common_headers):
    """Bug discovery: pincode must be digits-only."""
    payload = {
        "label": "HOME",
        "street": "Street Name 456",
        "city": "Hyderabad",
        "pincode": "ab12cd",
        "is_default": False,
    }
    response = client("POST", "/api/v1/addresses", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_add_address_rejects_undocumented_pin_code_field(client, common_headers):
    """Bug discovery: API should reject unknown key pin_code (expects pincode)."""
    payload = {
        "label": "HOME",
        "street": "Street Name 789",
        "city": "Hyderabad",
        "pin_code": "500001",
        "is_default": False,
    }
    response = client("POST", "/api/v1/addresses", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_add_address_with_7_digit_pincode_returns_400(client, common_headers):
    """Bug discovery: pincode longer than 6 digits should be rejected."""
    payload = {
        "label": "HOME",
        "street": "Street Name 741",
        "city": "Hyderabad",
        "pincode": "5000017",
        "is_default": False,
    }
    response = client("POST", "/api/v1/addresses", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_add_address_missing_pincode_returns_400(client, common_headers):
    """Bug discovery: address creation must reject missing pincode."""
    payload = {
        "label": "HOME",
        "street": "Street Name 911",
        "city": "Hyderabad",
        "is_default": False,
    }
    response = client("POST", "/api/v1/addresses", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_get_products_returns_only_active_products(client, common_headers):
    response = client("GET", "/api/v1/products", headers=common_headers)
    assert response.status_code == 200
    products = response.json()
    assert isinstance(products, list)
    for product in products:
        assert product.get("is_active", True) is True


def test_get_nonexistent_product_returns_404(client, common_headers):
    response = client("GET", "/api/v1/products/999999", headers=common_headers)
    assert response.status_code == 404


def test_cart_add_rejects_zero_quantity(client, common_headers):
    payload = {"product_id": 1, "quantity": 0}
    response = client("POST", "/api/v1/cart/add", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_cart_add_rejects_negative_quantity(client, common_headers):
    """Bug discovery: cart add should reject negative quantity."""
    payload = {"product_id": 1, "quantity": -1}
    response = client("POST", "/api/v1/cart/add", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_cart_add_rejects_negative_quantity(client, common_headers):
    payload = {"product_id": 1, "quantity": -2}
    response = client("POST", "/api/v1/cart/add", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_cart_update_rejects_non_positive_quantity(client, common_headers):
    payload = {"product_id": 1, "quantity": 0}
    response = client("POST", "/api/v1/cart/update", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_cart_remove_missing_product_returns_404(client, common_headers):
    payload = {"product_id": 999999}
    response = client("POST", "/api/v1/cart/remove", headers=common_headers, json=payload)
    assert response.status_code == 404


def test_wallet_add_rejects_amount_above_limit(client, common_headers):
    payload = {"amount": 100001}
    response = client("POST", "/api/v1/wallet/add", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_wallet_add_rejects_zero_amount(client, common_headers):
    payload = {"amount": 0}
    response = client("POST", "/api/v1/wallet/add", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_wallet_pay_rejects_non_positive_amount(client, common_headers):
    payload = {"amount": 0}
    response = client("POST", "/api/v1/wallet/pay", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_checkout_rejects_invalid_payment_method(client, common_headers):
    address_id = _ensure_address_id(client, common_headers)
    if address_id is None:
        pytest.skip("Could not create/find address for checkout validation.")
    payload = {
        "payment_method": "CRYPTO",
        "address_id": address_id,
    }
    response = client("POST", "/api/v1/checkout", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_checkout_rejects_empty_cart(client, common_headers):
    client("DELETE", "/api/v1/cart/clear", headers=common_headers)
    address_id = _ensure_address_id(client, common_headers)
    if address_id is None:
        pytest.skip("Could not create/find address for empty-cart checkout validation.")
    payload = {
        "payment_method": "COD",
        "address_id": address_id,
    }
    response = client("POST", "/api/v1/checkout", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_review_rejects_out_of_range_rating(client, common_headers):
    payload = {"rating": 6, "comment": "great"}
    response = client("POST", "/api/v1/products/1/reviews", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_review_rejects_empty_comment(client, common_headers):
    payload = {"rating": 4, "comment": ""}
    response = client("POST", "/api/v1/products/1/reviews", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_loyalty_redeem_rejects_zero_amount(client, common_headers):
    payload = {"amount": 0}
    response = client("POST", "/api/v1/loyalty/redeem", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_create_ticket_rejects_short_subject(client, common_headers):
    payload = {"subject": "Hi", "message": "Need help with my order"}
    response = client("POST", "/api/v1/support/ticket", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_create_ticket_rejects_too_long_message(client, common_headers):
    payload = {
        "subject": "Payment issue in checkout flow",
        "message": "a" * 501,
    }
    response = client("POST", "/api/v1/support/ticket", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_cancel_nonexistent_order_returns_404(client, common_headers):
    response = client("POST", "/api/v1/orders/999999/cancel", headers=common_headers)
    assert response.status_code == 404


def test_admin_users_requires_only_roll_header(client, admin_headers):
    response = client("GET", "/api/v1/admin/users", headers=admin_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_profile_update_rejects_non_numeric_phone_even_if_len_10(client, common_headers):
    """Bug discovery: non-numeric 10-char phone should be rejected."""
    payload = {"name": "Valid Name", "phone": "abcdefghij"}
    response = client("PUT", "/api/v1/profile", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_profile_update_rejects_phone_with_symbols(client, common_headers):
    """Bug discovery: phone should reject non-digit symbols even when length is 10."""
    payload = {"name": "Valid Name", "phone": "98@76#54$2"}
    response = client("PUT", "/api/v1/profile", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_profile_update_rejects_phone_with_spaces(client, common_headers):
    """Bug discovery: phone should reject whitespace characters."""
    payload = {"name": "Valid Name", "phone": "98765 4321"}
    response = client("PUT", "/api/v1/profile", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_address_create_accepts_valid_6_digit_pincode(client, common_headers):
    """Bug discovery: valid 6-digit pincode should be accepted."""
    payload = {
        "label": "OTHER",
        "street": f"Street {uuid4().hex[:8]} Lane",
        "city": "Hyderabad",
        "pincode": "500032",
        "is_default": False,
    }
    response = client("POST", "/api/v1/addresses", headers=common_headers, json=payload)
    assert response.status_code in {200, 201}
    data = response.json()
    # Some buggy implementations may store empty pincode despite accepting request.
    created = data.get("address", data)
    assert str(created.get("pincode", "")) == "500032"


def test_cart_total_equals_sum_of_item_subtotals(client, common_headers):
    """Bug discovery: cart total must exactly equal sum(item subtotal)."""
    client("DELETE", "/api/v1/cart/clear", headers=common_headers)

    products_resp = client("GET", "/api/v1/products", headers=common_headers)
    assert products_resp.status_code == 200
    products = products_resp.json()
    assert isinstance(products, list)
    # Prefer two different products, but fall back to one product with qty=2.
    eligible = [p for p in products if int(p.get("stock", 0)) > 0]
    if not eligible:
        pytest.skip("Need at least one in-stock product to validate cart total aggregation.")

    picks = eligible[:2]
    if len(picks) == 1 and int(picks[0].get("stock", 0)) >= 2:
        add = client(
            "POST",
            "/api/v1/cart/add",
            headers=common_headers,
            json={"product_id": picks[0]["product_id"], "quantity": 2},
        )
        assert add.status_code == 200
    else:
        for p in picks:
            add = client(
                "POST",
                "/api/v1/cart/add",
                headers=common_headers,
                json={"product_id": p["product_id"], "quantity": 1},
            )
            assert add.status_code == 200

    cart = client("GET", "/api/v1/cart", headers=common_headers)
    assert cart.status_code == 200
    body = cart.json()
    items = body.get("items", [])
    calc = sum(float(item.get("subtotal", 0)) for item in items)
    total = float(body.get("total", 0))
    assert total == calc


def test_expired_coupon_is_rejected(client, common_headers):
    """Bug discovery: EXPIRED100 should not be applied."""
    client("DELETE", "/api/v1/cart/clear", headers=common_headers)
    products_resp = client("GET", "/api/v1/products", headers=common_headers)
    assert products_resp.status_code == 200
    products = products_resp.json()
    in_stock = [p for p in products if int(p.get("stock", 0)) > 0]
    if not in_stock:
        pytest.skip("Need an in-stock product to build cart before coupon apply.")

    add = client(
        "POST",
        "/api/v1/cart/add",
        headers=common_headers,
        json={"product_id": in_stock[0]["product_id"], "quantity": 1},
    )
    assert add.status_code == 200

    response = client("POST", "/api/v1/coupon/apply", headers=common_headers, json={"code": "EXPIRED100"})
    assert response.status_code == 400


def test_checkout_cod_rejected_when_total_exceeds_5000(client, common_headers):
    """Bug discovery: COD should fail for order totals above 5000."""
    client("DELETE", "/api/v1/cart/clear", headers=common_headers)
    products_resp = client("GET", "/api/v1/products", headers=common_headers)
    assert products_resp.status_code == 200
    products = products_resp.json()
    if not products:
        pytest.skip("No products available for COD limit test.")

    # Pick highest-priced product with stock.
    ranked = sorted(
        [p for p in products if int(p.get("stock", 0)) > 0],
        key=lambda p: float(p.get("price", 0)),
        reverse=True,
    )
    if not ranked:
        pytest.skip("No in-stock product available for COD limit test.")
    item = ranked[0]

    price = float(item.get("price", 0))
    stock = int(item.get("stock", 0))
    if price <= 0:
        pytest.skip("Invalid product price for COD limit test.")

    qty = min(stock, int(5200 // price) + 1)
    if qty < 1:
        pytest.skip("Unable to construct cart above COD threshold.")

    add = client(
        "POST",
        "/api/v1/cart/add",
        headers=common_headers,
        json={"product_id": item["product_id"], "quantity": qty},
    )
    if add.status_code != 200:
        pytest.skip("Could not prepare high-value cart for COD limit test.")

    cart = client("GET", "/api/v1/cart", headers=common_headers)
    assert cart.status_code == 200
    if float(cart.json().get("total", 0)) <= 5000:
        pytest.skip("Cart total did not cross 5000; skipping COD threshold assertion.")

    address_id = _ensure_address_id(client, common_headers)
    if address_id is None:
        pytest.skip("Could not create/find address for COD threshold validation.")

    checkout = client(
        "POST",
        "/api/v1/checkout",
        headers=common_headers,
        json={"payment_method": "COD", "address_id": address_id},
    )
    assert checkout.status_code == 400


def test_cannot_cancel_delivered_order(client, common_headers):
    """Bug discovery: delivered orders should not be cancellable."""
    orders = client("GET", "/api/v1/orders", headers=common_headers)
    assert orders.status_code == 200
    delivered = None
    for order in orders.json():
        if str(order.get("status", "")).upper() == "DELIVERED":
            delivered = order
            break
    if delivered is None:
        pytest.skip("No delivered order found to validate cancel restriction.")

    cancel = client("POST", f"/api/v1/orders/{delivered['order_id']}/cancel", headers=common_headers, json={})
    assert cancel.status_code == 400


def test_review_rejects_rating_zero(client, common_headers):
    """Bug discovery: rating 0 must be rejected."""
    payload = {"rating": 0, "comment": "invalid"}
    response = client("POST", "/api/v1/products/1/reviews", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_update_address_rejects_label_change(client, common_headers):
    """Bug discovery: update endpoint should reject label change attempts."""
    address_id = _ensure_address_id(client, common_headers)
    if address_id is None:
        pytest.skip("Could not create/find address for update validation.")

    payload = {"label": "OFFICE"}
    response = client("PUT", f"/api/v1/addresses/{address_id}", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_update_address_rejects_pincode_change(client, common_headers):
    """Bug discovery: update endpoint should reject pincode change attempts."""
    address_id = _ensure_address_id(client, common_headers)
    if address_id is None:
        pytest.skip("Could not create/find address for update validation.")

    payload = {"pincode": "500099"}
    response = client("PUT", f"/api/v1/addresses/{address_id}", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_profile_update_rejects_alphanumeric_phone_len_10(client, common_headers):
    """Bug discovery: mixed alphanumeric phone should be rejected."""
    payload = {"name": "Valid Name", "phone": "98765abcde"}
    response = client("PUT", "/api/v1/profile", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_add_address_rejects_pincode_with_whitespace(client, common_headers):
    """Bug discovery: pincode should reject embedded whitespace."""
    payload = {
        "label": "HOME",
        "street": "Street Name 202",
        "city": "Hyderabad",
        "pincode": "500 01",
        "is_default": False,
    }
    response = client("POST", "/api/v1/addresses", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_cart_add_rejects_decimal_quantity(client, common_headers):
    """Bug discovery: quantity must be an integer value."""
    payload = {"product_id": 1, "quantity": 1.5}
    response = client("POST", "/api/v1/cart/add", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_profile_update_rejects_phone_with_country_code_prefix(client, common_headers):
    """Bug discovery: phone should reject +91 prefixed value when API expects 10 digits."""
    payload = {"name": "Valid Name", "phone": "+919876543210"}
    response = client("PUT", "/api/v1/profile", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_add_address_missing_city_returns_400(client, common_headers):
    """Bug discovery: address creation must reject missing city."""
    payload = {
        "label": "HOME",
        "street": "Street Name 303",
        "pincode": "500001",
        "is_default": False,
    }
    response = client("POST", "/api/v1/addresses", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_cart_update_rejects_decimal_quantity(client, common_headers):
    """Bug discovery: cart update should reject non-integer quantity."""
    payload = {"product_id": 1, "quantity": 2.25}
    response = client("POST", "/api/v1/cart/update", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_wallet_add_rejects_decimal_amount(client, common_headers):
    """Bug discovery: wallet top-up should reject fractional amount input."""
    payload = {"amount": 10.5}
    response = client("POST", "/api/v1/wallet/add", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_create_ticket_rejects_missing_message(client, common_headers):
    """Bug discovery: support ticket creation should reject missing message field."""
    payload = {"subject": "Payment issue in checkout flow"}
    response = client("POST", "/api/v1/support/ticket", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_profile_update_rejects_blank_name(client, common_headers):
    """Bug discovery: profile update should reject whitespace-only names."""
    payload = {"name": "   ", "phone": "9876543210"}
    response = client("PUT", "/api/v1/profile", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_add_address_rejects_city_with_only_digits(client, common_headers):
    """Bug discovery: city should reject numeric-only values."""
    payload = {
        "label": "HOME",
        "street": "Street Name 909",
        "city": "123456",
        "pincode": "500001",
        "is_default": False,
    }
    response = client("POST", "/api/v1/addresses", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_cart_add_rejects_string_quantity(client, common_headers):
    """Bug discovery: quantity must reject string payload values."""
    payload = {"product_id": 1, "quantity": "2"}
    response = client("POST", "/api/v1/cart/add", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_checkout_rejects_missing_address_id(client, common_headers):
    """Bug discovery: checkout should reject missing address identifier."""
    payload = {"payment_method": "COD"}
    response = client("POST", "/api/v1/checkout", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_review_rejects_decimal_rating(client, common_headers):
    """Bug discovery: rating should reject decimal values."""
    payload = {"rating": 4.5, "comment": "solid product"}
    response = client("POST", "/api/v1/products/1/reviews", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_profile_update_rejects_numeric_only_name(client, common_headers):
    """Bug discovery: numeric-only names should be rejected."""
    payload = {"name": "123456", "phone": "9876543210"}
    response = client("PUT", "/api/v1/profile", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_profile_update_rejects_name_with_symbols(client, common_headers):
    """Bug discovery: names containing only symbols should be rejected."""
    payload = {"name": "@@@###", "phone": "9876543210"}
    response = client("PUT", "/api/v1/profile", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_profile_update_rejects_phone_with_trailing_spaces(client, common_headers):
    """Bug discovery: phone with trailing spaces should be rejected."""
    payload = {"name": "Valid Name", "phone": "9876543210  "}
    response = client("PUT", "/api/v1/profile", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_profile_update_rejects_phone_with_newline(client, common_headers):
    """Bug discovery: phone containing newline should be rejected."""
    payload = {"name": "Valid Name", "phone": "98765\n4321"}
    response = client("PUT", "/api/v1/profile", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_profile_update_rejects_phone_with_tab(client, common_headers):
    """Bug discovery: phone containing tab should be rejected."""
    payload = {"name": "Valid Name", "phone": "98765\t4321"}
    response = client("PUT", "/api/v1/profile", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_profile_update_rejects_scientific_notation_phone(client, common_headers):
    """Bug discovery: scientific notation style phone must be rejected."""
    payload = {"name": "Valid Name", "phone": "1e10abcde2"}
    response = client("PUT", "/api/v1/profile", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_add_address_rejects_empty_street(client, common_headers):
    """Bug discovery: address creation should reject empty street."""
    payload = {
        "label": "HOME",
        "street": "",
        "city": "Hyderabad",
        "pincode": "500001",
        "is_default": False,
    }
    response = client("POST", "/api/v1/addresses", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_add_address_rejects_empty_city(client, common_headers):
    """Bug discovery: address creation should reject empty city."""
    payload = {
        "label": "HOME",
        "street": "Street Name 910",
        "city": "",
        "pincode": "500001",
        "is_default": False,
    }
    response = client("POST", "/api/v1/addresses", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_add_address_rejects_is_default_as_string(client, common_headers):
    """Bug discovery: is_default should reject non-boolean string values."""
    payload = {
        "label": "HOME",
        "street": "Street Name 911",
        "city": "Hyderabad",
        "pincode": "500001",
        "is_default": "false",
    }
    response = client("POST", "/api/v1/addresses", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_add_address_rejects_is_default_as_number(client, common_headers):
    """Bug discovery: is_default should reject numeric values."""
    payload = {
        "label": "HOME",
        "street": "Street Name 912",
        "city": "Hyderabad",
        "pincode": "500001",
        "is_default": 1,
    }
    response = client("POST", "/api/v1/addresses", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_add_address_rejects_pincode_as_integer(client, common_headers):
    """Bug discovery: pincode should reject integer type payload."""
    payload = {
        "label": "HOME",
        "street": "Street Name 913",
        "city": "Hyderabad",
        "pincode": 500001,
        "is_default": False,
    }
    response = client("POST", "/api/v1/addresses", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_add_address_rejects_city_with_special_chars(client, common_headers):
    """Bug discovery: city containing symbols should be rejected."""
    payload = {
        "label": "HOME",
        "street": "Street Name 914",
        "city": "Hyderabad@@",
        "pincode": "500001",
        "is_default": False,
    }
    response = client("POST", "/api/v1/addresses", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_wallet_add_rejects_amount_as_string(client, common_headers):
    """Bug discovery: wallet add should reject string amount."""
    payload = {"amount": "100"}
    response = client("POST", "/api/v1/wallet/add", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_wallet_add_rejects_amount_as_bool(client, common_headers):
    """Bug discovery: wallet add should reject boolean amount."""
    payload = {"amount": True}
    response = client("POST", "/api/v1/wallet/add", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_wallet_pay_rejects_decimal_amount(client, common_headers):
    """Bug discovery: wallet pay should reject fractional amounts."""
    payload = {"amount": 5.75}
    response = client("POST", "/api/v1/wallet/pay", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_wallet_pay_rejects_amount_as_string(client, common_headers):
    """Bug discovery: wallet pay should reject string amount."""
    payload = {"amount": "20"}
    response = client("POST", "/api/v1/wallet/pay", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_create_ticket_rejects_blank_subject(client, common_headers):
    """Bug discovery: support ticket should reject whitespace-only subject."""
    payload = {"subject": "   ", "message": "Need support for payment issue"}
    response = client("POST", "/api/v1/support/ticket", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_create_ticket_rejects_blank_message(client, common_headers):
    """Bug discovery: support ticket should reject whitespace-only message."""
    payload = {"subject": "Order issue", "message": "   "}
    response = client("POST", "/api/v1/support/ticket", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_profile_update_rejects_name_with_tab_only(client, common_headers):
    """Bug discovery: profile name should reject tab-only values."""
    payload = {"name": "\t\t", "phone": "9876543210"}
    response = client("PUT", "/api/v1/profile", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_profile_update_rejects_name_with_newline_only(client, common_headers):
    """Bug discovery: profile name should reject newline-only values."""
    payload = {"name": "\n\n", "phone": "9876543210"}
    response = client("PUT", "/api/v1/profile", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_profile_update_rejects_name_with_mixed_whitespace(client, common_headers):
    """Bug discovery: profile name should reject mixed whitespace values."""
    payload = {"name": " \t \n", "phone": "9876543210"}
    response = client("PUT", "/api/v1/profile", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_profile_update_rejects_phone_with_slashes(client, common_headers):
    """Bug discovery: phone should reject slash-separated value."""
    payload = {"name": "Valid Name", "phone": "12/34/56/7"}
    response = client("PUT", "/api/v1/profile", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_profile_update_rejects_phone_with_parentheses(client, common_headers):
    """Bug discovery: phone should reject parenthesized characters."""
    payload = {"name": "Valid Name", "phone": "(123)45678"}
    response = client("PUT", "/api/v1/profile", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_profile_update_rejects_phone_with_only_symbols(client, common_headers):
    """Bug discovery: phone should reject symbol-only values."""
    payload = {"name": "Valid Name", "phone": "!@#$%^&*()"}
    response = client("PUT", "/api/v1/profile", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_wallet_add_rejects_negative_decimal_amount(client, common_headers):
    """Bug discovery: wallet add should reject negative decimal amount."""
    payload = {"amount": -10.5}
    response = client("POST", "/api/v1/wallet/add", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_wallet_pay_rejects_negative_decimal_amount(client, common_headers):
    """Bug discovery: wallet pay should reject negative decimal amount."""
    payload = {"amount": -2.25}
    response = client("POST", "/api/v1/wallet/pay", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_create_ticket_rejects_message_with_only_newline(client, common_headers):
    """Bug discovery: support ticket should reject newline-only message."""
    payload = {"subject": "Order issue", "message": "\n"}
    response = client("POST", "/api/v1/support/ticket", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_create_ticket_rejects_message_with_only_tab(client, common_headers):
    """Bug discovery: support ticket should reject tab-only message."""
    payload = {"subject": "Order issue", "message": "\t"}
    response = client("POST", "/api/v1/support/ticket", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_profile_update_rejects_name_with_only_hyphens(client, common_headers):
    """Bug discovery: profile name should reject punctuation-only names."""
    payload = {"name": "----", "phone": "9876543210"}
    response = client("PUT", "/api/v1/profile", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_profile_update_rejects_name_with_only_underscores(client, common_headers):
    """Bug discovery: profile name should reject underscore-only names."""
    payload = {"name": "_____", "phone": "9876543210"}
    response = client("PUT", "/api/v1/profile", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_profile_update_rejects_name_with_html_tags(client, common_headers):
    """Bug discovery: profile name should reject HTML-like payloads."""
    payload = {"name": "<script>", "phone": "9876543210"}
    response = client("PUT", "/api/v1/profile", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_profile_update_rejects_name_with_sql_payload(client, common_headers):
    """Bug discovery: profile name should reject SQL-injection-like payloads."""
    payload = {"name": "' OR 1=1 --", "phone": "9876543210"}
    response = client("PUT", "/api/v1/profile", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_profile_update_rejects_name_with_unicode_symbols(client, common_headers):
    """Bug discovery: profile name should reject symbol-only unicode payloads."""
    payload = {"name": "%%%%", "phone": "9876543210"}
    response = client("PUT", "/api/v1/profile", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_profile_update_rejects_phone_with_dash_separators(client, common_headers):
    """Bug discovery: phone should reject dashed values."""
    payload = {"name": "Valid Name", "phone": "98765-4321"}
    response = client("PUT", "/api/v1/profile", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_profile_update_rejects_phone_with_dot_separators(client, common_headers):
    """Bug discovery: phone should reject dot-separated values."""
    payload = {"name": "Valid Name", "phone": "98.76.54.32"}
    response = client("PUT", "/api/v1/profile", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_profile_update_rejects_phone_with_letter_prefix(client, common_headers):
    """Bug discovery: phone should reject prefixed alphabetic characters."""
    payload = {"name": "Valid Name", "phone": "x987654321"}
    response = client("PUT", "/api/v1/profile", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_profile_update_rejects_phone_with_letter_suffix(client, common_headers):
    """Bug discovery: phone should reject suffixed alphabetic characters."""
    payload = {"name": "Valid Name", "phone": "987654321x"}
    response = client("PUT", "/api/v1/profile", headers=common_headers, json=payload)
    assert response.status_code == 400


def test_profile_update_rejects_phone_with_mixed_case_letters(client, common_headers):
    """Bug discovery: phone should reject mixed-case alphanumeric payloads."""
    payload = {"name": "Valid Name", "phone": "AbCdE12345"}
    response = client("PUT", "/api/v1/profile", headers=common_headers, json=payload)
    assert response.status_code == 400
