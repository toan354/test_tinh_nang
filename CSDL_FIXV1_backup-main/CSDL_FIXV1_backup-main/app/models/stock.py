# models/combined_model.py
from vnstock import Vnstock
from datetime import datetime
from supabase import create_client
import pandas as pd

# Cấu hình Supabase
url = "https://lmibkxgbkvwcegromqvi.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxtaWJreGdia3Z3Y2Vncm9tcXZpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ0NDYxOTQsImV4cCI6MjA2MDAyMjE5NH0.pH9R0eGaT-PnNTRsisHk3eH2WfmBa-ba9X_ZnrYFnak"

supabase = create_client(url, key)

class StockModel:
    def __init__(self, symbol):
        self.symbol = symbol
        self.company = Vnstock().stock(symbol=symbol, source='TCBS')
        self.quote = Vnstock().stock(symbol=symbol, source='VCI')

    # Phần đã có
    def get_company_profile(self):
        df = self.company.company.profile()
        return df["company_profile"].iloc[0], df["key_developments"].iloc[0]

    def get_officers_html(self):
        df = self.company.company.officers()
        return df[["officer_name", "officer_position"]].to_html(index=False, border=0)

    def get_shareholders_html(self):
        df = self.company.company.shareholders()
        if "Khác" in df["share_holder"].values:
            known_share = df[df["share_holder"] != "Khác"]["share_own_percent"].sum()
            df.loc[df['share_holder'] == 'Khác', 'share_own_percent'] = round(1.0 - known_share, 4)
        return df[["share_holder", "share_own_percent"]].to_html(index=False, border=0)

    # Phần thêm vào
    def get_realtime_data(self):
        today = datetime.today().strftime('%Y-%m-%d')
        df = self.quote.quote.history(start="2025-05-04", end=today).sort_values("time", ascending=False)
        df["change"] = df["close"].diff(-1).fillna(0)
        df["percent_change"] = df["change"] / df["close"].shift(-1).fillna(1) * 100
        df["change"] = df["change"].round(2)
        df["percent_change"] = df["percent_change"].round(2)
        return df.to_dict(orient="records")

    def get_saved_transactions(self):
        res = supabase.table("stocks").select("stock_id").eq("symbol", self.symbol).single().execute()
        if not res.data:
            return []
        stock_id = res.data["stock_id"]
        rows = supabase.table("transaction_price").select("*").eq("stock_id", stock_id).order("time", desc=True).execute().data
        
        # Bỏ qua dòng đầu tiên và chỉ lấy từ dòng thứ 2 trở đi
        if len(rows) > 1:
            rows = rows[1:]
            
        # Tính toán thay đổi giá
        for i in range(len(rows) - 1):
            curr = rows[i]
            prev = rows[i + 1]
            change = curr["close"] - prev["close"]
            curr["change"] = round(change, 2)
            curr["percent_change"] = round((change / prev["close"] * 100), 2) if prev["close"] != 0 else 0
        if rows:
            rows[-1]["change"] = 0
            rows[-1]["percent_change"] = 0
        return rows
# bản chuẩn