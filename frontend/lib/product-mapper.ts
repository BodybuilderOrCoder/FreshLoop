import type { Category, Product } from "../data/products";
import type { ProductInventory } from "./api";

type VisualStyle = {
  icon: string;
  color: string;
};

const categoryVisuals: Record<
  Exclude<Category, "All">,
  VisualStyle
> = {
  Produce: { icon: "🥬", color: "#eaf4d8" },
  "Dairy & Eggs": { icon: "🥛", color: "#e9f3ff" },
  "Meat & Seafood": { icon: "🍗", color: "#ffebe5" },
  Bakery: { icon: "🍞", color: "#fff0dd" },
  Pantry: { icon: "🛒", color: "#f2f0e6" },
  Beverages: { icon: "🥤", color: "#e9f3ff" },
};

/**
 * Creates a repeatable numeric ID for compatibility with existing
 * UI components that currently use number-based product IDs.
 *
 * The backend UUID remains the authoritative product identifier.
 */
function stableNumericId(value: string): number {
  let hash = 2166136261;

  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }

  return (hash >>> 0) + 1;
}

function mapCategory(
  item: ProductInventory,
): Exclude<Category, "All"> {
  const sourceCategory = item.category.toLowerCase();
  const sku = item.sku.toUpperCase();

  // Peanut butter belongs in Pantry, despite the broad source category.
  if (sku.includes("PEANUT-BUTTER")) {
    return "Pantry";
  }

  if (
    sourceCategory.includes("rau cu") ||
    sourceCategory.includes("trai cay")
  ) {
    return "Produce";
  }

  if (sourceCategory.includes("sua")) {
    return "Dairy & Eggs";
  }

  if (sourceCategory.includes("do uong")) {
    return "Beverages";
  }

  if (sourceCategory.includes("banh mi")) {
    return "Bakery";
  }

  return "Pantry";
}

export function mapInventoryProducts(
  items: ProductInventory[],
): Product[] {
  const mapped = items.map((item): Product => {
    const price = Number(item.unit_price);
    const inventoryQuantity = Number(item.available_stock);

    if (!Number.isFinite(price) || price < 0) {
      throw new Error(
        `Invalid price for product ${item.product_id}.`,
      );
    }

    const category = mapCategory(item);
    const visual = categoryVisuals[category];

    const stock =
      item.is_available && Number.isFinite(inventoryQuantity)
        ? Math.max(0, Math.floor(inventoryQuantity))
        : 0;

    return {
      id: stableNumericId(item.product_id),
      backendProductId: item.product_id,
      sku: item.sku,
      name: item.name,
      detail: `SKU: ${item.sku}`,
      price,
      unit: item.unit,
      category,
      icon: visual.icon,
      color: visual.color,
      stock,
      repeat: false,
    };
  });

  // Prevent a numeric hash collision from silently merging cart entries.
  const seenIds = new Map<number, string>();

  for (const product of mapped) {
    const backendId = product.backendProductId!;
    const existingBackendId = seenIds.get(product.id);

    if (existingBackendId && existingBackendId !== backendId) {
      throw new Error(
        `Product ID collision between ${existingBackendId} and ${backendId}.`,
      );
    }

    seenIds.set(product.id, backendId);
  }

  return mapped;
}