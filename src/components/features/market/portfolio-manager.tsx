"use client";

import { useState } from "react";
import { toast } from "sonner";

import { StateMessage } from "@/components/common";
import {
  useAddTransaction,
  useCreatePortfolio,
  usePortfolioDetail,
  usePortfolios,
  useUpdatePortfolio,
} from "@/hooks/market";

export function PortfolioManager() {
  const { data: portfolios, isPending, isError } = usePortfolios();
  const [selectedId, setSelectedId] = useState<number | null>(null);

  const [newPortfolioName, setNewPortfolioName] = useState("");
  const [editPortfolioName, setEditPortfolioName] = useState("");
  const [editPortfolioCurrency, setEditPortfolioCurrency] = useState("");
  const createPortfolio = useCreatePortfolio();

  const [txSymbol, setTxSymbol] = useState("");
  const [txType, setTxType] = useState<"BUY" | "SELL">("BUY");
  const [txQuantity, setTxQuantity] = useState("");
  const [txPrice, setTxPrice] = useState("");
  const [txFee, setTxFee] = useState("0");

  const activeId = selectedId ?? (portfolios && portfolios.length > 0 ? portfolios[0].id : null);
  const { data: detail, isPending: isDetailPending } = usePortfolioDetail(activeId ?? 0);
  const addTx = useAddTransaction(activeId ?? 0);
  const updatePortfolio = useUpdatePortfolio(activeId ?? 0);

  const handleCreatePortfolio = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPortfolioName.trim()) return;
    try {
      const res = await createPortfolio.mutateAsync({ name: newPortfolioName.trim() });
      setNewPortfolioName("");
      setSelectedId(res.id);
      toast.success("Portfolio created");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to create portfolio");
    }
  };

  const handleUpdatePortfolio = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!(editPortfolioName.trim() || detail?.name) || !(editPortfolioCurrency.trim() || detail?.currency)) return;
    try {
      await updatePortfolio.mutateAsync({
        name: (editPortfolioName.trim() || detail?.name || "").trim(),
        currency: (editPortfolioCurrency.trim() || detail?.currency || "").toUpperCase(),
      });
      toast.success("Portfolio updated");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to update portfolio");
    }
  };

  const handleAddTransaction = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!txSymbol.trim() || !txQuantity || !txPrice) return;
    try {
      await addTx.mutateAsync({
        symbol: txSymbol.trim().toUpperCase(),
        transaction_type: txType,
        quantity: parseFloat(txQuantity),
        price: parseFloat(txPrice),
        fee: parseFloat(txFee) || 0,
      });
      setTxSymbol("");
      setTxQuantity("");
      setTxPrice("");
      toast.success("Transaction recorded");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to record transaction");
    }
  };

  if (isPending) return <StateMessage variant="loading" />;
  if (isError) return <StateMessage variant="error">Failed to load portfolios.</StateMessage>;

  return (
    <div className="flex flex-col gap-6">
      {}
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border bg-card p-4">
        <div className="flex items-center gap-3">
          <label className="text-sm font-medium text-muted-foreground">Portfolio:</label>
          <select
            className="rounded-md border bg-background px-3 py-1.5 text-sm"
            value={activeId ?? ""}
            onChange={(e) => setSelectedId(Number(e.target.value))}
          >
            {portfolios?.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} ({p.currency})
              </option>
            ))}
          </select>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <form onSubmit={handleCreatePortfolio} className="flex items-center gap-2">
            <input
              type="text"
              placeholder="New portfolio name..."
              className="rounded-md border bg-background px-3 py-1.5 text-sm"
              value={newPortfolioName}
              onChange={(e) => setNewPortfolioName(e.target.value)}
            />
            <button
              type="submit"
              disabled={createPortfolio.isPending || !newPortfolioName.trim()}
              className="rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground disabled:opacity-50"
            >
              Create
            </button>
          </form>
          {detail ? (
            <form key={detail.id} onSubmit={handleUpdatePortfolio} className="flex items-center gap-2">
              <input
                aria-label="Portfolio name"
                className="w-36 rounded-md border bg-background px-3 py-1.5 text-sm"
                value={editPortfolioName || detail.name}
                onChange={(e) => setEditPortfolioName(e.target.value)}
              />
              <input
                aria-label="Portfolio currency"
                className="w-20 rounded-md border bg-background px-3 py-1.5 text-sm uppercase"
                value={editPortfolioCurrency || detail.currency}
                onChange={(e) => setEditPortfolioCurrency(e.target.value)}
              />
              <button
                type="submit"
                disabled={updatePortfolio.isPending}
                className="rounded-md border px-3 py-1.5 text-sm font-medium disabled:opacity-50"
              >
                Save
              </button>
            </form>
          ) : null}
        </div>
      </div>

      {activeId && detail ? (
        <div className="flex flex-col gap-6">
          {}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-7">
            <div className="rounded-xl border bg-card p-4">
              <p className="text-xs text-muted-foreground">Total Cost</p>
              <p className="text-xl font-semibold">
                {detail.currency} {detail.total_cost.toLocaleString()}
              </p>
            </div>
            <div className="rounded-xl border bg-card p-4">
              <p className="text-xs text-muted-foreground">Current Value</p>
              <p className="text-xl font-semibold">
                {detail.currency} {detail.current_value.toLocaleString()}
              </p>
            </div>
            <div className="rounded-xl border bg-card p-4">
              <p className="text-xs text-muted-foreground">Unrealized PnL</p>
              <p
                className={`text-xl font-semibold ${
                  detail.total_unrealized_pnl >= 0 ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"
                }`}
              >
                {detail.currency} {detail.total_unrealized_pnl.toLocaleString()} ({detail.total_unrealized_pnl_percent}%)
              </p>
            </div>
            <div className="rounded-xl border bg-card p-4">
              <p className="text-xs text-muted-foreground">Holdings Count</p>
              <p className="text-xl font-semibold">{detail.holdings.length} Assets</p>
            </div>
            <div className="rounded-xl border bg-card p-4">
              <p className="text-xs text-muted-foreground">Realized PnL</p>
              <p className="text-xl font-semibold">{detail.currency} {detail.total_realized_pnl.toLocaleString()}</p>
            </div>
            <div className="rounded-xl border bg-card p-4">
              <p className="text-xs text-muted-foreground">Annualized Volatility</p>
              <p className="text-xl font-semibold">{detail.risk.annualized_volatility_percent}%</p>
            </div>
            <div className="rounded-xl border bg-card p-4">
              <p className="text-xs text-muted-foreground">Max Concentration</p>
              <p className="text-xl font-semibold">{detail.risk.max_holding_concentration_percent}%</p>
            </div>
          </div>

          {/* Add Transaction Form */}
          <div className="rounded-xl border bg-card p-4">
            <h3 className="mb-3 text-sm font-semibold">Record Transaction</h3>
            <form onSubmit={handleAddTransaction} className="flex flex-wrap items-center gap-3">
              <input
                type="text"
                placeholder="Symbol (e.g. BBCA)"
                className="rounded-md border bg-background px-3 py-1.5 text-sm"
                value={txSymbol}
                onChange={(e) => setTxSymbol(e.target.value)}
              />
              <select
                className="rounded-md border bg-background px-3 py-1.5 text-sm"
                value={txType}
                onChange={(e) => setTxType(e.target.value as "BUY" | "SELL")}
              >
                <option value="BUY">BUY</option>
                <option value="SELL">SELL</option>
              </select>
              <input
                type="number"
                placeholder="Quantity"
                className="w-28 rounded-md border bg-background px-3 py-1.5 text-sm"
                value={txQuantity}
                onChange={(e) => setTxQuantity(e.target.value)}
              />
              <input
                type="number"
                placeholder="Price"
                className="w-32 rounded-md border bg-background px-3 py-1.5 text-sm"
                value={txPrice}
                onChange={(e) => setTxPrice(e.target.value)}
              />
              <input
                type="number"
                placeholder="Fee"
                className="w-24 rounded-md border bg-background px-3 py-1.5 text-sm"
                value={txFee}
                onChange={(e) => setTxFee(e.target.value)}
              />
              <button
                type="submit"
                disabled={addTx.isPending}
                className="rounded-md bg-primary px-4 py-1.5 text-sm font-medium text-primary-foreground disabled:opacity-50"
              >
                Add
              </button>
            </form>
          </div>

          {/* Holdings Table */}
          <div className="overflow-hidden rounded-xl border bg-card shadow-sm">
            <h3 className="border-b bg-muted/20 px-4 py-3 text-sm font-semibold">Current Holdings</h3>
            {detail.holdings.length === 0 ? (
              <p className="p-4 text-sm text-muted-foreground">No active holdings in this portfolio yet.</p>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/40 text-left text-muted-foreground">
                    <th className="px-4 py-3 font-medium">Symbol</th>
                    <th className="px-4 py-3 font-medium">Shares</th>
                    <th className="px-4 py-3 font-medium">Avg Buy Price</th>
                    <th className="px-4 py-3 font-medium">Current Price</th>
                    <th className="px-4 py-3 font-medium">Current Value</th>
                    <th className="px-4 py-3 font-medium">Unrealized PnL</th>
                  </tr>
                </thead>
                <tbody>
                  {detail.holdings.map((h) => (
                    <tr key={h.stock_id} className="border-b last:border-0 hover:bg-muted/20">
                      <td className="px-4 py-3 font-semibold text-primary">{h.symbol}</td>
                      <td className="px-4 py-3">{h.quantity.toLocaleString()}</td>
                      <td className="px-4 py-3">{h.avg_buy_price.toLocaleString()}</td>
                      <td className="px-4 py-3">{h.current_price !== null ? h.current_price.toLocaleString() : "—"}</td>
                      <td className="px-4 py-3">{h.current_value !== null ? h.current_value.toLocaleString() : "—"}</td>
                      <td
                        className={`px-4 py-3 font-medium ${
                          (h.unrealized_pnl ?? 0) >= 0 ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"
                        }`}
                      >
                        {h.unrealized_pnl !== null ? `${h.unrealized_pnl.toLocaleString()} (${h.unrealized_pnl_percent}%)` : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      ) : isDetailPending ? (
        <StateMessage variant="loading" />
      ) : (
        <StateMessage variant="empty">Create your first portfolio above to begin tracking investments.</StateMessage>
      )}
    </div>
  );
}
