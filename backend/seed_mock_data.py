import uuid
from datetime import datetime, timezone
from decimal import Decimal
import sys
import os

# Add parent directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, SessionLocal
from app.models.schema import (
    Base,
    User,
    Product,
    Warehouse,
    InventoryLevel,
    Order,
    OrderItem,
    PurchaseHistory,
)


def seed_database():
    print("Connecting to database and creating tables...")
    # Create tables if they do not exist
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")

    db = SessionLocal()
    try:
        # Check if data already exists
        if db.query(User).first():
            print("Database already contains data. Skipping initial seeding.")
            return

        print("Seeding initial mock data...")

        # 1. Users
        user_customer = User(
            user_id=uuid.uuid4(),
            email="customer@freshloop.vn",
            password_hash="pbkdf2:sha256:mock_hash_customer",
            name="Nguyen Van A",
            phone="0901234567",
            address="123 Nguyen Hue, Quan 1, TP.HCM",
            role="CUSTOMER",
        )
        user_admin = User(
            user_id=uuid.uuid4(),
            email="admin@freshloop.vn",
            password_hash="pbkdf2:sha256:mock_hash_admin",
            name="Admin Tran",
            phone="0987654321",
            address="FreshLoop HQ, TP.HCM",
            role="ADMIN",
        )
        db.add_all([user_customer, user_admin])
        db.flush()

        # 2. Warehouses
        wh1 = Warehouse(
            warehouse_id=uuid.uuid4(),
            code="HUB-01",
            name="Central Hub Quan 1",
            location="10 Le Duan, Ben Nghe, Quan 1, TP.HCM",
            service_zone="ZONE_D1_D3",
            is_active=True,
        )
        wh2 = Warehouse(
            warehouse_id=uuid.uuid4(),
            code="MART-03",
            name="Mini Mart Binh Thanh",
            location="45 Xo Viet Nghe Tinh, Binh Thanh, TP.HCM",
            service_zone="ZONE_BT",
            is_active=True,
        )
        db.add_all([wh1, wh2])
        db.flush()

        # 3. Products
        products = [
            Product(
                product_id=uuid.uuid4(),
                sku="MILK-VINAMILK-1L",
                name="Sua tuoi tiet trung Vinamilk 100% 1L",
                category="Sua & San pham tu sua",
                unit_price=Decimal("38000.00"),
                unit="Hop",
                is_available=True,
            ),
            Product(
                product_id=uuid.uuid4(),
                sku="BREAD-TOAST-500G",
                name="Banh mi sandwich Kinh Do 500g",
                category="Banh mi & Bakery",
                unit_price=Decimal("25000.00"),
                unit="Goi",
                is_available=True,
            ),
            Product(
                product_id=uuid.uuid4(),
                sku="EGG-BAHUAN-10P",
                name="Trung ga sach Ba Huan hop 10 qua",
                category="Trung & Bo",
                unit_price=Decimal("34000.00"),
                unit="Hop",
                is_available=True,
            ),
            Product(
                product_id=uuid.uuid4(),
                sku="APPLE-ENVY-1KG",
                name="Tao Envy New Zealand nhap khau 1kg",
                category="Trai cay tuoi",
                unit_price=Decimal("120000.00"),
                unit="Kg",
                is_available=True,
            ),
            Product(
                product_id=uuid.uuid4(),
                sku="BANANA-LABA-1KG",
                name="Chuoi Laba Da Lat 1kg",
                category="Trai cay tuoi",
                unit_price=Decimal("35000.00"),
                unit="Kg",
                is_available=True,
            ),
            Product(
                product_id=uuid.uuid4(),
                sku="VEG-LETTUCE-500G",
                name="Xa lach thuy canh Da Lat 500g",
                category="Rau cu qua",
                unit_price=Decimal("22000.00"),
                unit="Goi",
                is_available=True,
            ),
        ]
        db.add_all(products)
        db.flush()

        # 4. Inventory Levels
        inventory_items = []
        for p in products:
            # Stock at Central Hub
            inventory_items.append(
                InventoryLevel(
                    inventory_id=uuid.uuid4(),
                    product_id=p.product_id,
                    warehouse_id=wh1.warehouse_id,
                    quantity=100,
                    reserved_quantity=0,
                )
            )
            # Stock at Mini Mart
            inventory_items.append(
                InventoryLevel(
                    inventory_id=uuid.uuid4(),
                    product_id=p.product_id,
                    warehouse_id=wh2.warehouse_id,
                    quantity=30,
                    reserved_quantity=2,
                )
            )
        db.add_all(inventory_items)
        db.flush()

        # 5. Sample Order & Items
        sample_order = Order(
            order_id=uuid.uuid4(),
            user_id=user_customer.user_id,
            warehouse_id=wh1.warehouse_id,
            order_number="ORD-20261018-0001",
            status="CONFIRMED",
            total_amount=Decimal("97000.00"),
            delivery_address="123 Nguyen Hue, Quan 1, TP.HCM",
        )
        db.add(sample_order)
        db.flush()

        item1 = OrderItem(
            order_item_id=uuid.uuid4(),
            order_id=sample_order.order_id,
            product_id=products[0].product_id,  # Vinamilk
            quantity=1,
            unit_price=Decimal("38000.00"),
            total_price=Decimal("38000.00"),
        )
        item2 = OrderItem(
            order_item_id=uuid.uuid4(),
            order_id=sample_order.order_id,
            product_id=products[1].product_id,  # Bread
            quantity=1,
            unit_price=Decimal("25000.00"),
            total_price=Decimal("25000.00"),
        )
        item3 = OrderItem(
            order_item_id=uuid.uuid4(),
            order_id=sample_order.order_id,
            product_id=products[2].product_id,  # Egg
            quantity=1,
            unit_price=Decimal("34000.00"),
            total_price=Decimal("34000.00"),
        )
        db.add_all([item1, item2, item3])

        # 6. Sample Purchase History (Feature Store for ML)
        for p in products[:3]:
            db.add(
                PurchaseHistory(
                    history_id=uuid.uuid4(),
                    user_id=user_customer.user_id,
                    product_id=p.product_id,
                    total_purchases=5,
                    last_purchased_at=datetime.now(timezone.utc),
                    recency_score=Decimal("0.9500"),
                    implicit_rating=Decimal("4.7500"),
                )
            )

        db.commit()
        print("Initial mock data seeded successfully!")
        print(f"-> Created {len(products)} products across 2 warehouses.")
        print(f"-> Created sample customer: {user_customer.email}")

    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
