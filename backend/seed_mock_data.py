import uuid
import random
import argparse
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
TARGET_USERS = 50
TARGET_PRODUCTS = 200

# Fixed seed for 100% reproducible results
RANDOM_SEED = 42

VIETNAMESE_LAST_NAMES = [
    "Nguyen", "Tran", "Le", "Pham", "Hoang", "Huynh", "Phan", "Vu", "Vo",
    "Dang", "Bui", "Do", "Ho", "Ngo", "Duong", "Ly"
]
VIETNAMESE_MIDDLE_NAMES = ["Van", "Thi", "Huu", "Duc", "Minh", "Quoc", "Gia", "Thanh", "Ngoc", "Anh"]
VIETNAMESE_FIRST_NAMES = [
    "An", "Binh", "Cuong", "Dung", "Em", "Hai", "Hieu", "Hoang", "Huy",
    "Khanh", "Linh", "Long", "Minh", "Nam", "Nghia", "Phuc", "Quan", "Quang",
    "Son", "Tam", "Thai", "Thang", "Thinh", "Tien", "Toan", "Trung", "Tuan",
    "Tung", "Viet", "Vinh", "Trang", "Huong", "Mai", "Phuong", "Thao", "Ha"
]

STREETS = [
    "Nguyen Hue", "Le Duan", "Hai Ba Trung", "Pasteur", "Dien Bien Phu",
    "Nguyen Thi Minh Khai", "Vo Van Kiet", "Xo Viet Nghe Tinh", "Phan Dang Luu",
    "Hoang Van Thu", "Cong Hoa", "Nguyen Van Linh", "Huynh Tan Phat", "Pham Van Dong"
]
DISTRICTS = ["Quan 1", "Quan 3", "Quan 7", "Quan Binh Thanh", "Quan Phu Nhuan", "TP. Thu Duc"]

