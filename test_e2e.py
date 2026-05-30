"""End-to-end test using FastAPI's TestClient — no live server required."""
import os
# Use a fresh SQLite DB for testing
os.environ["DATABASE_URL"] = "sqlite:///./test_e2e.db"
if os.path.exists("test_e2e.db"):
    os.remove("test_e2e.db")

from fastapi.testclient import TestClient
from main import app

c = TestClient(app)

print("=" * 60)
print("OnyxAlways Orders — End-to-End Test")
print("=" * 60)

# 1) Health check
r = c.get("/api/health")
assert r.status_code == 200, r.text
print(f"✓ Health: {r.json()}")

# 2) Empty list
r = c.get("/api/orders")
assert r.status_code == 200 and r.json() == []
print(f"✓ Empty list returns []")

# 3) Create order
r = c.post("/api/orders", json={
    "client_name": "Marcus T.",
    "description": "25 black tees, gold chest logo, sizes M-XXL",
    "item_type": "T-Shirt",
    "quantity": 25,
    "material_cost": 87.50,
    "labor_cost": 75.00,
    "sale_price": 375.00,
    "due_date": "2026-06-15",
})
assert r.status_code == 201, r.text
o1 = r.json()
print(f"✓ Created order #{o1['id']}: {o1['client_name']}")
print(f"  status={o1['status']} cost=${o1['total_cost']} price=${o1['sale_price']} profit=${o1['profit']}")
assert o1["status"] == "NEW_ORDER"
assert float(o1["total_cost"]) == 162.50
assert float(o1["profit"]) == 212.50

# 4) Create second order
r = c.post("/api/orders", json={
    "client_name": "Jasmine L.",
    "description": "Custom door panel, gold lettering",
    "item_type": "Door",
    "quantity": 1,
    "material_cost": 120,
    "labor_cost": 80,
    "sale_price": 450,
})
assert r.status_code == 201
o2 = r.json()
print(f"✓ Created order #{o2['id']}: {o2['client_name']} profit=${o2['profit']}")

# 5) Advance order 1 through all 4 stages
expected = ["DESIGNING_APPROVAL", "PRODUCTION", "COMPLETE"]
for exp_status in expected:
    r = c.post(f"/api/orders/{o1['id']}/advance")
    assert r.status_code == 200, r.text
    assert r.json()["status"] == exp_status
    print(f"✓ Advanced order #{o1['id']} → {exp_status}")

# 6) Verify completed_at was stamped
r = c.get(f"/api/orders/{o1['id']}")
assert r.json()["completed_at"] is not None
print(f"✓ completed_at stamped: {r.json()['completed_at']}")

# 7) Advancing past COMPLETE should 400
r = c.post(f"/api/orders/{o1['id']}/advance")
assert r.status_code == 400
print(f"✓ Cannot advance past COMPLETE (got 400 as expected)")

# 8) Regress should clear completed_at
r = c.post(f"/api/orders/{o1['id']}/regress")
assert r.status_code == 200
assert r.json()["status"] == "PRODUCTION"
assert r.json()["completed_at"] is None
print(f"✓ Regress clears completed_at, status={r.json()['status']}")

# 9) Re-advance to complete for summary test
r = c.post(f"/api/orders/{o1['id']}/advance")
assert r.json()["status"] == "COMPLETE"

# 10) Summary
r = c.get("/api/summary")
s = r.json()
print(f"✓ Summary: {s}")
assert s["active_orders"] == 1    # order 2 is still NEW_ORDER
assert s["completed_orders"] == 1
assert float(s["outstanding_revenue"]) == 450.0  # order 2's sale price
assert float(s["lifetime_profit"]) == 212.50      # order 1's profit

# 11) PATCH update
r = c.patch(f"/api/orders/{o2['id']}", json={"sale_price": 500, "notes": "Rush job"})
assert r.status_code == 200
assert float(r.json()["sale_price"]) == 500
assert r.json()["notes"] == "Rush job"
print(f"✓ PATCH updated sale_price to $500, notes set")

# 12) Filter by status
r = c.get("/api/orders?status_filter=NEW_ORDER")
assert r.status_code == 200
assert len(r.json()) == 1
print(f"✓ Filter by status returns {len(r.json())} order(s)")

# 13) Frontend serves
r = c.get("/")
assert r.status_code == 200
assert "OnyxAlways" in r.text
assert "<!DOCTYPE html>" in r.text
print(f"✓ Frontend HTML serves ({len(r.text):,} bytes)")

# 14) Delete
r = c.delete(f"/api/orders/{o2['id']}")
assert r.status_code == 204
r = c.get(f"/api/orders/{o2['id']}")
assert r.status_code == 404
print(f"✓ DELETE works, follow-up GET returns 404")

# 15) Validation: missing required field
r = c.post("/api/orders", json={"description": "no client name"})
assert r.status_code == 422
print(f"✓ Validation rejects missing client_name with 422")

print("=" * 60)
print("ALL TESTS PASSED")
print("=" * 60)

# Cleanup
os.remove("test_e2e.db")
