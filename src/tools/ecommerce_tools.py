"""
E-commerce Tools for the Smart E-commerce Assistant.
Simulates real backend operations.
"""

# Mock inventory database
INVENTORY = {
    "iPhone": {"stock": 15, "price": 999.99},
    "iPad": {"stock": 8, "price": 499.99},
    "MacBook": {"stock": 5, "price": 1299.99},
    "AirPods": {"stock": 50, "price": 199.99},
}

# Mock discount codes database
DISCOUNT_CODES = {
    "WINNER": 20,  # 20% discount
    "SUMMER": 10,  # 10% discount
    "STUDENT": 15,  # 15% discount
    "INVALID": None,  # Invalid code
}

# Shipping costs per kg to destinations
SHIPPING_RATES = {
    "hanoi": {"cost_per_kg": 2.0, "base_cost": 5.0},
    "ho_chi_minh": {"cost_per_kg": 2.5, "base_cost": 5.0},
    "da_nang": {"cost_per_kg": 3.0, "base_cost": 5.0},
    "usa": {"cost_per_kg": 5.0, "base_cost": 15.0},
    "europe": {"cost_per_kg": 6.0, "base_cost": 20.0},
}

# Product weights
PRODUCT_WEIGHTS = {
    "iPhone": 0.2,  # kg
    "iPad": 0.5,
    "MacBook": 2.0,
    "AirPods": 0.1,
}


def check_stock(item_name: str) -> str:
    """
    Check stock availability for a product.
    
    Args:
        item_name: Name of the product (e.g., "iPhone")
    
    Returns:
        String describing stock status and price
    """
    item_lower = item_name.lower().strip('"')
    
    if item_lower in INVENTORY:
        stock = INVENTORY[item_lower]["stock"]
        price = INVENTORY[item_lower]["price"]
        
        if stock > 0:
            return f"Product '{item_name}' has {stock} units in stock. Price per unit: ${price}"
        else:
            return f"Product '{item_name}' is out of stock."
    else:
        return f"Product '{item_name}' not found in inventory. Available products: {list(INVENTORY.keys())}"


def get_discount(coupon_code: str) -> str:
    """
    Get discount percentage for a coupon code.
    
    Args:
        coupon_code: The discount coupon code
    
    Returns:
        String describing the discount
    """
    code_clean = coupon_code.lower().strip('"')
    
    if code_clean in DISCOUNT_CODES:
        discount_pct = DISCOUNT_CODES[code_clean]
        if discount_pct is not None:
            return f"Coupon code '{coupon_code}' provides {discount_pct}% discount."
        else:
            return f"Coupon code '{coupon_code}' is invalid and provides no discount."
    else:
        return f"Coupon code '{coupon_code}' not found. Valid codes: {list(DISCOUNT_CODES.keys())}"


def calc_shipping(weight: float, destination: str) -> str:
    """
    Calculate shipping cost for a destination.
    
    Args:
        weight: Total weight in kg
        destination: Destination city/region (e.g., "hanoi", "usa")
    
    Returns:
        String describing the shipping cost
    """
    dest_clean = destination.lower().strip('"')
    
    if dest_clean in SHIPPING_RATES:
        rate = SHIPPING_RATES[dest_clean]
        shipping_cost = rate["base_cost"] + (weight * rate["cost_per_kg"])
        return f"Shipping {weight}kg to {destination}: ${shipping_cost:.2f}"
    else:
        return f"Destination '{destination}' not supported. Available destinations: {list(SHIPPING_RATES.keys())}"


def get_tool_definitions() -> list:
    """
    Get list of tool definitions for the agent.
    
    Returns:
        List of tool dicts with name, description, and func
    """
    return [
        {
            "name": "check_stock",
            "description": "Check stock availability and price for a product. Usage: check_stock(item_name)",
            "func": check_stock
        },
        {
            "name": "get_discount",
            "description": "Get discount percentage for a coupon code. Usage: get_discount(coupon_code)",
            "func": get_discount
        },
        {
            "name": "calc_shipping",
            "description": "Calculate shipping cost for a destination. Usage: calc_shipping(weight_in_kg, destination)",
            "func": lambda args: calc_shipping_wrapper(args)
        }
    ]


def calc_shipping_wrapper(args: str) -> str:
    """
    Wrapper to parse arguments for calc_shipping from string format.
    """
    import re
    # Try to parse "weight, destination" format
    match = re.search(r'([\d.]+)\s*,\s*(["\']?)(\w+)\2', args)
    if match:
        weight = float(match.group(1))
        destination = match.group(3)
        return calc_shipping(weight, destination)
    else:
        return f"Error parsing arguments: {args}"


# Test the tools manually
if __name__ == "__main__":
    print(check_stock("iPhone"))
    print(get_discount("WINNER"))
    print(calc_shipping(2.2, "hanoi"))
