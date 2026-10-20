import uuid
import random
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import sys
import os

# Add parent directory to sys.path so app modules are resolvable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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

# Seed parameters conforming to Week 1 Task 3.3 Target Deliverables:
# 50 Users, 200 Products, 3 Warehouses, Full Inventory, Orders, Purchase History
TARGET_USERS = 50
TARGET_PRODUCTS = 200

VIETNAMESE_LAST_NAMES = [
    "Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ",
    "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Lý"
]
VIETNAMESE_MIDDLE_NAMES = ["Văn", "Thị", "Hữu", "Đức", "Minh", "Quốc", "Gia", "Thanh", "Ngọc", "Anh"]
VIETNAMESE_FIRST_NAMES = [
    "An", "Bình", "Cường", "Dũng", "Em", "Hải", "Hiếu", "Hoàng", "Huy",
    "Khánh", "Linh", "Long", "Minh", "Nam", "Nghĩa", "Phúc", "Quân", "Quang",
    "Sơn", "Tâm", "Thái", "Thắng", "Thịnh", "Tiến", "Toàn", "Trung", "Tuấn",
    "Tùng", "Việt", "Vinh", "Trang", "Hương", "Mai", "Phương", "Thảo", "Hà"
]

STREETS = [
    "Nguyễn Huệ", "Lê Duẩn", "Hai Bà Trưng", "Pasteur", "Điện Biên Phủ",
    "Nguyễn Thị Minh Khai", "Võ Văn Kiệt", "Xô Viết Nghệ Tĩnh", "Phan Đăng Lưu",
    "Hoàng Văn Thụ", "Cộng Hòa", "Nguyễn Văn Linh", "Huỳnh Tấn Phát", "Phạm Văn Đồng"
]
DISTRICTS = ["Quận 1", "Quận 3", "Quận 7", "Quận Bình Thạnh", "Quận Phú Nhuận", "TP. Thủ Đức"]

