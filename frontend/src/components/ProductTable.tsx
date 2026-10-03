import type { Product } from "../lib/api";
import { dollars } from "../lib/api";

export default function ProductTable({ products }: { products: Product[] }) {
  return (
    <div className="panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Inventory ledger</p>
          <h2>Catalog health</h2>
        </div>
        <span className="live-pill"><i /> Live</span>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr><th>Product</th><th>SKU</th><th>Price</th><th>Available</th><th>Reserved</th></tr>
          </thead>
          <tbody>
            {products.map((product) => (
              <tr key={product.id}>
                <td><strong>{product.name}</strong></td>
                <td><code>{product.sku}</code></td>
                <td>{dollars(product.price_cents)}</td>
                <td><span className={product.available_quantity < 10 ? "low-stock" : "stock"}>{product.available_quantity}</span></td>
                <td>{product.reserved_quantity}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
