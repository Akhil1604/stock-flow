import { useEffect, useMemo, useState } from "react";
import OrderForm from "./components/OrderForm";
import ProductTable from "./components/ProductTable";
import StatCard from "./components/StatCard";
import { api, dollars, type Order, type Product } from "./lib/api";

export default function App() {
  const [products, setProducts] = useState<Product[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [error, setError] = useState("");

  async function refresh() {
    try { setProducts(await api.products()); setError(""); }
    catch (err) { setError(err instanceof Error ? err.message : "API unavailable"); }
  }
  useEffect(() => { void refresh(); }, []);

  const available = useMemo(() => products.reduce((sum, item) => sum + item.available_quantity, 0), [products]);
  const reserved = useMemo(() => products.reduce((sum, item) => sum + item.reserved_quantity, 0), [products]);
  const revenue = useMemo(() => orders.reduce((sum, item) => sum + item.total_cents, 0), [orders]);

  function handleCreated(order: Order) { setOrders((current) => [order, ...current]); void refresh(); }

  return (
    <main className="shell">
      <header className="topbar">
        <div className="brand"><span className="brand-mark">S</span><span>stock<span>flow</span></span></div>
        <div className="system-state"><i /> Event-driven inventory control</div>
      </header>
      <section className="hero">
        <div><p className="eyebrow">Operations console · local environment</p><h1>Make every unit count.</h1><p className="hero-copy">A reliable order workflow that protects inventory from overselling while keeping every state change auditable.</p></div>
        <div className="hero-meta"><span>PostgreSQL</span><span>Redis</span><span>Kafka</span></div>
      </section>
      <section className="stats">
        <StatCard label="Available units" value={available} tone="blue" />
        <StatCard label="Reserved units" value={reserved} tone="amber" />
        <StatCard label="Session revenue" value={dollars(revenue)} tone="green" />
        <StatCard label="Orders created" value={orders.length} tone="blue" />
      </section>
      {error && <div className="banner error">Start the API with <code>make dev</code> to load the console. {error}</div>}
      <section className="content-grid">
        <ProductTable products={products} />
        <OrderForm products={products} onCreated={handleCreated} />
      </section>
      <section className="panel event-panel">
        <div className="panel-heading"><div><p className="eyebrow">This session</p><h2>Recent order events</h2></div><span className="muted">Outbox → Kafka</span></div>
        {orders.length === 0 ? <div className="empty">No events yet. Create a reservation to see the flow.</div> : <div className="events">{orders.map((order) => <div className="event" key={order.id}><span className="event-dot" /><div><strong>order.confirmed</strong><span>{order.id.slice(0, 8)} · {order.customer_email}</span></div><b>{dollars(order.total_cents)}</b></div>)}</div>}
      </section>
      <footer>StockFlow · reliable inventory reservation demo · <a href="http://localhost:8000/docs" target="_blank">API documentation ↗</a></footer>
    </main>
  );
}
