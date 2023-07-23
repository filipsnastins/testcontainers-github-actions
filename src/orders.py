from datetime import datetime

from pydantic import BaseModel


class Order(BaseModel):
    order_id: str
    customer_id: str
    products: list[str]
    created_at: datetime

    def to_json_dict(self) -> dict:
        return {
            "order_id": self.order_id,
            "customer_id": self.customer_id,
            "products": self.products,
            "created_at": self.created_at.isoformat(),
        }


class OrderCreatedEvent(BaseModel):
    event_id: str
    order_id: str
    customer_id: str
    products: list[str]
    created_at: datetime

    def to_json_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "order_id": self.order_id,
            "customer_id": self.customer_id,
            "products": self.products,
            "created_at": self.created_at.isoformat(),
        }
