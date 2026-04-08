"""Pydantic validation schemas for Olist dataset (9 CSV tables).

Each model maps 1:1 to the CSV column headers from the Olist Brazilian
E-Commerce dataset.  Used for row-level validation before writing to
MinIO / PostgreSQL bronze layer.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# 1. Orders
# ---------------------------------------------------------------------------
class OlistOrder(BaseModel):
    order_id: str
    customer_id: str
    order_status: str
    order_purchase_timestamp: datetime
    order_approved_at: Optional[datetime] = None
    order_delivered_carrier_date: Optional[datetime] = None
    order_delivered_customer_date: Optional[datetime] = None
    order_estimated_delivery_date: Optional[datetime] = None


# ---------------------------------------------------------------------------
# 2. Order Items
# ---------------------------------------------------------------------------
class OlistOrderItem(BaseModel):
    order_id: str
    order_item_id: int
    product_id: str
    seller_id: str
    shipping_limit_date: datetime
    price: float
    freight_value: float


# ---------------------------------------------------------------------------
# 3. Customers
# ---------------------------------------------------------------------------
class OlistCustomer(BaseModel):
    customer_id: str
    customer_unique_id: str
    customer_zip_code_prefix: str
    customer_city: str
    customer_state: str


# ---------------------------------------------------------------------------
# 4. Products
# ---------------------------------------------------------------------------
class OlistProduct(BaseModel):
    product_id: str
    product_category_name: Optional[str] = None
    product_name_lenght: Optional[float] = None  # sic — typo in original dataset
    product_description_lenght: Optional[float] = None
    product_photos_qty: Optional[float] = None
    product_weight_g: Optional[float] = None
    product_length_cm: Optional[float] = None
    product_height_cm: Optional[float] = None
    product_width_cm: Optional[float] = None


# ---------------------------------------------------------------------------
# 5. Sellers
# ---------------------------------------------------------------------------
class OlistSeller(BaseModel):
    seller_id: str
    seller_zip_code_prefix: str
    seller_city: str
    seller_state: str


# ---------------------------------------------------------------------------
# 6. Payments
# ---------------------------------------------------------------------------
class OlistPayment(BaseModel):
    order_id: str
    payment_sequential: int
    payment_type: str
    payment_installments: int
    payment_value: float


# ---------------------------------------------------------------------------
# 7. Reviews
# ---------------------------------------------------------------------------
class OlistReview(BaseModel):
    review_id: str
    order_id: str
    review_score: int
    review_comment_title: Optional[str] = None
    review_comment_message: Optional[str] = None
    review_creation_date: Optional[datetime] = None
    review_answer_timestamp: Optional[datetime] = None

    @field_validator("review_score")
    @classmethod
    def score_range(cls, v: int) -> int:
        if not 1 <= v <= 5:
            raise ValueError(f"review_score must be 1-5, got {v}")
        return v


# ---------------------------------------------------------------------------
# 8. Geolocation
# ---------------------------------------------------------------------------
class OlistGeolocation(BaseModel):
    geolocation_zip_code_prefix: str
    geolocation_lat: float
    geolocation_lng: float
    geolocation_city: str
    geolocation_state: str


# ---------------------------------------------------------------------------
# 9. Category Translation
# ---------------------------------------------------------------------------
class OlistCategoryTranslation(BaseModel):
    product_category_name: str
    product_category_name_english: str


# ---------------------------------------------------------------------------
# Registry: table name → (CSV filename, schema class)
# ---------------------------------------------------------------------------
OLIST_TABLES: dict[str, tuple[str, type[BaseModel]]] = {
    "orders":                ("olist_orders_dataset.csv",          OlistOrder),
    "order_items":           ("olist_order_items_dataset.csv",     OlistOrderItem),
    "customers":             ("olist_customers_dataset.csv",       OlistCustomer),
    "products":              ("olist_products_dataset.csv",        OlistProduct),
    "sellers":               ("olist_sellers_dataset.csv",         OlistSeller),
    "payments":              ("olist_order_payments_dataset.csv",  OlistPayment),
    "reviews":               ("olist_order_reviews_dataset.csv",   OlistReview),
    "geolocation":           ("olist_geolocation_dataset.csv",     OlistGeolocation),
    "category_translation":  ("product_category_name_translation.csv", OlistCategoryTranslation),
}