PRODUCT_CATALOG_TEMPLATES = [
    # 1. Rau củ quả (Vegetables & Fresh Produce)
    ("Rau củ quả", "Cà chua bi Hà Lan", "VEG-TOMATO-500G", Decimal("28000"), "Hộp 500g"),
    ("Rau củ quả", "Dưa leo baby Đà Lạt", "VEG-CUCUMBER-500G", Decimal("18000"), "Gói 500g"),
    ("Rau củ quả", "Xà lách xoăn thủy canh", "VEG-LETTUCE-300G", Decimal("22000"), "Cây 300g"),
    ("Rau củ quả", "Bắp cải tím Đà Lạt", "VEG-CABBAGE-1KG", Decimal("32000"), "Bắp 1kg"),
    ("Rau củ quả", "Cà rốt Đà Lạt hữu cơ", "VEG-CARROT-500G", Decimal("24000"), "Túi 500g"),
    ("Rau củ quả", "Khoai tây vàng Đà Lạt", "VEG-POTATO-1KG", Decimal("35000"), "Túi 1kg"),
    ("Rau củ quả", "Hành tây trắng củ to", "VEG-ONION-500G", Decimal("19000"), "Túi 500g"),
    ("Rau củ quả", "Bông cải xanh Baby", "VEG-BROCCOLI-400G", Decimal("38000"), "Cây 400g"),
    ("Rau củ quả", "Nấm đùi gà tươi", "VEG-MUSHROOM-KING-200G", Decimal("29000"), "Khay 200g"),
    ("Rau củ quả", "Nấm kim châm Hàn Quốc", "VEG-MUSHROOM-ENOKI-150G", Decimal("14000"), "Gói 150g"),
    ("Rau củ quả", "Ớt chuông đỏ Đà Lạt", "VEG-PEPPER-RED-300G", Decimal("33000"), "Quả 300g"),
    ("Rau củ quả", "Bí đỏ hồ lô hạt dẻ", "VEG-PUMPKIN-1KG", Decimal("25000"), "Quả 1kg"),
    ("Rau củ quả", "Tỏi cô đơn Lý Sơn", "VEG-GARLIC-LYSON-250G", Decimal("65000"), "Túi 250g"),
    ("Rau củ quả", "Gừng sẻ củ nhỏ thơm", "VEG-GINGER-300G", Decimal("21000"), "Túi 300g"),
    ("Rau củ quả", "Hành lá & Ngò rí gói gia vị", "VEG-HERBS-BUNDLE", Decimal("8000"), "Bó"),

    # 2. Trái cây tươi (Fresh Fruits)
    ("Trái cây tươi", "Chuối Laba Đà Lạt chín tự nhiên", "FRUIT-BANANA-LABA-1KG", Decimal("35000"), "Nải 1kg"),
    ("Trái cây tươi", "Táo Envy New Zealand size 70", "FRUIT-APPLE-ENVY-1KG", Decimal("139000"), "Túi 1kg"),
    ("Trái cây tươi", "Cam sành Hàm Yên mọng nước", "FRUIT-ORANGE-SANH-1KG", Decimal("32000"), "Kg"),
    ("Trái cây tươi", "Dưa hấu ruột đỏ không hạt", "FRUIT-WATERMELON-2KG", Decimal("45000"), "Quả 2kg"),
    ("Trái cây tươi", "Bưởi da xanh ruột hồng", "FRUIT-POMELO-DAXANH-1.5KG", Decimal("75000"), "Quả 1.5kg"),
    ("Trái cây tươi", "Xoài cát Hòa Lộc Tiền Giang", "FRUIT-MANGO-HOALOC-1KG", Decimal("85000"), "Kg"),
    ("Trái cây tươi", "Thanh long ruột đỏ Bình Thuận", "FRUIT-DRAGONFRUIT-1KG", Decimal("38000"), "Kg"),
    ("Trái cây tươi", "Nho đen không hạt Mỹ", "FRUIT-GRAPE-BLACK-500G", Decimal("115000"), "Hộp 500g"),
    ("Trái cây tươi", "Bơ sáp 034 Lâm Đồng", "FRUIT-AVOCADO-034-1KG", Decimal("60000"), "Kg"),
    ("Trái cây tươi", "Dâu tây giống Nhật Đà Lạt", "FRUIT-STRAWBERRY-300G", Decimal("125000"), "Hộp 300g"),
    ("Trái cây tươi", "Lê nâu Hàn Quốc giòn ngọt", "FRUIT-PEAR-KOREA-1KG", Decimal("95000"), "Túi 1kg"),
    ("Trái cây tươi", "Ổi nữ hoàng giòn ngọt", "FRUIT-GUAVA-1KG", Decimal("28000"), "Kg"),
    ("Trái cây tươi", "Chôm chôm nhãn Bến Tre", "FRUIT-RAMBUTAN-1KG", Decimal("45000"), "Kg"),
    ("Trái cây tươi", "Măng cụt Lái Thiêu tuyển chọn", "FRUIT-MANGOSTEEN-1KG", Decimal("110000"), "Kg"),
    ("Trái cây tươi", "Dừa xiêm xanh gọt trọc", "FRUIT-COCONUT-PEELED", Decimal("22000"), "Trái"),

    # 3. Thịt, Trứng & Hải sản (Meat, Eggs & Seafood)
    ("Thịt & Hải sản", "Thịt ba rọi heo MeatDeli 400g", "MEAT-PORK-BELLY-400G", Decimal("82000"), "Khay 400g"),
    ("Thịt & Hải sản", "Thịt nạc vai heo CP tươi sạch", "MEAT-PORK-SHOULDER-500G", Decimal("74000"), "Khay 500g"),
    ("Thịt & Hải sản", "Sườn non heo tươi ngon", "MEAT-PORK-RIBS-500G", Decimal("115000"), "Khay 500g"),
    ("Thịt & Hải sản", "Thăn bò Úc thái lát mỏng", "MEAT-BEEF-STEAK-300G", Decimal("135000"), "Khay 300g"),
    ("Thịt & Hải sản", "Thịt bò xay tươi sạch Vissan", "MEAT-BEEF-MINCED-300G", Decimal("79000"), "Khay 300g"),
    ("Thịt & Hải sản", "Ức gà phi lê CP không da", "MEAT-CHICKEN-BREAST-500G", Decimal("49000"), "Khay 500g"),
    ("Thịt & Hải sản", "Đùi tỏi gà tươi CP 500g", "MEAT-CHICKEN-DRUMSTICK-500G", Decimal("42000"), "Khay 500g"),
    ("Thịt & Hải sản", "Cá hồi Na Uy phi lê tươi sống", "FISH-SALMON-FILLET-250G", Decimal("175000"), "Khay 250g"),
    ("Thịt & Hải sản", "Tôm thẻ chân trắng lột nõn", "SEAFOOD-SHRIMP-300G", Decimal("98000"), "Khay 300g"),
    ("Thịt & Hải sản", "Mực ống Phan Thiết làm sạch", "SEAFOOD-SQUID-400G", Decimal("112000"), "Khay 400g"),
    ("Thịt & Hải sản", "Trứng gà sạch Ba Huân hộp 10", "EGG-BAHUAN-10P", Decimal("34000"), "Hộp 10 quả"),
    ("Thịt & Hải sản", "Trứng gà ta thảo mộc hộp 10", "EGG-GATA-10P", Decimal("45000"), "Hộp 10 quả"),
    ("Thịt & Hải sản", "Trứng cút sạch Tiên Triều 30 quả", "EGG-QUAIL-30P", Decimal("26000"), "Hộp 30 quả"),

    # 4. Sữa & Sản phẩm từ sữa (Milk & Dairy)
    ("Sữa & Sản phẩm từ sữa", "Sữa tươi tiệt trùng Vinamilk 100% 1L", "DAIRY-MILK-VINAMILK-1L", Decimal("38000"), "Hộp 1L"),
    ("Sữa & Sản phẩm từ sữa", "Sữa tươi TH True Milk ít đường 1L", "DAIRY-MILK-TH-1L", Decimal("41000"), "Hộp 1L"),
    ("Sữa & Sản phẩm từ sữa", "Sữa chua ăn có đường Vinamilk lốc 4", "DAIRY-YOGURT-VNM-4P", Decimal("28000"), "Lốc 4 hộp"),
    ("Sữa & Sản phẩm từ sữa", "Sữa chua uống Probi Men sống 5 chai", "DAIRY-PROBI-5P", Decimal("32000"), "Lốc 5 chai"),
    ("Sữa & Sản phẩm từ sữa", "Phô mai lát Con Bò Cười hộp 8 lát", "DAIRY-CHEESE-LAUGHINGCOW", Decimal("42000"), "Hộp 8 miếng"),
    ("Sữa & Sản phẩm từ sữa", "Bơ lạt tự nhiên Anchor New Zealand", "DAIRY-BUTTER-ANCHOR-227G", Decimal("89000"), "Gói 227g"),
    ("Sữa & Sản phẩm từ sữa", "Sữa đặc có đường Ông Thọ đỏ lon", "DAIRY-CONDENSED-MILK-380G", Decimal("26000"), "Lon 380g"),
    ("Sữa & Sản phẩm từ sữa", "Kem tươi Whipping Cream Tatua 500ml", "DAIRY-WHIPPING-500ML", Decimal("95000"), "Hộp 500ml"),
    ("Sữa & Sản phẩm từ sữa", "Sữa hạt đậu nành Fami nguyên chất lốc 6", "DAIRY-FAMI-SOY-6P", Decimal("27000"), "Lốc 6 hộp"),
    ("Sữa & Sản phẩm từ sữa", "Sữa hạnh nhân không đường 137 Degrees 1L", "DAIRY-ALMOND-137-1L", Decimal("92000"), "Hộp 1L"),

    # 5. Bánh mì, Bữa sáng & Ngũ cốc (Bakery & Breakfast)
    ("Bánh mì & Ngũ cốc", "Bánh mì sandwich Kinh Đô lát mềm 500g", "BAKERY-SANDWICH-KINHDO-500G", Decimal("25000"), "Gói 500g"),
    ("Bánh mì & Ngũ cốc", "Bánh mì hoa cúc Harrys Pháp 500g", "BAKERY-BRIOCHE-HARRYS-500G", Decimal("115000"), "Gói 500g"),
    ("Bánh mì & Ngũ cốc", "Yến mạch nguyên chất Quaker Oats 1kg", "BAKERY-OATS-QUAKER-1KG", Decimal("95000"), "Túi 1kg"),
    ("Bánh mì & Ngũ cốc", "Ngũ cốc Granola hoa quả sấy khô 500g", "BAKERY-GRANOLA-BERRY-500G", Decimal("135000"), "Hũ 500g"),
    ("Bánh mì & Ngũ cốc", "Mứt dâu tây Bonne Maman Pháp 370g", "BAKERY-JAM-STRAWBERRY-370G", Decimal("118000"), "Lọ 370g"),
    ("Bánh mì & Ngũ cốc", "Bơ đậu phộng hạt mịn Golden Farm 340g", "BAKERY-PEANUT-BUTTER-340G", Decimal("56000"), "Lọ 340g"),
    ("Bánh mì & Ngũ cốc", "Bánh quy lúa mì dinh dưỡng AFC rau cải", "BAKERY-CRACKER-AFC-200G", Decimal("32000"), "Hộp 200g"),

    # 6. Gia vị, Dầu ăn & Đồ khô (Pantry, Seasonings & Grains)
    ("Gia vị & Đồ khô", "Gạo thơm ST25 Ông Cua chính hãng 5kg", "PANTRY-RICE-ST25-5KG", Decimal("195000"), "Túi 5kg"),
    ("Gia vị & Đồ khô", "Gạo lứt đỏ Điện Biên dẻo thơm 2kg", "PANTRY-BROWN-RICE-2KG", Decimal("68000"), "Túi 2kg"),
    ("Gia vị & Đồ khô", "Dầu đậu nành nguyên chất Simply 1L", "PANTRY-OIL-SIMPLY-1L", Decimal("59000"), "Chai 1L"),
    ("Gia vị & Đồ khô", "Dầu ô liu Extra Virgin Filippo Berio 500ml", "PANTRY-OLIVE-OIL-500ML", Decimal("165000"), "Chai 500ml"),
    ("Gia vị & Đồ khô", "Nước mắm Phú Quốc Khải Hoàn 40 độ đạm", "PANTRY-FISH-SAUCE-500ML", Decimal("95000"), "Chai 500ml"),
    ("Gia vị & Đồ khô", "Nước tương Maggi Đậm Đặc hảo hạng 700ml", "PANTRY-SOY-SAUCE-MAGGI-700ML", Decimal("33000"), "Chai 700ml"),
    ("Gia vị & Đồ khô", "Hạt nêm thịt thăn xương ống Knorr 900g", "PANTRY-KNORR-900G", Decimal("72000"), "Gói 900g"),
    ("Gia vị & Đồ khô", "Muối tinh sấy I-ốt Bạc Liêu 1kg", "PANTRY-SALT-IODINE-1KG", Decimal("10000"), "Gói 1kg"),
    ("Gia vị & Đồ khô", "Đường tinh luyện Biên Hòa Pure 1kg", "PANTRY-SUGAR-BIENHOA-1KG", Decimal("31000"), "Gói 1kg"),
    ("Gia vị & Đồ khô", "Tiêu đen xay nguyên chất Đắk Lắk 100g", "PANTRY-PEPPER-BLACK-100G", Decimal("39000"), "Hũ 100g"),
    ("Gia vị & Đồ khô", "Tương ớt cay nồng Chinsu chai 500g", "PANTRY-CHILI-SAUCE-CHINSU-500G", Decimal("22000"), "Chai 500g"),
    ("Gia vị & Đồ khô", "Mì Hảo Hảo tôm chua cay thùng 30 gói", "PANTRY-NOODLE-HAOHAO-BOX30", Decimal("125000"), "Thùng 30 gói"),
    ("Gia vị & Đồ khô", "Miến dong sạch Tây Bắc cao cấp 500g", "PANTRY-VERMICELLI-500G", Decimal("46000"), "Gói 500g"),
    ("Gia vị & Đồ khô", "Hạt sen khô Huế loại 1 250g", "PANTRY-LOTUS-SEED-250G", Decimal("88000"), "Hộp 250g"),

    # 7. Đồ uống & Giải khát (Beverages)
    ("Đồ uống", "Nước ngọt Coca-Cola thùng 24 lon 320ml", "BEV-COCA-BOX24", Decimal("235000"), "Thùng 24 lon"),
    ("Đồ uống", "Trà xanh Không Độ vị chanh lốc 6 chai", "BEV-TEA-KHONGDO-6P", Decimal("54000"), "Lốc 6 chai"),
    ("Đồ uống", "Nước khoáng thiên nhiên LaVie 500ml lốc 6", "BEV-WATER-LAVIE-500ML-6P", Decimal("32000"), "Lốc 6 chai"),
    ("Đồ uống", "Nước cam ép Teppy tép cam tươi lốc 6 chai", "BEV-JUICE-TEPPY-6P", Decimal("55000"), "Lốc 6 chai"),
    ("Đồ uống", "Cà phê hòa tan G7 3in1 Trung Nguyên hộp 18", "BEV-COFFEE-G7-18P", Decimal("58000"), "Hộp 18 gói"),
    ("Đồ uống", "Bia Heineken Silver thùng 24 lon 330ml", "BEV-BEER-HEINEKEN-BOX24", Decimal("440000"), "Thùng 24 lon"),
    ("Đồ uống", "Nước dừa tươi đóng hộp Cocoxim 330ml", "BEV-COCONUT-COCOXIM-330ML", Decimal("18000"), "Hộp 330ml"),

    # 8. Hóa mỹ phẩm & Đồ gia dụng (Home & Personal Care)
    ("Chăm sóc gia đình", "Nước rửa chén Sunlight chanh 100 3.6kg", "HOME-SUNLIGHT-LEMON-3.6KG", Decimal("115000"), "Can 3.6kg"),
    ("Chăm sóc gia đình", "Nước giặt OMO Matic cửa trên túi 3.6kg", "HOME-OMO-MATIC-3.6KG", Decimal("175000"), "Túi 3.6kg"),
    ("Chăm sóc gia đình", "Nước lau sàn Sunlight hương hoa hạ 3.6kg", "HOME-FLOOR-CLEANER-3.6KG", Decimal("89000"), "Can 3.6kg"),
    ("Chăm sóc gia đình", "Giấy vệ sinh cuộn cao cấp Pulppy lốc 10", "HOME-TISSUE-PULPPY-10R", Decimal("78000"), "Lốc 10 cuộn"),
    ("Chăm sóc gia đình", "Nước xả vải Comfort một lần xả túi 3.2L", "HOME-COMFORT-SOFTENER-3.2L", Decimal("185000"), "Túi 3.2L"),
    ("Chăm sóc gia đình", "Kem đánh răng Colgate Total bảo vệ 12h", "HOME-TOOTHPASTE-COLGATE-150G", Decimal("48000"), "Tuýp 150g"),
    ("Chăm sóc gia đình", "Dầu gội Clear Men sạch gàu mát lạnh 630g", "HOME-SHAMPOO-CLEARMEN-630G", Decimal("165000"), "Chai 630g"),
    ("Chăm sóc gia đình", "Sữa tắm dưỡng ẩm Dove ẩm mượt 900g", "HOME-SHOWER-DOVE-900G", Decimal("189000"), "Chai 900g"),
]


