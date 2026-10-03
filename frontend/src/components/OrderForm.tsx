import { useState } from "react";
import type { Product, Order } from "../lib/api";
import { api, dollars } from "../lib/api";

export default function OrderForm({ products, onCreated }: { products: Product[]; onCreated: (order: Order) => void }) {
  const [email, setEmail] = useState("operator@example.com");
  const [sku, setSku] = useState(products[0]?.sku ?? "");
  const [quantity, setQuantity] = useState(1);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true); setError("");
    try {
      const order = await api.createOrder({ customer_email: email, items: [{ sku, quantity }] });
      onCreated(order);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create order");
    } finally { setBusy(false); }
  }

  const selected = products.find((item) => item.sku === sku);
  return (
    <div className="panel order-panel">
      <p className="eyebrow">Command center</p>
      <h2>Reserve inventory</h2>
      <p className="muted">Place an idempotent order and atomically reserve stock.</p>
      <form onSubmit={submit}>
        <label>Customer email<input value={email} onChange={(e) => setEmail(e.target.value)} type="email" required /></label>
        <label>Product<select value={sku} onChange={(e) => setSku(e.target.value)} required>
          {products.map((product) => <option key={product.sku} value={product.sku}>{product.name} · {dollars(product.price_cents)}</option>)}
        </select></label>
        <label>Quantity<input value={quantity} onChange={(e) => setQuantity(Number(e.target.value))} type="number" min="1" max="100" required /></label>
        {selected && <div className="availability">{selected.available_quantity} units available</div>}
        {error && <div className="error">{error}</div>}
        <button disabled={busy || products.length === 0}>{busy ? "Reserving…" : "Create reservation"}</button>
      </form>
    </div>
  );
}
