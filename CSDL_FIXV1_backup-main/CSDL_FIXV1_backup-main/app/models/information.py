import httpx

SUPABASE_URL = "https://gqudofrvqpesiyibtgnt.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdxdWRvZnJ2cXBlc2l5aWJ0Z250Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ0NDQ2MzgsImV4cCI6MjA2MDAyMDYzOH0.RTfN8iZBsQzCZvozVBs1jlPM5pMlq7YYMA-vHG1XMRE"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}"
}

client = httpx.AsyncClient()