def expand_catalog_to_target(templates, target_count=200):
    """Dynamically expands base templates to exactly target_count unique products."""
    products_data = list(templates)
    suffix_counter = 1
    while len(products_data) < target_count:
        base_cat, base_name, base_sku, base_price, base_unit = templates[len(products_data) % len(templates)]
        variant_name = f"{base_name} (Phiên bản {suffix_counter})"
        variant_sku = f"{base_sku}-V{suffix_counter}"
        # Slight price variation (+/- 5% to 15%)
        price_adj = Decimal(random.choice([0.9, 0.95, 1.05, 1.10]))
        variant_price = (base_price * price_adj).quantize(Decimal("1000"))
        products_data.append((base_cat, variant_name, variant_sku, variant_price, base_unit))
        suffix_counter += 1
    return products_data[:target_count]


def seed_database():
    print("=" * 60)
    print("FreshLoop Database Seeder — Week 1 Target Scale")
    print(f"Goal: {TARGET_USERS} Users, {TARGET_PRODUCTS} Products, 3 Warehouses, Orders & History")
    print("=" * 60)

    db = SessionLocal()
    try:
        # Check if users already seeded
        existing_users_count = db.query(User).count()
        if existing_users_count >= TARGET_USERS:
            print(f"[INFO] Database already contains {existing_users_count} users. Seeding skipped.")
            return

        print("\n>>> 1. Creating 3 Core Warehouses...")
        warehouses = [
            Warehouse(
                warehouse_id=uuid.uuid4(),
                code="HUB-01",
                name="Central Hub Quận 1",
                location="123 Lê Duẩn, Bến Nghé, Quận 1, TP.HCM",
                service_zone="ZONE_CENTRAL_D1_D3",
                is_active=True,
            ),
            Warehouse(
                warehouse_id=uuid.uuid4(),
                code="MART-02",
                name="FreshLoop Mini Mart Quận 7",
                location="88 Nguyễn Thị Thập, Tân Phú, Quận 7, TP.HCM",
                service_zone="ZONE_SOUTH_D7_NHA_BE",
                is_active=True,
            ),
            Warehouse(
                warehouse_id=uuid.uuid4(),
                code="MART-03",
                name="FreshLoop Mini Mart Bình Thạnh",
                location="45 Xô Viết Nghệ Tĩnh, Phường 19, Bình Thạnh, TP.HCM",
                service_zone="ZONE_EAST_BINH_THANH_THU_DUC",
                is_active=True,
            ),
        ]
        db.add_all(warehouses)
        db.flush()
        print(f"    Created {len(warehouses)} warehouses successfully.")

        print(f"\n>>> 2. Generating {TARGET_USERS} Realistic Vietnamese Users...")
        users = []
        # Predefined demo accounts
        users.append(
            User(
                user_id=uuid.uuid4(),
                email="admin@freshloop.vn",
                password_hash="pbkdf2:sha256:admin_secret_hash",
                name="Trần Hữu Thắng (Admin)",
                phone="0901000001",
                address="FreshLoop HQ, 123 Lê Duẩn, Quận 1, TP.HCM",
                role="ADMIN",
            )
        )
        users.append(
            User(
                user_id=uuid.uuid4(),
                email="staff@freshloop.vn",
                password_hash="pbkdf2:sha256:staff_secret_hash",
                name="Nguyễn Vũ Hiếu (Staff)",
                phone="0901000002",
                address="Kho HUB-01, Quận 1, TP.HCM",
                role="STAFF",
            )
        )

        for i in range(3, TARGET_USERS + 1):
            full_name = f"{random.choice(VIETNAMESE_LAST_NAMES)} {random.choice(VIETNAMESE_MIDDLE_NAMES)} {random.choice(VIETNAMESE_FIRST_NAMES)}"
            phone_num = f"09{random.randint(10000000, 99999999)}"
            email_addr = f"customer{i:03d}@freshloop.vn"
            street = f"{random.randint(10, 450)} {random.choice(STREETS)}, {random.choice(DISTRICTS)}, TP.HCM"
            users.append(
                User(
                    user_id=uuid.uuid4(),
                    email=email_addr,
                    password_hash=f"pbkdf2:sha256:mock_hash_user_{i}",
                    name=full_name,
                    phone=phone_num,
                    address=street,
                    role="CUSTOMER",
                )
            )
        db.add_all(users)
        db.flush()
        print(f"    Created {len(users)} users (1 Admin, 1 Staff, {len(users)-2} Customers).")

        print(f"\n>>> 3. Generating {TARGET_PRODUCTS} Products across 8 Grocery Categories...")
        full_catalog = expand_catalog_to_target(PRODUCT_CATALOG_TEMPLATES, TARGET_PRODUCTS)
        products = []
        for cat, name, sku, price, unit in full_catalog:
            p = Product(
                product_id=uuid.uuid4(),
                sku=sku,
                name=name,
                category=cat,
                unit_price=price,
                unit=unit,
                is_available=True,
            )
            products.append(p)
        db.add_all(products)
        db.flush()
        print(f"    Created {len(products)} products successfully.")

        print(f"\n>>> 4. Populating Inventory Levels across all 3 Warehouses ({len(products) * 3} records)...")
        inventory_records = []
        for p in products:
            for wh in warehouses:
                # Main Hub has larger stock, mini-marts have retail stock
                if wh.code == "HUB-01":
                    qty = random.randint(100, 400)
                    reserved = random.randint(0, 10)
                else:
                    qty = random.randint(15, 80)
                    reserved = random.randint(0, 4)

                inventory_records.append(
                    InventoryLevel(
                        inventory_id=uuid.uuid4(),
                        product_id=p.product_id,
                        warehouse_id=wh.warehouse_id,
                        quantity=qty,
                        reserved_quantity=reserved,
                    )
                )
        db.add_all(inventory_records)
        db.flush()
        print(f"    Created {len(inventory_records)} inventory rows.")

        print("\n>>> 5. Generating Sample Orders & Order Items (Realistic Historical Orders)...")
        orders = []
        order_items = []
        order_counter = 1

        # Generate 1 to 5 past orders for customers
        customer_users = [u for u in users if u.role == "CUSTOMER"]
        now = datetime.now(timezone.utc)

        for u in customer_users:
            num_orders = random.randint(1, 4)
            for _ in range(num_orders):
                order_days_ago = random.randint(1, 60)
                order_time = now - timedelta(days=order_days_ago, hours=random.randint(1, 12))
                wh = random.choice(warehouses)

                # Select 2 to 7 distinct products for this order
                num_items = random.randint(2, 6)
                purchased_products = random.sample(products, num_items)

                order_id = uuid.uuid4()
                total_order_amount = Decimal("0.00")

                for prod in purchased_products:
                    qty = random.randint(1, 3)
                    unit_p = prod.unit_price  # Snapshot current price
                    tot_p = unit_p * qty
                    total_order_amount += tot_p

                    order_items.append(
                        OrderItem(
                            order_item_id=uuid.uuid4(),
                            order_id=order_id,
                            product_id=prod.product_id,
                            quantity=qty,
                            unit_price=unit_p,
                            total_price=tot_p,
                        )
                    )

                orders.append(
                    Order(
                        order_id=order_id,
                        user_id=u.user_id,
                        warehouse_id=wh.warehouse_id,
                        order_number=f"ORD-2026-{order_counter:05d}",
                        status=random.choice(["DELIVERED", "DELIVERED", "DELIVERED", "CONFIRMED"]),
                        total_amount=total_order_amount,
                        delivery_address=u.address,
                        created_at=order_time,
                    )
                )
                order_counter += 1

        db.add_all(orders)
        db.flush()
        db.add_all(order_items)
        db.flush()
        print(f"    Created {len(orders)} orders containing {len(order_items)} order items.")

        print("\n>>> 6. Aggregating Purchase History Feature Store for Recommendation Baseline...")
        # Compute user-product interactions from generated orders
        interaction_counts = {}
        interaction_latest = {}

        for item in order_items:
            # find corresponding order
            ord_obj = next(o for o in orders if o.order_id == item.order_id)
            pair = (ord_obj.user_id, item.product_id)
            interaction_counts[pair] = interaction_counts.get(pair, 0) + item.quantity
            if pair not in interaction_latest or ord_obj.created_at > interaction_latest[pair]:
                interaction_latest[pair] = ord_obj.created_at

        purchase_history_records = []
        decay_lambda = 0.05  # daily decay factor for e^(-lambda * delta_t)

        for (u_id, p_id), count in interaction_counts.items():
            last_date = interaction_latest[(u_id, p_id)]
            days_ago = max(0, (now - last_date).days)
            # exponential time-decay
            recency_score = Decimal(str(round(float(2.71828 ** (-decay_lambda * days_ago)), 4)))
            implicit_rating = Decimal(str(round(count * float(recency_score), 4)))

            purchase_history_records.append(
                PurchaseHistory(
                    history_id=uuid.uuid4(),
                    user_id=u_id,
                    product_id=p_id,
                    total_purchases=count,
                    last_purchased_at=last_date,
                    recency_score=recency_score,
                    implicit_rating=implicit_rating,
                )
            )

        db.add_all(purchase_history_records)
        db.commit()
        print(f"    Created {len(purchase_history_records)} purchase history records.")

        print("\n" + "=" * 60)
        print("SEEDING COMPLETE!")
        print(f"• Users: {len(users)}")
        print(f"• Products: {len(products)}")
        print(f"• Warehouses: {len(warehouses)}")
        print(f"• Inventory rows: {len(inventory_records)}")
        print(f"• Orders: {len(orders)}")
        print(f"• Purchase history (Feature Store): {len(purchase_history_records)}")
        print("=" * 60)

    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] Seeding failed: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