PRODUCT_CATALOG_TEMPLATES = [
    # 1. Rau cu qua (Vegetables & Fresh Produce)
    ("Rau cu qua", "Ca chua bi Ha Lan", "VEG-TOMATO-500G", Decimal("28000"), "Hop 500g"),
    ("Rau cu qua", "Dua leo baby Da Lat", "VEG-CUCUMBER-500G", Decimal("18000"), "Goi 500g"),
    ("Rau cu qua", "Xa lach xoan thuy canh", "VEG-LETTUCE-300G", Decimal("22000"), "Cay 300g"),
    ("Rau cu qua", "Bap cai tim Da Lat", "VEG-CABBAGE-1KG", Decimal("32000"), "Bap 1kg"),
    ("Rau cu qua", "Ca rot Da Lat huu co", "VEG-CARROT-500G", Decimal("24000"), "Tui 500g"),
    ("Rau cu qua", "Khoai tay vang Da Lat", "VEG-POTATO-1KG", Decimal("35000"), "Tui 1kg"),
    ("Rau cu qua", "Hanh tay trang cu to", "VEG-ONION-500G", Decimal("19000"), "Tui 500g"),
    ("Rau cu qua", "Bong cai xanh Baby", "VEG-BROCCOLI-400G", Decimal("38000"), "Cay 400g"),
    ("Rau cu qua", "Nam dui ga tuoi", "VEG-MUSHROOM-KING-200G", Decimal("29000"), "Khay 200g"),
    ("Rau cu qua", "Nam kim cham Han Quoc", "VEG-MUSHROOM-ENOKI-150G", Decimal("14000"), "Goi 150g"),
    ("Rau cu qua", "Ot chuong do Da Lat", "VEG-PEPPER-RED-300G", Decimal("33000"), "Qua 300g"),
    ("Rau cu qua", "Bi do ho lo hat de", "VEG-PUMPKIN-1KG", Decimal("25000"), "Qua 1kg"),
    ("Rau cu qua", "Toi co don Ly Son", "VEG-GARLIC-LYSON-250G", Decimal("65000"), "Tui 250g"),
    ("Rau cu qua", "Gung se cu nho thom", "VEG-GINGER-300G", Decimal("21000"), "Tui 300g"),
    ("Rau cu qua", "Hanh la & Ngo ri goi gia vi", "VEG-HERBS-BUNDLE", Decimal("8000"), "Bo"),

    # 2. Trai cay tuoi (Fresh Fruits)
    ("Trai cay tuoi", "Chuoi Laba Da Lat chin tu nhien", "FRUIT-BANANA-LABA-1KG", Decimal("35000"), "Nai 1kg"),
    ("Trai cay tuoi", "Tao Envy New Zealand size 70", "FRUIT-APPLE-ENVY-1KG", Decimal("139000"), "Tui 1kg"),
    ("Trai cay tuoi", "Cam sanh Ham Yen mong nuoc", "FRUIT-ORANGE-SANH-1KG", Decimal("32000"), "Kg"),
    ("Trai cay tuoi", "Dua hau ruot do khong hat", "FRUIT-WATERMELON-2KG", Decimal("45000"), "Qua 2kg"),
    ("Trai cay tuoi", "Buoi da xanh ruot hong", "FRUIT-POMELO-DAXANH-1.5KG", Decimal("75000"), "Qua 1.5kg"),
    ("Trai cay tuoi", "Xoai cat Hoa Loc Tien Giang", "FRUIT-MANGO-HOALOC-1KG", Decimal("85000"), "Kg"),
    ("Trai cay tuoi", "Thanh long ruot do Binh Thuan", "FRUIT-DRAGONFRUIT-1KG", Decimal("38000"), "Kg"),
    ("Trai cay tuoi", "Nho den khong hat My", "FRUIT-GRAPE-BLACK-500G", Decimal("115000"), "Hop 500g"),
    ("Trai cay tuoi", "Bo sap 034 Lam Dong", "FRUIT-AVOCADO-034-1KG", Decimal("60000"), "Kg"),
    ("Trai cay tuoi", "Dau tay giong Nhat Da Lat", "FRUIT-STRAWBERRY-300G", Decimal("125000"), "Hop 300g"),
    ("Trai cay tuoi", "Le nau Han Quoc gion ngot", "FRUIT-PEAR-KOREA-1KG", Decimal("95000"), "Tui 1kg"),
    ("Trai cay tuoi", "Oi nu hoang gion ngot", "FRUIT-GUAVA-1KG", Decimal("28000"), "Kg"),
    ("Trai cay tuoi", "Chom chom nhan Ben Tre", "FRUIT-RAMBUTAN-1KG", Decimal("45000"), "Kg"),
    ("Trai cay tuoi", "Mang cut Lai Thieu tuyen chon", "FRUIT-MANGOSTEEN-1KG", Decimal("110000"), "Kg"),
    ("Trai cay tuoi", "Dua xiem xanh got troc", "FRUIT-COCONUT-PEELED", Decimal("22000"), "Trai"),

    # 3. Thit & Hai san (Meat & Seafood)
    ("Thit & Hai san", "Thit ba roi heo MeatDeli 400g", "MEAT-PORK-BELLY-400G", Decimal("82000"), "Khay 400g"),
    ("Thit & Hai san", "Thit nac vai heo CP tuoi sach", "MEAT-PORK-SHOULDER-500G", Decimal("74000"), "Khay 500g"),
    ("Thit & Hai san", "Suon non heo tuoi ngon", "MEAT-PORK-RIBS-500G", Decimal("115000"), "Khay 500g"),
    ("Thit & Hai san", "Than bo Uc thai lat mong", "MEAT-BEEF-STEAK-300G", Decimal("135000"), "Khay 300g"),
    ("Thit & Hai san", "Thit bo xay tuoi sach Vissan", "MEAT-BEEF-MINCED-300G", Decimal("79000"), "Khay 300g"),
    ("Thit & Hai san", "Uc ga phi le CP khong da", "MEAT-CHICKEN-BREAST-500G", Decimal("49000"), "Khay 500g"),
    ("Thit & Hai san", "Dui toi ga tuoi CP 500g", "MEAT-CHICKEN-DRUMSTICK-500G", Decimal("42000"), "Khay 500g"),
    ("Thit & Hai san", "Ca hoi Na Uy phi le tuoi song", "FISH-SALMON-FILLET-250G", Decimal("175000"), "Khay 250g"),
    ("Thit & Hai san", "Tom the chan trang lot non", "SEAFOOD-SHRIMP-300G", Decimal("98000"), "Khay 300g"),
    ("Thit & Hai san", "Muc ong Phan Thiet lam sach", "SEAFOOD-SQUID-400G", Decimal("112000"), "Khay 400g"),
    ("Thit & Hai san", "Trung ga sach Ba Huan hop 10", "EGG-BAHUAN-10P", Decimal("34000"), "Hop 10 qua"),
    ("Thit & Hai san", "Trung ga ta thao moc hop 10", "EGG-GATA-10P", Decimal("45000"), "Hop 10 qua"),
    ("Thit & Hai san", "Trung cut sach Tien Trieu 30 qua", "EGG-QUAIL-30P", Decimal("26000"), "Hop 30 qua"),

    # 4. Sua & San pham tu sua (Dairy)
    ("Sua & San pham tu sua", "Sua tuoi tiet trung Vinamilk 100% 1L", "DAIRY-MILK-VINAMILK-1L", Decimal("38000"), "Hop 1L"),
    ("Sua & San pham tu sua", "Sua tuoi TH True Milk it duong 1L", "DAIRY-MILK-TH-1L", Decimal("41000"), "Hop 1L"),
    ("Sua & San pham tu sua", "Sua chua an co duong Vinamilk loc 4", "DAIRY-YOGURT-VNM-4P", Decimal("28000"), "Loc 4 hop"),
    ("Sua & San pham tu sua", "Sua chua uong Probi Men song 5 chai", "DAIRY-PROBI-5P", Decimal("32000"), "Loc 5 chai"),
    ("Sua & San pham tu sua", "Pho mai lat Con Bo Cuoi hop 8 lat", "DAIRY-CHEESE-LAUGHINGCOW", Decimal("42000"), "Hop 8 mieng"),
    ("Sua & San pham tu sua", "Bo lat tu nhien Anchor New Zealand", "DAIRY-BUTTER-ANCHOR-227G", Decimal("89000"), "Goi 227g"),
    ("Sua & San pham tu sua", "Sua dac co duong Ong Tho do lon", "DAIRY-CONDENSED-MILK-380G", Decimal("26000"), "Lon 380g"),
    ("Sua & San pham tu sua", "Kem tuoi Whipping Cream Tatua 500ml", "DAIRY-WHIPPING-500ML", Decimal("95000"), "Hop 500ml"),
    ("Sua & San pham tu sua", "Sua hat dau nanh Fami nguyen chat loc 6", "DAIRY-FAMI-SOY-6P", Decimal("27000"), "Loc 6 hop"),
    ("Sua & San pham tu sua", "Sua hanh nhan khong duong 137 Degrees 1L", "DAIRY-ALMOND-137-1L", Decimal("92000"), "Hop 1L"),

    # 5. Banh mi, Bua sang & Ngu coc (Bakery & Breakfast)
    ("Banh mi & Ngu coc", "Banh mi sandwich Kinh Do lat mem 500g", "BAKERY-SANDWICH-KINHDO-500G", Decimal("25000"), "Goi 500g"),
    ("Banh mi & Ngu coc", "Banh mi hoa cuc Harrys Phap 500g", "BAKERY-BRIOCHE-HARRYS-500G", Decimal("115000"), "Goi 500g"),
    ("Banh mi & Ngu coc", "Yen mach nguyen chat Quaker Oats 1kg", "BAKERY-OATS-QUAKER-1KG", Decimal("95000"), "Tui 1kg"),
    ("Banh mi & Ngu coc", "Ngu coc Granola hoa qua say kho 500g", "BAKERY-GRANOLA-BERRY-500G", Decimal("135000"), "Hu 500g"),
    ("Banh mi & Ngu coc", "Mut dau tay Bonne Maman Phap 370g", "BAKERY-JAM-STRAWBERRY-370G", Decimal("118000"), "Lo 370g"),
    ("Banh mi & Ngu coc", "Bo dau phong hat min Golden Farm 340g", "BAKERY-PEANUT-BUTTER-340G", Decimal("56000"), "Lo 340g"),
    ("Banh mi & Ngu coc", "Banh quy lua mi dinh duong AFC rau cai", "BAKERY-CRACKER-AFC-200G", Decimal("32000"), "Hop 200g"),

    # 6. Gia vi, Dau an & Do kho (Pantry, Seasonings & Grains)
    ("Gia vi & Do kho", "Gao thom ST25 Ong Cua chinh hang 5kg", "PANTRY-RICE-ST25-5KG", Decimal("195000"), "Tui 5kg"),
    ("Gia vi & Do kho", "Gao lut do Dien Bien deo thom 2kg", "PANTRY-BROWN-RICE-2KG", Decimal("68000"), "Tui 2kg"),
    ("Gia vi & Do kho", "Dau dau nanh nguyen chat Simply 1L", "PANTRY-OIL-SIMPLY-1L", Decimal("59000"), "Chai 1L"),
    ("Gia vi & Do kho", "Dau o liu Extra Virgin Filippo Berio 500ml", "PANTRY-OLIVE-OIL-500ML", Decimal("165000"), "Chai 500ml"),
    ("Gia vi & Do kho", "Nuoc mam Phu Quoc Khai Hoan 40 do dam", "PANTRY-FISH-SAUCE-500ML", Decimal("95000"), "Chai 500ml"),
    ("Gia vi & Do kho", "Nuoc tuong Maggi Dam Dac hao hang 700ml", "PANTRY-SOY-SAUCE-MAGGI-700ML", Decimal("33000"), "Chai 700ml"),
    ("Gia vi & Do kho", "Hat nem thit than xuong ong Knorr 900g", "PANTRY-KNORR-900G", Decimal("72000"), "Goi 900g"),
    ("Gia vi & Do kho", "Muoi tinh say I-ot Bac Lieu 1kg", "PANTRY-SALT-IODINE-1KG", Decimal("10000"), "Goi 1kg"),
    ("Gia vi & Do kho", "Duong tinh luyen Bien Hoa Pure 1kg", "PANTRY-SUGAR-BIENHOA-1KG", Decimal("31000"), "Goi 1kg"),
    ("Gia vi & Do kho", "Tieu den xay nguyen chat Dak Lak 100g", "PANTRY-PEPPER-BLACK-100G", Decimal("39000"), "Hu 100g"),
    ("Gia vi & Do kho", "Tuong ot cay nong Chinsu chai 500g", "PANTRY-CHILI-SAUCE-CHINSU-500G", Decimal("22000"), "Chai 500g"),
    ("Gia vi & Do kho", "Mi Hao Hao tom chua cay thung 30 goi", "PANTRY-NOODLE-HAOHAO-BOX30", Decimal("125000"), "Thung 30 goi"),
    ("Gia vi & Do kho", "Mien dong sach Tay Bac cao cap 500g", "PANTRY-VERMICELLI-500G", Decimal("46000"), "Goi 500g"),
    ("Gia vi & Do kho", "Hat sen kho Hue loai 1 250g", "PANTRY-LOTUS-SEED-250G", Decimal("88000"), "Hop 250g"),

    # 7. Do uong & Giai khat (Beverages)
    ("Do uong", "Nuoc ngot Coca-Cola thung 24 lon 320ml", "BEV-COCA-BOX24", Decimal("235000"), "Thung 24 lon"),
    ("Do uong", "Tra xanh Khong Do vi chanh loc 6 chai", "BEV-TEA-KHONGDO-6P", Decimal("54000"), "Loc 6 chai"),
    ("Do uong", "Nuoc khoang thien nhien LaVie 500ml loc 6", "BEV-WATER-LAVIE-500ML-6P", Decimal("32000"), "Loc 6 chai"),
    ("Do uong", "Nuoc cam ep Teppy tep cam tuoi loc 6 chai", "BEV-JUICE-TEPPY-6P", Decimal("55000"), "Loc 6 chai"),
    ("Do uong", "Ca phe hoa tan G7 3in1 Trung Nguyen hop 18", "BEV-COFFEE-G7-18P", Decimal("58000"), "Hop 18 goi"),
    ("Do uong", "Bia Heineken Silver thung 24 lon 330ml", "BEV-BEER-HEINEKEN-BOX24", Decimal("440000"), "Thung 24 lon"),
    ("Do uong", "Nuoc dua tuoi dong hop Cocoxim 330ml", "BEV-COCONUT-COCOXIM-330ML", Decimal("18000"), "Hop 330ml"),

    # 8. Cham soc gia dinh (Home & Personal Care)
    ("Cham soc gia dinh", "Nuoc rua chen Sunlight chanh 100 3.6kg", "HOME-SUNLIGHT-LEMON-3.6KG", Decimal("115000"), "Can 3.6kg"),
    ("Cham soc gia dinh", "Nuoc giat OMO Matic cua tren tui 3.6kg", "HOME-OMO-MATIC-3.6KG", Decimal("175000"), "Tui 3.6kg"),
    ("Cham soc gia dinh", "Nuoc lau san Sunlight huong hoa ha 3.6kg", "HOME-FLOOR-CLEANER-3.6KG", Decimal("89000"), "Can 3.6kg"),
    ("Cham soc gia dinh", "Giay ve sinh cuon cao cap Pulppy loc 10", "HOME-TISSUE-PULPPY-10R", Decimal("78000"), "Loc 10 cuon"),
    ("Cham soc gia dinh", "Nuoc xa vai Comfort mot lan xa tui 3.2L", "HOME-COMFORT-SOFTENER-3.2L", Decimal("185000"), "Tui 3.2L"),
    ("Cham soc gia dinh", "Kem danh rang Colgate Total bao ve 12h", "HOME-TOOTHPASTE-COLGATE-150G", Decimal("48000"), "Tuyp 150g"),
    ("Cham soc gia dinh", "Dau goi Clear Men sach gau mat lanh 630g", "HOME-SHAMPOO-CLEARMEN-630G", Decimal("165000"), "Chai 630g"),
    ("Cham soc gia dinh", "Sua tam duong am Dove am muot 900g", "HOME-SHOWER-DOVE-900G", Decimal("189000"), "Chai 900g"),
]


