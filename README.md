Supabase Table To Create

```

create table public.voice_calls (
  id uuid default gen_random_uuid() primary key,
  call_id text unique not null,
  caller text,
  callee text,
  status text,
  duration integer,
  transcript text,
  recording_path text,
  cost numeric,
  metadata jsonb,
  raw_payload jsonb,
  created_at timestamp with time zone default now()
);


```
