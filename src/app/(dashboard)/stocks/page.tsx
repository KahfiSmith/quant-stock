import { RequireAuth } from "@/components/features/auth";
import { StockList } from "@/components/features/market";

export default function StocksPage() {
  return (
    <RequireAuth>
      <div className="mx-auto flex w-full max-w-5xl flex-col gap-4 p-6">
        <header>
          <p className="text-sm font-medium text-primary">Market data</p>
          <h1 className="text-2xl font-semibold tracking-tight">Stocks</h1>
        </header>
        <StockList />
      </div>
    </RequireAuth>
  );
}