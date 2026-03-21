"""Inventory module for vehicles, parts, tools, and cash."""

from streetrace_manager.models import Car


class InventoryModule:
    """Tracks tangible assets and cash balance."""

    def __init__(self):
        self._cars: dict[str, Car] = {}
        self._parts: dict[str, int] = {}
        self._tools: dict[str, int] = {}
        self._cash_balance = 0

    def add_cash(self, amount: int) -> None:
        """Increase cash balance by a positive amount."""
        if amount < 0:
            raise ValueError("Use spend_cash for deductions.")
        self._cash_balance += amount

    def spend_cash(self, amount: int) -> None:
        """Spend cash from inventory if balance allows."""
        if amount < 0:
            raise ValueError("Amount must be non-negative.")
        if amount > self._cash_balance:
            raise ValueError("Insufficient cash balance.")
        self._cash_balance -= amount

    def cash_balance(self) -> int:
        """Return current cash balance."""
        return self._cash_balance

    def add_car(self, car_id: str, model: str) -> Car:
        """Register a car in inventory."""
        if car_id in self._cars:
            raise ValueError("Car ID already exists.")
        car = Car(car_id=car_id, model=model)
        self._cars[car_id] = car
        return car

    def get_car(self, car_id: str) -> Car | None:
        """Get a car by ID."""
        return self._cars.get(car_id)

    def list_cars(self) -> list[Car]:
        """Return all tracked cars."""
        return list(self._cars.values())

    def mark_car_damaged(self, car_id: str) -> None:
        """Mark car as damaged and unavailable."""
        car = self.get_car(car_id)
        if car is None:
            raise ValueError("Unknown car ID.")
        car.is_damaged = True
        car.is_available = False

    def repair_car(self, car_id: str) -> None:
        """Mark car as repaired and available."""
        car = self.get_car(car_id)
        if car is None:
            raise ValueError("Unknown car ID.")
        car.is_damaged = False
        car.is_available = True

    def add_part(self, part_name: str, quantity: int) -> None:
        """Increase spare parts count for part_name."""
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")
        self._parts[part_name] = self._parts.get(part_name, 0) + quantity

    def add_tool(self, tool_name: str, quantity: int) -> None:
        """Increase tool count for tool_name."""
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")
        self._tools[tool_name] = self._tools.get(tool_name, 0) + quantity
