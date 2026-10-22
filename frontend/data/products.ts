export type Category =
  "All" | "Produce" | "Dairy & Eggs" | "Meat & Seafood" | "Bakery" | "Pantry";
export type Product = {
  id: number;
  name: string;
  detail: string;
  price: number;
  unit: string;
  category: Exclude<Category, "All">;
  icon: string;
  color: string;
  tag?: string;
  stock: number;
  repeat?: boolean;
};

export const products: Product[] = [
  {
    id: 1,
    name: "Fresh Avocado",
    detail: "Ripe & ready to eat",
    price: 32000,
    unit: "each",
    category: "Produce",
    icon: "🥑",
    color: "#eaf4d8",
    tag: "Best seller",
    stock: 24,
    repeat: true,
  },
  {
    id: 2,
    name: "Organic Bananas",
    detail: "Locally sourced",
    price: 28000,
    unit: "bunch",
    category: "Produce",
    icon: "🍌",
    color: "#fff4d7",
    stock: 18,
    repeat: true,
  },
  {
    id: 3,
    name: "Whole Milk",
    detail: "Fresh daily · 1L",
    price: 36000,
    unit: "bottle",
    category: "Dairy & Eggs",
    icon: "🥛",
    color: "#e9f3ff",
    tag: "Popular",
    stock: 9,
    repeat: true,
  },
  {
    id: 4,
    name: "Farm Fresh Eggs",
    detail: "Free range · 10 pack",
    price: 42000,
    unit: "box",
    category: "Dairy & Eggs",
    icon: "🥚",
    color: "#fff0e5",
    stock: 30,
    repeat: true,
  },
  {
    id: 5,
    name: "Cherry Tomatoes",
    detail: "Sweet & juicy · 250g",
    price: 26000,
    unit: "pack",
    category: "Produce",
    icon: "🍅",
    color: "#ffebea",
    tag: "Fresh pick",
    stock: 12,
  },
  {
    id: 6,
    name: "Sourdough Bread",
    detail: "Baked this morning",
    price: 59000,
    unit: "loaf",
    category: "Bakery",
    icon: "🍞",
    color: "#fff0dd",
    stock: 7,
  },
  {
    id: 7,
    name: "Chicken Breast",
    detail: "Skinless · 500g",
    price: 79000,
    unit: "pack",
    category: "Meat & Seafood",
    icon: "🍗",
    color: "#ffebe5",
    stock: 5,
  },
  {
    id: 8,
    name: "Jasmine Rice",
    detail: "Premium grain · 1kg",
    price: 39000,
    unit: "bag",
    category: "Pantry",
    icon: "🍚",
    color: "#f2f0e6",
    stock: 35,
  },
];