def expand_catalog_to_target(templates, target_count=200):
    """Expands base templates to exactly target_count unique products across realistic categories."""
    products_data = list(templates)
    suffix_counter = 1
    while len(products_data) < target_count:
        base_cat, base_name, base_sku, base_price, base_unit = templates[len(products_data) % len(templates)]
        variant_name = f"{base_name} (Phien ban {suffix_counter})"
        variant_sku = f"{base_sku}-V{suffix_counter}"
        price_adj = Decimal(random.choice([0.9, 0.95, 1.05, 1.10]))
        variant_price = (base_price * price_adj).quantize(Decimal("1000"))
        products_data.append((base_cat, variant_name, variant_sku, variant_price, base_unit))
        suffix_counter += 1
    return products_data[:target_count]


def clean_database(db):
    """Cleans all existing records in reverse dependency order for clean idempotent re-runs."""
    print(">>> Cleaning existing database records (idempotent run)...")
    db.query(PurchaseHistory).delete()
    db.query(OrderItem).delete()
    db.query(Order).delete()
    db.query(InventoryLevel).delete()
    db.query(Product).delete()
    db.query(Warehouse).delete()
    db.query(User).delete()
    db.commit()
    print("    Existing data wiped clean successfully.")


def seed_database(clean=False):
    # Fix seed for 100% reproducible data generation
    random.seed(RANDOM_SEED)

    print("=" * 70)
    print("FreshLoop Behavioral Grocery Seeder (Realistic Repetitive Purchases)")
    print(f"Target: {TARGET_USERS} Users, {TARGET_PRODUCTS} Products, 3 Warehouses, 8-12 Orders/User")
    print("Goal: High Repeat Purchase Rate for ALS Collaborative Filtering")
    print("=" * 70)

    db = SessionLocal()
    try:
        # Check if data already exists
        existing_users = db.query(User).count()
        if existing_users > 0:
            if clean:
                clean_database(db)
            else:
                print(f"[INFO] Database already contains {existing_users} users.")
                print("       Run with `--clean` to cleanly rebuild the database.")
                return

        # -------------------------------------------------------------
        # 1. WAREHOUSES (3 Locations)
        # -------------------------------------------------------------
        print("\n>>> 1. Creating 3 Core Warehouses...")
        warehouses = [
            Warehouse(
                warehouse_id=uuid.uuid4(),
                code="HUB-01",
                name="Central Hub Quan 1",
                location="123 Le Duan, Ben Nghe, Quan 1, TP.HCM",
                service_zone="ZONE_CENTRAL_D1_D3",
                is_active=True,
            ),
            Warehouse(
                warehouse_id=uuid.uuid4(),
                code="MART-02",
                name="FreshLoop Mini Mart Quan 7",
                location="88 Nguyen Thi Thap, Tan Phu, Quan 7, TP.HCM",
                service_zone="ZONE_SOUTH_D7_NHA_BE",
                is_active=True,
            ),
            Warehouse(
                warehouse_id=uuid.uuid4(),
                code="MART-03",
                name="FreshLoop Mini Mart Binh Thanh",
                location="45 Xo Viet Nghe Tinh, Phuong 19, Binh Thanh, TP.HCM",
                service_zone="ZONE_EAST_BINH_THANH_THU_DUC",
                is_active=True,
            ),
        ]
        db.add_all(warehouses)
        db.flush()
        print(f"    Created {len(warehouses)} warehouses successfully.")

        # -------------------------------------------------------------
        # 2. PRODUCTS (200 SKUs grouped by Category)
        # -------------------------------------------------------------
        print(f"\n>>> 2. Generating {TARGET_PRODUCTS} Products across 8 Grocery Categories...")
        full_catalog = expand_catalog_to_target(PRODUCT_CATALOG_TEMPLATES, TARGET_PRODUCTS)
        products = []
        category_map = {}  # category -> list of products

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
            category_map.setdefault(cat, []).append(p)

        db.add_all(products)
        db.flush()
        print(f"    Created {len(products)} products across {len(category_map)} categories.")

        # -------------------------------------------------------------
        # 3. INVENTORY LEVELS (600 Records: 200 Products x 3 Warehouses)
        # -------------------------------------------------------------
        print(f"\n>>> 3. Setting Inventory Levels ({len(products) * len(warehouses)} records)...")
        inventory_records = []
        for p in products:
            for wh in warehouses:
                if wh.code == "HUB-01":
                    qty = random.randint(120, 500)
                    reserved = random.randint(0, 10)
                else:
                    qty = random.randint(20, 90)
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

        # -------------------------------------------------------------
        # 4. USERS (50 Users: 1 Admin, 1 Staff, 48 Customers)
        # -------------------------------------------------------------
        print(f"\n>>> 4. Creating {TARGET_USERS} Vietnamese Users...")
        users = []
        users.append(
            User(
                user_id=uuid.uuid4(),
                email="admin@freshloop.vn",
                password_hash="pbkdf2:sha256:admin_secret_hash",
                name="Tran Huu Thang (Admin)",
                phone="0901000001",
                address="FreshLoop HQ, 123 Le Duan, Quan 1, TP.HCM",
                role="ADMIN",
            )
        )
        users.append(
            User(
                user_id=uuid.uuid4(),
                email="staff@freshloop.vn",
                password_hash="pbkdf2:sha256:staff_secret_hash",
                name="Nguyen Vu Hieu (Staff)",
                phone="0901000002",
                address="Kho HUB-01, Quan 1, TP.HCM",
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
        print(f"    Created {len(users)} users.")

        # -------------------------------------------------------------
        # 5. USER PERSONA & FAVORITE BASKET (8-15 products per customer)
        # -------------------------------------------------------------
        print("\n>>> 5. Assigning Habitual 'Favorite Baskets' (8-15 products) to each customer...")
        customer_users = [u for u in users if u.role == "CUSTOMER"]
        all_categories = list(category_map.keys())

        # user_id -> list of favorite products
        user_favorite_baskets = {}
        for u in customer_users:
            # Pick 2-3 preferred categories reflecting their lifestyle
            pref_cats = random.sample(all_categories, k=random.randint(2, 3))
            candidate_pool = []
            for c in pref_cats:
                candidate_pool.extend(category_map[c])

            # Basket size: 8 to 15 items
            basket_size = min(len(candidate_pool), random.randint(8, 15))
            basket = random.sample(candidate_pool, k=basket_size)

            # In addition, ensure 1-2 daily staple items (e.g. gạo, sữa, nước mắm, trứng)
            staple_cat = random.choice(["Gia vi & Do kho", "Sua & San pham tu sua", "Thit & Hai san"])
            staple_candidates = [p for p in category_map[staple_cat] if p not in basket]
            if staple_candidates:
                basket.append(random.choice(staple_candidates))

            user_favorite_baskets[u.user_id] = basket

        print(f"    Assigned personalized favorite baskets to {len(customer_users)} customers.")

        # -------------------------------------------------------------
        # 6. GENERATE 8-12 ORDERS PER USER ACROSS 60-90 DAYS (~1 order/week)
        # -------------------------------------------------------------
        print("\n>>> 6. Generating 8-12 Orders per User spread over 60-90 days...")
        now = datetime.now(timezone.utc)
        orders = []
        order_items = []
        order_counter = 1

        for u in customer_users:
            favorite_basket = user_favorite_baskets[u.user_id]
            outside_pool = [p for p in products if p not in favorite_basket]

            num_orders = random.randint(8, 12)
            # Generate spread timestamps roughly 5 to 8 days apart
            # Order 1 (oldest, ~80-90 days ago) to Order N (recent, ~1-3 days ago)
            current_day_offset = random.randint(75, 90)

            for order_idx in range(num_orders):
                # Decrement days offset with realistic jitter
                current_day_offset -= random.randint(5, 8)
                if current_day_offset < 1:
                    current_day_offset = random.randint(1, 3)

                order_time = now - timedelta(days=current_day_offset, hours=random.randint(1, 14), minutes=random.randint(0, 59))
                wh = random.choice(warehouses)

                # Realistic status:
                # Historical orders (>7 days ago) are finished (DELIVERED) or occasionally CANCELLED (5%)
                # Recent orders (<=7 days ago) can be DELIVERED, CONFIRMED, or PENDING
                if current_day_offset > 7:
                    status = "CANCELLED" if random.random() < 0.05 else "DELIVERED"
                else:
                    rand_status = random.random()
                    if rand_status < 0.65:
                        status = "DELIVERED"
                    elif rand_status < 0.90:
                        status = "CONFIRMED"
                    else:
                        status = "PENDING"

                # -------------------------------------------------------------
                # Order Item Selection (The Habitual Re-order Mechanism):
                # Each item in the favorite basket has 60% to 80% probability to appear!
                # -------------------------------------------------------------
                purchased_in_this_order = []
                for fav_prod in favorite_basket:
                    reorder_prob = random.uniform(0.60, 0.80)
                    if random.random() < reorder_prob:
                        purchased_in_this_order.append(fav_prod)

                # If by chance basket was empty, force at least 3 items
                if len(purchased_in_this_order) < 3:
                    purchased_in_this_order.extend(random.sample(favorite_basket, k=min(4, len(favorite_basket))))

                # Add 1 to 3 random items outside the basket (exploration / impulse)
                num_outside = random.randint(1, 3)
                purchased_in_this_order.extend(random.sample(outside_pool, k=num_outside))

                # Build Order and OrderItems
                order_id = uuid.uuid4()
                total_order_amount = Decimal("0.00")

                for prod in purchased_in_this_order:
                    qty = random.randint(1, 3)
                    unit_p = prod.unit_price  # Price snapshotting
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
                        status=status,
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
        print(f"    Created {len(orders)} total orders containing {len(order_items)} items.")

        # -------------------------------------------------------------
        # 7. AGGREGATE PURCHASE HISTORY (FEATURE STORE FOR ÂN)
        # -------------------------------------------------------------
        print("\n>>> 7. Aggregating PurchaseHistory Feature Store from FINISHED orders...")
        print("    Rule: ONLY counting finished orders (DELIVERED and CONFIRMED).")
        print("    Rule: total_purchases = number of distinct orders containing the item (Order Count).")

        # Map order_id -> order object for fast lookup
        order_dict = {o.order_id: o for o in orders}

        # (user_id, product_id) -> list of order_created_at from valid orders
        user_prod_orders = {}

        for item in order_items:
            ord_obj = order_dict[item.order_id]
            # Exclude PENDING and CANCELLED
            if ord_obj.status not in ("DELIVERED", "CONFIRMED"):
                continue

            pair = (ord_obj.user_id, item.product_id)
            user_prod_orders.setdefault(pair, []).append(ord_obj.created_at)

        purchase_history_records = []
        decay_lambda = 0.05  # daily decay factor for e^(-lambda * delta_t)

        repeat_purchase_counts = {}  # count -> number of pairs

        for (u_id, p_id), timestamps in user_prod_orders.items():
            order_frequency = len(timestamps)  # Distinct orders containing this product
            last_date = max(timestamps)
            days_ago = max(0, (now - last_date).days)

            # Exponential time-decay
            recency_score = Decimal(str(round(float(2.71828 ** (-decay_lambda * days_ago)), 4)))
            implicit_rating = Decimal(str(round(order_frequency * float(recency_score), 4)))

            purchase_history_records.append(
                PurchaseHistory(
                    history_id=uuid.uuid4(),
                    user_id=u_id,
                    product_id=p_id,
                    total_purchases=order_frequency,
                    last_purchased_at=last_date,
                    recency_score=recency_score,
                    implicit_rating=implicit_rating,
                )
            )

            repeat_purchase_counts[order_frequency] = repeat_purchase_counts.get(order_frequency, 0) + 1

        db.add_all(purchase_history_records)
        db.commit()

        # -------------------------------------------------------------
        # 8. SUMMARY STATISTICS
        # -------------------------------------------------------------
        pairs_ge_3 = sum(cnt for freq, cnt in repeat_purchase_counts.items() if freq >= 3)
        total_pairs = len(purchase_history_records)
        pct_ge_3 = (pairs_ge_3 / total_pairs * 100) if total_pairs > 0 else 0

        print("\n" + "=" * 70)
        print("SEEDING COMPLETE & VERIFIED!")
        print(f"• Users: {len(users)} ({len(customer_users)} Customers)")
        print(f"• Products: {len(products)}")
        print(f"• Warehouses: {len(warehouses)}")
        print(f"• Total Orders: {len(orders)}")
        print(f"  - Delivered/Confirmed: {sum(1 for o in orders if o.status in ('DELIVERED', 'CONFIRMED'))}")
        print(f"  - Pending/Cancelled:   {sum(1 for o in orders if o.status in ('PENDING', 'CANCELLED'))}")
        print(f"• PurchaseHistory records: {total_pairs}")
        print(f"• High Repeat Pairs (purchase_count >= 3): {pairs_ge_3} / {total_pairs} ({pct_ge_3:.1f}%)")
        print("  Distribution of repeat purchases per user-product:")
        for freq in sorted(repeat_purchase_counts.keys()):
            print(f"    - Bought in {freq:2d} orders: {repeat_purchase_counts[freq]:4d} pairs")
        print("=" * 70)

    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] Seeding failed: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FreshLoop Database Seeder")
    parser.add_argument("--clean", action="store_true", help="Clean existing data before seeding")
    args = parser.parse_args()

    seed_database(clean=args.clean)
